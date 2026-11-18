"""Admin-only endpoints: overview numbers, student accounts, feedback and analytics."""

import json
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import (
    CareerAssessmentRecord, CareerResource, ChatSession, Feedback, Message, MockInterview, User, get_db,
)
from backend.app.schemas import AdminOverviewResponse, UserResponse
from backend.app.security import hash_password, require_admin

router = APIRouter(prefix="/admin", tags=["Administrator Management"], dependencies=[Depends(require_admin)])


@router.get("/overview", response_model=AdminOverviewResponse)
def get_admin_overview(db: Session = Depends(get_db)):
    """Headline numbers for the admin dashboard."""
    week_ago = datetime.utcnow() - timedelta(days=7)
    students = db.query(User).filter(User.role == "student")
    total_students = students.count()
    active_students = students.filter(User.is_active.is_(True)).count()
    resource_counts = Counter()
    for message in db.query(Message).filter(Message.sender_type == "assistant", Message.sources.isnot(None)).all():
        try:
            resource_counts.update(json.loads(message.sources))
        except (TypeError, json.JSONDecodeError):
            continue
    average_rating = db.query(func.avg(Feedback.rating)).scalar()

    return AdminOverviewResponse(
        active_students=active_students,
        career_resources=db.query(CareerResource).count(),
        chats_this_week=db.query(ChatSession).filter(ChatSession.started_at >= week_ago).count(),
        flagged_responses=db.query(Feedback).filter(Feedback.is_accurate.is_(False)).count(),
        top_resources=[name for name, _ in resource_counts.most_common(5)],
        total_students=total_students,
        inactive_students=total_students - active_students,
        new_students_this_week=students.filter(User.created_at >= week_ago).count(),
        interviews_this_week=db.query(MockInterview).filter(MockInterview.created_at >= week_ago).count(),
        interviews_completed=db.query(MockInterview).filter(MockInterview.status == "completed").count(),
        assessments_total=db.query(CareerAssessmentRecord).count(),
        feedback_count=db.query(Feedback).count(),
        average_rating=round(float(average_rating), 1) if average_rating is not None else None,
    )


class StudentSummary(UserResponse):
    """A student account with the activity an administrator needs to see at a glance."""
    created_at: Optional[datetime] = None
    chat_count: int = 0
    interview_count: int = 0
    assessment_count: int = 0
    last_active: Optional[datetime] = None


def _counts(db: Session, column, *filters) -> dict:
    """Count rows per student for one column (chats, interviews and so on)."""
    query = db.query(column, func.count()).group_by(column)
    return dict(query.filter(*filters).all() if filters else query.all())


def _summaries(db: Session, students: List[User]) -> List[StudentSummary]:
    """Build a short activity summary for each student."""
    chats = _counts(db, ChatSession.user_id)
    interviews = _counts(db, MockInterview.user_id)
    assessments = _counts(db, CareerAssessmentRecord.user_id)
    last_chat = dict(db.query(ChatSession.user_id, func.max(ChatSession.started_at)).group_by(ChatSession.user_id).all())
    last_interview = dict(
        db.query(MockInterview.user_id, func.max(MockInterview.created_at)).group_by(MockInterview.user_id).all())
    summaries = []
    for student in students:
        moments = [moment for moment in (last_chat.get(student.user_id), last_interview.get(student.user_id)) if moment]
        summaries.append(StudentSummary(
            **UserResponse.model_validate(student).model_dump(),
            created_at=student.created_at,
            chat_count=chats.get(student.user_id, 0),
            interview_count=interviews.get(student.user_id, 0),
            assessment_count=assessments.get(student.user_id, 0),
            last_active=max(moments) if moments else None,
        ))
    return summaries


