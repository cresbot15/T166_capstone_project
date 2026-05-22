import bcrypt

def hash_password(password: str) -> str:
    """Creates salted bcrypt hash of password"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, password_hash: str) -> bool:
    """Check that password's hash is the same as password_hash"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())