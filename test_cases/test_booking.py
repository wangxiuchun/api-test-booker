"""
第一批测试用例：覆盖登录、创建、查询这个最基础的链路
"""
import requests
from config.settings import BASE_URL

"""
case1：测试登录接口能正常返回token
测试登录接口能正常返回token
这里直接用auth_token这个fixture作为参数，pytest会自动帮我们执行登录逻辑
"""
# 工程化pytest.ini中可选[smoke, regression]，用来标记用例类型，方便后续按类型执行
# 冒烟执行：pytest -m smoke --html=reports/smoke_report.html --self-contained-html
# @pytest.mark.smoke   
def test_auth_returns_token(auth_token):
    assert isinstance(auth_token, str)
    assert len(auth_token) > 0

"""
case2：测试创建预订接口能正常返回booking_id
测试创建预订接口：验证返回的数据和我们提交的数据一致
"""
def test_create_booking(created_booking):
    booking_id = created_booking["booking_id"]
    payload = created_booking["payload"]

    # booking_id应该是个整数
    assert isinstance(booking_id, int)

    # 用这个id去查询，验证数据确实存进去了，且字段值一致
    response = requests.get(f"{BASE_URL}/booking/{booking_id}")
    assert response.status_code == 200

    booking_data = response.json()
    assert booking_data["firstname"] == payload["firstname"]
    assert booking_data["totalprice"] == payload["totalprice"]

# case3：测试带token更新预订接口能正常更新
# 更新新创建预订接口：验证返回的数据和我们提交的数据一致
def test_update_booking(created_booking, updated_booking, auth_token):
    booking_id = created_booking["booking_id"]
    payload = updated_booking["payload"]
    headers = {
        "Cookie": f"token={auth_token}"
    }
    
    # booking_id应该是个整数
    assert isinstance(booking_id, int)
    
    response = requests.put(f"{BASE_URL}/booking/{booking_id}", json=payload, headers=headers)
    assert response.status_code == 200

    # 用这个id去查询，验证数据确实更新了，且字段值一致
    booking_data = response.json()
    print("更新断言：", booking_data["lastname"])
    assert booking_data["firstname"] == payload["firstname"]
    assert booking_data["totalprice"] == payload["totalprice"]    
    assert booking_data["lastname"] == payload["lastname"]

# case4：测试不带token更新预订
def test_update_without_token_should_fail(created_booking, updated_booking):
    booking_id = created_booking["booking_id"]
    payload = updated_booking["payload"]

    response = requests.put(
        f"{BASE_URL}/booking/{booking_id}", 
        json={"firstname": "Hacker", "lastname": "Test",
              "totalprice": 1, "depositpaid": False,
              "bookingdates": {"checkin": "2026-01-01", "checkout": "2026-01-02"}}
        # 注意：没有加 headers 里的 Cookie/token
        )
    # 期望被拒绝，不是200
    assert response.status_code == 403

# case5: 测试不带token删除预订接口
def test_delete_without_token_should_fail(created_booking):
    booking_id = created_booking["booking_id"]
    response = requests.delete(f"{BASE_URL}/booking/{booking_id}")
    # 期望被拒绝，不是201
    assert response.status_code == 403

# case6：测试带token删除预订接口能正常删除
# 删除新创建预订接口：验证返回的数据和我们提交的数据一致
def test_delete_booking(created_booking, auth_token):
    booking_id = created_booking["booking_id"]
    headers = {
        "Cookie": f"token={auth_token}"
    }
    
    # booking_id应该是个整数
    assert isinstance(booking_id, int)
    
    response = requests.delete(f"{BASE_URL}/booking/{booking_id}", headers=headers)
    print("删除断言：", response)
    assert response.status_code == 201

"""
case7：测试查询不存在的预订接口返回404
边界测试：查询一个不存在的booking_id，应该返回404
这种"故意测错误场景"的用例，在真实测试岗位里权重很高
"""
def test_get_nonexistent_booking_returns_404():
    response = requests.get(f"{BASE_URL}/booking/999999999")
    assert response.status_code == 404

# case8: 同一个逻辑跑三组不同的数据，pytest的参数化功能
import pytest
@pytest.mark.parametrize("totalprice,depositpaid", [
    (100, True),
    (0, False),
    (9999, True)
])
def test_create_booking_with_various_prices(totalprice, depositpaid):
    payload = {
        "firstname": "Wang",
        "lastname": "Test",
        "totalprice": totalprice,
        "depositpaid": depositpaid,
        "bookingdates": {
            "checkin": "2026-08-20",
            "checkout": "2026-08-25"
        },
        "additionalneeds": "Breakfast"
    }
    response = requests.post(f"{BASE_URL}/booking", json = payload)
    assert response.status_code == 200, f"创建预订失败：{response.text}"
    assert response.json()["booking"]["totalprice"] == totalprice