import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db, Feedback, User
from backend.app.schemas import FeedbackCreate, FeedbackResponse
from backend.app.security import get_current_user, require_admin

router = APIRouter(prefix="/feedback", tags=["Student Feedback"])


@router.post("", response_model=FeedbackResponse)
def submit_feedback(
    payload: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not 1 <= payload.rating <= 5:
        raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")
    if payload.session_id:
        from backend.app.database import ChatSession
        owned_session = db.query(ChatSession).filter(
            ChatSession.session_id == payload.session_id,
            ChatSession.user_id == user.user_id,
        ).first()
        if owned_session is None:
            raise HTTPException(status_code=404, detail="Chat session not found")

    fb = Feedback(
        feedback_id=str(uuid.uuid4()),
        user_id=user.user_id,
        session_id=payload.session_id,
        rating=payload.rating,
        is_accurate=payload.is_accurate,
        comments=payload.comments or "",
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return FeedbackResponse.from_orm(fb)


@router.get("", response_model=List[FeedbackResponse])
def list_feedbacks(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return db.query(Feedback).order_by(Feedback.created_at.desc()).all()
