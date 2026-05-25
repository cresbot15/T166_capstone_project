from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.user import User
from src.schemas.user import UserRegister, UserLogin, UserUpdate, UserResponse, TokenResponse
from src.services.auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user: UserRegister, db: Session = Depends(get_db)):
    conflicts = []
    if db.query(User).filter(User.email == user.email).first():
        conflicts.append("Email already in use")
    if conflicts:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflicts)

    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password_hash=hash_password(user.password),
        is_new_student=user.is_new_student,
        delivery_mode=user.delivery_mode,
        skills=user.skills,
        time_preferences=user.time_preferences,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, str(db_user.password_hash)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login details")

    return TokenResponse(access_token=create_token(db_user.id), token_type="bearer")  # type: ignore

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_me(update: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user
