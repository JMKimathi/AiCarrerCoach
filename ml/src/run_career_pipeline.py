"""Generate the synthetic pathway library and career catalogue, then prepare the searchable index."""

import argparse
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


CATALOGUE_STEPS = [
    ("Build the career catalogue and skills", "build_career_catalogue.py"),
    ("Build education requirements and pathway stages", "build_career_pathways.py"),
    ("Build CV templates", "build_cv_templates.py"),
    ("Build the interview question bank", "build_interview_questions.py"),
    ("Link official sources to careers", "build_career_resources.py"),
    ("Build opportunity templates", "build_opportunities.py"),
    ("Build the hybrid training data", "build_training_data.py"),
]


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(f"\n=== {label} ===", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-data-build", action="store_true",
                        help="Use the already generated synthetic dataset.")
    parser.add_argument("--skip-catalogue-build", action="store_true",
                        help="Use the already generated career catalogue tables in ml/data/careers.")
    parser.add_argument("--train-retriever", action="store_true",
                        help="Run the separate question-answer retrieval fine-tuning pipeline.")
    args = parser.parse_args()

    if not args.skip_data_build:
        run_step(
            "Generate the unified synthetic career pathway dataset",
            [sys.executable, str(ROOT_DIR / "ml" / "src" / "build_synthetic_career_dataset.py")],
            ROOT_DIR,
        )

    if not args.skip_catalogue_build:
        # Order matters: later builders read the role list from the catalogue builder.
        for label, script in CATALOGUE_STEPS:
            run_step(label, [sys.executable, str(ROOT_DIR / "ml" / "src" / script)], ROOT_DIR)

    run_step(
        "Prepare searchable article, pathway and career catalogue chunks",
        [sys.executable, str(ROOT_DIR / "ml" / "src" / "run_pipeline.py"), "--prepare-only"],
        ROOT_DIR,
    )

    if args.train_retriever:
        run_step(
            "Train and evaluate the separate RAG retriever",
            [sys.executable, str(ROOT_DIR / "ml" / "src" / "run_pipeline.py")],
            ROOT_DIR,
        )

    print("\nPipeline stages completed. Review each stage's manifest and metrics before promoting a model.")


if __name__ == "__main__":
    main()
