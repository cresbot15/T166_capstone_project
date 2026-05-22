from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
import os

from src.database import get_db
from src.models.user import User
from src.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse
from src.services.auth import hash_password, verify_password, create_token

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user: UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    
    # Check that username and email aren't taken
    conflicts = []
    if db.query(User).filter((User.email == user.email)).first():
        conflicts.append("Email already in use")
    if db.query(User).filter((User.username == user.username)).first():
        conflicts.append("Username already in use")
    if conflicts:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=conflicts)
    
    db_user = User(
        username = user.username,
        email=user.email,
        password_hash=hash_password(user.password)
    )

    # Add record to the database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model = TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(user.password, str(db_user.password_hash)):
        # Never tell the user if any information provided is correct
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login details")
    
    return TokenResponse(access_token=create_token(db_user.id), token_type="bearer") #type: ignore