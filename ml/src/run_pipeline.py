import json
import sys
import argparse
from pathlib import Path

# Set up paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))
from config import RESOURCES, CHUNKS, QA, TRAINED_DIR, CANDIDATE_DIR, METRICS, chunk_text
from embedding_cache import load_or_create_embeddings


def load_cached_base_retriever():
    """Load the downloaded MiniLM snapshot without requiring internet access."""
    from huggingface_hub import snapshot_download
    from sentence_transformers import SentenceTransformer

    try:
        local_path = snapshot_download(
            repo_id="sentence-transformers/all-MiniLM-L6-v2",
            local_files_only=True,
        )
    except Exception as exc:
        raise RuntimeError(
            "The all-MiniLM-L6-v2 base model is not available in the local Hugging Face cache. "
            "Download it once with internet access, then rerun the candidate training."
        ) from exc
    return SentenceTransformer(local_path)


def step_1_prepare_knowledge_base():
    print("=" * 60)
    print("STEP 1: Preparing knowledge base (chunking documents)...")
    print("=" * 60)
    records = []
    md_files = sorted(RESOURCES.glob("*.md"))
    for path in md_files:
        text = path.read_text(encoding="utf-8")
        title = text.strip().splitlines()[0].lstrip("# ").strip()
        resource_id = path.stem
        for i, chunk in enumerate(chunk_text(text)):
            records.append({
                "chunk_id": f"{resource_id}_{i}",
                "resource_id": resource_id,
                "title": title,
                "content": chunk,
            })

    # This synthetic pathway library is the only structured career dataset
    # used by the advice retrieval pipeline. Downloaded source-derived exports
    # are intentionally excluded from runtime advice.
    dataset = ROOT / "data" / "synthetic" / "career_feedback_dataset.jsonl"
    if not dataset.is_file():
        raise FileNotFoundError(f"Synthetic career dataset is missing: {dataset}. Run ml/src/build_synthetic_career_dataset.py first.")
    pathways = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    occupation_chunks = 0
    for item in pathways:
        fields = [
            f"Career pathway: {item['occupation_title']} ({item['sector']}).",
            f"Synthetic illustrative data: {item['limitations']}",
            f"Overview: {item['role_summary']}",
        ]
        for label, key in (
            ("Related courses", "related_courses"),
            ("Requirements and qualification notes", "requirements_and_qualification_notes"),
            ("Interest signals", "interest_signals"),
            ("Skills", "skills"), ("Preferred activities", "preferred_activities"),
            ("Example entry roles", "entry_level_roles"), ("Preparation ideas", "preparation_pathway"),
            ("Projects and practice", "portfolio_or_practice_ideas"),
            ("Application channel types", "application_channel_types"),
            ("Sample interview questions", "sample_interview_questions"),
            ("Example student questions", "example_student_queries"),
            ("CV tailoring", "cv_tailoring_guidance"), ("Possible progression", "progression_options"),
            ("Limitations", "limitations"),
        ):
            values = item[key]
            fields.append(f"{label}: " + ("; ".join(values) if isinstance(values, list) else values))
        fields.append(f"Local verification: {item['local_verification_note']}")
        content = "\n".join(fields)
        for index, segment in enumerate(_split_profile_text(content, max_chars=1500)):
            records.append({
                "chunk_id": f"synthetic_{item['record_id']}_{index}",
                "resource_id": f"synthetic_{item['record_id']}",
                "title": f"{item['occupation_title']} — {item['sector']} (illustrative)",
                "content": segment,
            })
            occupation_chunks += 1

    # The wider career catalogue (ml/data/careers) is indexed alongside the pathway
    # library when its tables have been generated. Without them this adds nothing.
    from career_chunks import build_career_chunks
    catalogue_records = build_career_chunks(ROOT / "data" / "careers")
    records.extend(catalogue_records)

    CHUNKS.parent.mkdir(parents=True, exist_ok=True)
    CHUNKS.write_text(json.dumps(records, indent=2), encoding="utf-8")
    print("Preparing a reusable vector cache for faster API startup...")
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer(str(TRAINED_DIR))
    embeddings = load_or_create_embeddings(
        records,
        CHUNKS,
        TRAINED_DIR,
        ROOT / "data" / "processed" / "chunk_embeddings.npy",
        ROOT / "data" / "processed" / "chunk_embeddings_manifest.json",
        model=embedder,
    )
    print(f"Cached {len(embeddings)} vectors.")
    resource_chunks = sum(1 for r in records if not r["resource_id"].startswith(("synthetic_", "career_")))
    print(f"Indexed {len(md_files)} written resources ({resource_chunks} chunks) and {occupation_chunks} synthetic pathway chunks.")
    catalogue_roles = len({r["resource_id"] for r in catalogue_records})
    print(f"Indexed {catalogue_roles} career catalogue roles ({len(catalogue_records)} chunks).")
    print(f"Saved to: {CHUNKS}\n")
    return records


