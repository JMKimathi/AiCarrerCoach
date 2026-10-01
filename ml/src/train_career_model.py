"""
ML Career Prediction Model Training & Multi-Model Comparison Pipeline
Trains and rigorously benchmarks 4 candidate classifiers:
1. Logistic Regression (Multinomial with L2 Regularization)
2. Calibrated Linear Support Vector Classifier (LinearSVC + Platt Scaling)
3. Multinomial Naive Bayes (with Laplace Smoothing)
4. Random Forest Classifier (Constrained depth to avoid overfitting)

    Selects with validation macro-F1, then reports a separate held-out test set.
Exports comparison metrics, confusion matrices, and serializes the winning pipeline.
"""

import json
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import joblib

from sklearn.base import clone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.naive_bayes import MultinomialNB
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT_DIR / "ml" / "data" / "tech_career_dataset.csv"
METRICS_DIR = ROOT_DIR / "ml" / "metrics"
MODEL_DIR = ROOT_DIR / "ml" / "models"
BACKEND_MODEL_DIR = ROOT_DIR / "backend" / "app"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_split(feature_text: str, label: str, seed: str = "career-split-v1") -> str:
    """Keep each deduplicated profile in the same split when data grows."""
    digest = hashlib.sha256(f"{seed}\0{label}\0{feature_text}".encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "big") % 100
    if bucket < 15:
        return "test"
    if bucket < 30:
        return "validation"
    return "train"


