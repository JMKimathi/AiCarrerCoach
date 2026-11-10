import json
import logging
import os
import random
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from backend.app.config import settings

sys.path.append(str(settings.MODEL_DIR.parents[1] / "src"))
from embedding_cache import load_or_create_embeddings

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    RAG engine for the FastAPI backend.
    Uses the fine-tuned sentence-transformer retriever and Gemini LLM.
    """

    _instance: Optional["RAGEngine"] = None

    def __init__(self):
        print(f"[RAG] Loading fine-tuned retriever from: {settings.MODEL_DIR}")
        self.model = SentenceTransformer(str(settings.MODEL_DIR))

        if not settings.CHUNKS_PATH.exists():
            raise FileNotFoundError(f"[RAG] Chunks file not found at: {settings.CHUNKS_PATH}")

        self.chunks: List[Dict[str, Any]] = json.loads(settings.CHUNKS_PATH.read_text(encoding="utf-8"))
        self.corpus = [c["content"] for c in self.chunks]

        print(f"[RAG] Loading or building embeddings for {len(self.corpus)} knowledge chunks...")
        self.corpus_embeddings = load_or_create_embeddings(
            self.chunks,
            settings.CHUNKS_PATH,
            settings.MODEL_DIR,
            settings.CHUNK_EMBEDDINGS_PATH,
            settings.CHUNK_EMBEDDINGS_MANIFEST_PATH,
            model=self.model,
        )
        print("[RAG] Knowledge Base Vector Index is READY.")

    @classmethod
    def get_instance(cls) -> "RAGEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
        scores = self.corpus_embeddings @ query_emb
        top_indices = np.argsort(-scores)[:top_k]

        results = []
        for idx in top_indices:
            item = dict(self.chunks[idx])
            item["score"] = float(scores[idx])
            results.append(item)
        return results

    def generate_response(
        self,
        query: str,
        student_name: str = "Student",
        course: str = "BSc Computer Science",
        career_goal: str = "Roles in AI and data",
        top_k: int = 5,
        supplemental_docs: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        normalized_query = " ".join(query.lower().strip().split())
        normalized_query = re.sub(r"[.!?,…]+$", "", normalized_query)
        english_greetings = {
            "hi", "hi there", "hello", "hello there", "hey", "hey there", "hey coach",
            "hello coach", "good morning", "good afternoon", "good evening", "good day",
            "how are you", "how are you doing", "how is it going", "how's it going",
            "what's up", "whats up", "howdy", "yo", "sup",
        }
        swahili_greetings = {
            "habari", "habari yako", "habari za asubuhi", "habari za mchana",
            "habari za jioni", "hujambo", "jambo", "niaje", "mambo", "sasa",
            "uko aje", "uko vipi", "shikamoo", "salama", "za asubuhi", "za mchana",
            "asubuhi njema", "mchana mwema", "jioni njema",
        }
        if normalized_query in english_greetings:
            return {
                "response": random.choice([
                    "Hi! What would you like help with today: exploring careers, building skills, improving your CV, or preparing for an interview?",
                    "Hello! Tell me what you’re working toward, and we can take it one step at a time. Are you exploring options or focused on a particular career?",
                    "Hey, good to hear from you. I can help you compare career paths, plan what to learn next, or practise for an interview. Where should we start?",
                    "Hi there! If you’re not sure where to begin, tell me what subjects or activities you enjoy and I’ll help you explore some possible paths.",
                    "Hello! You can ask me about Kenyan occupation options, the skills a role uses, study plans, CVs, or interviews. What’s on your mind?",
                    "I’m doing well, thanks for asking! What would be useful right now: career ideas, advice for a specific role, or help preparing for an opportunity?",
                ]),
                "sources": [],
                "source_details": [],
            }
        if normalized_query in swahili_greetings:
            if normalized_query == "shikamoo":
                greeting_reply = "Marahaba! Karibu. Ungependa kuchunguza taaluma, kujua ujuzi unaohitajika, kuboresha CV, au kufanya mazoezi ya usaili?"
            elif normalized_query == "hujambo":
                greeting_reply = "Sijambo, asante! Na wewe je? Naweza kukusaidia kuchunguza taaluma, kuboresha CV, au kujiandaa kwa usaili."
            elif normalized_query in {"mambo", "niaje", "sasa"}:
                greeting_reply = "Poa! Karibu. Ungependa tuzungumzie taaluma, ujuzi, CV, au maandalizi ya usaili?"
            elif normalized_query == "jambo":
                greeting_reply = "Jambo! Karibu. Naweza kukusaidia kuchunguza taaluma au kupanga hatua inayofuata. Ungependa tuanze na nini?"
            else:
                greeting_reply = "Nzuri, asante! Na wewe je? Naweza kukusaidia kuchunguza taaluma, kupanga ujuzi wa kujifunza, kuboresha CV, au kujiandaa kwa usaili. Ungependa tuanze na nini?"
            return {"response": greeting_reply, "sources": [], "source_details": []}
        if normalized_query in {"thanks", "thank you", "thank you coach", "thanks coach"}:
            return {
                "response": random.choice([
                    "You’re welcome! Would you like to explore another career option or work through a next step?",
                    "You’re welcome. I’m here if you want to keep going with your career plan.",
                    "Happy to help! What else would you like to figure out?",
                ]),
                "sources": [],
                "source_details": [],
            }
        if normalized_query in {"asante", "asante sana", "ahsante", "shukrani"}:
            return {
                "response": random.choice([
                    "Karibu! Ungependa kuchunguza chaguo jingine la taaluma au tuangalie hatua inayofuata?",
                    "Karibu sana. Niko hapa kukusaidia kuendelea na mpango wako wa taaluma.",
                    "Nafurahi kusaidia! Kuna jambo lingine ungependa kufahamu?",
                ]),
                "sources": [],
                "source_details": [],
            }

        retrieved_docs = self.retrieve(query, top_k=top_k)
        seen_titles = {doc.get("title", "Career Resource") for doc in retrieved_docs}
        for doc in supplemental_docs or []:
            title = doc.get("title", "Career Resource")
            if title not in seen_titles:
                retrieved_docs.append(doc)
                seen_titles.add(title)

        context_texts = []
        unique_sources = []
        source_details = []

        for doc in retrieved_docs:
            source_title = doc.get("title", "Career Resource")
            if source_title not in unique_sources:
                unique_sources.append(source_title)
            context_texts.append(f"--- Source: {source_title} ---\n{doc['content']}")
            source_details.append({
                "title": source_title,
                "score": round(doc["score"], 4),
                "content_snippet": doc["content"][:160].strip() + "...",
            })

        full_context = "\n\n".join(context_texts)

        # If user provides GEMINI_API_KEY
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")

        if api_key:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=api_key)
                system_instruction = (
                    "You are a warm, practical university career coach who speaks naturally to a student. "
                    "Reply in the language of the student's latest message, including English or Kiswahili. "
                    "If the student mixes both, follow the main language they used and keep technical terms clear. "
                    "Answer the student's latest question directly, in a few clear sentences or short paragraphs. "
                    "Use a list only when it makes steps easier to follow. Do not repeat the student's profile or "
                    "introduce yourself in every reply. Treat the recent conversation as context and respond to "
                    "follow-up questions without restarting the discussion. Personalize guidance using the profile "
                    "when relevant. Treat retrieved written guides and synthetic pathway examples as exploration material, not automatically verified facts. "
                    "The structured pathway dataset is synthetic and illustrative: never present its qualification, licensing, application-channel, "
                    "entry-role, interview, or progression examples as official Kenyan rules, live vacancies, or guaranteed routes. "
                    "For local requirements, current vacancies, salaries, admissions, or licensing, say that current verification is needed; do not invent details. "
                    "When suggesting several options, use distinct occupation titles supported by the retrieved passages. "
                    "For broad career-exploration questions, offer up to three distinct options when the context supports them, "
                    "briefly explain each, and ask which one the student wants to explore; do not claim a personal fit without evidence. "
                    "When pathway examples come from the synthetic dataset, call them illustrative and encourage the student to verify local specifics. "
                    "When a student asks for a career pathway, organize available guidance around role overview, relevant "
                    "skills, education or licensing, application routes, interview preparation, and role-specific CV advice. "
                    "Only state a section when the retrieved sources support it; clearly say when local requirements or current "
                    "application details are not in the knowledge base. If the course and goal are both missing and the student "
                    "asks for personal recommendations, ask one focused question about their course or the field they want to explore. "
                    "Be encouraging, specific, and professional, with a focus on students and Kenya."
                )

                history_text = "\n".join(
                    f"{turn['role'].title()}: {turn['text']}"
                    for turn in (conversation_history or [])
                ) or "No earlier messages in this conversation."

                prompt = (
                    f"Student Profile:\n"
                    f"- Name: {student_name}\n"
                    f"- Course: {course}\n"
                    f"- Career Goal: {career_goal}\n\n"
                    f"Recent conversation:\n{history_text}\n\n"
                    f"Career guidance context (written guides and synthetic illustrative pathways; verify local facts):\n"
                    f"{full_context}\n\n"
                    f"Student's latest message: {query}\n\n"
                    f"Reply naturally to that latest message. Keep it useful and conversational, and do not dump or quote the source passages."
                )

                response = None
                for model_index, model_name in enumerate(("gemini-3.8-flash", "gemini-3.5-flash-lite")):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                max_output_tokens=700,
                            ),
                        )
                        break
                    except Exception as model_error:
                        status_code = getattr(model_error, "code", None) or getattr(model_error, "status_code", None)
                        can_fallback = model_index == 0 and status_code in (429, 503)
                        if not can_fallback:
                            raise
                        logger.warning(
                            "Gemini model %s returned %s; retrying with fallback model gemini-3.5-flash-lite",
                            model_name,
                            status_code,
                        )
                if response is None:
                    raise RuntimeError("Gemini did not return a response from either configured model")
                answer_text = (response.text or "").strip()
                if not answer_text:
                    raise ValueError("Gemini returned an empty response")
            except Exception as e:
                logger.exception("Gemini response generation failed")
                best_doc = retrieved_docs[0] if retrieved_docs else None
                if best_doc:
                    excerpt = best_doc["content"].strip()
                    excerpt = re.sub(r"(?m)^#{1,6}\s*", "", excerpt)
                    excerpt = re.sub(r"\*\*(.*?)\*\*", r"\1", excerpt)
                    excerpt = excerpt[:500].rsplit(" ", 1)[0]
                    answer_text = (
                        "I’m having trouble generating a conversational reply right now, but I found a relevant "
                        f"guide: {best_doc.get('title', 'Career resource')}.\n\n{excerpt}\n\n"
                        "Tell me a little more about your goal and I can help narrow down the next step."
                    )
                else:
                    answer_text = "I’m having trouble generating a reply right now. Please try again in a moment."
        else:
            best_doc = retrieved_docs[0] if retrieved_docs else None
            if best_doc:
                excerpt = best_doc["content"].strip()[:700]
                answer_text = (
                    "I can still point you to relevant guidance, but the conversational AI service isn’t configured "
                    f"on this computer yet. The closest guide I found is {best_doc.get('title', 'Career resource')}:\n\n"
                    f"{excerpt}"
                )
            else:
                answer_text = "The conversational AI service isn’t configured yet, and I couldn’t find a matching guide."

        return {
            "response": answer_text,
            "sources": unique_sources,
            "source_details": source_details,
        }
