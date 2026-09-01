from pydantic import BaseModel, EmailStr, field_validator

from src.constants import USER_ROLE_STUDENT, USER_ROLES
from src.schemas.types import UtcDatetime

class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: str = USER_ROLE_STUDENT

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in USER_ROLES:
            raise ValueError(f"role must be one of {list(USER_ROLES)}")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None

class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    created_at: UtcDatetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"