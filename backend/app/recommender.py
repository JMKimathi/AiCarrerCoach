"""Career recommender: ranks every career in the catalogue for one student profile.

Three signals are combined (see Section 5.4.2 of the report and Part 9 of the evaluation notebook):
  - classifier: Logistic Regression trained on labelled synthetic profiles (probability per career);
  - skills overlap: skills the student shares with a career, weighted by their importance to it;
  - profile similarity: TF-IDF similarity between the profile and the career's description, skills and tasks.
When the classifier is confident its ranking leads; when it is unsure, the two content signals take over.
The trained classifier is cached in ml/models/career_recommender.joblib and rebuilt if missing (about 30 s).

If the fine-tuned career matcher (ml/models/career-matcher, trained with ml/notebooks/career_matcher_training.ipynb)
is present, it is used instead: one transformer model that compares the profile with every career's description,
so it can also rank careers it never saw in training. Without that folder the hybrid above is used.
"""

from __future__ import annotations

import csv
import re
import threading
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from backend.app.config import ML_DIR

CAREERS_DIR: Path = ML_DIR / "data" / "careers"
MODEL_PATH: Path = ML_DIR / "models" / "career_recommender.joblib"
MATCHER_DIR: Path = ML_DIR / "models" / "career-matcher"
PROFILE_COLUMNS = ["course", "specialisation", "skills", "interests", "experience_level", "certifications", "preferred_industry"]
SKILLS_SHARE = 0.3          # share of the content score given to skills overlap (rest: profile similarity)
CONFIDENCE_THRESHOLD = 0.6  # classifier probability at which its ranking is fully trusted
CLASSIFIER_SHARE = 0.8      # weight of the classifier inside the confident blend

_lock = threading.Lock()
_state: dict | None = None
_matcher: dict | None = None


def _rows(name: str) -> list[dict]:
    """Read one of the career CSV files into a list of rows."""
    with open(CAREERS_DIR / name, encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _profile_text(profile: dict) -> str:
    """Same tagged text the classifier was trained on: each item appears with its column tag."""
    parts = []
    for column in PROFILE_COLUMNS:
        tag = column.split("_")[0]
        for item in str(profile.get(column) or "").split(";"):
            item = item.strip()
            if item:
                parts.append(f"{tag}_{re.sub(r'[^a-z0-9]+', '_', item.lower())} {item}")
    return " ".join(parts)


def train_classifier() -> dict:
    """Train the backup Logistic Regression model if the saved one is missing."""
    rows = [row for row in _rows("career_training_data.csv") if row.get("split") == "train"]
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2, max_features=15000)
    features = vectorizer.fit_transform([_profile_text(row) for row in rows])
    model = LogisticRegression(C=10, max_iter=300).fit(features, [row["target_career_id"] for row in rows])
    model.coef_ = model.coef_.astype(np.float32)
    bundle = {"vectorizer": vectorizer, "model": model}
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_PATH, compress=3)
    return bundle


def _load() -> dict:
    """Load everything the recommender needs once and keep it in memory."""
    global _state
    with _lock:
        if _state is not None:
            return _state
        if MODEL_PATH.exists():
            bundle = joblib.load(MODEL_PATH)
        else:
            print("[Recommender] Training the career classifier (about 30 seconds, once)...")
            bundle = train_classifier()
        catalog = {row["career_id"]: row for row in _rows("career_catalog.csv")}
        career_ids = [c for c in bundle["model"].classes_ if c in catalog]
        skills: dict[str, list[tuple[str, float]]] = {}
        for row in _rows("career_skills.csv"):
            skills.setdefault(row["career_id"], []).append((row["skill"].strip(), float(row["importance"] or 1)))
        tasks: dict[str, list[str]] = {}
        for row in _rows("career_tasks.csv"):
            tasks.setdefault(row["career_id"], []).append(row["task"])
        documents = [" ".join([catalog[c]["role_title"], catalog[c].get("specialisation", ""), catalog[c].get("description", ""),
                               " ".join(s for s, _ in skills.get(c, [])), " ".join(tasks.get(c, []))]) for c in career_ids]
        doc_vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english").fit(documents)
        model = bundle["model"]
        _state = {
            "vectorizer": bundle["vectorizer"], "model": model, "catalog": catalog, "career_ids": career_ids,
            # The classifier only knows careers it was trained on; the career matcher can rank every career in
            # the catalogue, including ones added later, because it works from their descriptions.
            "all_ids": list(catalog),
            "class_index": [list(model.classes_).index(c) for c in career_ids],
            "skills": skills, "doc_vectorizer": doc_vectorizer, "doc_matrix": doc_vectorizer.transform(documents),
            "skill_totals": np.array([sum(w for _, w in skills.get(c, [])) or 1.0 for c in career_ids]),
            "career_words": {c: _stems(" ".join([catalog[c]["role_title"], catalog[c].get("specialisation", ""),
                                                 catalog[c].get("description", ""), " ".join(tasks.get(c, [])),
                                                 " ".join(s for s, _ in skills.get(c, []))]))
                             for c in catalog},
        }
        print(f"[Recommender] Ready: {len(catalog)} careers ({len(career_ids)} known to the classifier).")
        return _state


