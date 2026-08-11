from tests.conftest import (
    TEST_USER_EMAIL,
    TEST_USER_FNAME,
    TEST_USER_LNAME,
    TEST_USER_PASSWORD,
)

def test_register_creates_user(client):
    response = client.post("/auth/register", json={
        "first_name": TEST_USER_FNAME,
        "last_name": TEST_USER_LNAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    })

    assert response.status_code == 200
    response_body = response.json()
    assert response_body["email"] == TEST_USER_EMAIL

def test_register_login(client, make_user):
    make_user(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    request_body = {
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }

    response = client.post("/auth/login", json=request_body)

    assert response.status_code == 200
    response_body = response.json()
    assert "access_token" in response_body
    assert response_body["token_type"] == "bearer"

def test_register_login_wrong_email(client, make_user):
    make_user(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    request_body = {
        "email": "wrong@email.com",
        "password": TEST_USER_PASSWORD
    }
    
    response = client.post("/auth/login", json=request_body)

    assert response.status_code == 401
    # Login endpoint should not distinguish between incorrect username or password
    assert response.json()["detail"] == "Invalid login details"

def test_register_login_wrong_password(client, make_user):
    make_user(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    request_body = {
        "email": TEST_USER_EMAIL,
        "password": "wrong_password"
    }
    
    response = client.post("/auth/login", json=request_body)

    assert response.status_code == 401
    # Login endpoint should not distinguish between incorrect username or password
    assert response.json()["detail"] == "Invalid login details"

# Explicitly test that JWT works
def test_protected_endpoint_valid_login(client, auth_headers):
    headers = auth_headers(TEST_USER_EMAIL, TEST_USER_PASSWORD)

    response = client.get("/users/me", headers=headers)

    assert response.status_code == 200

def test_protected_endpoint_no_login(client):
    response = client.get("/users/me", headers={})

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"