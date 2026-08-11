import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from src.main import app

TEST_USER_FNAME = "Test"
TEST_USER_LNAME = "User"
TEST_USER_EMAIL = "user@test.com"
TEST_USER_PASSWORD = "Password123"
TEST_UNIT_NAME = "unit_name"
TEST_MIN_GROUP_SIZE = 2
TEST_MAX_GROUP_SIZE = 5

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
    def _make_user(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD):
        body = {
            "first_name": TEST_USER_FNAME,
            "last_name": TEST_USER_LNAME,
            "email": email,
            "password": password,
        }
        r = client.post("/auth/register", json=body)
        assert r.status_code == 200, r.text
        return r.json()

    return _make_user

@pytest.fixture()
def auth_headers(client, make_user):
    def _auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD):
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
    def _create_unit(headers, name=TEST_UNIT_NAME, min_group_size=TEST_MIN_GROUP_SIZE, max_group_size=TEST_MAX_GROUP_SIZE):
        body = {
            "name": name,
            "min_group_size": min_group_size,
            "max_group_size": max_group_size
        }
        r = client.post("/units/create", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _create_unit
