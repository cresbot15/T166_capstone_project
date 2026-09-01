from pydantic import BaseModel, field_validator
from src.schemas.types import UtcDatetime
from src.schemas.user import UserResponse

class GroupJoin(BaseModel):
    preference_code: str

    # Normalise codes
    @field_validator("preference_code")
    @classmethod
    def normalise_preference_code(cls, v: str) -> str:
        return v.strip().upper()

class GroupResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    preference_code: str | None = None
    unit_id: int
    creator_user_id: int | None = None
    is_public: bool = False
    members: list[UserResponse] = []
    status: str = "provisional"
    unmet_requirements: list[str] = []
    common_time_slots: list[str] = []
    created_at: UtcDatetime

class GroupJoinResponse(BaseModel):
    valid: bool
    reason: str | None = None
    group: GroupResponse | None = None

class GroupCreate(BaseModel):
    unit_id: int
    is_public: bool = False