def _format_profile_values(values):
    formatted = []
    for value in values:
        name = value.get("name") or value.get("title") or ""
        details = []
        for key, label in (("Importance", "importance"), ("Level", "level"),
                           ("In Demand", "in demand"), ("Hot Technology", "hot technology")):
            if value.get(key):
                details.append(f"{label}: {value[key]}")
        if value.get("workplace_example"):
            details.append(f"example: {value['workplace_example']}")
        if name:
            formatted.append(name + (f" ({'; '.join(details)})" if details else ""))
    return "; ".join(formatted)


def _select_profile_values(values, limit):
    """Keep the strongest O*NET entries so the runtime index stays compact."""
    def score(value):
        if value.get("hot_technology", "").casefold() in {"y", "yes", "true"}:
            return (2, 0.0)
        if value.get("in_demand", "").casefold() in {"y", "yes", "true"}:
            return (1, 0.0)
        numeric = []
        for key, raw in value.items():
            if key == "name":
                continue
            try:
                numeric.append(float(raw))
            except (TypeError, ValueError):
                continue
        return (0, max(numeric, default=0.0))

    return sorted(values, key=score, reverse=True)[:limit]


def _split_profile_text(text, max_chars=700):
    """Split long profile sections into bounded chunks on word boundaries."""
    words = text.split()
    parts = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            parts.append(current)
            current = word
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def step_2_train_retriever():
    import pandas as pd
    import random
    import torch
    from torch.utils.data import DataLoader
    from sentence_transformers import SentenceTransformer, InputExample, losses

    print("=" * 60)
    print("STEP 2: Fine-tuning retriever model (all-MiniLM-L6-v2)...")
    print("=" * 60)
    df = pd.read_csv(QA)
    random.seed(42)
    torch.manual_seed(42)
    authored_train = df[df["split"] == "train"]
    examples = [InputExample(texts=[row.query, row.positive_passage])
                for row in authored_train.itertuples(index=False)]
    dataset = ROOT / "data" / "synthetic" / "career_feedback_dataset.jsonl"
    pathway_pairs = 0
    if dataset.is_file():
        for line in dataset.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            path = json.loads(line)
            passage = "\n".join([
                f"Career pathway: {path['occupation_title']} ({path['sector']}).",
                path["role_summary"], path["requirements_and_qualification_notes"],
                "Skills: " + ", ".join(path["skills"]),
                "Preparation: " + "; ".join(path["preparation_pathway"]),
                "Practice: " + "; ".join(path["portfolio_or_practice_ideas"]),
                "CV advice: " + path["cv_tailoring_guidance"],
            ])
            for query in path.get("example_student_queries", [])[:2]:
                examples.append(InputExample(texts=[query, passage]))
                pathway_pairs += 1
    if len(examples) < 32:
        raise ValueError("Retriever training needs at least 32 unique authored and pathway pairs; add reviewed examples first.")
    print(f"Loaded {len(authored_train)} authored guide pairs and {pathway_pairs} balanced synthetic pathway pairs ({len(examples)} total).")

    loader = DataLoader(examples, shuffle=True, batch_size=8)

    print("Loading the locally cached base MiniLM model...")
    model = load_cached_base_retriever()
    train_loss = losses.MultipleNegativesRankingLoss(model)

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    print("Training for 2 epochs with MultipleNegativesRankingLoss; pathway examples are balanced at two per occupation.")
    model.fit(
        train_objectives=[(loader, train_loss)],
        epochs=2,
        warmup_steps=5,
        show_progress_bar=True,
        output_path=str(CANDIDATE_DIR),
    )
    chunks = json.loads(CHUNKS.read_text(encoding="utf-8"))
    load_or_create_embeddings(
        chunks,
        CHUNKS,
        CANDIDATE_DIR,
        ROOT / "data" / "processed" / "candidate_chunk_embeddings.npy",
        ROOT / "data" / "processed" / "candidate_chunk_embeddings_manifest.json",
        model=model,
    )
    print(f"Candidate retriever saved for review at: {CANDIDATE_DIR}\n")
    return model


