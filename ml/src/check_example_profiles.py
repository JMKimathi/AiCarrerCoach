"""Checks the recommender on 20 hand-written example profiles.

Each profile names the career category a careers adviser would expect. The check counts how often a career from
that category is ranked first, and how often one appears in the first three. It compares the fine-tuned career
matcher with the hybrid fallback. These are synthetic examples written for the check, not real students.

Run from the project root:  .\\backend\\.venv\\Scripts\\python.exe ml/src/check_example_profiles.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.app import recommender  # noqa: E402

rows = list(csv.DictReader(open(ROOT / "ml" / "data" / "evaluation" / "example_profiles.csv", encoding="utf-8")))


def run(label):
    """Score the example profiles and print how often the right category is first and in the top three."""
    first = top3 = 0
    for row in rows:
        profile = {"course": row["course"], "skills": row["skills"], "interests": row["interests"]}
        categories = [r["category"] for r in recommender.recommend(profile, top_k=3)]
        first += categories[:1] == [row["expected_category"]]
        top3 += row["expected_category"] in categories
    print(f"{label:28} category first: {first}/{len(rows)}   category in top 3: {top3}/{len(rows)}")
    return first, top3


results = {}
if recommender._load_matcher() is not None:
    results["Career matcher"] = run("Career matcher (fine-tuned)")
recommender.MATCHER_DIR = Path("does-not-exist")   # switch the matcher off to score the fallback
recommender._matcher = None
results["Hybrid"] = run("Hybrid fallback")
