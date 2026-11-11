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

# Messages that only ask the coach to carry on with what it was already saying.
_CONTINUE_PHRASES = {
    "continue", "please continue", "continue please", "go on", "go ahead", "carry on", "keep going",
    "proceed", "more", "tell me more", "next", "and then", "then", "finish", "finish it", "resume",
    "continue from where you left off", "continue where you left off", "continue from there",
    "proceed from where you left off", "pick up where you left off", "what next", "what else",
    "endelea", "endelea tafadhali", "tafadhali endelea", "endelea hapo", "halafu", "kisha",
}
# Words that point back at something said earlier, so the message cannot be understood alone.
_REFERENCE_WORDS = {
    "it", "its", "that", "this", "those", "these", "them", "they", "one", "ones", "first", "second",
    "third", "last", "above", "same", "former", "latter", "previous", "earlier", "again", "also",
    "instead", "more", "another", "other", "hiyo", "hilo", "hizo", "hayo", "huyo", "pia", "tena",
}


def _normalise(text: str) -> str:
    return re.sub(r"[.!?,…]+$", "", " ".join(text.lower().strip().split()))


def is_continuation(query: str) -> bool:
    """True when the student is only asking the coach to carry on."""
    return _normalise(query) in _CONTINUE_PHRASES


def is_follow_up(query: str) -> bool:
    """True when a message leans on the earlier conversation: it is short or points back at it."""
    words = re.findall(r"[a-z']+", query.lower())
    return is_continuation(query) or len(words) <= 6 or any(word in _REFERENCE_WORDS for word in words[:12])


def build_retrieval_query(query: str, conversation_history: Optional[List[Dict[str, str]]]) -> str:
    """Give the retriever the topic of the conversation, not just the latest words.

    Searching for "continue" or "tell me more about the second one" alone returns passages
    about nothing in particular. For a follow-up, the search uses the student's most recent
    message that stated a topic, together with the new message.
    """
    earlier = [turn["text"] for turn in (conversation_history or []) if turn.get("role") == "student"]
    if not earlier or not is_follow_up(query):
        return query
    topic = next((text for text in reversed(earlier) if not is_follow_up(text)), earlier[-1])[:400]
    return topic if is_continuation(query) else f"{topic} {query}"


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

        history = conversation_history or []
        continuing = bool(history) and is_continuation(query)
        follow_up = bool(history) and is_follow_up(query)
        retrieved_docs = self.retrieve(build_retrieval_query(query, history), top_k=top_k)
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
                    "Be encouraging, specific, and professional, with a focus on students and Kenya. "
                    "You are in one continuing conversation and you remember it: the recent conversation is what you and "
                    "the student have already said. Work out what words such as 'it', 'that', 'the second one' or 'more' "
                    "refer to from that conversation, and stay on the same subject unless the student changes it. "
                    "When the student asks you to continue, go on or proceed, carry on from exactly where your last reply "
                    "stopped: do not start again, do not repeat what you already said, and do not switch topic. "
                    "If a student message in the conversation has no coach reply after it, the student stopped you before "
                    "reading it; treat their newer message as extra instructions for that same request. "
                    "If the retrieved passages do not relate to the conversation, ignore them rather than changing the subject."
                )

                history_text = "\n".join(
                    f"{turn['role'].title()}: {turn['text']}"
                    for turn in history
                ) or "No earlier messages in this conversation."
                if continuing:
                    closing = (
                        "The student is asking you to carry on. Continue from exactly where your last reply in the "
                        "conversation ended, without repeating it. If that reply was already complete, add the next "
                        "most useful detail on the same subject."
                    )
                elif follow_up:
                    closing = (
                        "This is a follow-up. Answer it in the light of the conversation so far and stay on the same "
                        "subject. Keep it useful and conversational, and do not dump or quote the source passages."
                    )
                else:
                    closing = (
                        "Reply naturally to that latest message. Keep it useful and conversational, and do not dump "
                        "or quote the source passages."
                    )

                prompt = (
                    f"Student Profile:\n"
                    f"- Name: {student_name}\n"
                    f"- Course: {course}\n"
                    f"- Career Goal: {career_goal}\n\n"
                    f"Recent conversation:\n{history_text}\n\n"
                    f"Career guidance context (written guides and synthetic illustrative pathways; verify local facts):\n"
                    f"{full_context}\n\n"
                    f"Student's latest message: {query}\n\n"
                    f"{closing}"
                )

                response = None
                for model_index, model_name in enumerate(("gemini-3.8-flash", "gemini-3.5-flash-lite")):
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                max_output_tokens=1500,
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
                # A reply that ran out of room is trimmed to its last full sentence, and the
                # student is told they can ask for the rest.
                try:
                    finish_reason = str(response.candidates[0].finish_reason or "")
                except (AttributeError, IndexError, TypeError):
                    finish_reason = ""
                if "MAX_TOKENS" in finish_reason.upper():
                    cut = max(answer_text.rfind(". "), answer_text.rfind(".\n"), answer_text.rfind("? "), answer_text.rfind("! "))
                    if cut > len(answer_text) // 2:
                        answer_text = answer_text[:cut + 1]
                    answer_text += "\n\nThere is more to say on this. Send \"continue\" and I will carry on from here."
            except Exception as e:
                logger.exception("Gemini response generation failed")
                best_doc = retrieved_docs[0] if retrieved_docs else None
                if follow_up:
                    # A guide excerpt would look like a change of subject in the middle of a conversation.
                    answer_text = (
                        "I could not write a reply just now, so I have not lost our place. "
                        "Please send that again in a moment."
                    )
                    unique_sources, source_details = [], []
                elif best_doc:
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
