from src.constants import TIME_SLOT_ORDER
from tests.conftest import (
    TEST_UNIT_NAME,
    TEST_USER_EMAIL,
    TEST_USER_PASSWORD,
)

def test_get_time_slots_returns_the_master_list(client, auth_headers):
    headers = auth_headers()

    response = client.get("/time-slots", headers=headers)
    assert response.status_code == 200, response.text

    response_body = response.json()
    assert response_body == list(TIME_SLOT_ORDER)
    assert len(response_body) == 7 * 24
    assert response_body[0] == "monday00"
    assert response_body[-1] == "sunday23"

def test_get_time_slots_unauthenticated(client):
    response = client.get("/time-slots")
    assert response.status_code == 401, response.text

def test_time_slots_are_accepted_when_creating_a_unit(client, auth_headers, create_unit):
    headers = auth_headers(email=TEST_USER_EMAIL, password=TEST_USER_PASSWORD)

    response = client.get("/time-slots", headers=headers)
    assert response.status_code == 200, response.text
    chosen = response.json()[9:12]

    unit = create_unit(headers=headers, name=TEST_UNIT_NAME, time_slots=chosen)

    assert unit["time_slots"] == chosen
