from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db, CareerResource
from backend.app.schemas import ResourceListItem, ResourceDetail, ResourceCreate
from backend.app.security import require_admin
from backend.app.security import get_current_user
from backend.app.database import User

router = APIRouter(prefix="/resources", tags=["Career Resources"])


@router.get("", response_model=List[ResourceListItem])
def list_career_resources(
    category: Optional[str] = Query(None, description="Optional category filter e.g. CV Templates"),
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(CareerResource)
    if category and category.lower() != "all":
        query = query.filter(CareerResource.category.ilike(f"%{category}%"))
    resources = query.all()

    items = []
    for r in resources:
        # Create a clean 1-2 sentence summary from first paragraphs
        lines = [line.strip() for line in r.content.splitlines() if line.strip() and not line.startswith("#")]
        summary = lines[0] if lines else "Career guidance resource."
        if len(summary) > 160:
            summary = summary[:157] + "..."
        items.append(
            ResourceListItem(
                resource_id=r.resource_id,
                title=r.title,
                category=r.category,
                summary=summary,
            )
        )
    return items


@router.get("/{resource_id}", response_model=ResourceDetail)
def get_resource_detail(resource_id: str, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    res = db.query(CareerResource).filter(CareerResource.resource_id == resource_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Career resource not found.")
    return ResourceDetail.from_orm(res)


@router.post("", response_model=ResourceDetail)
def create_resource(payload: ResourceCreate, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    import re
    title = payload.title.strip()
    category = payload.category.strip()
    content = payload.content.strip()
    if len(title) < 3 or len(category) < 2 or len(content) < 10:
        raise HTTPException(status_code=422, detail="Title, category, and content are required")
    resource_id = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40]
    if not resource_id:
        raise HTTPException(status_code=422, detail="Title must include letters or numbers")
    existing = db.query(CareerResource).filter(CareerResource.resource_id == resource_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Resource with this title already exists.")

    new_res = CareerResource(
        resource_id=resource_id,
        title=title,
        category=category,
        content=content,
    )
    db.add(new_res)
    db.commit()
    db.refresh(new_res)
    return ResourceDetail.from_orm(new_res)
