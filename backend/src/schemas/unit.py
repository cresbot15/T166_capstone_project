from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from src.constants import (
    DEFAULT_MAX_GROUP_SIZE,
    DEFAULT_MIN_GROUP_SIZE,
    MAX_MAX_GROUP_SIZE,
    MIN_MAX_GROUP_SIZE,
    MIN_MIN_GROUP_SIZE,
    TIME_SLOT_ORDER,
    TIME_SLOTS,
)

class UnitCreate(BaseModel):
    name: str | None = None
    min_group_size: int = Field(default=DEFAULT_MIN_GROUP_SIZE, ge=MIN_MIN_GROUP_SIZE, le=MAX_MAX_GROUP_SIZE)
    max_group_size: int = Field(default=DEFAULT_MAX_GROUP_SIZE, ge=MIN_MAX_GROUP_SIZE, le=MAX_MAX_GROUP_SIZE)
    time_slots: list[str] | None = None

    @field_validator("time_slots")
    @classmethod
    def validate_time_slots(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        invalid = set(v) - TIME_SLOTS
        if invalid:
            raise ValueError(f"Invalid time slots: {sorted(invalid)}")
        if not v:
            raise ValueError("time_slots cannot be empty")
        # Dedupe and store chronologically so the stored order never depends on the request
        return [slot for slot in TIME_SLOT_ORDER if slot in set(v)]

    @model_validator(mode="after")
    def validate_group_size_range(self):
        if self.min_group_size > self.max_group_size:
            raise ValueError("min_group_size cannot be greater than max_group_size")
        return self

class UnitJoin(BaseModel):
    code: str

class UnitResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    code: str
    name: str | None = None
    min_group_size: int
    max_group_size: int
    time_slots: list[str] = []

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

class UnitMemberResponse(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: str
    is_new_student: bool
    delivery_mode: str | None = None
    skills: str | None = None
    time_preferences: list[str] = []

class UnitMeResponse(BaseModel):
    unit_id: int
    role: str
    is_new_student: bool
    delivery_mode: str | None = None
    skills: str | None = None
    time_preferences: list[str] = []
