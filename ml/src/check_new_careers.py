"""Tests the career matcher on the 30 careers added after the main evaluation (CAREER-453 to CAREER-482).

The matcher was never trained on these careers, so this shows how it copes with careers that have no student
data. Test profiles are made with the same generator as the training data (build_training_data.py, 30 per
career) and damaged with the same add_noise() rules as the evaluation notebook. Each profile is then ranked
against all 482 careers, and we report Hit@1, Hit@3 and MRR at 0%, 50% and 80% damage.

These are synthetic profiles built from the catalogue, so the undamaged score is optimistic; the 50% figure is
the one to compare with Figure 5.8 in the report.

Run from the project root:  .\\backend\\.venv\\Scripts\\python.exe ml/src/check_new_careers.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml" / "src"))
from backend.app import recommender  # noqa: E402
import build_training_data  # noqa: E402

FIRST_NEW_CAREER = 453
DAMAGE_LEVELS = (0.0, 0.5, 0.8)
CAREERS_DIR = ROOT / "ml" / "data" / "careers"

catalog = pd.read_csv(CAREERS_DIR / "career_catalog.csv", encoding="utf-8-sig").fillna("")
skills_table = pd.read_csv(CAREERS_DIR / "career_skills.csv", encoding="utf-8-sig").fillna("")
skills_by_career = skills_table.groupby("career_id")["skill"].apply(list).to_dict()
careers_in_category = catalog.groupby("category")["career_id"].apply(list).to_dict()
all_careers = catalog["career_id"].tolist()
category_of = dict(zip(catalog["career_id"], catalog["category"]))


def add_noise(frame: pd.DataFrame, level: float, seed: int = 42) -> pd.DataFrame:
    """Same damage as the evaluation notebook: drop skills and interests, borrow skills, blank fields."""
    if level <= 0:
        return frame.copy()
    random = np.random.default_rng(seed)
    noisy = frame.copy()
    for column in ("skills", "interests"):
        values = []
        for text in noisy[column]:
            items = [item.strip() for item in text.split(";") if item.strip()]
            kept = [item for item in items if random.random() >= level] or items[:1]
            values.append("; ".join(kept))
        noisy[column] = values
    distracted = []
    for skills, career_id in zip(noisy["skills"], noisy["target_career_id"]):
        items = [item for item in skills.split("; ") if item]
        neighbours = [other for other in careers_in_category[category_of[career_id]] if other != career_id]
        for _ in range(int(round(level * max(len(items), 3)))):
            pool = neighbours if random.random() < 0.7 else all_careers
            borrowed = skills_by_career.get(pool[random.integers(len(pool))], [])
            if borrowed:
                items.append(borrowed[random.integers(len(borrowed))])
        distracted.append("; ".join(items))
    noisy["skills"] = distracted
    for column in ("course", "specialisation", "certifications", "preferred_industry"):
        noisy.loc[random.random(len(noisy)) < level, column] = ""
    return noisy


def main() -> None:
    """Build the test profiles, rank them with the matcher and print the scores."""
    profiles = pd.DataFrame([row for row in build_training_data.build_synthetic(30)
                             if int(row["target_career_id"].split("-")[1]) >= FIRST_NEW_CAREER])
    matcher = recommender._load_matcher()
    if matcher is None:
        raise SystemExit("The career matcher is not installed in ml/models/career-matcher.")
    ids = np.array(recommender._load()["all_ids"])
    print(f"{len(profiles)} profiles for {profiles['target_career_id'].nunique()} new careers, "
          f"ranked against {len(ids)} careers")
    for level in DAMAGE_LEVELS:
        frame = add_noise(profiles, level)
        queries = matcher["model"].encode([recommender._profile_sentence(row) for row in frame.to_dict("records")],
                                          batch_size=64, normalize_embeddings=True)
        order = np.argsort(-(queries @ matcher["vectors"].T), axis=1)
        ranks = np.array([np.where(ids[row] == target)[0][0] + 1
                          for row, target in zip(order, frame["target_career_id"])])
        print(f"damage {level:.0%}: Hit@1 {np.mean(ranks == 1):.1%}  Hit@3 {np.mean(ranks <= 3):.1%}  "
              f"MRR {np.mean(1 / ranks) * 100:.1f}")


if __name__ == "__main__":
    main()
