import secrets
from sqlalchemy.orm import Session
from src.models.group import Group
from src.models.unit import Unit

# Exclude ambigious characters O/0 1/i/l
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 12

def _generate_code(db: Session, model, column) -> str:
    while True:
        code = "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LENGTH))
        if not db.query(model).filter(column == code).first():
            return code

def generate_preference_code(db: Session) -> str:
    """Generates a random group preference code that isn't already in use"""
    return _generate_code(db, Group, Group.preference_code)

def generate_unit_code(db: Session) -> str:
    """Generates a random unit join code that isn't already in use"""
    return _generate_code(db, Unit, Unit.code)
