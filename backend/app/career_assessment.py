"""Explainable career-family matching based on a student's stated evidence.

Scores are relative alignment scores, not probabilities or predictions of success.
Keep this catalogue versioned whenever prompts or scoring rules change.
"""

from dataclasses import dataclass
import re
from typing import Iterable


ASSESSMENT_VERSION = "career-paths-v1"


@dataclass(frozen=True)
class CareerPath:
    role: str
    skills: tuple[str, ...]
    interests: tuple[str, ...]
    activities: tuple[str, ...]
    next_steps: tuple[str, ...]


CAREER_PATHS = (
    CareerPath("Software Developer", ("programming", "python", "java", "kotlin", "javascript", "software", "web development", "mobile apps", "algorithms", "git"), ("building software", "problem solving", "apps", "websites", "technology"), ("coding", "building applications", "debugging", "solving technical problems"), ("Build a small application for a real user.", "Practise programming fundamentals and version control.")),
    CareerPath("Data Analyst / BI Specialist", ("sql", "spreadsheets", "excel", "statistics", "data visualization", "power bi", "tableau", "python", "reporting"), ("data", "business", "patterns", "decision making", "research"), ("analysing data", "creating dashboards", "explaining findings", "answering business questions"), ("Analyse a public dataset and explain three findings.", "Practise SQL queries and build a clear dashboard.")),
    CareerPath("Data Scientist / ML Engineer", ("python", "statistics", "machine learning", "pytorch", "tensorflow", "pandas", "experimentation", "data visualization"), ("artificial intelligence", "machine learning", "research", "mathematics", "data"), ("training models", "running experiments", "analysing data", "testing hypotheses"), ("Build a small, well-evaluated machine-learning project.", "Strengthen statistics, Python, and model evaluation.")),
    CareerPath("Data Engineer", ("sql", "python", "databases", "data pipelines", "etl", "cloud", "spark", "data modeling"), ("data", "systems", "reliability", "automation", "infrastructure"), ("organising data", "building pipelines", "automating workflows", "maintaining databases"), ("Create a pipeline that collects, cleans, and stores data.", "Practise SQL, data modelling, and pipeline monitoring.")),
    CareerPath("Cybersecurity Analyst", ("networking", "linux", "security", "incident response", "python", "risk analysis", "cloud", "ethical hacking"), ("security", "investigation", "privacy", "risk", "technology"), ("investigating incidents", "finding vulnerabilities", "monitoring systems", "protecting information"), ("Set up a safe cybersecurity practice lab.", "Study networking, Linux, and security fundamentals.")),
    CareerPath("DevOps / Cloud Engineer", ("linux", "cloud", "docker", "kubernetes", "automation", "networking", "ci/cd", "terraform", "scripting"), ("systems", "automation", "cloud", "reliability", "infrastructure"), ("automating deployments", "maintaining systems", "troubleshooting", "improving reliability"), ("Containerise and deploy a small application.", "Practise Linux, cloud basics, and deployment automation.")),
    CareerPath("UI/UX Designer", ("user research", "wireframing", "prototyping", "figma", "visual design", "accessibility", "usability testing"), ("design", "creativity", "people", "accessibility", "user experience"), ("interviewing users", "designing interfaces", "prototyping", "testing usability"), ("Improve one interface after talking to users.", "Create a case study showing research, design, and testing.")),
    CareerPath("QA / Test Engineer", ("testing", "python", "automation", "selenium", "playwright", "quality assurance", "api testing", "attention to detail"), ("quality", "problem solving", "reliability", "technology", "investigation"), ("testing applications", "reproducing bugs", "automating checks", "reviewing requirements"), ("Write test cases for an application you use.", "Practise API testing and one browser automation tool.")),
    CareerPath("Product / Business Analyst", ("communication", "requirements", "sql", "data analysis", "documentation", "facilitation", "process improvement"), ("business", "people", "planning", "technology", "decision making"), ("understanding user needs", "explaining ideas", "planning work", "improving processes"), ("Document a user problem and propose measurable improvements.", "Practise requirements writing and presenting evidence.")),
)

ASSESSMENT_OPTIONS = {
    "skills": sorted({term for path in CAREER_PATHS for term in path.skills}),
    "interests": sorted({term for path in CAREER_PATHS for term in path.interests}),
    "preferred_activities": sorted({term for path in CAREER_PATHS for term in path.activities}),
}


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9+#/ ]+", " ", value.lower()).strip()


def _matches(values: Iterable[str], terms: tuple[str, ...]) -> list[str]:
    matched = []
    normalised_terms = [_normalise(term) for term in terms]
    for value in values:
        text = _normalise(value)
        padded_text = f" {text} "
        if text and any(f" {term} " in padded_text or text == term for term in normalised_terms):
            matched.append(value.strip())
    return matched


def assess_career_paths(profile: dict, top_k: int = 4) -> dict:
    dimensions = (
        ("skills", 0.45),
        ("interests", 0.35),
        ("preferred_activities", 0.20),
    )
    provided = {key: [str(item).strip() for item in profile.get(key, []) if str(item).strip()] for key, _ in dimensions}
    active_dimensions = [(key, weight) for key, weight in dimensions if provided[key]]
    if not active_dimensions:
        raise ValueError("Provide at least one skill, interest, or preferred activity.")

    recommendations = []
    for path in CAREER_PATHS:
        terms = {"skills": path.skills, "interests": path.interests, "preferred_activities": path.activities}
        evidence = []
        weighted_score = 0.0
        for key, weight in active_dimensions:
            matched = _matches(provided[key], terms[key])
            evidence.extend(matched)
            weighted_score += weight * len(matched) / len(provided[key])

        missing_skills = [term for term in path.skills if not _matches(provided["skills"], (term,))][:4]
        recommendations.append({
            "role": path.role,
            "fit_score": round(weighted_score / sum(weight for _, weight in active_dimensions) * 100),
            "matching_evidence": list(dict.fromkeys(evidence))[:8],
            "skills_to_explore": missing_skills[:3],
            "next_steps": list(path.next_steps),
            "related_resources": [],
        })

    recommendations.sort(key=lambda item: (item["fit_score"], item["role"]), reverse=True)
    if recommendations[0]["fit_score"] == 0:
        recommendations = []
        summary = "We could not match those answers to the current career guide. Try a suggested option or describe a specific skill, interest, or activity."
        completeness = "needs more detail"
    else:
        summary = "These career families align most with the skills, interests, and activities you shared. Explore more than one option."
        completeness = "more useful" if len(active_dimensions) >= 2 and sum(map(len, provided.values())) >= 5 else "early exploration"
    return {
        "assessment_version": ASSESSMENT_VERSION,
        "profile_completeness": completeness,
        "summary": summary,
        "recommendations": recommendations[:top_k],
        "information_note": "Fit scores compare your answers with this versioned career guide. They are not probabilities, qualifications, or predictions of job success.",
    }
