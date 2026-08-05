import secrets
from sqlalchemy.orm import Session
from src.models.group import Group

# Exclude ambigious characters O/0 1/i/l
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 12

def generate_preference_code(db: Session) -> str:
    """Generates a random preference code that isn't already in use"""
    while True:
        code = "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LENGTH))
        if not db.query(Group).filter(Group.preference_code == code).first():
            return code
