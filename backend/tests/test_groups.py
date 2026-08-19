from src.services.requirements import COMMON_TIME_SLOT, MIN_GROUP_SIZE
from tests.conftest import (
    TEST_UNIT_NAME,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
)

SHARED_SLOTS = ["monday09", "wednesday09"]

def test_join_group_respects_unit_max_group_size(auth_headers, create_unit, enrol_user, create_group, join_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=2)

    preference_code = create_group(owner_headers, unit["id"])["preference_code"]

    second_headers = enrol_user(unit["code"], email="second@test.com")
    assert join_group(second_headers, preference_code).status_code == 200

    third_headers = enrol_user(unit["code"], email="third@test.com")

    response = join_group(third_headers, preference_code)
    assert response.status_code == 409
    assert response.json()["detail"] == "Group is full"

def test_join_group_allows_up_to_unit_max_group_size(auth_headers, create_unit, enrol_user, create_group, join_group, get_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=6)

    group = create_group(owner_headers, unit["id"])

    for i in range(5):
        headers = enrol_user(unit["code"], email=f"member{i}@test.com")
        assert join_group(headers, group["preference_code"]).status_code == 200, f"member {i} could not join"

    assert len(get_group(owner_headers, unit["id"], group["id"])["members"]) == 6

def test_join_group_preference_code_is_case_and_whitespace_insensitive(auth_headers, create_unit, enrol_user, create_group, join_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    group = create_group(owner_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")

    response = join_group(joiner_headers, f" {group['preference_code'].lower()}  ")
    assert response.status_code == 200, response.text
    assert response.json()["group"]["id"] == group["id"]

def test_joinable_groups_excludes_private_and_full_groups(auth_headers, create_unit, enrol_user, create_group, join_group, joinable_group_ids):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=2)

    open_headers = enrol_user(unit["code"], email="open_owner@test.com")
    open_group = create_group(open_headers, unit["id"], is_public=True)

    private_headers = enrol_user(unit["code"], email="private_owner@test.com")
    create_group(private_headers, unit["id"], is_public=False)

    full_headers = enrol_user(unit["code"], email="full_owner@test.com")
    full_group = create_group(full_headers, unit["id"], is_public=True)
    filler_headers = enrol_user(unit["code"], email="filler@test.com")
    assert join_group(filler_headers, full_group["preference_code"]).status_code == 200

    assert joinable_group_ids(owner_headers, unit["id"]) == [open_group["id"]]

def test_joinable_groups_drops_a_group_once_it_fills(auth_headers, create_unit, enrol_user, create_group, join_group, joinable_group_ids):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=2)

    group = create_group(owner_headers, unit["id"], is_public=True)

    observer_headers = enrol_user(unit["code"], email="observer@test.com")
    assert joinable_group_ids(observer_headers, unit["id"]) == [group["id"]]

    filler_headers = enrol_user(unit["code"], email="filler@test.com")
    assert join_group(filler_headers, group["preference_code"]).status_code == 200

    assert joinable_group_ids(observer_headers, unit["id"]) == []

def test_joinable_groups_excludes_the_callers_own_group(auth_headers, create_unit, enrol_user, create_group, join_group, joinable_group_ids):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=3)

    group = create_group(owner_headers, unit["id"], is_public=True)

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    assert joinable_group_ids(joiner_headers, unit["id"]) == [group["id"]]

    assert join_group(joiner_headers, group["preference_code"]).status_code == 200

    assert joinable_group_ids(joiner_headers, unit["id"]) == []
    assert joinable_group_ids(owner_headers, unit["id"]) == []

def test_joinable_groups_is_scoped_to_the_unit(auth_headers, create_unit, enrol_user, create_group, joinable_group_ids):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)
    other_unit = create_unit(headers=owner_headers, name="other_unit")

    group_headers = enrol_user(unit["code"], email="group_owner@test.com")
    group = create_group(group_headers, unit["id"], is_public=True)
    create_group(owner_headers, other_unit["id"], is_public=True)

    assert joinable_group_ids(owner_headers, unit["id"]) == [group["id"]]

def test_joinable_groups_requires_enrolment(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    outsider_headers = auth_headers(email="outsider@test.com", password=TEST_USER_PASSWORD)

    response = client.get(f"/groups/{unit['id']}/joinable", headers=outsider_headers)
    assert response.status_code == 403, response.text

def test_joinable_groups_unknown_unit(client, auth_headers):
    headers = auth_headers()

    response = client.get("/groups/0/joinable", headers=headers)
    assert response.status_code == 404, response.text

def test_group_reports_every_unmet_requirement(auth_headers, create_unit, create_group, get_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2)

    group = create_group(owner_headers, unit["id"])

    group = get_group(owner_headers, unit["id"], group["id"])
    assert group["unmet_requirements"] == [MIN_GROUP_SIZE, COMMON_TIME_SLOT]
    assert group["status"] == "provisional"

def test_group_reports_only_the_requirement_it_misses(auth_headers, create_unit, enrol_user, create_group, join_group, get_group, set_time_preferences):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2)
    set_time_preferences(owner_headers, unit["id"], ["monday09"])

    group = create_group(owner_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    set_time_preferences(joiner_headers, unit["id"], ["friday18"])
    assert join_group(joiner_headers, group["preference_code"]).status_code == 200

    group = get_group(owner_headers, unit["id"], group["id"])
    assert group["unmet_requirements"] == [COMMON_TIME_SLOT]
    assert group["status"] == "provisional"

def test_group_meeting_every_requirement_is_pending(auth_headers, create_unit, enrol_user, create_group, join_group, get_group, set_time_preferences):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2)
    set_time_preferences(owner_headers, unit["id"], SHARED_SLOTS)

    group = create_group(owner_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    set_time_preferences(joiner_headers, unit["id"], SHARED_SLOTS)
    assert join_group(joiner_headers, group["preference_code"]).status_code == 200

    group = get_group(owner_headers, unit["id"], group["id"])
    assert group["unmet_requirements"] == []
    assert group["status"] == "pending"
    assert group["common_time_slots"] == SHARED_SLOTS
