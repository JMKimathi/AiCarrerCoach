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
    __tablename__ = "messages"

    message_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.session_id"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON-serialized list of sources
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


class CareerResource(Base):
    __tablename__ = "career_resources"

    resource_id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    category = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), default="Strathmore University Careers Knowledge Base")
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
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
    __tablename__ = "career_assessments"

    assessment_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_version = Column(String(40), nullable=False)
    input_json = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user = relationship("User", backref="career_assessments")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_database():
    """Create schema and import authored career resources; never create demo users."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check resources
        if db.query(CareerResource).count() == 0:
            print("Seeding career knowledge base resources...")
            resources_dir = ROOT_DIR / "ml" / "data" / "resources"
            if resources_dir.exists():
                category_map = {
                    "software_engineer_cv": ("Software Engineer CV Template", "CV Templates"),
                    "cover_letter_guide": ("Cover Letter Writing Guide", "CV Templates"),
                    "behavioural_interviews": ("Behavioural Interview Question Bank", "Interview Prep"),
                    "technical_interviews": ("Technical Interview Practice: Algorithms", "Interview Prep"),
                    "careers_data_science": ("Careers in Data Science", "Career Paths"),
                    "portfolio_website": ("Building a Portfolio Website", "Skill Building"),
                }
                for md_file in resources_dir.glob("*.md"):
                    stem = md_file.stem
                    title, category = category_map.get(stem, (stem.replace("_", " ").title(), "General"))
                    content = md_file.read_text(encoding="utf-8")
                    res = CareerResource(
                        resource_id=stem,
                        title=title,
                        category=category,
                        content=content,
                    )
                    db.add(res)
                db.commit()
    finally:
        db.close()
