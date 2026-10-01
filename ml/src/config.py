from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESOURCES = DATA / "resources"
CHUNKS = DATA / "processed" / "chunks.json"
QA = DATA / "qa_pairs.csv"
MODELS = ROOT / "models"
BASELINE_DIR = MODELS / "minilm-baseline"
TRAINED_DIR = MODELS / "career-retriever"
METRICS = ROOT / "metrics" / "retrieval_metrics.json"


def chunk_text(text: str, max_chars: int = 420) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if buf and len(buf) + len(para) > max_chars:
            chunks.append(buf.strip())
            buf = para
        else:
            buf = f"{buf}\n\n{para}".strip()
    if buf:
        chunks.append(buf.strip())
    return chunks or [text.strip()]
