from tests.conftest import (
    TEST_UNIT_NAME,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
)

def test_create_unit(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password = TEST_USER_PASSWORD)

    request_body = {
        "name": TEST_UNIT_NAME
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 201

    response_body = response.json()

    assert isinstance(response_body["code"], str) and len(response_body["code"]) == 12
    assert response_body["name"] == TEST_UNIT_NAME

def test_create_unit_codes_are_unique(client, auth_headers, create_unit):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    first = create_unit(headers=headers, name=TEST_UNIT_NAME)
    second = create_unit(headers=headers, name=TEST_UNIT_NAME)

    assert first["code"] != second["code"]

def test_list_units_does_not_expose_code(client, auth_headers, create_unit):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)
    create_unit(headers=headers, name=TEST_UNIT_NAME)

    response = client.get("/units/", headers=headers)
    assert response.status_code == 200

    response_body = response.json()
    assert len(response_body) == 1
    assert "code" not in response_body[0]
    assert response_body[0]["name"] == TEST_UNIT_NAME
