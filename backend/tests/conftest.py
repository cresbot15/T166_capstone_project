import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.main import app

# Create test client with an in-memory SQLite database
@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    # Equivalent to the SessionLocal that gets declared in database.py
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def make_user(client):
    def _make_user(email="user@test.com", password="password123"):
        body = {
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password": password,
        }
        r = client.post("/auth/register", json=body)
        assert r.status_code == 200, r.text
        return r.json()

    return _make_user

@pytest.fixture()
def auth_headers(client, make_user):
    def _auth_headers(email="user@test.com", password="password123"):
        make_user(email=email, password=password)
        body = {
            "email": email,
            "password": password
        }
        r = client.post("/auth/login", json=body)
        assert r.status_code == 200, r.text
        token = r.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers

@pytest.fixture()
def create_unit(client):
    def _create_unit(headers, name="unit_name"):
        body = {
            "name": name
        }
        r = client.post("/units/create", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _create_unit
