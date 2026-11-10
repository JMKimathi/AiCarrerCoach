from typing import List
from datetime import datetime, timedelta
from collections import Counter
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.database import get_db, User, CareerResource, Message, Feedback, ChatSession
from backend.app.schemas import AdminOverviewResponse, UserResponse
from backend.app.security import require_admin

router = APIRouter(prefix="/admin", tags=["Administrator Management"], dependencies=[Depends(require_admin)])


@router.get("/overview", response_model=AdminOverviewResponse)
def get_admin_overview(db: Session = Depends(get_db)):
    active_students = db.query(User).filter(User.role == "student", User.is_active == True).count()
    resources_count = db.query(CareerResource).count()
    chats_this_week = db.query(ChatSession).filter(ChatSession.started_at >= datetime.utcnow() - timedelta(days=7)).count()
    flagged_feedback = db.query(Feedback).filter(Feedback.is_accurate == False).count()
    resource_counts = Counter()
    for message in db.query(Message).filter(Message.sender_type == "assistant", Message.sources.isnot(None)).all():
        try:
            resource_counts.update(json.loads(message.sources))
        except (TypeError, json.JSONDecodeError):
            continue

    return AdminOverviewResponse(
        active_students=active_students,
        career_resources=resources_count,
        chats_this_week=chats_this_week,
        flagged_responses=flagged_feedback,
        top_resources=[name for name, _ in resource_counts.most_common(5)],
    )


@router.get("/students", response_model=List[UserResponse])
def get_students(db: Session = Depends(get_db)):
    students = db.query(User).filter(User.role == "student").order_by(User.created_at.desc()).all()
    return [UserResponse.from_orm(s) for s in students]


class StudentStatusUpdate(BaseModel):
    is_active: bool


@router.put("/students/{user_id}/status", response_model=UserResponse)
def set_student_status(user_id: str, payload: StudentStatusUpdate, db: Session = Depends(get_db)):
    """Activate or deactivate a student account. A deactivated student cannot sign in or use a saved token."""
    student = db.query(User).filter(User.user_id == user_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student account not found.")
    student.is_active = payload.is_active
    db.commit()
    db.refresh(student)
    return UserResponse.from_orm(student)
