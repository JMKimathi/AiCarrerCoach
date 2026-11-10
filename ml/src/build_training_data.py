"""Build the hybrid student-profile training table: synthetic rows plus consented real rows.

Writes to ml/data/careers/:

  career_training_data.csv        student profiles labelled with a target career_id
  training_data_manifest.json     counts by origin and split, with the caveats below
  real/student_profiles.template.csv   header a real, consented dataset must follow

Synthetic rows are generated from the catalogue: each profile mixes some of a
role's core skills with sector skills, a course from that sector, interests and a
little unrelated noise, so profiles for neighbouring roles overlap the way real
students do.

Real rows are read from ml/data/careers/real/student_profiles.csv if that file
exists. It is ignored by Git. Only rows with consent_given = yes are used, and
names, emails and phone numbers must never be put in it. Every output row carries
`data_origin` (synthetic or real) so the two can always be evaluated separately.

Important: a model trained on the synthetic rows learns the rules of this
generator. Its score on synthetic test rows says how well it recovered those
rules, not how well it advises real students. Report synthetic and real results
separately, and make real-world claims only from the real rows.

Usage (from the repository root):
  python ml/src/build_training_data.py
  python ml/src/build_training_data.py --profiles-per-career 20
  python ml/src/build_training_data.py --check
"""

import argparse
import csv
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from build_career_catalogue import CATEGORIES, DEFAULT_OUTPUT_DIR, build_rows, write_csv  # noqa: E402
from build_career_pathways import CATEGORY_EDUCATION  # noqa: E402

SEED = 20261110
REAL_SUBDIR = "real"
REAL_FILENAME = "student_profiles.csv"
TEMPLATE_FILENAME = "student_profiles.template.csv"

# What students in each sector tend to say they are interested in.
CATEGORY_INTERESTS = {
    "Technology and Data": ["building apps", "solving puzzles", "working with data", "gadgets and new technology", "automation"],
    "Engineering and Built Environment": ["how things are built", "design and drawing", "mathematics and physics", "infrastructure", "fixing and improving systems"],
    "Health and Medicine": ["helping patients", "human biology", "public health", "caring for people", "medical science"],
    "Banking and Finance": ["money and markets", "working with numbers", "investing", "business news", "financial planning"],
    "Business and Entrepreneurship": ["starting a business", "persuading people", "brands and marketing", "leading teams", "spotting opportunities"],
    "Law and Governance": ["justice and fairness", "debating", "reading and argument", "politics and governance", "human rights"],
    "Education and Teaching": ["teaching others", "working with children or young people", "explaining ideas", "mentoring", "learning design"],
    "Agriculture and Environment": ["farming", "nature and conservation", "working outdoors", "food systems", "climate and sustainability"],
    "Media and Creative Industries": ["storytelling", "design and visual art", "film and music", "writing", "social media"],
    "Tourism and Hospitality": ["meeting new people", "travel", "food and cooking", "hosting and service", "events"],
    "Science and Research": ["experiments", "asking why things happen", "laboratory work", "mathematics and statistics", "discovery"],
    "Logistics and Operations": ["organising and planning", "how goods move", "aviation or shipping", "efficiency", "coordinating people"],
    "Social and Community Services": ["helping communities", "listening to people", "social justice", "volunteering", "working with vulnerable groups"],
    "Public Service and Development": ["public policy", "serving the country", "economics and development", "current affairs", "international relations"],
    "Energy, Manufacturing and Skilled Trades": ["working with my hands", "machines and tools", "electricity and energy", "making and repairing things", "practical problem solving"],
}

EXPERIENCE_LEVELS = [("no work experience", 35), ("attachment completed", 30), ("internship completed", 20), ("one to two years of work", 15)]
STUDY_STAGES = ["first year", "second year", "third year", "final year", "recent graduate"]
OPPORTUNITIES = ["industrial attachment", "internship", "graduate programme", "full-time job"]

COLUMNS = [
    "profile_id", "data_origin", "course", "specialisation", "study_stage", "skills", "interests",
    "experience_level", "certifications", "preferred_industry", "target_opportunity",
    "target_career_id", "target_career", "split",
]
REAL_COLUMNS = [
    "consent_given", "course", "specialisation", "study_stage", "skills", "interests",
    "experience_level", "certifications", "preferred_industry", "target_opportunity", "target_career_id",
]


def _split(profile_id: str) -> str:
    """Stable 70/15/15 split so rebuilding never moves a row between splits."""
    bucket = int(hashlib.md5(profile_id.encode("utf-8")).hexdigest(), 16) % 100
    return "train" if bucket < 70 else "validation" if bucket < 85 else "test"


def _split_list(text: str) -> list[str]:
    return [item.strip() for item in text.split(";") if item.strip()]


