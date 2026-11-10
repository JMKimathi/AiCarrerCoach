"""Train and evaluate a career classifier on the hybrid catalogue training table.

Reads ml/data/careers/career_training_data.csv (one student profile per row,
labelled with a target career_id) and compares three text classifiers:

  Logistic Regression, Multinomial Naive Bayes and Linear SVC,

each on two feature sets:

  full         course, specialisation, skills, interests, experience,
               certifications and preferred industry
  skills_only  the skills column alone, as a harder check

The table's own `split` column decides train, validation and test rows, so
results are comparable between runs. The model and feature set are chosen on
validation macro-F1 and the test rows are scored once.

How to read the results: the synthetic profiles were produced by
ml/src/build_training_data.py, so a high score means the classifier recovered
that generator's rules. It is NOT evidence that the model advises real students
well. Results for real, consented rows are reported separately whenever such
rows exist, and only those support real-world claims.

Outputs go to ml/metrics/catalogue-model/ and ml/models/catalogue-model/. The
backend does not load this model: its career assessment uses explainable
overlap matching by design.

Usage (from the repository root, with the ml environment):
  python ml/src/train_catalogue_model.py
  python ml/src/train_catalogue_model.py --no-save-model
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT_DIR / "ml" / "data" / "careers" / "career_training_data.csv"
CATALOG_PATH = ROOT_DIR / "ml" / "data" / "careers" / "career_catalog.csv"
METRICS_DIR = ROOT_DIR / "ml" / "metrics" / "catalogue-model"
MODEL_DIR = ROOT_DIR / "ml" / "models" / "catalogue-model"

FEATURE_SETS = {
    "full": ["course", "specialisation", "skills", "interests", "experience_level",
             "certifications", "preferred_industry"],
    "skills_only": ["skills"],
}
CAVEAT = (
    "Scores on synthetic rows show how well the classifier recovered the rules of the data generator. "
    "They are not real-world accuracy. Only results on real, consented rows support claims about real students."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def feature_text(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    parts = [frame[column].fillna("").astype(str).str.replace(";", ",") for column in columns]
    labelled = [column.replace("_", " ") + ": " + part for column, part in zip(columns, parts)]
    text = labelled[0]
    for part in labelled[1:]:
        text = text + ". " + part
    return text


def make_models() -> dict:
    return {
        "Logistic Regression": LogisticRegression(C=5.0, max_iter=400),
        "Multinomial Naive Bayes": MultinomialNB(alpha=0.3),
        "Linear SVC": LinearSVC(C=0.5),
    }


def make_pipeline(classifier) -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2), min_df=2, max_features=20000)),
        ("clf", classifier),
    ])


def class_scores(pipeline: Pipeline, texts: pd.Series) -> np.ndarray:
    """Per-class scores for ranking: probabilities where available, otherwise decision values."""
    if hasattr(pipeline, "predict_proba"):
        return pipeline.predict_proba(texts)
    return pipeline.decision_function(texts)


def evaluate(pipeline: Pipeline, texts: pd.Series, labels: pd.Series) -> dict:
    if len(labels) == 0:
        return {"rows": 0}
    scores = class_scores(pipeline, texts)
    classes = pipeline.classes_
    top3 = classes[np.argsort(-scores, axis=1)[:, :3]]
    predicted = top3[:, 0]
    truth = labels.to_numpy()
    return {
        "rows": int(len(labels)),
        "top1_accuracy": round(float(accuracy_score(truth, predicted)), 4),
        "top3_accuracy": round(float(np.mean([actual in row for actual, row in zip(truth, top3)])), 4),
        "macro_f1": round(float(f1_score(truth, predicted, average="macro", zero_division=0)), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-save-model", action="store_true", help="Write metrics only.")
    args = parser.parse_args()

    if not DATA_PATH.is_file():
        raise SystemExit(f"{DATA_PATH} is missing. Run `python ml/src/build_training_data.py` first.")
    frame = pd.read_csv(DATA_PATH, dtype=str).fillna("")
    required = {"data_origin", "split", "target_career_id", "skills"}
    missing = required - set(frame.columns)
    if missing:
        raise SystemExit(f"Training table is missing columns: {sorted(missing)}")
    category_of = {}
    if CATALOG_PATH.is_file():
        catalog = pd.read_csv(CATALOG_PATH, dtype=str)
        category_of = dict(zip(catalog["career_id"], catalog["category"]))

    splits = {name: frame[frame["split"] == name] for name in ("train", "validation", "test")}
    for name, rows in splits.items():
        if rows.empty:
            raise SystemExit(f"The {name} split is empty.")
    unseen = set(splits["test"]["target_career_id"]) - set(splits["train"]["target_career_id"])
    if unseen:
        raise SystemExit(f"{len(unseen)} careers appear in the test split but not in training.")
    print(f"[ML] {len(frame):,} profiles, {frame['target_career_id'].nunique()} careers. "
          f"train {len(splits['train']):,} | validation {len(splits['validation']):,} | test {len(splits['test']):,}")
    print(f"[ML] By origin: {frame['data_origin'].value_counts().to_dict()}")

    comparison = {}
    best = None
    for feature_set, columns in FEATURE_SETS.items():
        train_text = feature_text(splits["train"], columns)
        valid_text = feature_text(splits["validation"], columns)
        for model_name, classifier in make_models().items():
            pipeline = make_pipeline(classifier).fit(train_text, splits["train"]["target_career_id"])
            train_scores = evaluate(pipeline, train_text, splits["train"]["target_career_id"])
            valid_scores = evaluate(pipeline, valid_text, splits["validation"]["target_career_id"])
            key = f"{model_name} | {feature_set}"
            comparison[key] = {
                "model": model_name, "feature_set": feature_set,
                "train_top1_accuracy": train_scores["top1_accuracy"],
                "validation": valid_scores,
                "train_validation_gap": round(train_scores["top1_accuracy"] - valid_scores["top1_accuracy"], 4),
            }
            print(f"  {key:<42} train {train_scores['top1_accuracy']:.3f} | "
                  f"valid top-1 {valid_scores['top1_accuracy']:.3f} top-3 {valid_scores['top3_accuracy']:.3f} "
                  f"macro-F1 {valid_scores['macro_f1']:.3f}")
            # Choose within the full feature set; skills_only is reported as a harder check.
            if feature_set == "full" and (best is None or valid_scores["macro_f1"] > best["macro_f1"]):
                best = {"key": key, "model": model_name, "macro_f1": valid_scores["macro_f1"]}

    print(f"\n[ML] Selected on validation macro-F1: {best['key']}")
    train_val = pd.concat([splits["train"], splits["validation"]])
    test = splits["test"]
    final = {}
    final_pipelines = {}
    for feature_set, columns in FEATURE_SETS.items():
        pipeline = make_pipeline(make_models()[best["model"]]).fit(
            feature_text(train_val, columns), train_val["target_career_id"])
        final_pipelines[feature_set] = pipeline
        by_origin = {
            origin: evaluate(pipeline, feature_text(rows, columns), rows["target_career_id"])
            for origin, rows in test.groupby("data_origin")
        }
        by_origin.setdefault("real", {"rows": 0})
        final[feature_set] = {"all_test_rows": evaluate(pipeline, feature_text(test, columns), test["target_career_id"]),
                              "by_data_origin": by_origin}

    # Sector-level view: is the predicted career at least in the right category?
    full_pipeline = final_pipelines["full"]
    predicted = full_pipeline.predict(feature_text(test, FEATURE_SETS["full"]))
    sector_accuracy = None
    if category_of:
        truth_sector = test["target_career_id"].map(category_of).to_numpy()
        predicted_sector = np.array([category_of.get(career_id, "") for career_id in predicted])
        sector_accuracy = round(float(np.mean(truth_sector == predicted_sector)), 4)

    majority = splits["train"]["target_career_id"].value_counts().idxmax()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    summary = {
        "model_version": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "caveat": CAVEAT,
        "dataset_sha256": sha256_file(DATA_PATH),
        "profiles": int(len(frame)),
        "careers": int(frame["target_career_id"].nunique()),
        "data_origin_counts": frame["data_origin"].value_counts().to_dict(),
        "split_sizes": {name: int(len(rows)) for name, rows in splits.items()},
        "selection_metric": "validation macro-F1 on the full feature set",
        "selected_model": best["model"],
        "model_comparison_on_validation": comparison,
        "final_test_metrics": final,
        "test_category_accuracy_full_features": sector_accuracy,
        "majority_class_baseline_top1_accuracy": round(float(np.mean(test["target_career_id"] == majority)), 4),
        "used_by_backend": False,
    }
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    metrics_path = METRICS_DIR / "catalogue_model_metrics.json"
    metrics_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"[ML] Final test (full features): {final['full']['all_test_rows']}")
    print(f"[ML] Final test (skills only):   {final['skills_only']['all_test_rows']}")
    print(f"[ML] Real rows in test: {final['full']['by_data_origin']['real']['rows']}. {CAVEAT}")
    print(f"[ML] Saved metrics to {metrics_path}")
    if not args.no_save_model:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model_path = MODEL_DIR / "catalogue_model.pkl"
        joblib.dump(full_pipeline, model_path)
        print(f"[ML] Saved model to {model_path} (not loaded by the backend)")


if __name__ == "__main__":
    main()
