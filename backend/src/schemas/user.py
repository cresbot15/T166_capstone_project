from pydantic import BaseModel, EmailStr, field_validator
from src.constants import TIME_SLOTS

class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    is_new_student: bool = False
    delivery_mode: str | None = None
    skills: str | None = None
    time_preferences: list[str] = []
    
    @field_validator("time_preferences")
    @classmethod
    def validate_time_preferences(cls, v: list[str]) -> list[str]:
        # Creates a set of time slots then removes all valid timeslot entries
        # if there are any items left in the set they are invalid timeslots
        invalid = set(v) - TIME_SLOTS
        if invalid:
            raise ValueError(f"Invalid time slots: {sorted(invalid)}")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    is_new_student: bool | None = None
    delivery_mode: str | None = None
    skills: str | None = None
    time_preferences: list[str] | None = None

    @field_validator("time_preferences")
    @classmethod
    def validate_time_preferences(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        invalid = set(v) - TIME_SLOTS
        if invalid:
            raise ValueError(f"Invalid time slots: {sorted(invalid)}")
        return v

class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    is_new_student: bool
    delivery_mode: str | None = None
    skills: str | None = None
    time_preferences: list[str] = []

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"