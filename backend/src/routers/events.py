from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from src.database import get_db
from src.models.group import Group
from src.models.unit import UnitMembership
from src.models.unit_event import UnitEvent
from src.models.user import User
from src.schemas.unit_event import UnitEventResponse
from src.services.auth import require_unit_staff

router = APIRouter()


def _events(
    db: Session,
    unit_id: int,
    limit: int,
    offset: int,
    group_id: int | None = None,
    user_id: int | None = None,
):
    query = (
        db.query(UnitEvent)
        .options(selectinload(UnitEvent.actor_user), selectinload(UnitEvent.subject_user))
        .filter(UnitEvent.unit_id == unit_id)
    )
    if group_id is not None:
        query = query.filter(UnitEvent.group_id == group_id)
    if user_id is not None:
        query = query.filter(
            or_(UnitEvent.actor_user_id == user_id, UnitEvent.subject_user_id == user_id)
        )

    return (
        query.order_by(UnitEvent.created_at.desc(), UnitEvent.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


@router.get("/{unit_id}", response_model=list[UnitEventResponse])
def get_unit_events(
    unit_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _staff: UnitMembership = Depends(require_unit_staff),
):
    '''Returns the audit log for the given unit, newest first

    Only usable by unit owners and administrators'''
    return [UnitEventResponse.model_validate(e) for e in _events(db, unit_id, limit, offset)]


@router.get("/{unit_id}/group/{group_id}", response_model=list[UnitEventResponse])
def get_group_events(
    unit_id: int,
    group_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _staff: UnitMembership = Depends(require_unit_staff),
):
    '''Returns the audit log entries for one group in the given unit, newest first

    Only usable by unit owners and administrators'''
    if not db.query(Group).filter(Group.id == group_id, Group.unit_id == unit_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    return [UnitEventResponse.model_validate(e) for e in _events(db, unit_id, limit, offset, group_id)]


@router.get("/{unit_id}/user/{user_id}", response_model=list[UnitEventResponse])
def get_user_events(
    unit_id: int,
    user_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _staff: UnitMembership = Depends(require_unit_staff),
):
    '''Returns the audit log entries involving one user in the given unit, newest first

    Covers events the user caused and events that happened to them. Users who
    have left the unit still have history, so current membership is not required.

    Only usable by unit owners and administrators'''
    if not db.query(User).filter(User.id == user_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return [
        UnitEventResponse.model_validate(e)
        for e in _events(db, unit_id, limit, offset, user_id=user_id)
    ]
