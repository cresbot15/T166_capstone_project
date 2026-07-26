from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.unit import Unit
from src.models.user import User
from src.schemas.unit import UnitCreate, UnitResponse
from src.services.auth import get_current_user

router = APIRouter()

@router.get("/", response_model=list[UnitResponse])
def get_units(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Unit).all()

@router.post("/create", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
def create_unit(body: UnitCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Unit).filter(Unit.code == body.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Unit code already exists")

    unit = Unit(code=body.code, name=body.name)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit