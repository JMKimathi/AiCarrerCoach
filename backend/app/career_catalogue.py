"""Read-only access to the generated career catalogue in ml/data/careers.

The tables are loaded once, on first use, and kept in memory. If they have not
been generated yet, `load_catalogue` raises CatalogueUnavailable so routes can
answer with a clear 503 instead of a stack trace. Restart the API after
rebuilding the tables.

All content is synthetic and illustrative; see ml/src/build_career_catalogue.py.
"""

import csv
import json
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from backend.app.config import ML_DIR

CAREERS_DIR: Path = ML_DIR / "data" / "careers"
INFORMATION_NOTE = (
    "Career information here is synthetic and illustrative. It is not a list of live vacancies or an "
    "official statement of requirements. Confirm current details with employers, institutions and regulators."
)


class CatalogueUnavailable(RuntimeError):
    """Raised when the career tables have not been generated."""


def _read_csv(name: str) -> list[dict]:
    """Load one CSV from ml/data/careers as a list of dictionaries."""
    path = CAREERS_DIR / name
    if not path.is_file():
        raise CatalogueUnavailable(
            f"{name} is missing. Run `python ml/src/run_career_pipeline.py` to generate the career catalogue."
        )
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_optional_csv(name: str) -> list[dict]:
    """Detail tables are optional so an older data folder still loads."""
    return _read_csv(name) if (CAREERS_DIR / name).is_file() else []


TITLE_TYPES = ("alternative", "specialism", "entry", "progression", "leadership", "beyond", "lateral")


