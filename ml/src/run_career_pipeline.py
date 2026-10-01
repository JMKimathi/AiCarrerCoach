"""Run the career-data preparation pipeline and optionally train its models.

Examples:
  python ml/src/run_career_pipeline.py --input-dir "C:/Users/Mwiti/Downloads/Datasets"
  python ml/src/run_career_pipeline.py --input-dir "C:/Users/Mwiti/Downloads/Datasets" --train-classifier
  python ml/src/run_career_pipeline.py --input-dir "C:/Users/Mwiti/Downloads/Datasets" --train-classifier --promote-model

The job-market tables, O*NET occupation profiles, career classifier, and RAG
retriever remain separate artifacts with separate evaluation purposes.
"""

import argparse
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(f"\n=== {label} ===", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=Path.home() / "Downloads" / "Datasets")
    parser.add_argument("--skip-data-build", action="store_true")
    parser.add_argument("--train-classifier", action="store_true",
                        help="Train a new classifier from ml/data/tech_career_dataset.csv.")
    parser.add_argument("--promote-model", action="store_true",
                        help="Promote the trained classifier after saving versioned evaluation artifacts.")
    parser.add_argument("--train-retriever", action="store_true",
                        help="Run the separate question-answer retrieval fine-tuning pipeline.")
    args = parser.parse_args()

    if args.promote_model and not args.train_classifier:
        parser.error("--promote-model requires --train-classifier")

    if not args.skip_data_build:
        run_step(
            "Build normalized O*NET and LinkedIn-derived tables",
            [sys.executable, str(ROOT_DIR / "ml" / "src" / "build_career_datasets.py"),
             "--input-dir", str(args.input_dir)],
            ROOT_DIR,
        )

    if args.train_classifier:
        command = [sys.executable, str(ROOT_DIR / "ml" / "src" / "train_career_model.py")]
        if args.promote_model:
            command.append("--promote")
        run_step("Train and evaluate versioned career-role classifier", command, ROOT_DIR)

    if args.train_retriever:
        run_step(
            "Train and evaluate the separate RAG retriever",
            [sys.executable, str(ROOT_DIR / "ml" / "src" / "run_pipeline.py")],
            ROOT_DIR,
        )

    print("\nPipeline stages completed. Review each stage's manifest and metrics before promoting a model.")


if __name__ == "__main__":
    main()
