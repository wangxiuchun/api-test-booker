"""
http_client.py
"""
import os
import logging
import json
import requests
from config.settings import BASE_URL
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

os.makedirs("reports", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("reports/api_test.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("api_test")

# 用Session复用连接，减少并发场景下重复建立TCP连接对本地网络环境（如VPN）造成的压力
_session = requests.Session()
# 配置自动重试：遇到连接失败，最多重试3次，每次间隔递增（避免瞬时冲击）
_retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,  # 重试间隔：0.5秒、1秒、2秒，逐渐拉长
    status_forcelist=[500, 502, 503, 504],  # 服务端错误也一并重试
)
_adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=_retry_strategy)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)


def _log_request(method, url, kwargs):
    logger.info(f"→ 请求: {method} {url}")
    if "json" in kwargs:
        logger.info(f"  请求体: {json.dumps(kwargs['json'], ensure_ascii=False)}")
    if "headers" in kwargs:
        logger.info(f"  请求头: {kwargs['headers']}")


def _log_response(response):
    logger.info(f"← 响应: {response.status_code}")
    logger.info(f"  响应体: {response.text[:500]}")


def _request(method, path, **kwargs):
    url = f"{BASE_URL}{path}"
    _log_request(method, url, kwargs)

    response = _session.request(method, url, **kwargs)  # 改成用session

    _log_response(response)
    return response


def get(path, **kwargs):
    return _request("GET", path, **kwargs)


def post(path, **kwargs):
    return _request("POST", path, **kwargs)


def put(path, **kwargs):
    return _request("PUT", path, **kwargs)


def delete(path, **kwargs):
    return _request("DELETE", path, **kwargs)