_STOP = {"with", "from", "that", "this", "your", "work", "working", "about", "into", "other", "their", "them", "have",
         "using", "skills", "people", "things", "being", "more", "they", "such", "will", "able", "also"}


def _stems(text: str) -> set[str]:
    """Rough word roots so that 'analysis', 'analyse' and 'analytical' count as the same idea."""
    words = re.findall(r"[a-z]{4,}", text.lower())
    return {w[:5] for w in words if w not in _STOP}


def _reasons(clean: dict, career_id: str, state: dict, student_skills: set[str]) -> list[str]:
    """Explain a suggestion only with answers the student actually gave."""
    reasons = []
    shared = sorted(((w, s) for s, w in state["skills"].get(career_id, []) if s.lower() in student_skills), reverse=True)
    if shared:
        reasons.append("Uses your skills in " + ", ".join(s for _, s in shared[:3]))
    words = state["career_words"].get(career_id, set())
    linked = [item.strip() for item in clean.get("interests", "").split(";")
              if item.strip() and _stems(item) & words][:3]
    if linked:
        reasons.append("Linked to what you said you enjoy: " + ", ".join(linked))
    course = clean.get("course", "").strip()
    if course and _stems(course) & words:
        reasons.append(f"Related to your course ({course})")
    return reasons


def _label(rank: int, score: int, cut: int) -> str:
    """Scores are relative to this student's best match, so the wording avoids sounding certain."""
    if rank == 0:
        return "Top suggestion"
    return "Also worth exploring" if score >= cut else "Related option"


def _scale(values: np.ndarray) -> np.ndarray:
    """Squash a list of scores into the 0 to 1 range so they can be combined."""
    low, high = values.min(), values.max()
    return (values - low) / (high - low) if high > low else np.zeros_like(values)


def _career_text(row: dict, skills: list[tuple[str, float]], tasks: list[str]) -> str:
    """Must match career_text() in the training notebook."""
    ordered = [s for s, _ in sorted(skills, key=lambda item: -item[1])]
    return (f"{row['role_title']}. {row.get('category', '')}. Skills: {', '.join(ordered)}. "
            f"{row.get('description', '')} Tasks: {' '.join(tasks)}")


def _profile_sentence(profile: dict) -> str:
    """Must match profile_to_text() in the training notebook."""
    labels = (("course", "Course"), ("specialisation", "Specialisation"), ("skills", "Skills"), ("interests", "Interests"),
              ("certifications", "Certifications"), ("preferred_industry", "Preferred industry"))
    return ". ".join(f"{label}: {str(profile.get(key, '')).replace(';', ',')}" for key, label in labels if str(profile.get(key, "")).strip())


def _load_matcher() -> dict | None:
    """Load the fine-tuned career matcher if it is available on disk."""
    global _matcher
    if not (MATCHER_DIR / "modules.json").is_file():
        return None
    state = _load()
    with _lock:
        if _matcher is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(str(MATCHER_DIR), device="cpu")
            tasks: dict[str, list[str]] = {}
            for row in _rows("career_tasks.csv"):
                tasks.setdefault(row["career_id"], []).append(row["task"])
            texts = [_career_text(state["catalog"][c], state["skills"].get(c, []), tasks.get(c, [])) for c in state["all_ids"]]
            _matcher = {"model": model, "vectors": model.encode(texts, batch_size=64, normalize_embeddings=True)}
            print(f"[Recommender] Career matcher loaded from {MATCHER_DIR}")
        return _matcher


