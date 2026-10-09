"""Create and validate cached vectors for the backend's RAG knowledge index."""

import hashlib
import json
from pathlib import Path


def _chunk_digest(chunks_path: Path) -> str:
    digest = hashlib.sha256()
    with chunks_path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _model_files(model_dir: Path) -> list[dict]:
    return [
        {
            "path": str(path.relative_to(model_dir)),
            "size": path.stat().st_size,
            "modified_ns": path.stat().st_mtime_ns,
        }
        for path in sorted(model_dir.rglob("*"))
        if path.is_file()
    ]


def cache_is_current(chunks_path: Path, model_dir: Path, cache_path: Path, manifest_path: Path) -> bool:
    if not all(path.is_file() for path in (chunks_path, cache_path, manifest_path)):
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        manifest.get("chunks_sha256") == _chunk_digest(chunks_path)
        and manifest.get("model_files") == _model_files(model_dir)
    )


def load_or_create_embeddings(
    chunks: list[dict],
    chunks_path: Path,
    model_dir: Path,
    cache_path: Path,
    manifest_path: Path,
    model=None,
):
    """Load a matching vector cache, or compute and persist the current index."""
    import numpy as np

    if cache_is_current(chunks_path, model_dir, cache_path, manifest_path):
        try:
            cached = np.load(cache_path, mmap_mode="r")
            if cached.ndim == 2 and cached.shape[0] == len(chunks):
                return cached
        except (OSError, ValueError):
            pass

    if model is None:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(str(model_dir))

    vectors = model.encode(
        [chunk["content"] for chunk in chunks],
        batch_size=64,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_cache = cache_path.with_suffix(cache_path.suffix + ".tmp")
    with temporary_cache.open("wb") as handle:
        np.save(handle, vectors)
    temporary_cache.replace(cache_path)

    manifest = {
        "chunks_sha256": _chunk_digest(chunks_path),
        "model_files": _model_files(model_dir),
        "shape": list(vectors.shape),
    }
    temporary_manifest = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    temporary_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    temporary_manifest.replace(manifest_path)
    return vectors
