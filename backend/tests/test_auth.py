TEST_USER_FNAME = "Test"
TEST_USER_LNAME = "User"
TEST_USER_EMAIL = "user@test.com"
TEST_USER_PASSWORD = "Password123"

def test_register_creates_user(client):
    response = client.post("/auth/register", json={
        "first_name": TEST_USER_FNAME,
        "last_name": TEST_USER_LNAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    })

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == TEST_USER_EMAIL
    assert body["group_id"] is None
    assert body["units"] == []

def test_register_login(client, make_user):
    make_user(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    response = client.post("/auth/login", json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"