def train_and_evaluate(promote: bool = False):
    print(f"[ML] Loading dataset from: {DATA_PATH}")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Training dataset not found at {DATA_PATH}. Please run extract_tech_dataset.py first.")

    df = pd.read_csv(DATA_PATH)
    required = {"target_category", "feature_text"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    print(f"[ML] Loaded {len(df):,} records across {df['target_category'].nunique()} categories.")
    print("[ML] Class distribution:\n", df["target_category"].value_counts())
    df = df.dropna(subset=["target_category"]).copy()
    df["target_category"] = df["target_category"].astype(str).str.strip()
    df["feature_text"] = df["feature_text"].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    df = df[(df["feature_text"] != "") & (df["target_category"] != "")]
    conflicting = df.groupby("feature_text")["target_category"].nunique()
    conflicting_texts = set(conflicting[conflicting > 1].index)
    if conflicting_texts:
        raise ValueError(
            f"Found {len(conflicting_texts)} identical profiles with conflicting labels; "
            "resolve these before training."
        )
    original_rows = len(df)
    df = df.drop_duplicates(subset=["feature_text"], keep="first").reset_index(drop=True)
    duplicates_removed = original_rows - len(df)
    print(f"[ML] Removed {duplicates_removed:,} duplicate profiles before splitting.")
    if df.empty:
        raise ValueError("No non-empty labeled profiles remain after cleaning.")

    X = df["feature_text"]
    y = df["target_category"].astype(str)
    class_counts = y.value_counts()
    too_small = class_counts[class_counts < 5]
    if not too_small.empty:
        raise ValueError(f"Need at least 5 unique rows per label for train/validation/test splits: {too_small.to_dict()}")

    # Stable hash partitions keep existing validation/test examples held out
    # across later reruns as new profiles are appended.
    df["_split"] = [stable_split(text, label) for text, label in zip(X, y)]
    split_counts = df["_split"].value_counts().to_dict()
    empty_splits = {name for name in ("train", "validation", "test") if split_counts.get(name, 0) == 0}
    if empty_splits:
        raise ValueError(f"Stable split produced empty partitions: {sorted(empty_splits)}")
    split_data = {}
    for split_name in ("train", "validation", "test"):
        rows = df[df["_split"] == split_name]
        split_labels = set(rows["target_category"])
        missing_labels = sorted(set(y) - split_labels)
        if missing_labels:
            raise ValueError(f"Stable {split_name} partition is missing classes: {missing_labels}")
        split_data[split_name] = (rows["feature_text"], rows["target_category"].astype(str))
    X_train, y_train = split_data["train"]
    X_valid, y_valid = split_data["validation"]
    X_test, y_test = split_data["test"]
    train_val_rows = df[df["_split"].isin(["train", "validation"])]
    X_train_val = train_val_rows["feature_text"]
    y_train_val = train_val_rows["target_category"].astype(str)
    print(f"[ML] Stable splits — train: {len(X_train):,} | validation: {len(X_valid):,} | final test: {len(X_test):,}")

    # Anti-overfitting / Anti-underfitting TF-IDF configuration:
    # - sublinear_tf=True: log-scale term frequencies to prevent high-frequency skills from dominating
    # - min_df=3: ignores rare typos/noise (anti-overfitting)
    # - max_df=0.85: ignores ubiquitous terms across all classes
    # - ngram_range=(1, 2): captures both single skills ('python') and compound phrases ('machine learning', 'cloud security')
    tfidf_params = {
        "sublinear_tf": True,
        "min_df": 3,
        "max_df": 0.85,
        "ngram_range": (1, 2),
        "max_features": 8000,
    }

    # Define candidate model architectures with controlled regularization
    models = {
        "Logistic Regression (L2)": LogisticRegression(
            C=1.0,  # Standard L2 regularization to prevent coefficient explosion
            max_iter=1000,
            solver="lbfgs",
            random_state=42,
        ),
        "Calibrated LinearSVC": CalibratedClassifierCV(
            estimator=LinearSVC(C=0.5, dual="auto", max_iter=2000, random_state=42),
            method="sigmoid",
            cv=3,
        ),
        "Multinomial Naive Bayes": MultinomialNB(
            alpha=0.5  # Moderate Laplace smoothing
        ),
        "Random Forest (Depth-limited)": RandomForestClassifier(
            n_estimators=120,
            max_depth=25,  # Strict depth limit to prevent memorizing training set
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
        ),
    }

    results = {}

    print("\n" + "=" * 70)
    print(f"{'Model Architecture':<32} | {'Train Acc':<10} | {'Valid Acc':<9} | {'Valid Macro F1':<14}")
    print("-" * 70)

    for name, clf in models.items():
        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(**tfidf_params)),
            ("clf", clf),
        ])

        # Fit model
        pipe.fit(X_train, y_train)
        # Predictions
        train_preds = pipe.predict(X_train)
        valid_preds = pipe.predict(X_valid)

        train_acc = accuracy_score(y_train, train_preds)
        prec, rec, weighted_f1, _ = precision_recall_fscore_support(
            y_valid, valid_preds, average="weighted", zero_division=0
        )
        macro_prec, macro_rec, macro_f1, _ = precision_recall_fscore_support(
            y_valid, valid_preds, average="macro", zero_division=0
        )

        results[name] = {
            "train_accuracy": round(float(train_acc), 4),
            "validation_accuracy": round(float(accuracy_score(y_valid, valid_preds)), 4),
            "train_validation_gap": round(float(train_acc - accuracy_score(y_valid, valid_preds)), 4),
            "validation_weighted_precision": round(float(prec), 4),
            "validation_weighted_recall": round(float(rec), 4),
            "validation_weighted_f1": round(float(weighted_f1), 4),
            "validation_macro_precision": round(float(macro_prec), 4),
            "validation_macro_recall": round(float(macro_rec), 4),
            "validation_macro_f1": round(float(macro_f1), 4),
        }

        print(f"{name:<32} | {train_acc*100:6.2f}%   | {accuracy_score(y_valid, valid_preds)*100:6.2f}%  | {macro_f1*100:6.2f}%")

    print("=" * 70)

    # Select only with validation macro-F1. The final test set is evaluated once.
    best_name = max(results.keys(), key=lambda k: results[k]["validation_macro_f1"])
    best_pipe = Pipeline([
        ("tfidf", TfidfVectorizer(**tfidf_params)),
        ("clf", clone(models[best_name])),
    ])
    best_pipe.fit(X_train_val, y_train_val)
    print(f"\nModel selected on validation macro-F1: {best_name}")

    # Generate Detailed Classification Report for Best Model
    y_best_pred = best_pipe.predict(X_test)
    test_accuracy = accuracy_score(y_test, y_best_pred)
    test_weighted = precision_recall_fscore_support(y_test, y_best_pred, average="weighted", zero_division=0)
    test_macro = precision_recall_fscore_support(y_test, y_best_pred, average="macro", zero_division=0)
    majority_label = y_train.value_counts().idxmax()
    majority_accuracy = accuracy_score(y_test, [majority_label] * len(y_test))
    print(f"Final held-out test accuracy: {test_accuracy:.3f} | macro-F1: {test_macro[2]:.3f} | weighted-F1: {test_weighted[2]:.3f} | majority baseline accuracy: {majority_accuracy:.3f}")
    report_dict = classification_report(y_test, y_best_pred, output_dict=True, zero_division=0)
    print("\nDetailed Per-Class Performance:")
    print(classification_report(y_test, y_best_pred, zero_division=0))

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_metrics_dir = METRICS_DIR / "career-model" / run_id
    run_model_dir = MODEL_DIR / "career-model" / run_id
    run_metrics_dir.mkdir(parents=True, exist_ok=True)
    run_model_dir.mkdir(parents=True, exist_ok=True)
    summary_data = {
        "model_version": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_comparison": results,
        "selected_best_model": best_name,
        "selection_metric": "validation_macro_f1",
        "final_test_metrics": {
            "accuracy": round(float(test_accuracy), 4),
            "majority_baseline_accuracy": round(float(majority_accuracy), 4),
            "macro_precision": round(float(test_macro[0]), 4),
            "macro_recall": round(float(test_macro[1]), 4),
            "macro_f1": round(float(test_macro[2]), 4),
            "weighted_precision": round(float(test_weighted[0]), 4),
            "weighted_recall": round(float(test_weighted[1]), 4),
            "weighted_f1": round(float(test_weighted[2]), 4),
        },
        "best_model_classification_report": report_dict,
        "classes": sorted(list(best_pipe.classes_)),
        "dataset_size": len(df),
        "duplicate_profiles_removed": duplicates_removed,
        "source_distribution": df["source"].fillna("(missing)").value_counts().to_dict() if "source" in df.columns else {},
        "label_distribution": df["target_category"].value_counts().to_dict(),
        "split_strategy": "stable SHA-256 bucket of label and exact feature text (career-split-v1)",
        "split_sizes": split_counts,
        "train_size": len(X_train),
        "validation_size": len(X_valid),
        "test_size": len(X_test),
        "dataset_sha256": sha256_file(DATA_PATH),
        "probability_calibrated": False,
        "promotion_requested": promote,
    }
    metrics_json_path = run_metrics_dir / "career_model_metrics.json"
    metrics_json_path.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
    print(f"Saved metrics summary to: {metrics_json_path}")

    # Keep all artifacts for each training run so future rounds can be compared.
    plot_model_comparison(results, best_name, run_metrics_dir / "career_model_comparison.png")

    plot_confusion_matrix(y_test, y_best_pred, best_pipe.classes_, best_name, run_metrics_dir / "confusion_matrix.png")

    best_model_path = run_model_dir / "career_model.pkl"
    joblib.dump(best_pipe, best_model_path)
    print(f"Saved versioned model artifact to: {best_model_path}")
    if promote:
        BACKEND_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        backend_model_path = BACKEND_MODEL_DIR / "career_model.pkl"
        staged_path = BACKEND_MODEL_DIR / "career_model.pkl.new"
        joblib.dump(best_pipe, staged_path)
        staged_path.replace(backend_model_path)
        print(f"Promoted version {run_id} to backend at: {backend_model_path}")
    else:
        print("Model was not promoted. Re-run with --promote after reviewing the held-out metrics.")

    # Run quick sanity inference
    test_profile = "Qualifications: BSc Computer Science. Experience: 0 to 1 Years. Skills: Python, SQL, pandas, PyTorch, Machine Learning, scikit-learn, Data Visualisation."
    probs = best_pipe.predict_proba([test_profile])[0]
    top_indices = np.argsort(-probs)[:3]
    print("\nSanity Check Inference Test:")
    print(f"Input: {test_profile}")
    for idx in top_indices:
        print(f"  -> {best_pipe.classes_[idx]}: {probs[idx]*100:.2f}%")


