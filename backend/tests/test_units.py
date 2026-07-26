TEST_USER_FNAME = "Test"
TEST_USER_LNAME = "User"
TEST_USER_EMAIL = "user@test.com"
TEST_USER_PASSWORD = "Password123"
TEST_UNIT_CODE = "unit_code"
TEST_UNIT_NAME = "unit_name"

def test_create_unit(client, auth_headers):
    headers = auth_headers(email=TEST_USER_EMAIL, password = TEST_USER_PASSWORD)

    request_body = {
        "name": TEST_UNIT_NAME,
        "code": TEST_UNIT_CODE
    }

    response = client.post("/units/create", headers=headers, json=request_body)
    assert response.status_code == 201

    response_body = response.json()

    assert response_body["code"] == TEST_UNIT_CODE
    assert response_body["name"] == TEST_UNIT_NAME