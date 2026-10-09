import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend/ or ml/ or project root
BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
ML_DIR = ROOT_DIR / "ml"

load_dotenv(BACKEND_DIR / ".env")
load_dotenv(ML_DIR / ".env")
load_dotenv(ROOT_DIR / ".env")


class Settings:
    PROJECT_NAME: str = "Strathmore Intelligent AI Career Coach API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ]

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'career_coach.db'}")

    # AI Models
    MODEL_DIR: Path = ML_DIR / "models" / "career-retriever"
    CHUNKS_PATH: Path = ML_DIR / "data" / "processed" / "chunks.json"
    CHUNK_EMBEDDINGS_PATH: Path = ML_DIR / "data" / "processed" / "chunk_embeddings.npy"
    CHUNK_EMBEDDINGS_MANIFEST_PATH: Path = ML_DIR / "data" / "processed" / "chunk_embeddings_manifest.json"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours


settings = Settings()
