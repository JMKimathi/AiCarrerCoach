from datetime import datetime
from typing import List, Optional
import re
from pydantic import BaseModel, Field, ConfigDict, field_validator


def _normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
        raise ValueError("Enter a valid email address")
    return normalized


# --- Auth Schemas ---
class LoginRequest(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)
    course: Optional[str] = Field(default=None, max_length=100)
    career_goal: Optional[str] = Field(default=None, max_length=150)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    course: Optional[str] = Field(default=None, max_length=100)
    career_goal: Optional[str] = Field(default=None, max_length=150)


class UserResponse(BaseModel):
    user_id: str
    full_name: str
    email: str
    role: str
    course: Optional[str] = None
    career_goal: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


# --- Chat Schemas ---
class ChatQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class SourceDetail(BaseModel):
    title: str
    score: float
    content_snippet: str


class ChatQueryResponse(BaseModel):
    session_id: str
    response: str
    sources: List[str]
    source_details: List[SourceDetail]


class MessageResponse(BaseModel):
    message_id: str
    sender_type: str
    content: str
    sources: List[str] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
    started_at: datetime
    message_count: int

    class Config:
        from_attributes = True


# --- Resource Schemas ---
class ResourceListItem(BaseModel):
    resource_id: str
    title: str
    category: str
    summary: str

    class Config:
        from_attributes = True


class ResourceDetail(BaseModel):
    resource_id: str
    title: str
    category: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ResourceCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    category: str = Field(min_length=2, max_length=100)
    content: str = Field(min_length=10, max_length=30000)


# --- Feedback Schemas ---
class FeedbackCreate(BaseModel):
    rating: int
    is_accurate: bool = True
    comments: Optional[str] = ""
    session_id: Optional[str] = None


class FeedbackResponse(BaseModel):
    feedback_id: str
    rating: int
    is_accurate: bool
    comments: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Admin Analytics ---
class AdminOverviewResponse(BaseModel):
    active_students: int
    career_resources: int
    chats_this_week: int
    flagged_responses: int
    top_resources: List[str]


# --- ML Career Prediction Schemas ---
class CareerPredictionRequest(BaseModel):
    skills: str
    qualifications: Optional[str] = "BSc Computer Science"
    experience: Optional[str] = "0 to 1 Years"


class RoleConfidence(BaseModel):
    role: str
    confidence_score: float = Field(description="Uncalibrated model output; not a probability of success")
    confidence_percentage: str = Field(description="Formatted uncalibrated model output")


class CareerPredictionResponse(BaseModel):
    primary_role: str
    confidence: float = Field(description="Uncalibrated model output; not a probability of success")
    confidence_percentage: str
    top_3_recommendations: List[RoleConfidence]
    advice: str
    retrieved_interview_prep: Optional[List[str]] = []
    interpretation_note: str = "Model scores are uncalibrated and describe label ranking only; they are not probabilities of success or employability."


class CareerAssessmentRequest(BaseModel):
    """Structured, self-reported evidence for explainable career exploration."""

    skills: List[str] = Field(default_factory=list, max_length=40)
    interests: List[str] = Field(default_factory=list, max_length=20)
    preferred_activities: List[str] = Field(default_factory=list, max_length=20)


class CareerPathMatch(BaseModel):
    role: str
    fit_score: int = Field(ge=0, le=100, description="Relative match score, not probability of career success")
    matching_evidence: List[str]
    skills_to_explore: List[str]
    next_steps: List[str]
    related_resources: List[str] = Field(default_factory=list)


class CareerAssessmentResponse(BaseModel):
    assessment_version: str
    profile_completeness: str
    summary: str
    recommendations: List[CareerPathMatch]
    information_note: str
