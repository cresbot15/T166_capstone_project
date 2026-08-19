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
    def _create_unit(headers, name=TEST_UNIT_NAME, min_group_size=TEST_MIN_GROUP_SIZE, max_group_size=TEST_MAX_GROUP_SIZE, time_slots=None):
        body = {
            "name": name,
            "min_group_size": min_group_size,
            "max_group_size": max_group_size
        }
        if time_slots is not None:
            body["time_slots"] = time_slots
        r = client.post("/units/create", json=body, headers=headers)
        assert r.status_code == 201, r.text
        return r.json()

    return _create_unit

@pytest.fixture()
def join_unit(client):
    def _join_unit(headers, code):
        r = client.post("/units/join", json={"code": code}, headers=headers)
        assert r.status_code == 200, r.text
        return r.json()

    return _join_unit

@pytest.fixture()
def enrol_user(auth_headers, join_unit):
    def _enrol_user(code, email, password=TEST_USER_PASSWORD):
        headers = auth_headers(email=email, password=password)
        join_unit(headers, code)
        return headers

    return _enrol_user

@pytest.fixture()
def join_group(client):
    def _join_group(headers, preference_code):
        return client.post("/groups/join", json={"preference_code": preference_code}, headers=headers)

    return _join_group

@pytest.fixture()
def get_group(client):
    def _get_group(headers, unit_id, group_id):
        r = client.get(f"/groups/{unit_id}", headers=headers)
        assert r.status_code == 200, r.text
        return next(g for g in r.json() if g["id"] == group_id)

    return _get_group

@pytest.fixture()
def joinable_group_ids(client):
    def _joinable_group_ids(headers, unit_id):
        r = client.get(f"/groups/{unit_id}/joinable", headers=headers)
        assert r.status_code == 200, r.text
        return sorted(g["id"] for g in r.json())

    return _joinable_group_ids

@pytest.fixture()
def set_time_preferences(client):
    def _set_time_preferences(headers, unit_id, slots):
        r = client.patch(f"/units/{unit_id}/me", json={"time_preferences": slots}, headers=headers)
        assert r.status_code == 200, r.text
        return r.json()

    return _set_time_preferences

@pytest.fixture()
def create_group(client):
    def _create_group(headers, unit_id, is_public=False):
        body = {
            "unit_id": unit_id,
            "is_public": is_public
        }
        r = client.post("/groups/create", json=body, headers=headers)
        assert r.status_code == 200, r.text
        return r.json()

    return _create_group
