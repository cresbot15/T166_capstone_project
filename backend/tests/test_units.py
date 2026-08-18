from src.constants import (
    DEFAULT_MAX_GROUP_SIZE,
    DEFAULT_MIN_GROUP_SIZE,
    MAX_MAX_GROUP_SIZE,
    MIN_MAX_GROUP_SIZE,
    MIN_MIN_GROUP_SIZE,
)
from tests.conftest import (
    TEST_MAX_GROUP_SIZE,
    TEST_MIN_GROUP_SIZE,
    TEST_UNIT_NAME,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
)

def test_create_unit(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password = TEST_USER_PASSWORD)

    request_body = {
        "name": TEST_UNIT_NAME,
        "min_group_size": TEST_MIN_GROUP_SIZE,
        "max_group_size": TEST_MAX_GROUP_SIZE
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 201

    response_body = response.json()

    assert isinstance(response_body["code"], str) and len(response_body["code"]) == 12
    assert response_body["name"] == TEST_UNIT_NAME
    assert response_body["min_group_size"] == TEST_MIN_GROUP_SIZE
    assert response_body["max_group_size"] == TEST_MAX_GROUP_SIZE

def test_create_unit_defaults_group_sizes(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    response = client.post("/units/create", headers=headers, json={"name": TEST_UNIT_NAME})
    assert response.status_code == 201
    assert response.json()["min_group_size"] == DEFAULT_MIN_GROUP_SIZE
    assert response.json()["max_group_size"] == DEFAULT_MAX_GROUP_SIZE

def test_create_unit_rejects_out_of_range_max_group_size(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    for size in (MIN_MAX_GROUP_SIZE - 1, MAX_MAX_GROUP_SIZE + 1):
        request_body = {
            "name": TEST_UNIT_NAME,
            "max_group_size": size
        }

        response = client.post("/units/create", headers=headers, json=request_body)
        assert response.status_code == 422, response.text

def test_create_unit_rejects_out_of_range_min_group_size(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    for size in (MIN_MIN_GROUP_SIZE - 1, MAX_MAX_GROUP_SIZE + 1):
        request_body = {
            "name": TEST_UNIT_NAME,
            "min_group_size": size
        }

        response = client.post("/units/create", headers=headers, json=request_body)
        assert response.status_code == 422, response.text

def test_create_unit_rejects_min_greater_than_max(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    request_body = {
        "name": TEST_UNIT_NAME,
        "min_group_size": 5,
        "max_group_size": 4
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 422, response.text
    assert "min_group_size cannot be greater than max_group_size" in response.text

def test_create_unit_allows_min_equal_to_max(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    request_body = {
        "name": TEST_UNIT_NAME,
        "min_group_size": 4,
        "max_group_size": 4
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 201, response.text
    assert response.json()["min_group_size"] == 4

def test_create_unit_codes_are_unique(client, auth_headers, create_unit):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    first = create_unit(headers=headers, name=TEST_UNIT_NAME)
    second = create_unit(headers=headers, name=TEST_UNIT_NAME)

    assert first["code"] != second["code"]

def _enrol(client, headers, code):
    response = client.post("/units/join", headers=headers, json={"code": code})
    assert response.status_code == 200, response.text

def _student_count(client, headers, unit_id):
    response = client.get(f"/units/{unit_id}/student_count", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["student_count"]

def test_unit_member_count_unit_nonexistent(client, auth_headers):
    headers = auth_headers()

    response = client.get("/units/0/student_count", headers=headers)
    assert response.status_code == 404, response.text

def test_unit_member_count_requires_enrolment(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    outsider_headers = auth_headers(email="outsider@test.com", password=TEST_USER_PASSWORD)

    response = client.get(f"/units/{unit['id']}/student_count", headers=outsider_headers)
    assert response.status_code == 403, response.text

def test_unit_member_count_unauthenticated(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    response = client.get(f"/units/{unit['id']}/student_count")
    assert response.status_code == 401, response.text

def test_unit_member_count_excludes_the_owner(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    assert _student_count(client, owner_headers, unit["id"]) == 0

def test_unit_member_count_counts_enrolled_students(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    for i in range(3):
        _enrol(client, auth_headers(email=f"student{i}@test.com", password=TEST_USER_PASSWORD), unit["code"])

    assert _student_count(client, owner_headers, unit["id"]) == 3

def test_unit_member_count_excludes_administrators(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    promoted_email = "promoted@test.com"
    _enrol(client, auth_headers(email=promoted_email, password=TEST_USER_PASSWORD), unit["code"])
    _enrol(client, auth_headers(email="student@test.com", password=TEST_USER_PASSWORD), unit["code"])

    assert _student_count(client, owner_headers, unit["id"]) == 2

    response = client.get(f"/units/{unit['id']}/members", headers=owner_headers)
    assert response.status_code == 200, response.text
    promoted_id = next(m["user_id"] for m in response.json() if m["email"] == promoted_email)

    response = client.patch(
        f"/units/{unit['id']}/members/{promoted_id}",
        headers=owner_headers,
        json={"role": "administrator"},
    )
    assert response.status_code == 200, response.text

    assert _student_count(client, owner_headers, unit["id"]) == 1

def test_unit_member_count_is_scoped_to_unit(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)
    other_unit = create_unit(headers=owner_headers, name="other_unit")

    for i in range(2):
        _enrol(client, auth_headers(email=f"student{i}@test.com", password=TEST_USER_PASSWORD), unit["code"])

    for i in range(4):
        _enrol(client, auth_headers(email=f"other_student{i}@test.com", password=TEST_USER_PASSWORD), other_unit["code"])

    assert _student_count(client, owner_headers, unit["id"]) == 2
    assert _student_count(client, owner_headers, other_unit["id"]) == 4
