import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "src"))
from config import CHUNKS, TRAINED_DIR

load_dotenv()


class CareerCoachRAG:
    """
    Retrieval-Augmented Generation (RAG) Service for Strathmore AI Career Coach.
    Uses the fine-tuned sentence-transformer retriever and Gemini LLM.
    """

    def __init__(self, model_dir: Path = TRAINED_DIR, chunks_path: Path = CHUNKS):
        print(f"Loading fine-tuned retriever from: {model_dir}")
        self.retriever = SentenceTransformer(str(model_dir))

        if not chunks_path.exists():
            raise FileNotFoundError(f"Knowledge base chunks not found at: {chunks_path}. Run run_pipeline.py first.")

        self.chunks: List[Dict[str, Any]] = json.loads(chunks_path.read_text(encoding="utf-8"))
        self.corpus = [c["content"] for c in self.chunks]
        print(f"Encoding {len(self.corpus)} knowledge chunks for fast in-memory search...")
        self.corpus_embeddings = self.retriever.encode(
            self.corpus, convert_to_numpy=True, normalize_embeddings=True
        )
        print("RAG Knowledge Base ready.")

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Encodes the student's query and performs cosine similarity search.
        """
        query_emb = self.retriever.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
        scores = self.corpus_embeddings @ query_emb
        top_indices = np.argsort(-scores)[:top_k]

        results = []
        for idx in top_indices:
            item = dict(self.chunks[idx])
            item["score"] = float(scores[idx])
            results.append(item)
        return results

    def generate_grounded_response(
        self,
        query: str,
        student_name: str = "John",
        course: str = "BSc Computer Science",
        career_goal: str = "Roles in AI and data",
        top_k: int = 3,
    ) -> Dict[str, Any]:
        """
        Executes the full RAG pipeline:
        1. Retrieve top-k context chunks.
        2. Prompt the LLM grounded in that context.
        3. Returns answer + citations.
        """
        retrieved_docs = self.retrieve(query, top_k=top_k)

        # Build context block
        context_texts = []
        unique_sources = []
        for doc in retrieved_docs:
            source_title = doc.get("title", "Career Resource")
            if source_title not in unique_sources:
                unique_sources.append(source_title)
            context_texts.append(f"--- Document: {source_title} ---\n{doc['content']}")

        full_context = "\n\n".join(context_texts)

        # Check for Gemini API Key
        gemini_api_key = os.getenv("GEMINI_API_KEY")

        if gemini_api_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=gemini_api_key)

                system_instruction = (
                    "You are the Strathmore University Intelligent Career Guidance Coach. "
                    "Your role is to give supportive, highly actionable, and accurate career advice "
                    "tailored to university students in Kenya. "
                    "You MUST ground your guidance directly in the verified knowledge base passages provided. "
                    "If the knowledge base provides specific rules (e.g. CV page length, STAR format, local job trends), "
                    "adhere strictly to them. Be concise, motivating, and professional."
                )

                prompt = (
                    f"Student Profile:\n"
                    f"- Name: {student_name}\n"
                    f"- Course: {course}\n"
                    f"- Career Goal: {career_goal}\n\n"
                    f"Verified Knowledge Base Context:\n"
                    f"{full_context}\n\n"
                    f"Student Query: {query}\n\n"
                    f"Provide tailored guidance grounded in the context above:"
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3,
                    ),
                )
                answer_text = response.text.strip()
            except Exception as e:
                answer_text = (
                    f"Retrieved relevant resources successfully, but encountered an API issue with LLM generation: {e}\n\n"
                    f"Relevant knowledge summary:\n" + "\n".join([f"• {d['content'][:150]}..." for d in retrieved_docs])
                )
        else:
            # Informative fallback when GEMINI_API_KEY is not yet configured
            answer_text = (
                f"Based on your profile ({course}, aiming for {career_goal}), here is guidance grounded in our verified career knowledge base:\n\n"
                + "\n\n".join([f"• From **{d['title']}**:\n{d['content']}" for d in retrieved_docs[:2]])
                + "\n\n*(Note: Set GEMINI_API_KEY in .env for full conversational synthesis)*"
            )

        return {
            "query": query,
            "answer": answer_text,
            "sources": unique_sources,
            "retrieved_chunks": retrieved_docs,
        }


if __name__ == "__main__":
    coach = CareerCoachRAG()
    test_question = "How should I structure my CV for software engineering internships?"
    print(f"\nAsking: '{test_question}'")
    result = coach.generate_grounded_response(test_question)
    print("\n--- ANSWER ---")
    print(result["answer"])
    print("\n--- SOURCES CITED ---")
    print(result["sources"])
