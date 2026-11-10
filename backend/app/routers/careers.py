"""Browse the career catalogue and build a CV tailored to one career."""

import sys
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.app import career_catalogue
from backend.app.config import ML_DIR
from backend.app.database import User
from backend.app.security import get_current_user

# The CV renderer lives with the pipeline code so the templates and the renderer stay in step.
if str(ML_DIR / "src") not in sys.path:
    sys.path.append(str(ML_DIR / "src"))
from build_cv_templates import render_cv  # noqa: E402

router = APIRouter(prefix="/careers", tags=["Career Catalogue"])

OPPORTUNITY_TYPES = {"internship", "industrial attachment", "graduate programme", "full-time job"}


class CVProject(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=600)


class CVExperience(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    organisation: str = Field(default="", max_length=120)
    period: str = Field(default="", max_length=60)
    highlights: List[str] = Field(default_factory=list, max_length=6)


class CVRequest(BaseModel):
    """Details for the CV. Name, email and course fall back to the signed-in account."""
    full_name: Optional[str] = Field(default=None, max_length=150)
    email: Optional[str] = Field(default=None, max_length=254)
    phone: Optional[str] = Field(default=None, max_length=40)
    location: Optional[str] = Field(default=None, max_length=120)
    links: List[str] = Field(default_factory=list, max_length=4)
    course: Optional[str] = Field(default=None, max_length=100)
    institution: Optional[str] = Field(default=None, max_length=150)
    graduation_year: Optional[str] = Field(default=None, max_length=10)
    target_opportunity: Optional[str] = Field(default=None, max_length=40)
    skills: List[str] = Field(default_factory=list, max_length=30)
    projects: List[CVProject] = Field(default_factory=list, max_length=8)
    experience: List[CVExperience] = Field(default_factory=list, max_length=8)
    certifications: List[str] = Field(default_factory=list, max_length=12)
    activities: List[str] = Field(default_factory=list, max_length=12)
    referees: List[str] = Field(default_factory=list, max_length=3)


class CVResponse(BaseModel):
    career_id: str
    role_title: str
    markdown: str
    matched_skills: List[str]
    skills_to_build: List[str]
    cv_tips: List[str]
    note: str = (
        "This CV is built only from the details you supplied. Replace every bracketed prompt with your own "
        "information and check it before sending."
    )


def _catalogue_call(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except career_catalogue.CatalogueUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/categories")
def get_categories(_user: User = Depends(get_current_user)):
    return {"categories": _catalogue_call(career_catalogue.list_categories)}


@router.get("")
def list_careers(
    category: Optional[str] = Query(None, description="Exact category name, e.g. Technology and Data"),
    q: Optional[str] = Query(None, max_length=80, description="Words to match in the title, focus area or core skills"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _user: User = Depends(get_current_user),
):
    return _catalogue_call(career_catalogue.search_careers, category=category, query=q, limit=limit, offset=offset)


@router.get("/{career_id}")
def get_career_detail(career_id: str, _user: User = Depends(get_current_user)):
    career = _catalogue_call(career_catalogue.get_career, career_id.strip().upper())
    if career is None:
        raise HTTPException(status_code=404, detail="Career not found.")
    return career


@router.post("/{career_id}/cv", response_model=CVResponse)
def build_cv(career_id: str, payload: CVRequest, user: User = Depends(get_current_user)):
    template = _catalogue_call(career_catalogue.get_cv_template, career_id.strip().upper())
    if template is None:
        raise HTTPException(status_code=404, detail="Career not found.")
    opportunity = (payload.target_opportunity or "").strip().lower()
    if opportunity and opportunity not in OPPORTUNITY_TYPES:
        raise HTTPException(
            status_code=422,
            detail="target_opportunity must be one of: " + ", ".join(sorted(OPPORTUNITY_TYPES)),
        )
    profile = payload.model_dump()
    profile["full_name"] = (payload.full_name or user.full_name or "").strip()
    profile["email"] = (payload.email or user.email or "").strip()
    profile["course"] = (payload.course or user.course or "").strip()
    profile["target_opportunity"] = opportunity
    try:
        result = render_cv(template, profile)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CVResponse(**result)
