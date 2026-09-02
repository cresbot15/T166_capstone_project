from src.constants import (
    GROUP_EVENT_CREATED,
    GROUP_EVENT_MEMBER_JOINED,
    GROUP_EVENT_MEMBER_LEFT,
    GROUP_EVENT_MEMBER_REMOVED,
    UNIT_EVENT_MEMBER_JOINED,
    UNIT_EVENT_MEMBER_LEFT,
    UNIT_EVENT_ROLE_CHANGED,
    UNIT_ROLE_ADMINISTRATOR,
)
from tests.conftest import (
    TEST_UNIT_NAME,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
)

def _events(client, headers, path):
    response = client.get(path, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()

def _types(events):
    return [e["event_type"] for e in events]

def _member_id(client, headers, unit_id, email):
    response = client.get(f"/units/{unit_id}/members", headers=headers)
    assert response.status_code == 200, response.text
    return next(m["user_id"] for m in response.json() if m["email"] == email)

def test_unit_events_record_joining_and_leaving(client, auth_headers, create_unit, enrol_user):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    student_headers = enrol_user(unit["code"], email="student@test.com")
    response = client.delete(f"/units/{unit['id']}/leave", headers=student_headers)
    assert response.status_code == 204, response.text

    events = _events(client, owner_headers, f"/events/{unit['id']}")

    assert _types(events) == [
        UNIT_EVENT_MEMBER_LEFT,
        UNIT_EVENT_MEMBER_JOINED,
        UNIT_EVENT_MEMBER_JOINED,
    ]

def test_creating_a_group_records_the_group_and_its_creator(client, auth_headers, create_unit, enrol_user, create_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    creator_headers = enrol_user(unit["code"], email="creator@test.com")
    group = create_group(creator_headers, unit["id"])

    events = _events(client, owner_headers, f"/events/{unit['id']}/group/{group['id']}")

    assert _types(events) == [GROUP_EVENT_MEMBER_JOINED, GROUP_EVENT_CREATED]
    assert all(e["group_id"] == group["id"] for e in events)

def test_role_change_records_the_transition(client, auth_headers, create_unit, enrol_user):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    enrol_user(unit["code"], email="promoted@test.com")
    promoted_id = _member_id(client, owner_headers, unit["id"], "promoted@test.com")

    response = client.patch(
        f"/units/{unit['id']}/members/{promoted_id}",
        headers=owner_headers,
        json={"role": UNIT_ROLE_ADMINISTRATOR},
    )
    assert response.status_code == 200, response.text

    events = _events(client, owner_headers, f"/events/{unit['id']}")
    change = next(e for e in events if e["event_type"] == UNIT_EVENT_ROLE_CHANGED)

    assert change["detail"] == {"from": "student", "to": UNIT_ROLE_ADMINISTRATOR}
    assert change["subject_user_id"] == promoted_id
    assert change["subject_name"] is not None

def test_user_events_cover_both_acting_and_being_acted_on(client, auth_headers, create_unit, enrol_user, create_group, join_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    creator_headers = enrol_user(unit["code"], email="creator@test.com")
    group = create_group(creator_headers, unit["id"])

    removed_headers = enrol_user(unit["code"], email="removed@test.com")
    assert join_group(removed_headers, group["preference_code"]).status_code == 200
    removed_id = _member_id(client, owner_headers, unit["id"], "removed@test.com")
    assert client.delete(f"/groups/{unit['id']}/{group['id']}/members/{removed_id}", headers=owner_headers).status_code == 204

    events = _events(client, owner_headers, f"/events/{unit['id']}/user/{removed_id}")

    assert _types(events) == [
        GROUP_EVENT_MEMBER_REMOVED,
        GROUP_EVENT_MEMBER_JOINED,
        UNIT_EVENT_MEMBER_JOINED,
    ]

def test_user_events_survive_leaving_the_unit(client, auth_headers, create_unit, enrol_user):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    departed_headers = enrol_user(unit["code"], email="departed@test.com")
    departed_id = _member_id(client, owner_headers, unit["id"], "departed@test.com")

    assert client.delete(f"/units/{unit['id']}/leave", headers=departed_headers).status_code == 204

    events = _events(client, owner_headers, f"/events/{unit['id']}/user/{departed_id}")
    assert _types(events) == [UNIT_EVENT_MEMBER_LEFT, UNIT_EVENT_MEMBER_JOINED]

def test_events_are_staff_only(client, auth_headers, create_unit, enrol_user, create_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    student_headers = enrol_user(unit["code"], email="student@test.com")
    group = create_group(student_headers, unit["id"])
    student_id = _member_id(client, owner_headers, unit["id"], "student@test.com")

    for path in (
        f"/events/{unit['id']}",
        f"/events/{unit['id']}/group/{group['id']}",
        f"/events/{unit['id']}/user/{student_id}",
    ):
        response = client.get(path, headers=student_headers)
        assert response.status_code == 403, f"{path} -> {response.status_code}"

def test_events_unknown_group_and_user(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    assert client.get(f"/events/{unit['id']}/group/999", headers=owner_headers).status_code == 404
    assert client.get(f"/events/{unit['id']}/user/999", headers=owner_headers).status_code == 404

def test_events_are_correctly_paginated(client, auth_headers, create_unit, enrol_user):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    for i in range(4):
        enrol_user(unit["code"], email=f"student{i}@test.com")

    all_events = _events(client, owner_headers, f"/events/{unit['id']}")
    assert len(all_events) == 5

    first_page = _events(client, owner_headers, f"/events/{unit['id']}?limit=2")
    second_page = _events(client, owner_headers, f"/events/{unit['id']}?limit=2&offset=2")

    assert [e["id"] for e in first_page] == [e["id"] for e in all_events[:2]]
    assert [e["id"] for e in second_page] == [e["id"] for e in all_events[2:4]]
