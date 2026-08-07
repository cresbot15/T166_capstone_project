from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.group import Group, GroupMembership
from src.models.unit import Unit, UnitMembership
from src.models.user import User
from src.schemas.group import GroupJoin, GroupJoinResponse, GroupResponse, GroupCreate
from src.services.auth import get_current_user
from src.services.codes import generate_preference_code

router = APIRouter()

def _group_in_unit_or_404(db: Session, unit_id: int, group_id: int) -> Group:
    group = db.query(Group).filter(Group.id == group_id, Group.unit_id == unit_id).first()
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


@router.post("/join", response_model=GroupJoinResponse)
def join_group(body: GroupJoin, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(Group).filter(Group.preference_code == body.preference_code).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid preference code")

    if any(g.unit_id == group.unit_id for g in current_user.groups):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already in a group for this unit")

    if len(group.members) >= 5:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Group is full")

    if group.unit not in current_user.units:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not enrolled in this unit")

    db.add(GroupMembership(user_id=current_user.id, group_id=group.id))
    db.commit()
    db.refresh(group)

    return GroupJoinResponse(valid=True, group=GroupResponse.model_validate(group))

@router.post("/create", response_model=GroupResponse)
def create_group(body: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    unit = db.query(Unit).filter(Unit.id == body.unit_id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    if unit not in current_user.units:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this unit")

    # User is already in a group for this unit
    if any(g.unit_id == unit.id for g in current_user.groups):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already in a group for this unit")

    group = Group(preference_code=generate_preference_code(db), unit_id=unit.id, creator_user_id=current_user.id, is_public=body.is_public)
    db.add(group)
    db.commit()
    db.refresh(group)

    db.add(GroupMembership(user_id=current_user.id, group_id=group.id))
    db.commit()
    db.refresh(group)

    return GroupResponse.model_validate(group)

@router.get("/my-groups", response_model=list[GroupResponse])
def get_my_groups(current_user: User = Depends(get_current_user)):
    return [GroupResponse.model_validate(g) for g in current_user.groups]

@router.get("/{unit_id}", response_model=list[GroupResponse])
def get_groups(unit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this unit")

    query = db.query(Group).filter(Group.unit_id == unit_id)
    if membership.role not in ("owner", "administrator"):
        member_group_ids = [g.id for g in current_user.groups if g.unit_id == unit_id]
        query = query.filter(or_(Group.is_public == True, Group.id.in_(member_group_ids)))

    return [GroupResponse.model_validate(g) for g in query.all()]

@router.get("/{unit_id}/{group_id}/recommended-times", response_model=list[str])
def get_recommended_times(unit_id: int, group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = _group_in_unit_or_404(db, unit_id, group_id)

    if current_user not in group.members:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")

    other_members = [m for m in group.members if m.id != current_user.id]

    if not other_members:
        return []

    sets = []
    for m in other_members:
        profile = next((p for p in m.unit_profiles if p.unit_id == unit_id), None)
        sets.append(set(profile.time_preferences if profile else []))

    result = sets[0]
    for s in sets[1:]:
        result = result & s

    return sorted(result)

@router.delete("/{unit_id}/{group_id}/leave", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def leave_group(unit_id: int, group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = _group_in_unit_or_404(db, unit_id, group_id)

    if current_user not in group.members:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")

    membership = db.query(GroupMembership).filter_by(user_id=current_user.id, group_id=group.id).first()
    db.delete(membership)
    db.commit()

    if len(group.members) == 0:
        db.delete(group)
        db.commit()