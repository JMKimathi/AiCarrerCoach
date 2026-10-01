import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
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
            raise HTTPException(status_code=404, detail="Chat session not found")

    if not session:
        session = ChatSession(
            session_id=str(uuid.uuid4()),
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
        .limit(10)
        .all()
    )
    conversation_history = [
        {"role": "student" if item.sender_type == "user" else "coach", "text": item.content}
        for item in reversed(recent_messages)
    ]

    # 3. Save student's question to database
    user_msg = Message(
        message_id=str(uuid.uuid4()),
        session_id=session.session_id,
        sender_type="user",
        content=query_text,
    )
    db.add(user_msg)

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
            top_k=3,
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

    return ChatQueryResponse(
        session_id=session.session_id,
        response=rag_result["response"],
        sources=rag_result["sources"],
        source_details=rag_result["source_details"],
    )


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
