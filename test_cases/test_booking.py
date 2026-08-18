"""
第一批测试用例：覆盖登录、创建、查询这个最基础的链路
"""
from utils import http_client
import pytest
from config.settings import BASE_URL

"""
case1：测试登录接口能正常返回token
测试登录接口能正常返回token
这里直接用auth_token这个fixture作为参数，pytest会自动帮我们执行登录逻辑
"""
@pytest.mark.smoke
def test_auth_returns_token(auth_token):
    assert isinstance(auth_token, str)
    assert len(auth_token) > 0

"""
case2：测试创建预订接口能正常返回booking_id
"""
@pytest.mark.smoke
def test_create_booking(created_booking):
    booking_id = created_booking["booking_id"]
    payload = created_booking["payload"]

    # booking_id应该是个整数
    assert isinstance(booking_id, int)

    # 用这个id去查询，验证数据确实存进去了，且字段值一致
    response = http_client.get(f"/booking/{booking_id}")
    assert response.status_code == 200

    booking_data = response.json()
    assert booking_data["firstname"] == payload["firstname"]
    assert booking_data["totalprice"] == payload["totalprice"]

# case3：更新预订，测试带token
def test_update_booking(created_booking, updated_booking, auth_token):
    booking_id = created_booking["booking_id"]
    payload = updated_booking["payload"]
    headers = {
        "Cookie": f"token={auth_token}"
    }
    
    # booking_id应该是个整数
    assert isinstance(booking_id, int)
    
    response = http_client.put(f"/booking/{booking_id}", json=payload, headers=headers)
    assert response.status_code == 200

    # 用这个id去查询，验证数据确实更新了，且字段值一致
    booking_data = response.json()
    print("更新断言：", booking_data["lastname"])
    assert booking_data["firstname"] == payload["firstname"]
    assert booking_data["totalprice"] == payload["totalprice"]    
    assert booking_data["lastname"] == payload["lastname"]

# case4：更新预订，测试不带token
def test_update_without_token_should_fail(created_booking, updated_booking):
    booking_id = created_booking["booking_id"]
    payload = updated_booking["payload"]

    response = http_client.put(
        f"/booking/{booking_id}", 
        json={"firstname": "Hacker", "lastname": "Test",
              "totalprice": 1, "depositpaid": False,
              "bookingdates": {"checkin": "2026-01-01", "checkout": "2026-01-02"}
             }
        # 注意：没有加 headers 里的 Cookie/token
        )
    # 期望被拒绝，不是200
    assert response.status_code == 403

# case5: 删除预订接口，测试不带token
def test_delete_without_token_should_fail(created_booking):
    booking_id = created_booking["booking_id"]
    response = http_client.delete(f"/booking/{booking_id}")
    # 期望被拒绝，不是201
    assert response.status_code == 403

# case6：删除预订接口，测试带token
def test_delete_booking(created_booking, auth_token):
    booking_id = created_booking["booking_id"]
    headers = {
        "Cookie": f"token={auth_token}"
    }
    
    # booking_id应该是个整数
    assert isinstance(booking_id, int)
    
    response = http_client.delete(f"/booking/{booking_id}", headers=headers)
    print("删除断言：", response)
    assert response.status_code == 201

"""
case7：测试查询不存在的预订接口返回404
边界测试：查询一个不存在的booking_id，应该返回404，"故意测错误场景"的用例
"""
def test_get_nonexistent_booking_returns_404():
    response = http_client.get(f"/booking/999999999")
    assert response.status_code == 404

# case8: 同一个逻辑跑三组不同的数据，pytest的参数化功能
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
    response = http_client.post(f"/booking", json = payload)
    assert response.status_code == 200, f"创建预订失败：{response.text}"
    assert response.json()["booking"]["totalprice"] == totalprice

# case9:补充边界case（必填字段缺失、错误数据类型）
# 每一项结构：(case_name, payload, expected_status, check_fn)
# check_fn 接收response，返回True/False，用来校验响应体里的具体细节
INVALID_DATA_CASES = [
    (
        {"lastname": "Test", "totalprice": 100, "depositpaid": True,
         "bookingdates": {"checkin": "2026-08-20", "checkout": "2026-08-25"}},
        500,
        None
    ),
    (
        {"firstname": "Wang", "lastname": "Test", "totalprice": "一百",
         "depositpaid": True,
         "bookingdates": {"checkin": "2026-08-20", "checkout": "2026-08-25"}},
        200,
        lambda r: r.json()["booking"]["totalprice"] is None
    ),
    (
        {"firstname": "Wang", "lastname": "Test", "totalprice": 100,
         "depositpaid": True,
         "bookingdates": {"checkin": "2026-13-99", "checkout": "2026-08-25"}},
        200,
        lambda r: "NaN" in r.json()["booking"]["bookingdates"]["checkin"]
    ),
]

# 单独维护一份用例名称列表，跟上面的元组一一对应，避免用索引去猜
INVALID_DATA_CASE_IDS = [
    "缺少firstname字段",
    "totalprice类型错误",
    "checkin日期格式非法",
]

@pytest.mark.parametrize(
    "payload,expected_status,check_fn",
    INVALID_DATA_CASES,
    ids=INVALID_DATA_CASE_IDS
)

@pytest.mark.regression
def test_create_booking_with_invalid_data(payload, expected_status, check_fn):
    """
    已知缺陷记录：接口对不合法输入没有做校验，
    要么服务端直接报错(500)，要么静默把脏数据写入后仍返回200。
    """
    response = http_client.post(f"/booking", json=payload)

    assert response.status_code == expected_status, (
        f"预期状态码{expected_status}，实际{response.status_code}，"
        f"可能是接口行为发生了变化"
    )

    if check_fn is not None:
        assert check_fn(response), f"响应体细节校验失败，实际返回：{response.text}"