from pydantic import BaseModel
from src.schemas.user import UserResponse

class GroupJoin(BaseModel):
    preference_code: str

class GroupResponse(BaseModel):
    id: int
    preference_code: str | None = None
    members: list[UserResponse] = []

    class Config:
        from_attributes = True

class GroupJoinResponse(BaseModel):
    valid: bool
    reason: str | None = None
    group: GroupResponse | None = None