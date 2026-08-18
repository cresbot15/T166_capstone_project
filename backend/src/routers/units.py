from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.unit import Unit, UnitMembership, UnitProfile
from src.models.user import User
from src.schemas.unit import (
    UnitCreate,
    UnitJoin,
    UnitResponse,
    UnitPublicResponse,
    UnitRoleUpdate,
    UnitMembershipResponse,
    UnitMemberResponse,
    UnitProfileUpdate,
    UnitMeResponse,
)
from src.services.auth import get_current_user, require_unit_staff
from src.services.codes import generate_unit_code

router = APIRouter()

@router.get("/", response_model=list[UnitPublicResponse])
def get_units(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Unit).all()

@router.get("/me", response_model=list[UnitResponse])
def get_my_units(current_user: User = Depends(get_current_user)):
    return current_user.units

@router.post("/create", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(body: UnitCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    unit = Unit(
        code=generate_unit_code(db),
        name=body.name,
        min_group_size=body.min_group_size,
        max_group_size=body.max_group_size,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)

    db.add(UnitMembership(user_id=current_user.id, unit_id=unit.id, role="owner"))
    db.add(UnitProfile(user_id=current_user.id, unit_id=unit.id))
    db.commit()

    return unit

@router.post("/join", response_model=UnitResponse)
def join_unit(body: UnitJoin, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    unit = db.query(Unit).filter(Unit.code == body.code).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    if unit in current_user.units:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already enrolled in unit")

    db.add(UnitMembership(user_id=current_user.id, unit_id=unit.id, role="student"))
    db.add(UnitProfile(user_id=current_user.id, unit_id=unit.id))
    db.commit()
    return unit

@router.delete("/{unit_id}/leave", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def leave_unit(unit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enrolled in unit")

    if any(g.unit_id == unit_id for g in current_user.groups):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Leave your group in this unit first")

    db.delete(membership)

    profile = db.query(UnitProfile).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    db.delete(profile)

    db.commit()

@router.get("/{unit_id}/me", response_model=UnitMeResponse)
def get_my_unit_profile(unit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enrolled in this unit")

    profile = db.query(UnitProfile).filter_by(user_id=current_user.id, unit_id=unit_id).first()

    return UnitMeResponse(
        unit_id=unit_id,
        role=membership.role,
        is_new_student=profile.is_new_student,
        delivery_mode=profile.delivery_mode,
        skills=profile.skills,
        time_preferences=profile.time_preferences,
    )

@router.patch("/{unit_id}/me", response_model=UnitMeResponse)
def update_my_unit_profile(unit_id: int, body: UnitProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enrolled in this unit")

    profile = db.query(UnitProfile).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)

    return UnitMeResponse(
        unit_id=unit_id,
        role=membership.role,
        is_new_student=profile.is_new_student,
        delivery_mode=profile.delivery_mode,
        skills=profile.skills,
        time_preferences=profile.time_preferences,
    )

@router.get("/{unit_id}/members", response_model=list[UnitMemberResponse])
def get_unit_members(unit_id: int, db: Session = Depends(get_db), _staff: UnitMembership = Depends(require_unit_staff)):
    memberships = (
        db.query(UnitMembership, User)
        .join(User, User.id == UnitMembership.user_id)
        .filter(UnitMembership.unit_id == unit_id)
        .order_by(User.last_name, User.first_name)
        .all()
    )

    profiles = {p.user_id: p for p in db.query(UnitProfile).filter(UnitProfile.unit_id == unit_id).all()}

    members = []
    for membership, user in memberships:
        profile = profiles.get(user.id)
        members.append(UnitMemberResponse(
            user_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=membership.role,
            is_new_student=profile.is_new_student if profile else False,
            delivery_mode=profile.delivery_mode if profile else None,
            skills=profile.skills if profile else None,
            time_preferences=profile.time_preferences if profile else [],
        ))

    return members

@router.patch("/{unit_id}/members/{user_id}", response_model=UnitMembershipResponse)
def set_member_role(unit_id: int, user_id: int, body: UnitRoleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    caller_membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    if not caller_membership or caller_membership.role != "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the unit owner can change member roles")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    membership = db.query(UnitMembership).filter_by(user_id=target_user.id, unit_id=unit_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not enrolled in this unit")

    if membership.role == "owner":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change the owner's role")

    membership.role = body.role
    db.commit()
    db.refresh(membership)
    return membership

@router.get("/{unit_id}/student_count")
def get_student_count(unit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Unit).filter(Unit.id == unit_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    caller_membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    if not caller_membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not enrolled in this unit")

    student_count = db.query(UnitMembership).filter_by(unit_id=unit_id, role="student").count()

    return {"student_count": student_count}

@router.get("/{unit_id}/export/students")
def export_unit_students(unit_id: int, db: Session = Depends(get_db), curent_user: User = Depends(get_current_user)):
    pass

@router.get("/{unit_id}/export/groups")
def export_unit_groups(unit_id: int, db: Session = Depends(get_db), curent_user: User = Depends(get_current_user)):
    pass