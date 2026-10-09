import json
import sys
import argparse
from pathlib import Path

# Set up paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))
from config import RESOURCES, CHUNKS, QA, TRAINED_DIR, METRICS, chunk_text
from embedding_cache import load_or_create_embeddings


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

    # Add structured O*NET profiles to the same index the backend loads.
    # LinkedIn skill counts are intentionally excluded because this export has
    # no likely Kenya postings and must not imply local demand.
    onet_profiles = ROOT / "data" / "processed" / "derived" / "onet_occupation_skills.jsonl"
    if onet_profiles.is_file():
        for line in onet_profiles.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            profile = json.loads(line)
            code = profile.get("onet_soc_code", "").strip()
            role = profile.get("occupation_title", "Occupation").strip()
            if not code or not role:
                continue
            resource_id = f"onet_{code}"
            source_note = "Source: O*NET 31.0 U.S. occupational reference; local requirements may differ."
            zone = profile.get("job_zone", "")
            description = profile.get("description", "").strip()
            if len(description) > 420:
                description = description[:420].rsplit(" ", 1)[0] + "…"
            fields = [f"Occupation: {role} (O*NET-SOC {code}).", description]
            if zone:
                fields.append(f"Preparation reference: O*NET Job Zone {zone} (U.S. reference, not a Kenyan qualification requirement).")
            aliases = "; ".join(profile.get("job_titles", [])[:4])
            if aliases:
                fields.append(f"Also called: {aliases}.")
            for label, values, limit in (
                ("Essential skills", profile.get("essential_skills", []), 4),
                ("Software skills", profile.get("software_skills", []), 2),
                ("Interests", profile.get("career_interests", []), 6),
                ("Specific interest areas", profile.get("specific_interests", []), 3),
                ("Typical work", profile.get("work_activities", []), 4),
            ):
                text = _format_profile_values(_select_profile_values(values, limit))
                if text:
                    fields.append(f"{label}: {text}.")
            fields.append(source_note)
            content = "\n".join(field for field in fields if field)
            for index, segment in enumerate(_split_profile_text(content, max_chars=1500)):
                records.append({
                    "chunk_id": f"{resource_id}_{index}",
                    "resource_id": resource_id,
                    "title": f"{role} (O*NET occupation profile)",
                    "content": segment,
                })

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
    print(f"Indexed {len(md_files)} written resources and {len(records) - sum(1 for r in records if r['resource_id'].startswith('onet_'))} resource chunks, plus {sum(1 for r in records if r['resource_id'].startswith('onet_'))} O*NET occupation chunks.")
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
    from torch.utils.data import DataLoader
    from sentence_transformers import SentenceTransformer, InputExample, losses

    print("=" * 60)
    print("STEP 2: Fine-tuning retriever model (all-MiniLM-L6-v2)...")
    print("=" * 60)
    df = pd.read_csv(QA)
    train_df = df[df["split"] == "train"]
    print(f"Loaded {len(train_df)} training question-passage pairs.")

    examples = [
        InputExample(texts=[row.query, row.positive_passage])
        for row in train_df.itertuples(index=False)
    ]
    loader = DataLoader(examples, shuffle=True, batch_size=4)

    print("Loading base SentenceTransformer('all-MiniLM-L6-v2')...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    train_loss = losses.MultipleNegativesRankingLoss(model)

    TRAINED_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Training for 4 epochs with MultipleNegativesRankingLoss...")
    model.fit(
        train_objectives=[(loader, train_loss)],
        epochs=4,
        warmup_steps=5,
        show_progress_bar=True,
        output_path=str(TRAINED_DIR),
    )
    chunks = json.loads(CHUNKS.read_text(encoding="utf-8"))
    load_or_create_embeddings(
        chunks,
        CHUNKS,
        TRAINED_DIR,
        ROOT / "data" / "processed" / "chunk_embeddings.npy",
        ROOT / "data" / "processed" / "chunk_embeddings_manifest.json",
        model=model,
    )
    print(f"Fine-tuned retriever successfully saved to: {TRAINED_DIR}\n")
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
    corpus = [c["content"] for c in chunks]
    resource_ids = [c["resource_id"] for c in chunks]

    def compute_recall_at_k(model, k):
        doc_emb = model.encode(corpus, convert_to_numpy=True, normalize_embeddings=True)
        hits = 0
        for row in eval_df.itertuples(index=False):
            q = model.encode([row.query], convert_to_numpy=True, normalize_embeddings=True)[0]
            scores = doc_emb @ q
            top = np.argsort(-scores)[:k]
            retrieved = {resource_ids[i] for i in top}
            if row.resource_id in retrieved:
                hits += 1
        return hits / len(eval_df)

    print("Evaluating baseline 'all-MiniLM-L6-v2'...")
    baseline = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"Evaluating fine-tuned model from '{TRAINED_DIR}'...")
    trained = SentenceTransformer(str(TRAINED_DIR))

    results = {
        "baseline_recall@1": round(compute_recall_at_k(baseline, 1), 4),
        "baseline_recall@3": round(compute_recall_at_k(baseline, 3), 4),
        "trained_recall@1": round(compute_recall_at_k(trained, 1), 4),
        "trained_recall@3": round(compute_recall_at_k(trained, 3), 4),
        "eval_questions": int(len(eval_df)),
    }

    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\n--- EVALUATION RESULTS ---")
    print(json.dumps(results, indent=2))

    # Generate Chapter 5 comparison chart
    labels = ["Recall@1", "Recall@3"]
    x = np.arange(len(labels))
    plt.figure(figsize=(7, 4.5))
    bar1 = plt.bar(x - 0.18, [results["baseline_recall@1"], results["baseline_recall@3"]], 0.35, label="MiniLM Baseline", color="#4A90E2")
    bar2 = plt.bar(x + 0.18, [results["trained_recall@1"], results["trained_recall@3"]], 0.35, label="Fine-Tuned Retriever", color="#2ECC71")

    # Add values on top of bars
    for bar in bar1:
        height = bar.get_height()
        plt.annotate(f"{height:.0%}", xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')
    for bar in bar2:
        height = bar.get_height()
        plt.annotate(f"{height:.0%}", xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold')

    plt.xticks(x, labels, fontsize=11, fontweight='bold')
    plt.ylim(0, 1.15)
    plt.ylabel("Retrieval Score", fontsize=11)
    plt.title("Career Knowledge-Base Retrieval: Baseline vs. Fine-Tuned", fontsize=12, fontweight='bold')
    plt.legend(loc="upper left")
    plt.grid(axis='y', linestyle='--', alpha=0.5)
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
    args = parser.parse_args()
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
