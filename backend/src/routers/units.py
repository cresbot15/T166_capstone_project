from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.unit import Unit, UnitMembership
from src.models.user import User
from src.schemas.unit import UnitCreate, UnitJoin, UnitResponse
from src.services.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=list[UnitResponse])
def get_units(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Unit).all()

@router.get("/me", response_model=list[UnitResponse])
def get_my_units(current_user: User = Depends(get_current_user)):
    return current_user.units

@router.post("/create", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(body: UnitCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Unit).filter(Unit.code == body.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unit code already exists")

    unit = Unit(code=body.code, name=body.name)
    db.add(unit)
    db.commit()
    db.refresh(unit)

    db.add(UnitMembership(user_id=current_user.id, unit_id=unit.id, role="owner"))
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
    db.commit()
    return unit

@router.delete("/{code}/leave", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
def leave_unit(code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    unit = db.query(Unit).filter(Unit.code == code).first()
    if not unit or unit not in current_user.units:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not enrolled in unit")

    if any(g.unit_id == unit.id for g in current_user.groups):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Leave your group in this unit first")

    membership = db.query(UnitMembership).filter_by(user_id=current_user.id, unit_id=unit.id).first()
    db.delete(membership)
    db.commit()
