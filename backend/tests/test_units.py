import csv
import io

from src.constants import (
    DEFAULT_MAX_GROUP_SIZE,
    DEFAULT_MIN_GROUP_SIZE,
    MAX_MAX_GROUP_SIZE,
    MIN_MAX_GROUP_SIZE,
    MIN_MIN_GROUP_SIZE,
    TIME_SLOT_ORDER,
)
from src.routers.units import EXPORT_COLUMNS
from src.services.requirements import MIN_GROUP_SIZE
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

def test_create_unit_sets_max_new_students(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    request_body = {
        "name": TEST_UNIT_NAME,
        "max_new_students": 2
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 201, response.text
    assert response.json()["max_new_students"] == 2

def test_create_unit_defaults_to_no_max_new_students(auth_headers, create_unit):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    unit = create_unit(headers=headers, name=TEST_UNIT_NAME)

    assert unit["max_new_students"] is None

def test_create_unit_allows_zero_max_new_students(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    request_body = {
        "name": TEST_UNIT_NAME,
        "max_new_students": 0
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 201, response.text
    assert response.json()["max_new_students"] == 0

def test_create_unit_rejects_out_of_range_max_new_students(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    for size in (-1, MAX_MAX_GROUP_SIZE + 1):
        request_body = {
            "name": TEST_UNIT_NAME,
            "max_new_students": size
        }

        response = client.post("/units/create", headers=headers, json=request_body)
        assert response.status_code == 422, response.text

def test_create_unit_defaults_to_every_time_slot(client, auth_headers, create_unit):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    unit = create_unit(headers=headers, name=TEST_UNIT_NAME)

    assert unit["time_slots"] == list(TIME_SLOT_ORDER)
    assert len(unit["time_slots"]) == 7 * 24

def test_create_unit_accepts_a_subset_of_time_slots(client, auth_headers, create_unit):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    unit = create_unit(headers=headers, name=TEST_UNIT_NAME, time_slots=["wednesday14", "monday09"])

    assert unit["time_slots"] == ["monday09", "wednesday14"]

def test_create_unit_rejects_unknown_time_slots(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    request_body = {
        "name": TEST_UNIT_NAME,
        "time_slots": ["monday09", "mondayMorning", "monday24"]
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 422, response.text
    assert "mondayMorning" in response.text
    assert "monday24" in response.text

def test_create_unit_rejects_empty_time_slots(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    request_body = {
        "name": TEST_UNIT_NAME,
        "time_slots": []
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 422, response.text

def test_time_preferences_must_be_offered_by_the_unit(client, auth_headers, create_unit, set_time_preferences):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=headers, name=TEST_UNIT_NAME, time_slots=["monday09", "monday10"])

    set_time_preferences(headers, unit["id"], ["monday09"])

    response = client.patch(
        f"/units/{unit['id']}/me",
        headers=headers,
        json={"time_preferences": ["monday09", "friday18"]},
    )
    assert response.status_code == 422, response.text
    assert "friday18" in response.text

def test_time_preferences_still_reject_unknown_slots(client, auth_headers, create_unit):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=headers, name=TEST_UNIT_NAME)

    response = client.patch(
        f"/units/{unit['id']}/me",
        headers=headers,
        json={"time_preferences": ["notARealSlot"]},
    )
    assert response.status_code == 422, response.text

def test_join_unit_code_is_case_and_whitespace_insensitive(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    student_headers = auth_headers(email="student@test.com", password=TEST_USER_PASSWORD)

    response = client.post("/units/join", headers=student_headers, json={"code": f"  {unit['code'].lower()} "})
    assert response.status_code == 200, response.text
    assert response.json()["id"] == unit["id"]

def test_join_unit_rejects_an_incorrect_code(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    student_headers = auth_headers(email="student@test.com", password=TEST_USER_PASSWORD)

    response = client.post("/units/join", headers=student_headers, json={"code": "notarealcode"})
    assert response.status_code == 404, response.text

def test_create_unit_codes_are_unique(client, auth_headers, create_unit):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    first = create_unit(headers=headers, name=TEST_UNIT_NAME)
    second = create_unit(headers=headers, name=TEST_UNIT_NAME)

    assert first["code"] != second["code"]

def _student_count(client, headers, unit_id):
    response = client.get(f"/units/{unit_id}/student_count", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["student_count"]

def _export_rows(client, headers, unit_id):
    response = client.get(f"/units/{unit_id}/export", headers=headers)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")
    reader = csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")))
    return response, {row["email"]: row for row in reader}

def test_export_lists_every_member_with_their_group(client, auth_headers, create_unit, enrol_user, create_group, set_time_preferences, set_new_student):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2)

    grouped_headers = enrol_user(unit["code"], email="grouped@test.com")
    set_time_preferences(grouped_headers, unit["id"], ["monday09", "monday10"])
    set_new_student(grouped_headers, unit["id"], True)
    group = create_group(grouped_headers, unit["id"])

    ungrouped_headers = enrol_user(unit["code"], email="ungrouped@test.com")
    set_time_preferences(ungrouped_headers, unit["id"], ["monday09"])

    response, rows = _export_rows(client, owner_headers, unit["id"])

    assert response.headers["content-disposition"] == f'attachment; filename="{unit["code"]}-students.csv"'
    assert set(rows) == {TEST_USER_EMAIL, "grouped@test.com", "ungrouped@test.com"}

    grouped = rows["grouped@test.com"]
    assert grouped["role"] == "student"
    assert grouped["is_new_student"] == "True"
    assert grouped["time_preference_count"] == "2"
    assert grouped["group_id"] == str(group["id"])
    assert grouped["preference_code"] == group["preference_code"]
    assert grouped["group_status"] == "provisional"
    assert grouped["group_unmet_requirements"] == MIN_GROUP_SIZE
    assert grouped["group_member_count"] == "1"

def test_export_header_matches_the_declared_columns(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    response = client.get(f"/units/{unit['id']}/export", headers=owner_headers)
    assert response.status_code == 200, response.text

    header = next(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert header == EXPORT_COLUMNS

def test_export_is_staff_only(client, auth_headers, create_unit, enrol_user):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    student_headers = enrol_user(unit["code"], email="student@test.com")

    response = client.get(f"/units/{unit['id']}/export", headers=student_headers)
    assert response.status_code == 403, response.text

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

def test_unit_member_count_counts_enrolled_students(client, auth_headers, create_unit, enrol_user):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    for i in range(3):
        enrol_user(unit["code"], email=f"student{i}@test.com")

    assert _student_count(client, owner_headers, unit["id"]) == 3

def test_unit_member_count_excludes_administrators(client, auth_headers, create_unit, enrol_user):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    promoted_email = "promoted@test.com"
    enrol_user(unit["code"], email=promoted_email)
    enrol_user(unit["code"], email="student@test.com")

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

def test_unit_member_count_is_scoped_to_unit(client, auth_headers, create_unit, enrol_user):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)
    other_unit = create_unit(headers=owner_headers, name="other_unit")

    for i in range(2):
        enrol_user(unit["code"], email=f"student{i}@test.com")

    for i in range(4):
        enrol_user(other_unit["code"], email=f"other_student{i}@test.com")

    assert _student_count(client, owner_headers, unit["id"]) == 2
    assert _student_count(client, owner_headers, other_unit["id"]) == 4
