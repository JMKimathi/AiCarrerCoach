import json
import threading
import uuid
from collections import OrderedDict
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.database import get_db, ChatSession, Message, User, CareerResource
from backend.app.security import get_current_user
from backend.app.schemas import (
    ChatQueryRequest,
    ChatQueryResponse,
    MessageResponse,
    ChatSessionResponse,
)
from backend.app.rag_engine import RAGEngine

router = APIRouter(prefix="/chat", tags=["Career Coach Chat"])

HISTORY_MESSAGES = 20          # earlier messages sent to the coach with each new one
HISTORY_CHARS = 1200           # older messages are shortened to this many characters
RECENT_HISTORY_CHARS = 6000    # the two latest messages are kept almost whole so "continue" works

# Replies the student stopped. A request the student cancels while the coach is still writing is
# remembered here so its reply is not saved; one that had just finished has its reply removed.
_stop_lock = threading.Lock()
_stopped_requests: "OrderedDict[str, bool]" = OrderedDict()
_finished_requests: "OrderedDict[str, str]" = OrderedDict()   # request id -> saved reply's message id
_REMEMBERED_REQUESTS = 500


def _remember(store: OrderedDict, key: str, value) -> None:
    store[key] = value
    while len(store) > _REMEMBERED_REQUESTS:
        store.popitem(last=False)


def _shorten(text: str, limit: int) -> str:
    """Keep the start and the end of a long message, since the end is where a reply left off."""
    if len(text) <= limit:
        return text
    head = limit * 2 // 3
    return text[:head].rstrip() + " [...] " + text[-(limit - head):].lstrip()