def step_3_evaluate_retrieval():
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    from sentence_transformers import SentenceTransformer

    print("=" * 60)
    print("STEP 3: Evaluating retrieval performance (Baseline vs Trained)...")
    print("=" * 60)
    chunks = json.loads(CHUNKS.read_text(encoding="utf-8"))
    eval_df = pd.read_csv(QA).query("split == 'eval'")
    evaluation_pairs = [(row.query, row.resource_id, "authored_guides") for row in eval_df.itertuples(index=False)]
    real_eval_path = ROOT / "data" / "evaluation" / "student_queries_eval.csv"
    real_eval_count = 0
    if real_eval_path.is_file():
        real_df = pd.read_csv(real_eval_path).fillna("")
        required_columns = {
            "query_id", "query", "expected_resource_id", "sector",
            "consent_confirmed", "deidentified", "human_reviewed",
        }
        missing_columns = required_columns - set(real_df.columns)
        if missing_columns:
            raise ValueError(f"Real evaluation file is missing columns: {sorted(missing_columns)}")
        known_resources = {chunk["resource_id"] for chunk in chunks}
        accepted = {"true", "yes", "1"}
        for row in real_df.itertuples(index=False):
            if not all(str(getattr(row, key)).strip().casefold() in accepted
                       for key in ("consent_confirmed", "deidentified", "human_reviewed")):
                continue
            query = str(row.query).strip()
            target = str(row.expected_resource_id).strip()
            if not query or not target:
                continue
            if target not in known_resources:
                raise ValueError(f"Unknown expected_resource_id '{target}' in {real_eval_path}")
            evaluation_pairs.append((query, target, "real_student_queries"))
            real_eval_count += 1
    synthetic_dataset = ROOT / "data" / "synthetic" / "career_feedback_dataset.jsonl"
    if synthetic_dataset.is_file():
        for line in synthetic_dataset.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            pathway = json.loads(line)
            target = f"synthetic_{pathway['record_id']}"
            evaluation_pairs.extend((query, target, "synthetic_pathways") for query in pathway.get("retrieval_eval_queries", []))
    corpus = [c["content"] for c in chunks]
    resource_ids = [c["resource_id"] for c in chunks]

    def compute_ranking_metrics(model):
        if not evaluation_pairs:
            raise ValueError("qa_pairs.csv must contain at least one row with split='eval'.")
        doc_emb = model.encode(corpus, convert_to_numpy=True, normalize_embeddings=True)
        chunks_by_resource = {}
        for index, resource_id in enumerate(resource_ids):
            chunks_by_resource.setdefault(resource_id, []).append(index)
        grouped = {}
        for query, target_resource, group in evaluation_pairs:
            q = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
            # Rank distinct resources by their best matching chunk so a guide
            # split into many chunks does not crowd other resources out.
            scores = {
                resource_id: float(np.max(doc_emb[indices] @ q))
                for resource_id, indices in chunks_by_resource.items()
            }
            ranked_resources = sorted(scores, key=scores.get, reverse=True)
            try:
                rank = ranked_resources.index(target_resource) + 1
            except ValueError:
                rank = len(ranked_resources) + 1
            values = grouped.setdefault(group, {
                "count": 0,
                "recall@1": 0.0,
                "recall@3": 0.0,
                "mrr": 0.0,
                "ndcg@3": 0.0,
            })
            values["count"] += 1
            values["recall@1"] += float(rank <= 1)
            values["recall@3"] += float(rank <= 3)
            values["mrr"] += 1.0 / rank
            if rank <= 3:
                gain = 1.0 / np.log2(rank + 1)
                values["ndcg@3"] += gain
        return {
            group: {key: round(value / values["count"], 4) for key, value in values.items() if key != "count"}
            | {"questions": values["count"]}
            for group, values in grouped.items()
        }

    print("Evaluating baseline 'all-MiniLM-L6-v2'...")
    baseline = load_cached_base_retriever()
    evaluation_model_path = CANDIDATE_DIR if CANDIDATE_DIR.is_dir() else TRAINED_DIR
    print(f"Evaluating retriever from '{evaluation_model_path}'...")
    trained = SentenceTransformer(str(evaluation_model_path))

    baseline_metrics = compute_ranking_metrics(baseline)
    candidate_metrics = compute_ranking_metrics(trained)
    active = SentenceTransformer(str(TRAINED_DIR))
    active_metrics = compute_ranking_metrics(active)
    authored_count = sum(1 for _, _, group in evaluation_pairs if group == "authored_guides")
    synthetic_count = sum(1 for _, _, group in evaluation_pairs if group == "synthetic_pathways")
    results = {
        "baseline_metrics_by_group": baseline_metrics,
        "candidate_metrics_by_group": candidate_metrics,
        "active_metrics_by_group": active_metrics,
        "authored_guide_questions": authored_count,
        "real_student_questions": real_eval_count,
        "synthetic_pathway_diagnostics": synthetic_count,
        "total_queries": len(evaluation_pairs),
        "eval_target_resources": int(len({target for _, target, _ in evaluation_pairs})),
        "candidate_model_path": str(evaluation_model_path),
        "candidate_selected_by_backend_when_present": True,
        "metric_type": "Information-retrieval ranking diagnostics only; these are not model accuracy, career-fit accuracy, or job-outcome measures.",
        "evaluation_scope_note": "Authored guide set has eight questions. Synthetic pathway checks are generated from the same synthetic records and measure indexing consistency only; they are not independent real-student evaluations. Collect consented, de-identified student queries and human relevance judgements before making quality claims.",
    }

    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\n--- EVALUATION RESULTS ---")
    print(json.dumps(results, indent=2))

    # Compare ranking quality separately by query source. These are not accuracy scores.
    group_labels = {
        "authored_guides": f"Authored guides (n={authored_count})",
        "real_student_queries": f"Reviewed student queries (n={real_eval_count})",
        "synthetic_pathways": f"Synthetic diagnostics (n={synthetic_count})",
    }
    groups = [group for group in group_labels if group in baseline_metrics]
    labels = [group_labels[group] for group in groups]
    x = np.arange(len(groups))
    plt.figure(figsize=(8, 4.8))
    for metrics, label, color, offset in (
        (baseline_metrics, "Base MiniLM", "#4A90E2", -0.24),
        (active_metrics, "Previous retriever", "#F39C12", 0.0),
        (candidate_metrics, "Balanced candidate", "#2ECC71", 0.24),
    ):
        values = [metrics[group]["mrr"] for group in groups]
        bars = plt.bar(x + offset, values, 0.23, label=label, color=color)
        for bar, value in zip(bars, values):
            plt.annotate(f"{value:.2f}", xy=(bar.get_x() + bar.get_width() / 2, value),
                         xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=8)
    plt.xticks(x, labels, fontsize=9)
    plt.ylim(0, 1.12)
    plt.ylabel("Mean reciprocal rank (search position)")
    plt.title("Retrieval ranking diagnostic — not career or model accuracy")
    plt.legend(loc="lower right")
    plt.grid(axis='y', linestyle='--', alpha=0.4)
    plt.tight_layout()

    chart_path = METRICS.with_suffix(".png")
    plt.savefig(chart_path, dpi=160)
    plt.close()
    print(f"Saved evaluation chart to: {chart_path}\n")
    return results


