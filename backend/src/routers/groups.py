from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.models.group import Group
from src.models.user import User
from src.schemas.group import GroupJoin, GroupJoinResponse, GroupResponse, GroupCreate
from src.services.auth import get_current_user

router = APIRouter()

@router.post("/join", response_model=GroupJoinResponse)
def join_group(body: GroupJoin, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check user isn't already in a group
    if current_user.group_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already in a group")

    # Find the group by preference code
    group = db.query(Group).filter(Group.preference_code == body.preference_code).first()
    if not group:
        return GroupJoinResponse(valid=False, reason="Invalid preference code")

    # Check group isn't full
    if len(group.members) >= 5:
        return GroupJoinResponse(valid=False, reason="Group is full")

    # Add user to group
    current_user.group_id = group.id
    db.commit()
    db.refresh(group)

    return GroupJoinResponse(valid=True, group=GroupResponse.model_validate(group))

@router.post("/create", response_model=GroupResponse)
def create_group(body: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Check user isn't already in a group
    if current_user.group_id is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already in a group")

    # Check preference code isn't already in use if one was provided
    if body.preference_code:
        existing = db.query(Group).filter(Group.preference_code == body.preference_code).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Preference code already in use")

    # Create the group
    group = Group(preference_code=body.preference_code)
    db.add(group)
    db.commit()
    db.refresh(group)

    # Add the creator to the group
    current_user.group_id = group.id
    db.commit()
    db.refresh(group)

    return GroupResponse.model_validate(group)

@router.get("/groups", response_model=list[GroupResponse])
def get_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    groups = db.query(Group).all()
    return [GroupResponse.model_validate(group) for group in groups]

@router.delete("/leave_group", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def leave_group(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.group_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not in a group")
    
    group = db.query(Group).filter(Group.id == current_user.group_id).first()
    
    current_user.group_id = None #type: ignore
    db.commit()

    # If group is empty, delete it
    if len(group.members) == 0: #type: ignore
        db.delete(group)
        db.commit()