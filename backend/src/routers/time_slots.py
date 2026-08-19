from fastapi import APIRouter, Depends

from src.constants import TIME_SLOT_ORDER
from src.models.user import User
from src.services.auth import get_current_user

router = APIRouter()

@router.get("", response_model=list[str])
def get_time_slots(current_user: User = Depends(get_current_user)):
    """The master slot list, chronologically ordered, for choosing a unit's time_slots."""
    return list(TIME_SLOT_ORDER)
