"""
Ingests 'Software Questions.csv' into the RAG knowledge base.
Appends formatted Q&A chunks into ml/data/processed/chunks.json
and ensures the RAG retriever index stays synchronized.
"""

import json
import re
from pathlib import Path
import pandas as pd

CSV_PATH = Path(r"C:\Users\Mwiti\Downloads\Datasets\Software Questions.csv")
CHUNKS_PATH = Path("ml/data/processed/chunks.json")
BACKEND_CHUNKS_PATH = Path("backend/app") / "chunks.json"  # If any


def slugify(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def ingest_questions():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Software Questions CSV not found at {CSV_PATH}")

    df = pd.read_csv(CSV_PATH, encoding="latin1")
    print(f"Loaded {len(df)} questions from {CSV_PATH}")

    # Load existing chunks if available
    if CHUNKS_PATH.exists():
        existing_chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
        print(f"Existing knowledge chunks: {len(existing_chunks)}")
    else:
        existing_chunks = []

    # Filter out any previously ingested technical interview questions to prevent duplicates
    base_chunks = [c for c in existing_chunks if not c.get("chunk_id", "").startswith("tech_qa_")]

    new_chunks = []
    for idx, row in df.iterrows():
        q_num = row.get("Question Number", idx + 1)
        question = str(row.get("Question", "")).strip()
        answer = str(row.get("Answer", "")).strip()
        category = str(row.get("Category", "Software Engineering")).strip()
        difficulty = str(row.get("Difficulty", "Medium")).strip()

        cat_slug = slugify(category)
        chunk_id = f"tech_qa_{cat_slug}_{q_num}"
        resource_id = f"tech_interviews_{cat_slug}"
        title = f"Technical Interview: {category} ({difficulty})"

        content = (
            f"# Technical Interview Preparation: {category}\n\n"
            f"**Question:** {question}\n\n"
            f"**Difficulty Level:** {difficulty}\n\n"
            f"**Concept & Model Answer:**\n{answer}"
        )

        new_chunks.append({
            "chunk_id": chunk_id,
            "resource_id": resource_id,
            "title": title,
            "category": category,
            "difficulty": difficulty,
            "content": content,
        })

    total_chunks = base_chunks + new_chunks
    CHUNKS_PATH.write_text(json.dumps(total_chunks, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Successfully updated {CHUNKS_PATH}:")
    print(f"  Base chunks: {len(base_chunks)}")
    print(f"  Added software interview questions: {len(new_chunks)}")
    print(f"  Total chunks in knowledge base: {len(total_chunks)}")


if __name__ == "__main__":
    ingest_questions()