def build_synthetic(profiles_per_career: int) -> list[dict]:
    catalog, skills = build_rows()
    by_career: dict[str, dict[str, list[str]]] = {}
    for row in skills:
        by_career.setdefault(row["career_id"], {}).setdefault(row["skill_type"], []).append(row["skill"])
    core_by_category: dict[str, list[str]] = {}
    for role in catalog:
        core_by_category.setdefault(role["category"], []).extend(by_career[role["career_id"]]["core"])
    all_categories = list(CATEGORIES)

    rng = random.Random(SEED)
    rows = []
    for role in catalog:
        career_id, category = role["career_id"], role["category"]
        role_skills = by_career[career_id]
        courses = _split_list(CATEGORY_EDUCATION[category][0])
        certifications = _split_list(CATEGORY_EDUCATION[category][2])
        for index in range(1, profiles_per_career + 1):
            chosen = rng.sample(role_skills["core"], k=rng.randint(2, len(role_skills["core"])))
            chosen += rng.sample(role_skills["preferred"], k=rng.randint(0, 2))
            chosen += rng.sample(role_skills["transferable"], k=rng.randint(1, 3))
            if rng.random() < 0.45:  # a skill picked up from a neighbouring role in the same sector
                chosen.append(rng.choice(core_by_category[category]))
            if rng.random() < 0.15:  # an unrelated skill, as real profiles often have
                chosen.append(rng.choice(core_by_category[rng.choice(all_categories)]))
            chosen = list(dict.fromkeys(chosen))
            rng.shuffle(chosen)

            interests = rng.sample(CATEGORY_INTERESTS[category], k=rng.randint(1, 3))
            if rng.random() < 0.6:
                interests.append(role["specialisation"])
            if rng.random() < 0.2:
                interests.append(rng.choice(CATEGORY_INTERESTS[rng.choice(all_categories)]))
            interests = list(dict.fromkeys(interests))

            experience = rng.choices([name for name, _ in EXPERIENCE_LEVELS],
                                     weights=[weight for _, weight in EXPERIENCE_LEVELS])[0]
            stage = rng.choice(STUDY_STAGES)
            opportunity = rng.choice(OPPORTUNITIES if stage in ("final year", "recent graduate")
                                     else OPPORTUNITIES[:2])
            profile_id = f"SYN-{career_id.split('-')[1]}-{index:03d}"
            rows.append({
                "profile_id": profile_id, "data_origin": "synthetic",
                "course": rng.choice(courses),
                "specialisation": role["specialisation"] if rng.random() < 0.7 else "",
                "study_stage": stage, "skills": "; ".join(chosen), "interests": "; ".join(interests),
                "experience_level": experience,
                "certifications": rng.choice(certifications) if rng.random() < 0.3 else "",
                "preferred_industry": category if rng.random() < 0.85 else rng.choice(all_categories),
                "target_opportunity": opportunity,
                "target_career_id": career_id, "target_career": role["role_title"],
                "split": _split(profile_id),
            })
    return rows


def load_real(path: Path) -> tuple[list[dict], dict]:
    """Read consented real profiles. Returns usable rows and a report of what was skipped."""
    report = {"file_found": path.is_file(), "rows_read": 0, "rows_used": 0,
              "skipped_no_consent": 0, "skipped_unknown_career": 0}
    if not path.is_file():
        return [], report
    titles = {role["career_id"]: role["role_title"] for role in build_rows()[0]}
    rows = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(REAL_COLUMNS) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")
        forbidden = {"name", "full_name", "email", "phone", "student_id", "admission_number"} & {
            (name or "").strip().lower() for name in reader.fieldnames or []}
        if forbidden:
            raise ValueError(f"{path.name} must not contain identifying columns: {sorted(forbidden)}")
        for record in reader:
            report["rows_read"] += 1
            if record["consent_given"].strip().lower() != "yes":
                report["skipped_no_consent"] += 1
                continue
            career_id = record["target_career_id"].strip()
            if career_id not in titles:
                report["skipped_unknown_career"] += 1
                continue
            profile_id = f"REAL-{report['rows_used'] + 1:05d}"
            rows.append({
                "profile_id": profile_id, "data_origin": "real",
                **{column: record[column].strip() for column in COLUMNS
                   if column in REAL_COLUMNS and column != "target_career_id"},
                "target_career_id": career_id, "target_career": titles[career_id],
                "split": _split(profile_id),
            })
            report["rows_used"] += 1
    return rows, report


def validate(rows: list[dict]) -> dict:
    missing = set(CATEGORIES) - set(CATEGORY_INTERESTS)
    if missing:
        raise ValueError(f"Categories without interest signals: {sorted(missing)}")
    ids = [row["profile_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate profile_id values")
    if any(row["data_origin"] not in ("synthetic", "real") for row in rows):
        raise ValueError("Every row must be marked synthetic or real")
    if any(not row["skills"] for row in rows if row["data_origin"] == "synthetic"):
        raise ValueError("Synthetic profiles must list at least one skill")
    return {
        "profiles": len(rows),
        "by_origin": dict(Counter(row["data_origin"] for row in rows)),
        "by_split": dict(Counter(row["split"] for row in rows)),
        "target_careers": len({row["target_career_id"] for row in rows}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--profiles-per-career", type=int, default=30)
    parser.add_argument("--check", action="store_true", help="Validate the table without writing files.")
    args = parser.parse_args()
    if args.profiles_per_career < 1:
        raise SystemExit("--profiles-per-career must be at least 1")

    real_dir = args.output_dir / REAL_SUBDIR
    synthetic = build_synthetic(args.profiles_per_career)
    real, real_report = load_real(real_dir / REAL_FILENAME)
    rows = synthetic + real
    summary = validate(rows)
    summary["real_data"] = real_report
    summary["caveat"] = (
        "Synthetic rows follow generator rules. Scores on them do not measure real-world accuracy; "
        "evaluate synthetic and real rows separately."
    )
    if args.check:
        print(json.dumps(summary, indent=2))
        print("Validation passed; no files written.")
        return
    real_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "career_training_data.csv", COLUMNS, rows)
    write_csv(real_dir / TEMPLATE_FILENAME, REAL_COLUMNS, [])
    (args.output_dir / "training_data_manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} profiles ({len(synthetic)} synthetic, {len(real)} real) to {args.output_dir}")


if __name__ == "__main__":
    main()
