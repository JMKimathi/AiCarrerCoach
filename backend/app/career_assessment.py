"""Explainable matching against the single synthetic pathway library."""

import json
import re
from pathlib import Path
from typing import Iterable


ROOT_DIR = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT_DIR / "ml" / "data" / "synthetic" / "career_feedback_dataset.jsonl"
ASSESSMENT_VERSION = "synthetic-pathways-v1"


def load_pathways() -> list[dict]:
    if not DATASET_PATH.is_file():
        raise RuntimeError(f"Synthetic career dataset is missing: {DATASET_PATH}")
    return [json.loads(line) for line in DATASET_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


CAREER_PATHS = load_pathways()
ASSESSMENT_OPTIONS = {
    "courses": sorted({term for path in CAREER_PATHS for term in path["related_courses"]}),
    "career_goals": sorted({term for path in CAREER_PATHS for term in [path["occupation_title"], *path["alternate_titles"]]}),
    "skills": sorted({term for path in CAREER_PATHS for term in path["skills"]}),
    "interests": sorted({term for path in CAREER_PATHS for term in path["interest_signals"]}),
    "preferred_activities": sorted({term for path in CAREER_PATHS for term in path["preferred_activities"]}),
}


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9+#/ ]+", " ", value.lower()).strip()


def _matches(values: Iterable[str], terms: Iterable[str]) -> list[str]:
    matched = []
    normalised_terms = [_normalise(term) for term in terms]
    for value in values:
        text = _normalise(value)
        padded_text = f" {text} "
        if text and any(f" {term} " in padded_text or text == term for term in normalised_terms):
            matched.append(value.strip())
    return matched


def assess_career_paths(profile: dict, top_k: int = 4) -> dict:
    dimensions = (("course", 0.15, "related_courses"), ("career_goal", 0.10, "goal_terms"),
                  ("skills", 0.35, "skills"), ("interests", 0.25, "interest_signals"),
                  ("preferred_activities", 0.15, "preferred_activities"))
    provided = {}
    for key, _, _ in dimensions:
        raw = profile.get(key) or []  # a missing or null field counts as empty
        raw = [raw] if isinstance(raw, str) else raw
        provided[key] = [str(item).strip() for item in raw if str(item).strip()]
    active = [(key, weight, field) for key, weight, field in dimensions if provided[key]]
    if not active:
        raise ValueError("Provide at least one skill, interest, or preferred activity.")

    recommendations = []
    for path in CAREER_PATHS:
        fields = dict(path)
        fields["goal_terms"] = [
            path["occupation_title"], path["sector"], *path["alternate_titles"],
            *path["related_courses"], *path["interest_signals"],
        ]
        evidence, score = [], 0.0
        for key, weight, field in active:
            found = _matches(provided[key], fields[field])
            evidence.extend(found)
            score += weight * len(found) / len(provided[key])
        skills_to_explore = [skill for skill in path["skills"]
                             if not _matches(provided["skills"], (skill,))][:4]
        recommendations.append({
            "role": path["occupation_title"],
            "fit_score": round(score / sum(weight for _, weight, _ in active) * 100),
            "matching_evidence": list(dict.fromkeys(evidence))[:8],
            "skills_to_explore": skills_to_explore[:3],
            "next_steps": path["preparation_pathway"][:3] + path["portfolio_or_practice_ideas"][:2],
            "role_summary": path["role_summary"],
            "entry_level_roles": path["entry_level_roles"],
            "application_channel_types": path["application_channel_types"],
            "sample_interview_questions": path["sample_interview_questions"],
            "cv_tailoring_guidance": path["cv_tailoring_guidance"],
            "progression_options": path["progression_options"],
            "requirements_and_qualification_notes": path["requirements_and_qualification_notes"],
            "related_resources": [],
        })
    recommendations.sort(key=lambda item: (item["fit_score"], item["role"]), reverse=True)
    recommendations = [item for item in recommendations if item["fit_score"] > 0]
    if not recommendations:
        summary = "I could not match those answers to a pathway yet. Try a suggested option or add a skill, interest, or activity in your own words."
        completeness = "needs more detail"
    else:
        summary = "These illustrative pathways have signals in common with what you shared. Treat them as options to explore, not a decision about your future."
        completeness = "more useful" if len(active) >= 2 and sum(map(len, provided.values())) >= 5 else "early exploration"
    return {
        "assessment_version": ASSESSMENT_VERSION,
        "profile_completeness": completeness,
        "summary": summary,
        "recommendations": recommendations[:top_k],
        "information_note": "Pathways come from a synthetic illustrative dataset. Fit scores show overlap with your answers only; they are not probabilities, qualifications, admission criteria, or predictions of job success. Verify local course, licensing, and employer requirements.",
    }
