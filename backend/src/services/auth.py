import os
import bcrypt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.user import User

security = HTTPBearer()

def hash_password(password: str) -> str:
    """Creates salted bcrypt hash of password"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    """Check that password's hash is the same as password_hash"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())

def get_jwt_secret():
    secret = os.getenv("JWT_SECRET")
    if secret is None:
        raise RuntimeError("JWT_SECRET environment variable is not set")
    return secret

def create_token(user_id: int) -> str:
    secret = get_jwt_secret()
    payload = {
        "id": user_id,
        "exp": datetime.now() + timedelta(hours=24)
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def get_current_user(token = Depends(security), db: Session = Depends(get_db)) -> User:
    try:
        secret = get_jwt_secret()
        payload = jwt.decode(token.credentials, secret, algorithms=["HS256"])
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    return user