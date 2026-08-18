from tests.conftest import (
    TEST_UNIT_NAME,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
)

def _join_group(client, headers, preference_code):
    return client.post("/groups/join", headers=headers, json={"preference_code": preference_code})

def _joinable_group_ids(client, headers, unit_id):
    response = client.get(f"/groups/{unit_id}/joinable", headers=headers)
    assert response.status_code == 200, response.text
    return sorted(g["id"] for g in response.json())

def test_join_group_respects_unit_max_group_size(client, auth_headers, create_unit, enrol_user, create_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=2)

    preference_code = create_group(owner_headers, unit["id"])["preference_code"]

    second_headers = enrol_user(unit["code"], email="second@test.com")
    assert _join_group(client, second_headers, preference_code).status_code == 200

    third_headers = enrol_user(unit["code"], email="third@test.com")

    response = _join_group(client, third_headers, preference_code)
    assert response.status_code == 409
    assert response.json()["detail"] == "Group is full"

def test_join_group_allows_up_to_unit_max_group_size(client, auth_headers, create_unit, enrol_user, create_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=6)

    preference_code = create_group(owner_headers, unit["id"])["preference_code"]

    for i in range(5):
        headers = enrol_user(unit["code"], email=f"member{i}@test.com")
        assert _join_group(client, headers, preference_code).status_code == 200, f"member {i} could not join"

    response = client.get(f"/groups/{unit['id']}", headers=owner_headers)
    assert response.status_code == 200, response.text
    assert len(response.json()[0]["members"]) == 6

def test_joinable_groups_excludes_private_and_full_groups(client, auth_headers, create_unit, enrol_user, create_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=2)

    open_headers = enrol_user(unit["code"], email="open_owner@test.com")
    open_group = create_group(open_headers, unit["id"], is_public=True)

    private_headers = enrol_user(unit["code"], email="private_owner@test.com")
    create_group(private_headers, unit["id"], is_public=False)

    full_headers = enrol_user(unit["code"], email="full_owner@test.com")
    full_group = create_group(full_headers, unit["id"], is_public=True)
    filler_headers = enrol_user(unit["code"], email="filler@test.com")
    assert _join_group(client, filler_headers, full_group["preference_code"]).status_code == 200

    assert _joinable_group_ids(client, owner_headers, unit["id"]) == [open_group["id"]]

def test_joinable_groups_drops_a_group_once_it_fills(client, auth_headers, create_unit, enrol_user, create_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=2)

    group = create_group(owner_headers, unit["id"], is_public=True)

    observer_headers = enrol_user(unit["code"], email="observer@test.com")
    assert _joinable_group_ids(client, observer_headers, unit["id"]) == [group["id"]]

    filler_headers = enrol_user(unit["code"], email="filler@test.com")
    assert _join_group(client, filler_headers, group["preference_code"]).status_code == 200

    assert _joinable_group_ids(client, observer_headers, unit["id"]) == []

def test_joinable_groups_excludes_the_callers_own_group(client, auth_headers, create_unit, enrol_user, create_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=3)

    group = create_group(owner_headers, unit["id"], is_public=True)

    joiner_headers = enrol_user(unit["code"], email="joiner@test.com")
    assert _joinable_group_ids(client, joiner_headers, unit["id"]) == [group["id"]]

    assert _join_group(client, joiner_headers, group["preference_code"]).status_code == 200

    assert _joinable_group_ids(client, joiner_headers, unit["id"]) == []
    assert _joinable_group_ids(client, owner_headers, unit["id"]) == []

def test_joinable_groups_is_scoped_to_the_unit(client, auth_headers, create_unit, enrol_user, create_group):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME)
    other_unit = create_unit(headers=owner_headers, name="other_unit")

    group_headers = enrol_user(unit["code"], email="group_owner@test.com")
    group = create_group(group_headers, unit["id"], is_public=True)
    create_group(owner_headers, other_unit["id"], is_public=True)

    assert _joinable_group_ids(client, owner_headers, unit["id"]) == [group["id"]]

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
