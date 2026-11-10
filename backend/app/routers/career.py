"""Career exploration and assessment endpoints backed by synthetic pathways."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.schemas import (
    CareerAssessmentRequest,
    CareerAssessmentResponse,
    CareerPredictionRequest,
    CareerPredictionResponse,
    RoleConfidence,
)
from backend.app.database import get_db, User, CareerAssessmentRecord
from backend.app.security import get_current_user
import json
import uuid
from backend.app.rag_engine import RAGEngine
from backend.app.career_assessment import ASSESSMENT_OPTIONS, ASSESSMENT_VERSION, CAREER_PATHS, assess_career_paths

router = APIRouter(prefix="/career", tags=["Career Prediction & Assessment"])

@router.get("/assessment-options")
def get_assessment_options():
    """Return suggested answer tags while still accepting students' own wording."""
    return {"assessment_version": ASSESSMENT_VERSION, "options": ASSESSMENT_OPTIONS}


@router.post("/assess", response_model=CareerAssessmentResponse)
def assess_career_path(request: CareerAssessmentRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Rank career families from multiple student signals with visible evidence."""
    try:
        result = assess_career_paths(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Retrieval only adds links to existing guidance; it does not determine the ranking.
    try:
        rag = RAGEngine.get_instance()
        interests = " ".join(request.interests)
        skills = " ".join(request.skills)
        for recommendation in result["recommendations"]:
            retrieved = rag.retrieve(f"{recommendation['role']} career skills learning path {interests} {skills}", top_k=2)
            recommendation["related_resources"] = list(dict.fromkeys(
                item.get("title", "Career resource") for item in retrieved
            ))
    except Exception:
        # Assessment remains usable if optional retrieval assets are not installed.
        pass

    record = CareerAssessmentRecord(
        assessment_id=str(uuid.uuid4()),
        user_id=user.user_id,
        assessment_version=result["assessment_version"],
        input_json=json.dumps(request.model_dump()),
        result_json=json.dumps(result),
    )
    db.add(record)
    db.commit()
    return result


@router.post("/predict", response_model=CareerPredictionResponse)
def predict_career_path(
    request: CareerPredictionRequest,
    _user: User = Depends(get_current_user),
):
    skills = request.skills.strip()
    if not skills:
        raise HTTPException(status_code=400, detail="Please provide at least one skill or career-related detail.")

    profile = [part.strip() for part in (skills, request.qualifications or "", request.experience or "") if part.strip()]
    ranked = assess_career_paths({"skills": profile})["recommendations"][:3]
    if not ranked:
        raise HTTPException(status_code=400, detail="Those details did not match the current pathway examples. Add a skill or interest in your own words.")

    path_by_role = {path["occupation_title"]: path for path in CAREER_PATHS}
    top_recommendations: List[RoleConfidence] = [
        RoleConfidence(role=item["role"], confidence_score=round(item["fit_score"] / 100, 4),
                       confidence_percentage=f"{item['fit_score']}% relative answer overlap")
        for item in ranked
    ]
    primary_role = top_recommendations[0].role
    primary_path = path_by_role[primary_role]
    advice_sections = [
        primary_path["role_summary"],
        "Study and qualification notes: " + primary_path["requirements_and_qualification_notes"],
        "Preparation ideas: " + "; ".join(primary_path["preparation_pathway"]),
        "CV focus: " + primary_path["cv_tailoring_guidance"],
        "Check locally: " + primary_path["local_verification_note"],
    ]

    retrieved_interview_prep: List[str] = list(primary_path["sample_interview_questions"])
    try:
        rag = RAGEngine.get_instance()
        rag_query = f"{primary_role} interview questions {skills}"
        results = rag.retrieve(rag_query, top_k=2)
        for r in results:
            title = r.get("title", "Resource")
            snippet = r.get("content", "").split("\n\n")[0]
            retrieved_interview_prep.append(f"{title}: {snippet[:140]}...")
    except Exception:
        # Gracefully handle RAG offline
        pass

    return CareerPredictionResponse(
        primary_role=primary_role,
        advice="\n\n".join(advice_sections),
        retrieved_interview_prep=retrieved_interview_prep,
        confidence=top_recommendations[0].confidence_score,
        confidence_percentage=top_recommendations[0].confidence_percentage,
        top_3_recommendations=top_recommendations,
        interpretation_note="These rankings come from a synthetic illustrative dataset. The score is overlap with provided wording, not model confidence, probability of success, qualification, or employability. Verify local requirements.",
    )
