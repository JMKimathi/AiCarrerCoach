"""
Interactive Demo Script for Strathmore AI Career Coach Model
Run this in front of your supervisor or lecturer to show the trained retriever in action.
"""

import sys
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT / "src"))

from rag_service import CareerCoachRAG


def main():
    print("=" * 65)
    print("   STRATHMORE UNIVERSITY — AI CAREER COACH (RAG DEMO)   ")
    print("=" * 65)
    print("Loading fine-tuned model from: ml/models/career-retriever/ ...")
    coach = CareerCoachRAG()
    print("\nModel successfully loaded into memory!")
    print("Type any career or interview question below (or 'exit' to quit).\n")

    sample_questions = [
        "How should I structure my CV for software engineering?",
        "What is the STAR method for behavioural interviews?",
        "What entry-level roles can I get in Data Science in Kenya?",
        "How long should my cover letter be?",
    ]

    print("Suggested test questions to try:")
    for i, sq in enumerate(sample_questions, 1):
        print(f"  {i}. {sq}")
    print("-" * 65)

    while True:
        try:
            query = input("\nEnter student question: ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit", "q"):
                print("Exiting demo. Goodbye!")
                break

            print("\nSearching knowledge base with fine-tuned retriever...")
            result = coach.generate_grounded_response(query)

            print("\n[GROUNDED ANSWER]:")
            print(result["answer"])

            print("\n[VERIFIED SOURCES RETRIEVED]:")
            for src in result["sources"]:
                print(f"  * {src}")

            print("\n[RETRIEVAL CONFIDENCE / COSINE SCORES]:")
            for doc in result["retrieved_chunks"]:
                print(f"  * {doc['title']}: {doc['score']:.4f}")

            print("-" * 65)

        except KeyboardInterrupt:
            print("\nExiting demo.")
            break


if __name__ == "__main__":
    main()