def _group(rows: list[dict]) -> dict[str, list[dict]]:
    """Group rows by career_id so each career's details can be looked up quickly."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["career_id"]].append(row)
    return dict(grouped)


@lru_cache(maxsize=1)
def load_catalogue() -> dict:
    """Build the full catalogue (careers plus their skills, pay, tasks and so on) and cache it."""
    careers = {row["career_id"]: row for row in _read_csv("career_catalog.csv")}
    templates_path = CAREERS_DIR / "cv_templates.jsonl"
    if not templates_path.is_file():
        raise CatalogueUnavailable("cv_templates.jsonl is missing. Run `python ml/src/run_career_pipeline.py`.")
    templates = {}
    for line in templates_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            templates[item["career_id"]] = item
    return {
        "careers": careers,
        "skills": _group(_read_csv("career_skills.csv")),
        "education": {row["career_id"]: row for row in _read_csv("career_education.csv")},
        "pathways": _group(_read_csv("career_pathways.csv")),
        "resources": _group(_read_csv("career_resources.csv")),
        "opportunities": _group(_read_csv("opportunity_templates.csv")),
        "questions": _group(_read_csv("interview_questions.csv")),
        "titles": _group(_read_optional_csv("career_titles.csv")),
        "tasks": _group(_read_optional_csv("career_tasks.csv")),
        "tools": _group(_read_optional_csv("career_tools.csv")),
        "related": _group(_read_optional_csv("career_related.csv")),
        "settings": _group(_read_optional_csv("career_work_settings.csv")),
        "salaries": {row["category"]: row for row in _read_optional_csv("salary_guide.csv")},
        "internship_pay": _read_optional_csv("internship_pay.csv"),
        "job_sources": _read_optional_csv("job_sources.csv"),
        "cv_templates": templates,
    }


def list_categories() -> list[dict]:
    """Return each category with how many careers sit under it."""
    counts: dict[str, int] = defaultdict(int)
    for row in load_catalogue()["careers"].values():
        counts[row["category"]] += 1
    return [{"category": name, "career_count": count} for name, count in counts.items()]


def search_careers(category: str | None = None, query: str | None = None, limit: int = 50, offset: int = 0) -> dict:
    """Filter by category and free text. Text matches the title, focus area and core skills."""
    catalogue = load_catalogue()
    words = [word for word in (query or "").lower().split() if word]
    matches = []
    for career_id, row in catalogue["careers"].items():
        if category and row["category"].lower() != category.strip().lower():
            continue
        core = [item["skill"] for item in catalogue["skills"].get(career_id, []) if item["skill_type"] == "core"]
        if words:
            haystack = " ".join([row["role_title"], row["specialisation"], *core]).lower()
            if not all(word in haystack for word in words):
                continue
        matches.append({
            "career_id": career_id, "role_title": row["role_title"], "category": row["category"],
            "specialisation": row["specialisation"], "core_skills": core,
            "commonly_regulated": row["commonly_regulated"] == "yes",
        })
    return {"total": len(matches), "items": matches[offset:offset + limit]}


def get_career(career_id: str) -> dict | None:
    """Return everything we know about one career, or None if the id is unknown."""
    catalogue = load_catalogue()
    row = catalogue["careers"].get(career_id)
    if row is None:
        return None
    skills: dict[str, list[str]] = defaultdict(list)
    for item in catalogue["skills"].get(career_id, []):
        skills[item["skill_type"]].append(item["skill"])
    education = catalogue["education"].get(career_id, {})
    job_titles: dict[str, list[str]] = {title_type: [] for title_type in TITLE_TYPES}
    for item in catalogue["titles"].get(career_id, []):
        job_titles.setdefault(item["title_type"], []).append(item["title"])
    task_rows = catalogue["tasks"].get(career_id, [])
    work_settings = catalogue["settings"].get(career_id, [])
    return {
        "career_id": career_id,
        "role_title": row["role_title"],
        "category": row["category"],
        "specialisation": row["specialisation"],
        "description": row["description"],
        "commonly_regulated": row["commonly_regulated"] == "yes",
        "market_scope": row["market_scope"],
        "core_skills": skills["core"],
        "preferred_skills": skills["preferred"],
        "transferable_skills": skills["transferable"],
        "education": {
            "typical_study_areas": education.get("typical_study_areas", ""),
            "typical_qualification_levels": education.get("typical_qualification_levels", ""),
            "example_certifications": education.get("example_certifications", ""),
            "verify_with": education.get("verify_with", ""),
            "verification_note": education.get("verification_note", ""),
        },
        "pathway": [
            {"stage_number": int(item["stage_number"]), "stage_name": item["stage_name"],
             "example_title": item["example_title"], "opportunity_type": item["opportunity_type"],
             "typical_timing": item["typical_timing"], "what_to_build": item["what_to_build"]}
            for item in sorted(catalogue["pathways"].get(career_id, []), key=lambda item: int(item["stage_number"]))
        ],
        "opportunities": [
            {key: item[key] for key in (
                "opportunity_id", "opportunity_type", "market", "example_title", "employer_type", "eligibility",
                "typical_duration", "typical_timing", "applicants_usually_show", "documents_usually_requested",
                "where_advertised", "search_phrases", "notes")}
            for item in catalogue["opportunities"].get(career_id, [])
        ],
        "job_titles": job_titles,
        "day_to_day_tasks": [item["task"] for item in task_rows],
        "tools": [item["tool"] for item in catalogue["tools"].get(career_id, [])],
        "detail_is_role_specific": any(item["detail_source"] == "authored" for item in task_rows),
        "related_careers": [
            {"career_id": item["related_career_id"], "role_title": item["related_role_title"],
             "category": item["related_category"], "relation": item["relation"],
             "common_ground": item["common_ground"]}
            for item in catalogue["related"].get(career_id, [])
        ],
        "employers": [item["setting"] for item in work_settings if item["setting_type"] == "employer"],
        "working_patterns": [item["setting"] for item in work_settings if item["setting_type"] == "working pattern"],
        "official_sources": [
            {"source_name": item["source_name"], "url": item["url"], "source_type": item["source_type"],
             "market": item["market"], "what_to_check": item["what_to_check"],
             "role_specific": item["link_reason"] == "role-specific"}
            for item in catalogue["resources"].get(career_id, [])
        ],
        "pay": _pay_for(catalogue, row["category"]),
        "where_to_look": [
            {"name": item["name"], "url": item["url"], "kind": item["kind"], "note": item["note"], "checked": item["checked"]}
            for item in catalogue["job_sources"]
            if item["categories"] == "all" or row["category"] in item["categories"].split(";")
        ],
        "information_note": INFORMATION_NOTE,
    }


def _pay_for(catalogue: dict, category: str) -> dict | None:
    """Indicative monthly gross pay for the career's field, with its source and the date it was checked."""
    salary = catalogue["salaries"].get(category)
    if salary is None:
        return None
    return {
        "survey_area": salary["survey_area"],
        "typical_low_kes": int(salary["typical_low_kes"]),
        "typical_high_kes": int(salary["typical_high_kes"]),
        "average_kes": int(salary["average_kes"]),
        "source_name": salary["source_name"],
        "source_url": salary["source_url"],
        "checked": salary["checked"],
        "note": "Middle 80% of monthly gross pay reported for this field in Kenya. Starting salaries usually sit near the "
                "lower figure and experienced staff nearer the upper one; pay varies by employer, sector and location.",
        "internships": [
            {"scheme": item["scheme"], "detail": item["detail"], "source_name": item["source_name"],
             "source_url": item["source_url"], "checked": item["checked"]}
            for item in catalogue["internship_pay"]
        ],
    }


def get_cv_template(career_id: str) -> dict | None:
    """Return the CV template written for this career, if there is one."""
    return load_catalogue()["cv_templates"].get(career_id)
