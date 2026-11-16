"""Hybrid career recommender: ranks the 452 catalogue careers for one student profile.

Three signals are combined (see Section 5.4.2 of the report and Part 9 of the evaluation notebook):
  - classifier: Logistic Regression trained on labelled synthetic profiles (probability per career);
  - skills overlap: skills the student shares with a career, weighted by their importance to it;
  - profile similarity: TF-IDF similarity between the profile and the career's description, skills and tasks.
When the classifier is confident its ranking leads; when it is unsure, the two content signals take over.
The trained classifier is cached in ml/models/career_recommender.joblib and rebuilt if missing (about 30 s).
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
PROFILE_COLUMNS = ["course", "specialisation", "skills", "interests", "experience_level", "certifications", "preferred_industry"]
SKILLS_SHARE = 0.3          # share of the content score given to skills overlap (rest: profile similarity)
CONFIDENCE_THRESHOLD = 0.6  # classifier probability at which its ranking is fully trusted
CLASSIFIER_SHARE = 0.8      # weight of the classifier inside the confident blend

_lock = threading.Lock()
_state: dict | None = None


def _rows(name: str) -> list[dict]:
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
            "class_index": [list(model.classes_).index(c) for c in career_ids],
            "skills": skills, "doc_vectorizer": doc_vectorizer, "doc_matrix": doc_vectorizer.transform(documents),
            "skill_totals": np.array([sum(w for _, w in skills.get(c, [])) or 1.0 for c in career_ids]),
        }
        print(f"[Recommender] Ready: {len(career_ids)} careers.")
        return _state


def _scale(values: np.ndarray) -> np.ndarray:
    low, high = values.min(), values.max()
    return (values - low) / (high - low) if high > low else np.zeros_like(values)


def recommend(profile: dict, top_k: int = 5) -> list[dict]:
    """profile keys: course, specialisation, skills, interests, certifications, preferred_industry
    (lists or semicolon-separated strings). Returns the top careers with the reasons behind each."""
    state = _load()
    clean = {key: "; ".join(value) if isinstance(value, (list, tuple)) else (value or "") for key, value in profile.items()}
    student_skills = {s.strip().lower() for s in clean.get("skills", "").split(";") if s.strip()}
    if not student_skills and not clean.get("interests", "").strip() and not clean.get("course", "").strip():
        return []

    probabilities = state["model"].predict_proba(state["vectorizer"].transform([_profile_text(clean)]))[0][state["class_index"]]
    overlap = np.array([sum(w for s, w in state["skills"].get(c, []) if s.lower() in student_skills)
                        for c in state["career_ids"]]) / state["skill_totals"]
    plain = " ".join(clean.get(k, "") for k in ("course", "specialisation", "skills", "interests", "certifications", "preferred_industry"))
    similarity = (state["doc_vectorizer"].transform([plain]) @ state["doc_matrix"].T).toarray()[0]

    content = SKILLS_SHARE * _scale(overlap) + (1 - SKILLS_SHARE) * _scale(similarity)
    trust = min(float(probabilities.max()) / CONFIDENCE_THRESHOLD, 1.0)
    scores = trust * (CLASSIFIER_SHARE * _scale(probabilities) + (1 - CLASSIFIER_SHARE) * content) + (1 - trust) * content

    results = []
    for index in np.argsort(-scores)[:top_k]:
        career_id = state["career_ids"][index]
        row = state["catalog"][career_id]
        shared = sorted(((w, s) for s, w in state["skills"].get(career_id, []) if s.lower() in student_skills), reverse=True)
        reasons = []
        if shared:
            reasons.append("Uses your skills in " + ", ".join(s for _, s in shared[:3]))
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
            "match_label": "Strong match" if score >= 60 else "Good match" if score >= 25 else "Worth exploring",
            "reasons": reasons or ["A partial match to your profile; add more skills for better suggestions"],
        })
    return results
