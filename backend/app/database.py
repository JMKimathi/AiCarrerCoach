"""Database tables and the start-up seeding of career guides.

We use SQLAlchemy on top of PostgreSQL. Each class below is one table."""

import uuid
from datetime import datetime
from typing import Generator
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    Boolean,
    Integer,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from backend.app.config import settings, ROOT_DIR

def _create_engine():
    """Connect to PostgreSQL using the URL from the settings."""
    db_url = settings.DATABASE_URL
    kwargs = {"pool_pre_ping": True}
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if db_url.startswith("sqlite:"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(db_url, **kwargs)


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """A student or admin account."""
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="student")  # 'student' or 'admin'
    course = Column(String(100), default="BSc Computer Science")
    career_goal = Column(String(150), default="Roles in AI and data")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")


class ChatSession(Base):
    """One conversation between a student and the coach."""
    __tablename__ = "chat_sessions"

    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    title = Column(String(150), default="New Career Consultation")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """A single message in a chat session, from either the student or the coach."""
    __tablename__ = "messages"

    message_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.session_id"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON-serialized list of sources
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


class CareerResource(Base):
    """A career guide shown in the Knowledge section."""
    __tablename__ = "career_resources"

    resource_id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), default="Strathmore University Careers Knowledge Base")
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    """Feedback a student leaves about the app or a resource."""
    __tablename__ = "feedback"

    feedback_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    session_id = Column(String(36), nullable=True)
    rating = Column(Integer, nullable=False)  # 1 to 5
    is_accurate = Column(Boolean, default=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feedback")


class CareerAssessmentRecord(Base):
    """A saved career assessment so students can look back at past results."""
    __tablename__ = "career_assessments"

    assessment_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_version = Column(String(40), nullable=False)
    input_json = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", backref="career_assessments")


class MockInterview(Base):
    """One practice interview: the planned questions, the transcript so far and the feedback."""
    __tablename__ = "mock_interviews"

    interview_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    career_id = Column(String(20), nullable=False)
    role_title = Column(String(150), nullable=False)
    opportunity_type = Column(String(40), nullable=True)
    status = Column(String(20), nullable=False, default="in_progress")  # 'in_progress' or 'completed'
    plan_json = Column(Text, nullable=False)
    transcript_json = Column(Text, nullable=False)
    current_index = Column(Integer, nullable=False, default=0)
    follow_ups_used = Column(Integer, nullable=False, default=0)
    feedback_text = Column(Text, nullable=True)
    feedback_generated_by = Column(String(20), nullable=True)  # 'gemini' or 'built-in'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    user = relationship("User", backref="mock_interviews")


def get_db() -> Generator[Session, None, None]:
    """Give each request its own database session and close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_database():
    """Create schema and import authored career resources; never create demo users.

    Guides added to ml/data/resources later are picked up on the next start, but a resource that is
    already in the database is left alone, so edits made by an administrator are never overwritten.
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        resources_dir = ROOT_DIR / "ml" / "data" / "resources"
        if resources_dir.exists():
            # Friendly titles and the category each guide is filed under in the app.
            category_map = {
                "software_engineer_cv": ("Software Engineer CV Template", "CV Templates"),
                "cover_letter_guide": ("Cover Letter Writing Guide", "CV Templates"),
                "general_cv_guide": ("Writing a CV for Any Field", "CV Templates"),
                "behavioural_interviews": ("Behavioural Interview Question Bank", "Interview Prep"),
                "technical_interviews": ("Technical Interview Practice: Algorithms", "Interview Prep"),
                "careers_data_science": ("Careers in Data Science", "Career Paths"),
                "choosing_a_career_path": ("Choosing a Career Path", "Career Paths"),
                "portfolio_website": ("Building a Portfolio Website", "Skill Building"),
                "linkedin_and_networking": ("Using LinkedIn and Networking", "Skill Building"),
                "finding_internships_and_attachments": ("Finding Internships and Attachments", "Job Search"),
                "avoiding_job_scams": ("Avoiding Job and Internship Scams", "Job Search"),
                "online_and_freelance_work": ("Online and Freelance Work", "Job Search"),
                "understanding_pay_and_offers": ("Understanding Pay and Job Offers", "Workplace"),
                "starting_your_first_job": ("Starting Your First Job", "Workplace"),
            }
            existing = {row[0] for row in db.query(CareerResource.resource_id).all()}
            added = 0
            for md_file in sorted(resources_dir.glob("*.md")):
                stem = md_file.stem
                if stem in existing:
                    continue
                title, category = category_map.get(stem, (stem.replace("_", " ").title(), "General"))
                db.add(CareerResource(resource_id=stem, title=title, category=category,
                                      content=md_file.read_text(encoding="utf-8")))
                added += 1
            if added:
                db.commit()
                print(f"Added {added} career guide(s) to the knowledge base.")
    finally:
        db.close()