@router.post("", response_model=ChatQueryResponse)
def chat_with_coach(
    payload: ChatQueryRequest,
    student: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query_text = payload.query.strip()
    if not query_text:
        raise HTTPException(status_code=400, detail="Query message cannot be empty.")

    # 2. Resolve or create chat session
    session = None
    if payload.session_id:
        session = db.query(ChatSession).filter(
            ChatSession.session_id == payload.session_id,
            ChatSession.user_id == student.user_id,
        ).first()
        if session is None:
            # The app chooses the id of a new conversation itself, so the conversation keeps one
            # id from its first message even if that first reply is stopped. Ids must be new UUIDs.
            try:
                new_session_id = str(uuid.UUID(payload.session_id))
            except ValueError as exc:
                raise HTTPException(status_code=404, detail="Chat session not found") from exc
            if db.query(ChatSession).filter(ChatSession.session_id == new_session_id).first() is not None:
                raise HTTPException(status_code=404, detail="Chat session not found")
        else:
            new_session_id = None
    else:
        new_session_id = None

    if not session:
        session = ChatSession(
            session_id=new_session_id or str(uuid.uuid4()),
            user_id=student.user_id,
            title=query_text[:50] + ("..." if len(query_text) > 50 else ""),
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # Include recent turns so follow-up questions can build on the conversation.
    recent_messages = (
        db.query(Message)
        .filter(Message.session_id == session.session_id)
        .order_by(Message.created_at.desc())
        .limit(HISTORY_MESSAGES)
        .all()
    )
    ordered = list(reversed(recent_messages))
    conversation_history = [
        {
            "role": "student" if item.sender_type == "user" else "coach",
            "text": _shorten(item.content, RECENT_HISTORY_CHARS if index >= len(ordered) - 2 else HISTORY_CHARS),
        }
        for index, item in enumerate(ordered)
    ]

    # 3. Save student's question to database
    user_msg = Message(
        message_id=str(uuid.uuid4()),
        session_id=session.session_id,
        sender_type="user",
        content=query_text,
    )
    db.add(user_msg)
    # Saved straight away so a message sent while this one is still being answered can see it.
    db.commit()

    # Add current database resources to trained-index results so resources an
    # administrator adds later are available without rebuilding embeddings.
    terms = {term.lower().strip(".,?!") for term in query_text.split() if len(term) > 3}
    resources = db.query(CareerResource).all()
    ranked = sorted(
        resources,
        key=lambda item: sum(term in f"{item.title} {item.category} {item.content}".lower() for term in terms),
        reverse=True,
    )[:3]
    ranked = [item for item in ranked if any(term in f"{item.title} {item.category} {item.content}".lower() for term in terms)]
    supplemental = [
        {"title": item.title, "content": item.content, "score": 0.0}
        for item in ranked
    ]

    # 4. Run through fine-tuned RAG engine
    try:
        rag = RAGEngine.get_instance()
        rag_result = rag.generate_response(
            query=query_text,
            student_name=student.full_name,
            course=student.course or "Not provided",
            career_goal=student.career_goal or "Not provided",
            top_k=5,
            supplemental_docs=supplemental,
            conversation_history=conversation_history,
        )
    except Exception as exc:
        # Keep chat usable before ML artifacts are installed by retrieving the
        # authored Markdown resources stored in the database.
        if not ranked:
            raise HTTPException(status_code=503, detail="Career knowledge base is not available yet") from exc
        rag_result = {
            "response": "I found these relevant career resources in the knowledge base:\n\n" + "\n\n".join(
                f"**{item.title}**\n{item.content[:900]}" for item in ranked
            ),
            "sources": [item.title for item in ranked],
            "source_details": [
                {"title": item.title, "score": 0.0, "content_snippet": item.content[:160].strip()}
                for item in ranked
            ],
        }

    # A reply the student stopped is not saved. Their question stays, so their next message
    # reads as more instructions for the same request.
    request_id = (payload.request_id or "").strip()
    if request_id:
        with _stop_lock:
            stopped = _stopped_requests.pop(request_id, False)
        if stopped:
            return ChatQueryResponse(
                session_id=session.session_id, response="", sources=[], source_details=[], stopped=True,
            )

    # 5. Save assistant's reply to database
    assistant_msg = Message(
        message_id=str(uuid.uuid4()),
        session_id=session.session_id,
        sender_type="assistant",
        content=rag_result["response"],
        sources=json.dumps(rag_result["sources"]),
    )
    db.add(assistant_msg)
    db.commit()
    if request_id:
        with _stop_lock:
            _remember(_finished_requests, request_id, assistant_msg.message_id)

    return ChatQueryResponse(
        session_id=session.session_id,
        response=rag_result["response"],
        sources=rag_result["sources"],
        source_details=rag_result["source_details"],
    )


class StopRequest(BaseModel):
    request_id: str = Field(min_length=8, max_length=64)


@router.post("/stop")
def stop_reply(
    payload: StopRequest,
    student: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stop a reply the student no longer wants. The question is kept; the reply is dropped."""
    with _stop_lock:
        finished_message_id = _finished_requests.pop(payload.request_id, None)
        if finished_message_id is None:
            _remember(_stopped_requests, payload.request_id, True)
    if finished_message_id is not None:
        # The reply was saved a moment before the stop arrived, so take it back out.
        message = (
            db.query(Message)
            .join(ChatSession, ChatSession.session_id == Message.session_id)
            .filter(Message.message_id == finished_message_id, ChatSession.user_id == student.user_id)
            .first()
        )
        if message is not None:
            db.delete(message)
            db.commit()
    return {"stopped": True}


@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_chat_sessions(
    student: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == student.user_id).order_by(ChatSession.started_at.desc()).all()

    result = []
    for s in sessions:
        count = db.query(Message).filter(Message.session_id == s.session_id).count()
        result.append(
            ChatSessionResponse(
                session_id=s.session_id,
                title=s.title,
                started_at=s.started_at,
                message_count=count,
            )
        )
    return result


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(
    session_id: str,
    student: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == student.user_id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")

    messages = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at.asc()).all()
    results = []
    for m in messages:
        srcs = []
        if m.sources:
            try:
                srcs = json.loads(m.sources)
            except Exception:
                srcs = []
        results.append(
            MessageResponse(
                message_id=m.message_id,
                sender_type=m.sender_type,
                content=m.content,
                sources=srcs,
                created_at=m.created_at,
            )
        )
    return results
