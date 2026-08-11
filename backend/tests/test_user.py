from tests.conftest import (
    TEST_USER_EMAIL,
    TEST_USER_FNAME,
    TEST_USER_LNAME,
    TEST_USER_PASSWORD,
)

def test_get_me(client, auth_headers):
    headers = auth_headers()

    response = client.get("/users/me", headers=headers)

    assert response.status_code == 200

    response_body = response.json()
    assert response_body["first_name"] == TEST_USER_FNAME
    assert response_body["last_name"] == TEST_USER_LNAME
    assert response_body["email"] == TEST_USER_EMAIL

def test_get_me_unauthenticated(client):
    response = client.get("/users/me")
    assert response.status_code == 401

def test_patch_me(client, auth_headers):
    headers = auth_headers()

    first_name_patched  = TEST_USER_FNAME + " patched"
    last_name_patched   = TEST_USER_LNAME + " patched"
    request_body = {
        "first_name": first_name_patched,
        "last_name": last_name_patched
    }

    response_patch = client.patch("/users/me", headers=headers, json=request_body)
    assert response_patch.status_code == 200

    response_get = client.get("/users/me", headers=headers)
    assert response_get.status_code == 200

    response_body = response_get.json()
    assert response_body["first_name"] == first_name_patched
    assert response_body["last_name"] == last_name_patched
    assert response_body["email"] == TEST_USER_EMAIL


def test_patch_me_unauthenticated(client):
    first_name  = TEST_USER_FNAME + " patched"
    last_name   = TEST_USER_LNAME + " patched"
    request_body = {
        "first_name": first_name,
        "last_name": last_name
    }
    response = client.patch("/users/me", json=request_body)
    assert response.status_code == 401

def test_patch_me_empty_body(client, auth_headers):
    headers = auth_headers()
    request_body = {}

    response = client.patch("/users/me", headers=headers, json=request_body)
    assert response.status_code == 200

    response_body = response.json()
    assert response_body["first_name"] == TEST_USER_FNAME
    assert response_body["last_name"] == TEST_USER_LNAME
    assert response_body["email"] == TEST_USER_EMAIL

def test_patch_me_explicit_null(client,auth_headers):
    headers = auth_headers()
    request_body = {
        "first_name": None,
        "last_name": None
    }

    response = client.patch("/users/me", headers=headers, json=request_body)
    assert response.status_code == 200

    response_body = response.json()
    assert response_body["first_name"] == TEST_USER_FNAME
    assert response_body["last_name"] == TEST_USER_LNAME
    assert response_body["email"] == TEST_USER_EMAIL

def test_me_partial(client, auth_headers):
    headers = auth_headers()

    first_name  = TEST_USER_FNAME + " patched"

    request_body = {
        "first_name": first_name,
    }

    response = client.patch("/users/me", headers=headers, json=request_body)
    assert response.status_code == 200

    response_body = response.json()
    assert response_body["first_name"] == first_name
    assert response_body["last_name"] == TEST_USER_LNAME
    assert response_body["email"] == TEST_USER_EMAIL

def test_invalid_type(client,auth_headers):
    headers = auth_headers()
    request_body = {
        "first_name": 123,
        "last_name": TEST_USER_LNAME
    }

    response = client.patch("/users/me", headers=headers, json=request_body)
    assert response.status_code == 422