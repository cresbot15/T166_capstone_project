from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email:EmailStr
    password:str

class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str
    email: EmailStr

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"