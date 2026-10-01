import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.database import get_db, User
from backend.app.schemas import LoginRequest, RegisterRequest, ProfileUpdateRequest, AuthResponse, UserResponse
from backend.app.security import create_access_token, get_current_user, hash_password, is_password_hashed, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=UserResponse)
def get_profile(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
def update_profile(payload: ProfileUpdateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.full_name = payload.full_name.strip()
    user.course = payload.course.strip() if payload.course else None
    user.career_goal = payload.career_goal.strip() if payload.career_goal else None
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not is_password_hashed(user.password_hash):
        user.password_hash = hash_password(payload.password)
        db.commit()

    token = create_access_token(user)
    return AuthResponse(
        token=token,
        user=UserResponse.from_orm(user),
    )


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email_clean = payload.email.strip().lower()
    if len(payload.full_name.strip()) < 2:
        raise HTTPException(status_code=422, detail="Full name must contain at least 2 characters")
    existing = db.query(User).filter(User.email.ilike(email_clean)).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in.",
        )

    new_user = User(
        user_id=str(uuid.uuid4()),
        full_name=payload.full_name.strip(),
        email=email_clean,
        password_hash=hash_password(payload.password),
        role="student",
        course=payload.course,
        career_goal=payload.career_goal,
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email address already exists") from exc
    db.refresh(new_user)

    token = create_access_token(new_user)
    return AuthResponse(
        token=token,
        user=UserResponse.from_orm(new_user),
    )