def step_4_interactive_test():
    import numpy as np
    from sentence_transformers import SentenceTransformer

    print("=" * 60)
    print("STEP 4: Quick Live Retrieval Test")
    print("=" * 60)
    trained = SentenceTransformer(str(TRAINED_DIR))
    chunks = json.loads(CHUNKS.read_text(encoding="utf-8"))
    corpus = [c["content"] for c in chunks]
    doc_emb = trained.encode(corpus, convert_to_numpy=True, normalize_embeddings=True)

    test_queries = [
        "How should I structure my tech CV for an internship?",
        "What questions are asked in behavioural interviews?",
        "What entry level roles are available in AI and Data Science in Nairobi?"
    ]

    for q in test_queries:
        print(f"\n[Query]: {q}")
        q_vec = trained.encode([q], convert_to_numpy=True, normalize_embeddings=True)[0]
        scores = doc_emb @ q_vec
        top_idx = np.argsort(-scores)[:2]
        for rank, idx in enumerate(top_idx, start=1):
            chunk = chunks[idx]
            print(f"  Rank {rank} (Score: {scores[idx]:.3f}) [{chunk['title']}]:")
            print(f"    \"{chunk['content'][:140]}...\"")


def main():
    parser = argparse.ArgumentParser(description="Prepare or train the career knowledge retrieval pipeline.")
    parser.add_argument("--prepare-only", action="store_true",
                        help="Rebuild searchable chunks without training the retriever.")
    parser.add_argument("--evaluate-only", action="store_true",
                        help="Evaluate baseline, current, and candidate retrievers without training.")
    args = parser.parse_args()
    if args.evaluate_only:
        step_3_evaluate_retrieval()
        return
    if args.prepare_only:
        step_1_prepare_knowledge_base()
        return
    step_1_prepare_knowledge_base()
    step_2_train_retriever()
    step_3_evaluate_retrieval()
    step_4_interactive_test()
    print("\nALL PIPELINE STEPS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
