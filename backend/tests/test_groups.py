from src.services.requirements import COMMON_TIME_SLOT, MAX_NEW_STUDENTS, MIN_GROUP_SIZE
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

def test_group_over_max_new_students_is_provisional(auth_headers, create_unit, enrol_user, create_group, join_group, get_group, set_time_preferences, set_new_student):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2, max_new_students=1)
    set_time_preferences(owner_headers, unit["id"], SHARED_SLOTS)
    set_new_student(owner_headers, unit["id"], True)

    group = create_group(owner_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    set_time_preferences(joiner_headers, unit["id"], SHARED_SLOTS)
    set_new_student(joiner_headers, unit["id"], True)
    assert join_group(joiner_headers, group["preference_code"]).status_code == 200

    group = get_group(owner_headers, unit["id"], group["id"])
    assert group["unmet_requirements"] == [MAX_NEW_STUDENTS]
    assert group["status"] == "provisional"

def test_group_at_max_new_students_is_pending(auth_headers, create_unit, enrol_user, create_group, join_group, get_group, set_time_preferences, set_new_student):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2, max_new_students=1)
    set_time_preferences(owner_headers, unit["id"], SHARED_SLOTS)
    set_new_student(owner_headers, unit["id"], True)

    group = create_group(owner_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    set_time_preferences(joiner_headers, unit["id"], SHARED_SLOTS)
    assert join_group(joiner_headers, group["preference_code"]).status_code == 200

    group = get_group(owner_headers, unit["id"], group["id"])
    assert group["unmet_requirements"] == []
    assert group["status"] == "pending"

def test_group_ignores_new_students_when_the_unit_sets_no_maximum(auth_headers, create_unit, enrol_user, create_group, join_group, get_group, set_time_preferences, set_new_student):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2)
    assert unit["max_new_students"] is None

    set_time_preferences(owner_headers, unit["id"], SHARED_SLOTS)
    set_new_student(owner_headers, unit["id"], True)

    group = create_group(owner_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    set_time_preferences(joiner_headers, unit["id"], SHARED_SLOTS)
    set_new_student(joiner_headers, unit["id"], True)
    assert join_group(joiner_headers, group["preference_code"]).status_code == 200

    group = get_group(owner_headers, unit["id"], group["id"])
    assert group["unmet_requirements"] == []
    assert group["status"] == "pending"

def test_zero_max_new_students_admits_a_group_with_no_new_students(auth_headers, create_unit, enrol_user, create_group, join_group, get_group, set_time_preferences, set_new_student):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2, max_new_students=0)
    set_time_preferences(owner_headers, unit["id"], SHARED_SLOTS)

    group = create_group(owner_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    set_time_preferences(joiner_headers, unit["id"], SHARED_SLOTS)
    assert join_group(joiner_headers, group["preference_code"]).status_code == 200

    assert get_group(owner_headers, unit["id"], group["id"])["unmet_requirements"] == []

    set_new_student(joiner_headers, unit["id"], True)

    group = get_group(owner_headers, unit["id"], group["id"])
    assert group["unmet_requirements"] == [MAX_NEW_STUDENTS]
    assert group["status"] == "provisional"

def test_joining_is_never_blocked_by_max_new_students(auth_headers, create_unit, enrol_user, create_group, join_group, get_group, set_time_preferences, set_new_student):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2, max_new_students=0)
    set_time_preferences(owner_headers, unit["id"], SHARED_SLOTS)

    group = create_group(owner_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    set_time_preferences(joiner_headers, unit["id"], SHARED_SLOTS)
    set_new_student(joiner_headers, unit["id"], True)

    response = join_group(joiner_headers, group["preference_code"])
    assert response.status_code == 200, response.text

    group = get_group(owner_headers, unit["id"], group["id"])
    assert len(group["members"]) == 2
    assert group["unmet_requirements"] == [MAX_NEW_STUDENTS]

def _member_ids(client, headers, unit_id, group_id):
    response = client.get(f"/groups/{unit_id}", headers=headers)
    assert response.status_code == 200, response.text
    group = next(g for g in response.json() if g["id"] == group_id)
    return [m["id"] for m in group["members"]]

def test_staff_can_remove_a_member_from_a_group(client, auth_headers, create_unit, enrol_user, create_group, join_group, get_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2)

    creator_headers = enrol_user(unit["code"], email="creator@test.com")
    group = create_group(creator_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    assert join_group(joiner_headers, group["preference_code"]).status_code == 200

    member_ids = _member_ids(client, owner_headers, unit["id"], group["id"])
    assert len(member_ids) == 2
    removed_id = member_ids[1]

    response = client.delete(f"/groups/{unit['id']}/{group['id']}/members/{removed_id}", headers=owner_headers)
    assert response.status_code == 204, response.text

    assert _member_ids(client, owner_headers, unit["id"], group["id"]) == [member_ids[0]]

def test_removing_the_last_member_deletes_the_group(client, auth_headers, create_unit, enrol_user, create_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    creator_headers = enrol_user(unit["code"], email="creator@test.com")
    group = create_group(creator_headers, unit["id"])

    member_ids = _member_ids(client, owner_headers, unit["id"], group["id"])

    response = client.delete(f"/groups/{unit['id']}/{group['id']}/members/{member_ids[0]}", headers=owner_headers)
    assert response.status_code == 204, response.text

    response = client.get(f"/groups/{unit['id']}", headers=owner_headers)
    assert response.status_code == 200, response.text
    assert response.json() == []

def test_removing_a_member_can_make_a_group_provisional(client, auth_headers, create_unit, enrol_user, create_group, join_group, get_group, set_time_preferences):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, min_group_size=2)

    creator_headers = enrol_user(unit["code"], email="creator@test.com")
    set_time_preferences(creator_headers, unit["id"], SHARED_SLOTS)
    group = create_group(creator_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    set_time_preferences(joiner_headers, unit["id"], SHARED_SLOTS)
    assert join_group(joiner_headers, group["preference_code"]).status_code == 200

    assert get_group(owner_headers, unit["id"], group["id"])["status"] == "pending"

    removed_id = _member_ids(client, owner_headers, unit["id"], group["id"])[1]
    response = client.delete(f"/groups/{unit['id']}/{group['id']}/members/{removed_id}", headers=owner_headers)
    assert response.status_code == 204, response.text

    group = get_group(owner_headers, unit["id"], group["id"])
    assert group["status"] == "provisional"
    assert group["unmet_requirements"] == [MIN_GROUP_SIZE]

def test_removing_a_member_who_is_not_in_the_group(client, auth_headers, create_unit, enrol_user, create_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    creator_headers = enrol_user(unit["code"], email="creator@test.com")
    group = create_group(creator_headers, unit["id"])

    enrol_user(unit["code"], email="bystander@test.com")
    bystander_id = next(
        m["user_id"]
        for m in client.get(f"/units/{unit['id']}/members", headers=owner_headers).json()
        if m["email"] == "bystander@test.com"
    )

    response = client.delete(f"/groups/{unit['id']}/{group['id']}/members/{bystander_id}", headers=owner_headers)
    assert response.status_code == 404, response.text

def test_students_cannot_remove_group_members(client, auth_headers, create_unit, enrol_user, create_group, join_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)

    creator_headers = enrol_user(unit["code"], email="creator@test.com")
    group = create_group(creator_headers, unit["id"])

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    assert join_group(joiner_headers, group["preference_code"]).status_code == 200

    member_ids = _member_ids(client, owner_headers, unit["id"], group["id"])

    response = client.delete(f"/groups/{unit['id']}/{group['id']}/members/{member_ids[0]}", headers=joiner_headers)
    assert response.status_code == 403, response.text

    assert len(_member_ids(client, owner_headers, unit["id"], group["id"])) == 2
