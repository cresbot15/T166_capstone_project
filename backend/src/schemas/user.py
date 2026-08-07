from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str

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

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"