"""
Career Prediction API Router.
Stage 1: Predicts best-fit tech career roles from student profile (skills, qualifications, experience).
Stage 2: Retrieves tailored career guidance and technical interview questions from RAG knowledge base.
"""

from pathlib import Path
from typing import Optional, List
import joblib
import numpy as np
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
from backend.app.career_assessment import ASSESSMENT_OPTIONS, ASSESSMENT_VERSION, assess_career_paths

router = APIRouter(prefix="/career", tags=["Career Prediction & Assessment"])

ROOT_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = ROOT_DIR / "backend" / "app" / "career_model.pkl"
_model_cache = None


def get_model():
    global _model_cache
    if _model_cache is None:
        if not MODEL_PATH.exists():
            # Check ml/models fallback
            fallback = ROOT_DIR / "ml" / "models" / "career_model.pkl"
            if fallback.exists():
                _model_cache = joblib.load(fallback)
            else:
                raise RuntimeError(f"Trained career model not found at {MODEL_PATH}")
        else:
            _model_cache = joblib.load(MODEL_PATH)
    return _model_cache


ROLE_ADVICE_MAP = {
    "Backend Developer": (
        "Focus on core data structures, REST/GraphQL APIs, database normalization (SQL & NoSQL), "
        "and server concurrency. Build and deploy an end-to-end backend service with authentication and testing."
    ),
    "Frontend Developer": (
        "Focus on modern JavaScript/TypeScript, React or Vue, CSS layout architecture, state management, "
        "and web accessibility (a11y). Create responsive, high-performance web applications."
    ),
    "Full-Stack Developer": (
        "Balance both frontend UI and backend services. Master API integration, state management, "
        "and database design with containerized deployment."
    ),
    "Mobile App Developer": (
        "Focus on Kotlin/Android Jetpack Compose or Flutter. Practice reactive state management, "
        "offline caching with SQLite/Room, and clean architecture."
    ),
    "DevOps / Cloud Engineer": (
        "Focus on Linux fundamentals, Docker containerization, CI/CD pipelines (GitHub Actions), "
        "Terraform (IaC), and cloud platforms (AWS or GCP)."
    ),
    "Data Scientist / ML Engineer": (
        "Strengthen statistical fundamentals, scikit-learn, PyTorch/TensorFlow, and ML model deployment. "
        "Build end-to-end projects demonstrating data cleaning, feature engineering, and model evaluation."
    ),
    "Data Analyst / BI Specialist": (
        "Master SQL querying (CTEs, window functions), Power BI or Tableau visualization dashboards, "
        "and business problem translation into quantitative metrics."
    ),
    "Data Engineer": (
        "Focus on data pipeline orchestration (Airflow), SQL data modeling, distributed computing (Spark), "
        "and cloud data warehouses (BigQuery/Snowflake)."
    ),
    "Cybersecurity Analyst": (
        "Focus on network security, threat modeling, SIEM log monitoring, OWASP Top 10 vulnerabilities, "
        "and foundational certifications like CompTIA Security+."
    ),
    "QA / Test Engineer": (
        "Focus on test automation frameworks (Selenium, Playwright, PyTest), API testing (Postman), "
        "and CI test integration to ensure software quality."
    ),
    "Network & Systems Engineer": (
        "Focus on TCP/IP networking, routing/switching, Linux server administration, and infrastructure automation."
    ),
    "UI/UX Designer": (
        "Focus on user research, wireframing in Figma, interactive prototyping, and design systems with usability testing."
    ),
    "Database Administrator": (
        "Focus on database performance tuning, indexing strategies, backup/recovery, replication, and high availability."
    ),
}


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
    db: Session = Depends(get_db),
):
    try:
        model = get_model()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Career prediction model is temporarily unavailable: {str(e)}",
        )

    # Clean input
    skills = request.skills.strip()
    if not skills:
        raise HTTPException(status_code=400, detail="Please provide at least one technical skill.")

    quals = request.qualifications.strip() if request.qualifications else "BSc Computer Science"
    exp = request.experience.strip() if request.experience else "0 to 1 Years"

    composite_input = f"Qualifications: {quals}. Experience: {exp}. Skills: {skills}."

    # Compute prediction probabilities
    try:
        probs = model.predict_proba([composite_input])[0]
        classes = model.classes_
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

    # Sort top 3
    top_indices = np.argsort(-probs)[:3]
    top_recommendations: List[RoleConfidence] = []

    for idx in top_indices:
        role_name = classes[idx]
        score = float(probs[idx])
        top_recommendations.append(
            RoleConfidence(
                role=role_name,
                confidence_score=round(score, 4),
                confidence_percentage=f"{score * 100:.1f}%",
            )
        )

    primary_role = top_recommendations[0].role
    confidence = top_recommendations[0].confidence_score
    confidence_str = top_recommendations[0].confidence_percentage

    # Fetch role-specific advice
    base_advice = ROLE_ADVICE_MAP.get(
        primary_role,
        "Continue building relevant hands-on projects, practicing technical problems, and refining your CV.",
    )

    # Retrieve relevant interview questions from RAG engine if available
    retrieved_interview_prep: List[str] = []
    try:
        rag = RAGEngine.get_instance()
        rag_query = f"{primary_role} interview questions technical concepts {skills}"
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
        confidence=confidence,
        confidence_percentage=confidence_str,
        top_3_recommendations=top_recommendations,
        advice=base_advice,
        retrieved_interview_prep=retrieved_interview_prep,
    )