def plot_model_comparison(results: dict, best_name: str, out_path: Path):
    names = list(results.keys())
    train_accs = [results[n]["train_accuracy"] * 100 for n in names]
    validation_accs = [results[n]["validation_accuracy"] * 100 for n in names]
    validation_f1s = [results[n]["validation_macro_f1"] * 100 for n in names]

    x = np.arange(len(names))
    width = 0.25

    plt.figure(figsize=(12, 6))
    plt.bar(x - width, train_accs, width, label="Train Accuracy", color="#3b82f6", alpha=0.85)
    plt.bar(x, validation_accs, width, label="Validation Accuracy", color="#10b981", alpha=0.85)
    plt.bar(x + width, validation_f1s, width, label="Validation Macro F1", color="#8b5cf6", alpha=0.85)

    plt.ylabel("Score (%)", fontsize=12)
    plt.title("Career Model Selection: Training vs Validation", fontsize=14, fontweight="bold")
    plt.xticks(x, [n.replace(" ", "\n") for n in names], fontsize=10)
    plt.ylim(0, 105)
    plt.legend(loc="lower right", frameon=True)
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()

    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved comparison plot to: {out_path}")


def plot_confusion_matrix(y_true, y_pred, classes, model_name, out_path: Path):
    from sklearn.metrics import ConfusionMatrixDisplay
    fig, ax = plt.subplots(figsize=(12, 10))
    short_labels = [c.replace(" / ", "/").replace("Engineer", "Eng").replace("Developer", "Dev") for c in classes]
    disp = ConfusionMatrixDisplay.from_predictions(
        y_true,
        y_pred,
        labels=classes,
        display_labels=short_labels,
        normalize="true",
        cmap="Blues",
        values_format=".2f",
        xticks_rotation=45,
        ax=ax,
        colorbar=True,
    )
    plt.title(f"Normalized Confusion Matrix ({model_name})", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Predicted Category", fontsize=11)
    plt.ylabel("True Category", fontsize=11)
    plt.tight_layout()

    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"Saved confusion matrix plot to: {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and evaluate a versioned career-role classifier.")
    parser.add_argument("--promote", action="store_true", help="Replace the backend model after evaluation.")
    args = parser.parse_args()
    train_and_evaluate(promote=args.promote)
