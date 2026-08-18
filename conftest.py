"""
conftest.py

pytest会自动读取这个文件，里面的fixture可以被任何test_*.py文件直接使用，
不需要手动import。

今天定义两个fixture：
1. auth_token：登录一次，拿到token，后续需要鉴权的接口（更新/删除）都要用
2. created_booking：创建一条预订数据，返回它的booking_id，方便后面的用例直接用
   （避免每个用例都要重新创建一遍数据）
"""
import pytest
import requests
from config.settings import BASE_URL, AUTH_USERNAME, AUTH_PASSWORD

@pytest.fixture(scope="session")
def auth_token():
    """
    登录拿token，scope="session"意味着整个测试运行期间只登录一次，
    所有用例共用这个token，不用每个用例都重新登录（省时间也更真实）
    """
    response = requests.post(
        f"{BASE_URL}/auth",
        json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD}
    )
    assert response.status_code == 200, f"登录失败：{response.text}"
    token = response.json()["token"]
    return token


@pytest.fixture
def created_booking():
    """
    每个用例调用这个fixture时，会先创建一条新的预订数据，
    返回booking_id和创建时用的原始数据，方便后面用例对比字段是否一致。

    注意这里没有scope="session"，意味着每个用例调用它都会重新创建一条，
    互不干扰（避免用例之间因为共用数据而互相影响，这是接口测试的重要原则）
    """
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
    response = requests.post(f"{BASE_URL}/booking", json=payload)
    assert response.status_code == 200, f"创建预订失败：{response.text}"

    booking_id = response.json()["bookingid"]
    return {"booking_id": booking_id, "payload": payload}

# 更新
@pytest.fixture
def updated_booking():
    """
    每个用例调用这个fixture时，会先创建一条新的预订数据，更新它，
    返回booking_id和更新后的数据，方便后面用例对比字段是否一致。

    注意这里没有scope="session"，意味着每个用例调用它都会重新创建一条，
    互不干扰（避免用例之间因为共用数据而互相影响，这是接口测试的重要原则）
    """
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
    response = requests.get(f"{BASE_URL}/booking", json=payload)
    assert response.status_code == 200, f"查询预订失败：{response.text}"

    return {"payload": payload}