def _student_or_404(db: Session, user_id: str) -> User:
    """Fetch a student account or return a 404 if it does not exist."""
    student = db.query(User).filter(User.user_id == user_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student account not found.")
    return student


@router.get("/students", response_model=List[StudentSummary])
def get_students(db: Session = Depends(get_db)):
    """List all student accounts with their activity."""
    students = db.query(User).filter(User.role == "student").order_by(User.created_at.desc()).all()
    return _summaries(db, students)


class StudentStatusUpdate(BaseModel):
    """Body for activating or deactivating a student account."""
    is_active: bool


@router.put("/students/{user_id}/status", response_model=StudentSummary)
def set_student_status(user_id: str, payload: StudentStatusUpdate, db: Session = Depends(get_db)):
    """Activate or deactivate a student account. A deactivated student cannot sign in or use a saved token."""
    student = _student_or_404(db, user_id)
    student.is_active = payload.is_active
    db.commit()
    db.refresh(student)
    return _summaries(db, [student])[0]


class PasswordReset(BaseModel):
    """Body for an admin setting a new password for a student."""
    new_password: str = Field(min_length=8, max_length=128)


@router.put("/students/{user_id}/password", response_model=StudentSummary)
def reset_student_password(user_id: str, payload: PasswordReset, db: Session = Depends(get_db)):
    """Set a temporary password for a student who is locked out. Only the hash is stored."""
    student = _student_or_404(db, user_id)
    student.password_hash = hash_password(payload.new_password)
    db.commit()
    db.refresh(student)
    return _summaries(db, [student])[0]


@router.delete("/students/{user_id}", status_code=204)
def delete_student(user_id: str, db: Session = Depends(get_db)):
    """Remove a student account together with their chats, feedback, assessments and practice interviews."""
    student = _student_or_404(db, user_id)
    db.query(MockInterview).filter(MockInterview.user_id == user_id).delete(synchronize_session=False)
    db.query(CareerAssessmentRecord).filter(CareerAssessmentRecord.user_id == user_id).delete(synchronize_session=False)
    db.delete(student)  # chats, messages and feedback go with the account through the ORM cascade
    db.commit()


class FeedbackItem(BaseModel):
    """One feedback entry as shown to the admin."""
    feedback_id: str
    student_name: str
    student_email: str
    rating: int
    is_accurate: bool
    comments: Optional[str] = None
    created_at: Optional[datetime] = None


@router.get("/feedback", response_model=List[FeedbackItem])
def list_feedback(flagged_only: bool = False, limit: int = 50, db: Session = Depends(get_db)):
    """Recent student feedback, newest first. `flagged_only` keeps answers marked inaccurate."""
    query = db.query(Feedback, User).join(User, User.user_id == Feedback.user_id)
    if flagged_only:
        query = query.filter(Feedback.is_accurate.is_(False))
    rows = query.order_by(Feedback.created_at.desc()).limit(max(1, min(limit, 200))).all()
    return [
        FeedbackItem(
            feedback_id=item.feedback_id, student_name=user.full_name, student_email=user.email,
            rating=item.rating, is_accurate=bool(item.is_accurate), comments=item.comments,
            created_at=item.created_at,
        )
        for item, user in rows
    ]


class DailyActivity(BaseModel):
    """Activity counts for one day, used by the analytics charts."""
    date: str
    label: str
    chats: int
    interviews: int
    new_students: int


@router.get("/activity", response_model=List[DailyActivity])
def get_activity(days: int = 7, db: Session = Depends(get_db)):
    """Chats started, practice interviews started and new student accounts for each of the last `days` days."""
    days = max(1, min(days, 30))
    today = datetime.utcnow().date()
    first_day = today - timedelta(days=days - 1)
    since = datetime.combine(first_day, datetime.min.time())

    def per_day(column, *filters) -> Counter:
        """Count how many rows were created on each day."""
        moments = db.query(column).filter(column >= since, *filters).all()
        return Counter(moment.date() for (moment,) in moments if moment)

    chats = per_day(ChatSession.started_at)
    interviews = per_day(MockInterview.created_at)
    new_students = per_day(User.created_at, User.role == "student")
    return [
        DailyActivity(
            date=day.isoformat(), label=day.strftime("%a"),
            chats=chats.get(day, 0), interviews=interviews.get(day, 0), new_students=new_students.get(day, 0),
        )
        for day in (first_day + timedelta(days=offset) for offset in range(days))
    ]
