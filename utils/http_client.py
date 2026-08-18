"""
http_client.py

统一封装HTTP请求，替代直接调用requests。
好处：
1. 不用每个用例都手写完整URL（BASE_URL在这里统一拼接）
2. 每次请求自动记录日志，排查失败用例时能看到完整的请求/响应细节
3. 以后要统一加header、改超时时间，只需要改这一个文件
"""
import logging
import json
import requests
from config.settings import BASE_URL
import os

os.makedirs("reports", exist_ok=True)  # 加在logging.basicConfig之前

# 配置日志：同时写入文件和打印到终端
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("reports/api_test.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("api_test")


def _log_request(method, url, kwargs):
    """记录请求发出前的完整信息"""
    logger.info(f"→ 请求: {method} {url}")
    if "json" in kwargs:
        logger.info(f"  请求体: {json.dumps(kwargs['json'], ensure_ascii=False)}")
    if "headers" in kwargs:
        logger.info(f"  请求头: {kwargs['headers']}")


def _log_response(response):
    """记录响应返回后的完整信息"""
    logger.info(f"← 响应: {response.status_code}")
    logger.info(f"  响应体: {response.text[:500]}")  # 只记前500字符，避免日志过长


def _request(method, path, **kwargs):
    """
    所有请求的统一入口。
    path是相对路径（比如"/booking/123"），这里自动拼接BASE_URL，
    调用方不用再自己写f"{BASE_URL}/booking/123"这种拼接逻辑
    """
    url = f"{BASE_URL}{path}"
    _log_request(method, url, kwargs)

    response = requests.request(method, url, **kwargs)

    _log_response(response)
    return response


# 对外暴露的四个方法，业务代码只需要用这几个，不用直接接触requests
def get(path, **kwargs):
    return _request("GET", path, **kwargs)


def post(path, **kwargs):
    return _request("POST", path, **kwargs)


def put(path, **kwargs):
    return _request("PUT", path, **kwargs)


def delete(path, **kwargs):
    return _request("DELETE", path, **kwargs)