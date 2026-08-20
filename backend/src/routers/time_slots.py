from fastapi import APIRouter, Depends

from src.constants import TIME_SLOT_ORDER
from src.models.user import User
from src.services.auth import get_current_user

router = APIRouter()

@router.get("", response_model=list[str])
def get_time_slots(current_user: User = Depends(get_current_user)):
    '''Returns the master list, of time_slots for the application'''
    return list(TIME_SLOT_ORDER)
