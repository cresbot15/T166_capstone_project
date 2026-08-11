from tests.conftest import (
    TEST_UNIT_NAME,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
)

def _join_unit(client, headers, code):
    response = client.post("/units/join", headers=headers, json={"code": code})
    assert response.status_code == 200, response.text

def _join_group(client, headers, preference_code):
    return client.post("/groups/join", headers=headers, json={"preference_code": preference_code})

def test_join_group_respects_unit_max_group_size(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=2)

    response = client.post("/groups/create", headers=owner_headers, json={"unit_id": unit["id"]})
    assert response.status_code == 200, response.text
    preference_code = response.json()["preference_code"]

    second_headers = auth_headers(email="second@test.com", password=TEST_USER_PASSWORD)
    _join_unit(client, second_headers, unit["code"])
    assert _join_group(client, second_headers, preference_code).status_code == 200

    third_headers = auth_headers(email="third@test.com", password=TEST_USER_PASSWORD)
    _join_unit(client, third_headers, unit["code"])

    response = _join_group(client, third_headers, preference_code)
    assert response.status_code == 409
    assert response.json()["detail"] == "Group is full"

def test_join_group_allows_up_to_unit_max_group_size(client, auth_headers, create_unit):
    owner_headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    unit = create_unit(headers=owner_headers, name=TEST_UNIT_NAME, max_group_size=6)

    response = client.post("/groups/create", headers=owner_headers, json={"unit_id": unit["id"]})
    assert response.status_code == 200, response.text
    preference_code = response.json()["preference_code"]

    for i in range(5):
        headers = auth_headers(email=f"member{i}@test.com", password=TEST_USER_PASSWORD)
        _join_unit(client, headers, unit["code"])
        assert _join_group(client, headers, preference_code).status_code == 200, f"member {i} could not join"

    response = client.get(f"/groups/{unit['id']}", headers=owner_headers)
    assert response.status_code == 200
    assert len(response.json()[0]["members"]) == 6
