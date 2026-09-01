import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from src.constants import TIME_SLOT_ORDER, UNIT_ROLE_OWNER, UNIT_ROLE_STUDENT
from src.database import get_db
from src.models.group import Group
from src.models.unit import Unit, UnitMembership, UnitProfile
from src.models.user import User
from src.schemas.unit import (
    UnitCreate,
    UnitJoin,
    UnitResponse,
    UnitRoleUpdate,
    UnitMembershipResponse,
    UnitMemberResponse,
    UnitProfileUpdate,
    UnitMeResponse,
)
from src.services.auth import get_current_user, require_coordinator, require_unit_staff
from src.services.codes import generate_unit_code

router = APIRouter()

@router.get("/me", response_model=list[UnitResponse])
def get_my_units(current_user: User = Depends(get_current_user)):
    '''Returns all units that the currently logged in user is enrolled in'''
    return current_user.units

@router.post("/create", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(body: UnitCreate, db: Session = Depends(get_db), current_user: User = Depends(require_coordinator)):
    '''Attempts to create a unit as the logged in user
    
    The logged in user will added to the unit as its owner'''
    unit = Unit(
        code=generate_unit_code(db),
        name=body.name,
        min_group_size=body.min_group_size,
        max_group_size=body.max_group_size,
        max_new_students=body.max_new_students,
        time_slots=body.time_slots or list(TIME_SLOT_ORDER),
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)

    db.add(UnitMembership(user_id=current_user.id, unit_id=unit.id, role=UNIT_ROLE_OWNER))
    db.add(UnitProfile(user_id=current_user.id, unit_id=unit.id))
    db.commit()

    return unit

@router.post("/join", response_model=UnitResponse)
def join_unit(body: UnitJoin, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    '''Attempts to join the a unit using the unit join code in the body as the logged in user'''
    unit = db.query(Unit).filter(Unit.code == body.code).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    if unit in current_user.units:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already enrolled in unit")

    db.add(UnitMembership(user_id=current_user.id, unit_id=unit.id, role=UNIT_ROLE_STUDENT))
    db.add(UnitProfile(user_id=current_user.id, unit_id=unit.id))
    db.commit()
    return unit

@router.delete("/{unit_id}/leave", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def leave_unit(unit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    '''Attempts to remove the logged in user from the given unit'''
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
    '''Gets the unit profile of the currently logged in user'''
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
    '''Updates the unit profile of the currently logged in user
    
    Any body parameters not sent will remain unchanged, they will not be nulled'''
    membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enrolled in this unit")

    if body.time_preferences is not None:
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        invalid = sorted(set(body.time_preferences) - set(unit.time_slots))
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Time slots not offered by this unit: {invalid}",
            )

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
def get_unit_members(unit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    '''Usable by any member of the unit (owner, administrator, or student) so
    students can find others in their unit. Role changes remain owner-only,
    enforced separately by PATCH /{unit_id}/members/{user_id}.

    Returns a list of all current members in the given unit'''
    membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enrolled in this unit")

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
    '''This endpoint is only usable by unit owners and administrators'''
    caller_membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    if not caller_membership or caller_membership.role != UNIT_ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the unit owner can change member roles")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    membership = db.query(UnitMembership).filter_by(user_id=target_user.id, unit_id=unit_id).first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not enrolled in this unit")

    if membership.role == UNIT_ROLE_OWNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot change the owner's role")

    membership.role = body.role
    db.commit()
    db.refresh(membership)
    return membership

@router.get("/{unit_id}/student_count")
def get_student_count(unit_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    '''Returns the number of students currently enrolled in the given unit'''
    if not db.query(Unit).filter(Unit.id == unit_id).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")

    caller_membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit_id).first()
    if not caller_membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not enrolled in this unit")

    student_count = db.query(UnitMembership).filter_by(unit_id=unit_id, role=UNIT_ROLE_STUDENT).count()

    return {"student_count": student_count}

EXPORT_COLUMNS = [
    "user_id",
    "first_name",
    "last_name",
    "email",
    "role",
    "is_new_student",
    "delivery_mode",
    "skills",
    "time_preference_count",
    "group_id",
    "preference_code",
    "group_status",
    "group_unmet_requirements",
    "group_member_count",
    "group_common_time_slots",
]

@router.get("/{unit_id}/export", response_class=Response)
def export_unit_students(unit_id: int, db: Session = Depends(get_db), _staff: UnitMembership = Depends(require_unit_staff)):
    '''This endpoint is only usable by the owner of the given unit
    
    Exports a csv file with information about all students in the unit'''
    unit = db.query(Unit).filter(Unit.id == unit_id).first()

    memberships = (
        db.query(UnitMembership, User)
        .join(User, User.id == UnitMembership.user_id)
        .filter(UnitMembership.unit_id == unit_id)
        .order_by(User.last_name, User.first_name)
        .all()
    )

    profiles = {p.user_id: p for p in db.query(UnitProfile).filter(UnitProfile.unit_id == unit_id).all()}

    # Grade each group once rather than per member
    group_by_user = {}
    group_columns = {}
    for group in db.query(Group).filter(Group.unit_id == unit_id).all():
        group_columns[group.id] = [
            group.id,
            group.preference_code,
            group.status,
            "; ".join(group.unmet_requirements),
            len(group.members),
            "; ".join(group.common_time_slots),
        ]
        for member in group.members:
            group_by_user[member.id] = group.id

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(EXPORT_COLUMNS)

    for membership, user in memberships:
        profile = profiles.get(user.id)
        group_id = group_by_user.get(user.id)

        writer.writerow([
            user.id,
            user.first_name,
            user.last_name,
            user.email,
            membership.role,
            profile.is_new_student if profile else False,
            profile.delivery_mode if profile else None,
            profile.skills if profile else None,
            len(profile.time_preferences) if profile else 0,
            *(group_columns[group_id] if group_id else [None] * 6),
        ])

    filename = f"{unit.code}-students.csv"

    return Response(
        # Excel misreads UTF-8 without a byte order mark
        content=buffer.getvalue().encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )