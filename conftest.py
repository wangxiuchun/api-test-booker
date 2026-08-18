"""
conftest.py

pytest会自动读取这个文件，里面的fixture可以被任何test_*.py文件直接使用，
不需要手动import。
"""
import pytest
from utils import http_client
from config.settings import BASE_URL, AUTH_USERNAME, AUTH_PASSWORD

@pytest.fixture(scope="session")
def auth_token():
    response = http_client.post(
        "/auth",
        json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD}
    )
    assert response.status_code == 200, f"登录失败：{response.text}"
    token = response.json()["token"]
    return token

# 创建预订
@pytest.fixture
def created_booking():
    payload = {
        "firstname": "Wang",
        "lastname": "Test",
        "totalprice": 150,
        "depositpaid": True,
        "bookingdates": {
            "checkin": "2026-08-20",
            "checkout": "2026-08-25"
        },
        "additionalneeds": "Breakfast"
    }
    response = http_client.post(f"/booking", json=payload)
    assert response.status_code == 200, f"创建预订失败：{response.text}"

    booking_id = response.json()["bookingid"]
    return {"booking_id": booking_id, "payload": payload}

# 更新
@pytest.fixture
def updated_booking():
    payload = {
        "firstname": "Wang",
        "lastname": "Test—Updated",
        "totalprice": 150,
        "depositpaid": True,
        "bookingdates": {
            "checkin": "2026-08-20",
            "checkout": "2026-08-25"
        },
        "additionalneeds": "Breakfast"
    }
    response = http_client.get(f"/booking", json=payload)
    assert response.status_code == 200, f"查询预订失败：{response.text}"

    return {"payload": payload}
