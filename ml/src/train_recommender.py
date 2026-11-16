"""Train (or retrain) the hybrid recommender's classifier and save it to ml/models/career_recommender.joblib.

Run from the project root:  .\\backend\\.venv\\Scripts\\python.exe ml/src/train_recommender.py
The backend also trains it automatically the first time it is needed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.app.recommender import MODEL_PATH, train_classifier  # noqa: E402

if __name__ == "__main__":
    train_classifier()
    print("Saved", MODEL_PATH)