def rank_pathways(profile: dict, paths: list[dict]) -> list[str] | None:
    """Order the broad career pathways with the same model that ranks the roles, so both agree.
    Returns None when the career matcher is not installed (the word-overlap order is then kept)."""
    matcher = _load_matcher()
    if matcher is None or not paths:
        return None
    if "path_vectors" not in matcher:
        texts = [f"{p['occupation_title']}. {p.get('sector', '')}. Skills: {', '.join(p.get('skills', []))}. {p.get('role_summary', '')}"
                 for p in paths]
        matcher["path_titles"] = [p["occupation_title"] for p in paths]
        matcher["path_vectors"] = matcher["model"].encode(texts, batch_size=64, normalize_embeddings=True)
    clean = {key: "; ".join(value) if isinstance(value, (list, tuple)) else (value or "") for key, value in profile.items()}
    query = matcher["model"].encode([_profile_sentence(clean)], normalize_embeddings=True)[0]
    similarity = matcher["path_vectors"] @ query
    return [matcher["path_titles"][i] for i in np.argsort(-similarity)]


def warm_up() -> None:
    """Load the models at start-up so the first assessment does not wait for them."""
    try:
        _load()
        _load_matcher()
    except Exception as exc:
        print(f"[Recommender] Not loaded yet: {exc}")


def recommend(profile: dict, top_k: int = 5) -> list[dict]:
    """profile keys: course, specialisation, skills, interests, certifications, preferred_industry
    (lists or semicolon-separated strings). Returns the top careers with the reasons behind each."""
    state = _load()
    clean = {key: "; ".join(value) if isinstance(value, (list, tuple)) else (value or "") for key, value in profile.items()}
    student_skills = {s.strip().lower() for s in clean.get("skills", "").split(";") if s.strip()}
    if not student_skills and not clean.get("interests", "").strip() and not clean.get("course", "").strip():
        return []

    matcher = _load_matcher()
    if matcher is not None:
        query = matcher["model"].encode([_profile_sentence(clean)], normalize_embeddings=True)[0]
        similarity = matcher["vectors"] @ query
        top, middle = float(similarity.max()), float(np.median(similarity))
        results = []
        for rank, index in enumerate(np.argsort(-similarity)[:top_k]):
            career_id = state["all_ids"][index]
            row = state["catalog"][career_id]
            score = int(round(100 * max(0.0, (float(similarity[index]) - middle) / (top - middle)))) if top > middle else 0
            reasons = _reasons(clean, career_id, state, student_skills)
            if len(reasons) < 2:
                reasons.append("Its description and tasks are close to your answers overall")
            results.append({
                "career_id": str(career_id), "role_title": row["role_title"], "category": row.get("category", ""),
                "match_score": score, "match_label": _label(rank, score, 65), "reasons": reasons,
            })
        return results

    probabilities = state["model"].predict_proba(state["vectorizer"].transform([_profile_text(clean)]))[0][state["class_index"]]
    overlap = np.array([sum(w for s, w in state["skills"].get(c, []) if s.lower() in student_skills)
                        for c in state["career_ids"]]) / state["skill_totals"]
    plain = " ".join(clean.get(k, "") for k in ("course", "specialisation", "skills", "interests", "certifications", "preferred_industry"))
    similarity = (state["doc_vectorizer"].transform([plain]) @ state["doc_matrix"].T).toarray()[0]

    content = SKILLS_SHARE * _scale(overlap) + (1 - SKILLS_SHARE) * _scale(similarity)
    trust = min(float(probabilities.max()) / CONFIDENCE_THRESHOLD, 1.0)
    scores = trust * (CLASSIFIER_SHARE * _scale(probabilities) + (1 - CLASSIFIER_SHARE) * content) + (1 - trust) * content

    results = []
    for rank, index in enumerate(np.argsort(-scores)[:top_k]):
        career_id = state["career_ids"][index]
        row = state["catalog"][career_id]
        reasons = _reasons(clean, career_id, state, student_skills)
        shared = bool(reasons)
        if trust >= 0.5 and probabilities[index] >= 0.05:
            reasons.append("Students with a profile like yours chose this career")
        if similarity[index] > 0 and (not shared or trust < 0.5):
            reasons.append("Its description and tasks match what you told us")
        score = int(round(float(scores[index]) * 100))
        results.append({
            "career_id": str(career_id),
            "role_title": row["role_title"],
            "category": row.get("category", ""),
            "match_score": score,
            "match_label": _label(rank, score, 25),
            "reasons": reasons or ["A partial match to your profile; add more skills for better suggestions"],
        })
    return results
