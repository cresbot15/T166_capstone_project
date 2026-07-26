TEST_USER_FNAME = "Test"
TEST_USER_LNAME = "User"
TEST_USER_EMAIL = "user@test.com"
TEST_USER_PASSWORD = "Password123"
TEST_UNIT_CODE = "unit_code"
TEST_UNIT_NAME = "unit_name"

def test_create_unit(client, auth_headers):
    headers = auth_headers()

    request_body = {
        "name": TEST_UNIT_NAME,
        "code": TEST_UNIT_CODE
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 201

    response_body = response.json()

    assert response_body["code"] == TEST_UNIT_CODE
    assert response_body["name"] == TEST_UNIT_NAME

def test_create_duplicate_unit(client, auth_headers, create_unit):
    headers = auth_headers()

    create_unit(headers=headers, code=TEST_UNIT_CODE, name=TEST_UNIT_NAME)

    request_body = {
        "name": TEST_UNIT_NAME,
        "code": TEST_UNIT_CODE
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 409
    assert response.json()["detail"] == "Unit code already exists"
    