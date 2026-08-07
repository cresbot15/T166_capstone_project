from typing import Literal
from pydantic import BaseModel, field_validator
from src.constants import TIME_SLOTS

class UnitCreate(BaseModel):
    name: str | None = None

class UnitJoin(BaseModel):
    code: str

class UnitResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    code: str
    name: str | None = None

class UnitPublicResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str | None = None

class UnitRoleUpdate(BaseModel):
    role: Literal["administrator", "student"]

class UnitMembershipResponse(BaseModel):
    model_config = {"from_attributes": True}

    user_id: int
    unit_id: int
    role: str

class UnitProfileUpdate(BaseModel):
    is_new_student: bool | None = None
    delivery_mode: str | None = None
    skills: str | None = None
    time_preferences: list[str] | None = None

    # time_preferences stores raw JSON so we need to validate the the input here in the code
    @field_validator("time_preferences")
    @classmethod
    def validate_time_preferences(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        invalid = set(v) - TIME_SLOTS
        if invalid:
            raise ValueError(f"Invalid time slots: {sorted(invalid)}")
        return v

class UnitMeResponse(BaseModel):
    unit_id: int
    role: str
    is_new_student: bool
    delivery_mode: str | None = None
    skills: str | None = None
    time_preferences: list[str] = []
