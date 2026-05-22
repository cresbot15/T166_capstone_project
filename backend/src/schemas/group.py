from pydantic import BaseModel
from src.schemas.user import UserResponse

class GroupJoin(BaseModel):
    preference_code: str

class GroupResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    preference_code: str | None = None
    members: list[UserResponse] = []

class GroupJoinResponse(BaseModel):
    valid: bool
    reason: str | None = None
    group: GroupResponse | None = None

class GroupCreate(BaseModel):
    preference_code: str | None = None