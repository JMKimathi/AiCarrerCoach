"""Mock interview practice for a chosen career."""

import json
import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app import career_catalogue, interview_engine
from backend.app.database import MockInterview, User, get_db
from backend.app.security import get_current_user

router = APIRouter(prefix="/interviews", tags=["Mock Interviews"])

OPPORTUNITY_TYPES = {"internship", "industrial attachment", "graduate programme", "full-time job"}
MAX_CANDIDATE_TURNS = 30  # hard stop so a session can never run forever


class InterviewStart(BaseModel):
    career_id: str = Field(min_length=1, max_length=20)
    opportunity_type: Optional[str] = Field(default=None, max_length=40)
    question_count: int = Field(default=6, ge=3, le=10)


class InterviewAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)


class InterviewTurn(BaseModel):
    speaker: str
    kind: str
    text: str


class InterviewState(BaseModel):
    interview_id: str
    career_id: str
    role_title: str
    opportunity_type: Optional[str]
    status: str
    question_number: int
    total_questions: int
    interviewer_message: Optional[str] = None
    transcript: List[InterviewTurn] = Field(default_factory=list)
    feedback: Optional[str] = None
    feedback_generated_by: Optional[str] = None
    note: str = "Practice interview with AI-generated questions and feedback. It does not represent any employer."


def _state(record: MockInterview, interviewer_message: Optional[str] = None, include_transcript: bool = True) -> InterviewState:
    plan = json.loads(record.plan_json)
    transcript = json.loads(record.transcript_json)
    return InterviewState(
        interview_id=record.interview_id, career_id=record.career_id, role_title=record.role_title,
        opportunity_type=record.opportunity_type, status=record.status,
        question_number=min(record.current_index + 1, len(plan)), total_questions=len(plan),
        interviewer_message=interviewer_message,
        transcript=[InterviewTurn(speaker=turn["speaker"], kind=turn["kind"], text=turn["text"])
                    for turn in transcript] if include_transcript else [],
        feedback=record.feedback_text, feedback_generated_by=record.feedback_generated_by,
    )


def _own_interview(interview_id: str, user: User, db: Session) -> MockInterview:
    record = db.query(MockInterview).filter(
        MockInterview.interview_id == interview_id, MockInterview.user_id == user.user_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return record


@router.post("", response_model=InterviewState, status_code=201)
def start_interview(payload: InterviewStart, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    career_id = payload.career_id.strip().upper()
    opportunity = (payload.opportunity_type or "").strip().lower() or None
    if opportunity and opportunity not in OPPORTUNITY_TYPES:
        raise HTTPException(status_code=422,
                            detail="opportunity_type must be one of: " + ", ".join(sorted(OPPORTUNITY_TYPES)))
    try:
        catalogue = career_catalogue.load_catalogue()
    except career_catalogue.CatalogueUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    career = catalogue["careers"].get(career_id)
    questions = catalogue["questions"].get(career_id)
    if career is None or not questions:
        raise HTTPException(status_code=404, detail="Career not found.")

    plan = interview_engine.plan_interview(questions, career_id, payload.question_count, opportunity,
                                           seed=secrets.randbits(32))
    opening = interview_engine.opening_turn(career["role_title"], opportunity, plan)
    record = MockInterview(
        user_id=user.user_id, career_id=career_id, role_title=career["role_title"],
        opportunity_type=opportunity, status="in_progress", plan_json=json.dumps(plan),
        transcript_json=json.dumps([{"speaker": "interviewer", "kind": "question", "text": opening,
                                     "question_index": 0}]),
        current_index=0, follow_ups_used=0,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _state(record, interviewer_message=opening)


@router.get("")
def list_interviews(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.query(MockInterview).filter(MockInterview.user_id == user.user_id).order_by(
        MockInterview.created_at.desc()).limit(50).all()
    return [
        {"interview_id": record.interview_id, "career_id": record.career_id, "role_title": record.role_title,
         "opportunity_type": record.opportunity_type, "status": record.status,
         "has_feedback": bool(record.feedback_text), "created_at": record.created_at}
        for record in records
    ]


@router.get("/{interview_id}", response_model=InterviewState)
def get_interview(interview_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _state(_own_interview(interview_id, user, db))


@router.post("/{interview_id}/answer", response_model=InterviewState)
def answer_question(interview_id: str, payload: InterviewAnswer, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    record = _own_interview(interview_id, user, db)
    if record.status != "in_progress":
        raise HTTPException(status_code=409, detail="This interview has ended. Start a new one to keep practising.")
    answer = payload.answer.strip()
    if not answer:
        raise HTTPException(status_code=422, detail="Answer cannot be empty.")

    plan = json.loads(record.plan_json)
    transcript = json.loads(record.transcript_json)
    transcript.append({"speaker": "candidate", "kind": "answer", "text": answer,
                       "question_index": record.current_index})
    candidate_turns = sum(turn["speaker"] == "candidate" for turn in transcript)
    if candidate_turns >= MAX_CANDIDATE_TURNS:
        turn = {"text": "We have run out of time for this practice session. Thank you. You can now ask for feedback.",
                "kind": "closing", "current_index": record.current_index,
                "follow_ups_used": record.follow_ups_used, "finished": True}
    else:
        turn = interview_engine.next_turn(record.role_title, record.opportunity_type, plan, transcript,
                                          record.current_index, record.follow_ups_used, answer)
    transcript.append({"speaker": "interviewer", "kind": turn["kind"], "text": turn["text"],
                       "question_index": turn["current_index"]})
    record.transcript_json = json.dumps(transcript)
    record.current_index = turn["current_index"]
    record.follow_ups_used = turn["follow_ups_used"]
    if turn["finished"]:
        record.status = "completed"
        record.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    return _state(record, interviewer_message=turn["text"], include_transcript=False)


@router.post("/{interview_id}/finish", response_model=InterviewState)
def finish_interview(interview_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """End the interview (early if needed) and return feedback. Feedback is generated once and then reused."""
    record = _own_interview(interview_id, user, db)
    if record.status == "in_progress":
        record.status = "completed"
        record.completed_at = datetime.utcnow()
    if not record.feedback_text:
        feedback = interview_engine.build_feedback(record.role_title, record.opportunity_type,
                                                   json.loads(record.plan_json), json.loads(record.transcript_json))
        record.feedback_text = feedback["text"]
        record.feedback_generated_by = feedback["generated_by"]
    db.commit()
    db.refresh(record)
    return _state(record)
