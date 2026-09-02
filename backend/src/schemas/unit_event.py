from pydantic import BaseModel
from src.schemas.types import UtcDatetime


class UnitEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    unit_id: int
    event_type: str
    actor_user_id: int | None = None
    actor_name: str | None = None
    subject_user_id: int | None = None
    subject_name: str | None = None
    group_id: int | None = None
    detail: dict | None = None
    created_at: UtcDatetime
