"""Turn the career catalogue tables into searchable knowledge chunks for the retriever.

Each role in ml/data/careers/ becomes three passages that share one resource_id
(`career_<career_id>`), so the retriever ranks a role once however many passages
it has:

  overview     what the role is, its skills, study areas and regulation note
  getting in   pathway stages, opportunity types, where openings are advertised
               and the official sources to check
  applying     CV layout and tips plus a sample of practice interview questions

The passages repeat the tables' own caveat: the content is synthetic and
illustrative, and local requirements must be verified.

`build_career_chunks` returns an empty list when the catalogue has not been
generated, so the existing pipeline keeps working without it.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

REQUIRED_FILES = (
    "career_catalog.csv", "career_skills.csv", "career_education.csv", "career_pathways.csv",
    "career_resources.csv", "interview_questions.csv", "opportunity_templates.csv", "cv_templates.jsonl",
)
CAVEAT = "Illustrative synthetic guidance; verify current local requirements before relying on it."
INTERVIEW_TYPES_SHOWN = ("skill", "situational", "behavioural", "motivation", "ethics", "curveball")


def _read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_optional(path: Path) -> list[dict]:
    return _read_csv(path) if path.is_file() else []


def _group(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["career_id"]].append(row)
    return grouped


def _split(text: str, max_chars: int) -> list[str]:
    """Split on line boundaries first, then on words, keeping each part within max_chars."""
    parts, current = [], ""
    for line in text.split("\n"):
        candidate = f"{current}\n{line}".strip() if current else line
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            parts.append(current)
        current = ""
        for word in line.split():
            candidate = f"{current} {word}".strip()
            if len(candidate) > max_chars and current:
                parts.append(current)
                current = word
            else:
                current = candidate
    if current:
        parts.append(current)
    return parts


def build_career_chunks(careers_dir: Path, max_chars: int = 1500) -> list[dict]:
    if not all((careers_dir / name).is_file() for name in REQUIRED_FILES):
        return []
    catalog = _read_csv(careers_dir / "career_catalog.csv")
    skills = _group(_read_csv(careers_dir / "career_skills.csv"))
    education = {row["career_id"]: row for row in _read_csv(careers_dir / "career_education.csv")}
    pathways = _group(_read_csv(careers_dir / "career_pathways.csv"))
    resources = _group(_read_csv(careers_dir / "career_resources.csv"))
    questions = _group(_read_csv(careers_dir / "interview_questions.csv"))
    opportunities = _group(_read_csv(careers_dir / "opportunity_templates.csv"))
    titles = _group(_read_optional(careers_dir / "career_titles.csv"))
    tasks = _group(_read_optional(careers_dir / "career_tasks.csv"))
    tools = _group(_read_optional(careers_dir / "career_tools.csv"))
    related = _group(_read_optional(careers_dir / "career_related.csv"))
    settings = _group(_read_optional(careers_dir / "career_work_settings.csv"))
    templates = {}
    for line in (careers_dir / "cv_templates.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            templates[item["career_id"]] = item

    records: list[dict] = []
    for role in catalog:
        career_id, title, category = role["career_id"], role["role_title"], role["category"]
        by_type: dict[str, list[str]] = defaultdict(list)
        for row in skills[career_id]:
            by_type[row["skill_type"]].append(row["skill"])
        study = education[career_id]
        titles_by_type: dict[str, list[str]] = defaultdict(list)
        for row in titles.get(career_id, []):
            titles_by_type[row["title_type"]].append(row["title"])

        def listed(label: str, items: list[str]) -> str:
            return f"{label}: {'; '.join(items)}." if items else ""

        overview = "\n".join(line for line in [
            f"Career: {title} ({category}). {CAVEAT}",
            f"Overview: {role['description']}",
            f"Focus area: {role['specialisation']}.",
            listed("Also known as", titles_by_type["alternative"]),
            listed("Specialisms", titles_by_type["specialism"]),
            listed("Day-to-day tasks", [row["task"] for row in tasks.get(career_id, [])]),
            listed("Tools and technologies", [row["tool"] for row in tools.get(career_id, [])]),
            listed("Where people in this role work", [row["setting"] for row in settings.get(career_id, [])
                                                      if row["setting_type"] == "employer"]),
            listed("Working patterns", [row["setting"] for row in settings.get(career_id, [])
                                        if row["setting_type"] == "working pattern"]),
            f"Core skills: {', '.join(by_type['core'])}.",
            f"Helpful skills: {', '.join(by_type['preferred'] + by_type['transferable'])}.",
            f"Typical study areas: {study['typical_study_areas']}.",
            f"Typical qualification levels: {study['typical_qualification_levels']}.",
            f"Certifications to explore: {study['example_certifications']}.",
            f"Regulation: {study['verification_note']}",
            f"Markets: {role['market_scope']}.",
        ] if line)

        stage_lines = [
            f"Stage {row['stage_number']} - {row['stage_name']}: {row['example_title']} "
            f"({row['opportunity_type']}). {row['typical_timing']}. {row['what_to_build']}"
            for row in sorted(pathways[career_id], key=lambda row: int(row["stage_number"]))
        ]
        kenya = [row for row in opportunities[career_id] if row["market"] == "Kenya"]
        opportunity_lines = [
            f"{row['opportunity_type'].capitalize()}: {row['eligibility']}. {row['typical_duration']}. "
            f"{row['typical_timing']}. Applicants usually show: {row['applicants_usually_show']}. "
            f"Documents: {row['documents_usually_requested']}."
            for row in kenya
        ]
        specific = [row for row in resources[career_id] if row["link_reason"] != "general"]
        general = [row for row in resources[career_id] if row["link_reason"] == "general"]
        source_lines = [f"{row['source_name']} ({row['url']}): {row['what_to_check']}"
                        for row in specific + general[:3]]
        getting_in = "\n".join(line for line in [
            f"How to get into {title} ({category}): attachment, internship, graduate programme and job routes. {CAVEAT}",
            *stage_lines,
            listed("Entry-level job titles", titles_by_type["entry"]),
            listed("Progression titles", titles_by_type["progression"]),
            listed("Leadership destinations", titles_by_type["leadership"]),
            listed("Where this path can also lead", titles_by_type["beyond"]),
            listed("Related careers to consider", [row["related_role_title"] for row in related.get(career_id, [])]),
            "Typical opportunities in Kenya (patterns, not live vacancies):",
            *opportunity_lines,
            f"Where openings are usually advertised: {kenya[0]['where_advertised']}." if kenya else "",
            "International roles: check visa and work-permit rules and whether your qualification is recognised.",
            "Official sources to check:",
            *source_lines,
        ] if line)

        template = templates[career_id]
        sample = []
        for question_type in INTERVIEW_TYPES_SHOWN:
            sample += [row["question"] for row in questions[career_id] if row["question_type"] == question_type][:2]
        applying = "\n".join([
            f"CV and interview preparation for {title} ({category}). {CAVEAT}",
            "Suggested CV sections in order: " + ", ".join(section["heading"] for section in template["sections"]) + ".",
            "Skills to highlight on the CV: " + ", ".join(template["skills_to_highlight"]) + ".",
            "CV bullet examples to adapt: " + " ".join(template["bullet_starters"]),
            "CV tips: " + " ".join(template["cv_tips"]),
            template["regulated_note"],
            f"Practice interview questions for {title}:",
            *[f"- {text}" for text in sample],
        ])

        for part_name, label, text in (
            ("overview", "career overview", overview),
            ("getting_in", "getting started", getting_in),
            ("applying", "CV and interview preparation", applying),
        ):
            for index, segment in enumerate(_split(text, max_chars)):
                records.append({
                    "chunk_id": f"career_{career_id}_{part_name}_{index}",
                    "resource_id": f"career_{career_id}",
                    "title": f"{title} — {label} (illustrative)",
                    "content": segment,
                })
    return records
