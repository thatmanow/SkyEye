"""Redis 7 客户端（缓存 / 配额计数 / JWT 黑名单 / Celery Broker）

Redis 不可用时配额降级为 MySQL 计数（quota_service 内部处理），缓存直接穿透。
"""
import logging
from typing import Optional

import redis as redis_py

from tyt.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB

logger = logging.getLogger(__name__)

_client: Optional[redis_py.Redis] = None


def get_redis() -> Optional[redis_py.Redis]:
    global _client
    if _client is not None:
        return _client
    try:
        _client = redis_py.Redis(
            host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD or None,
            db=REDIS_DB, decode_responses=True, socket_connect_timeout=2, socket_timeout=2,
        )
        _client.ping()
        logger.info("Redis connected: %s:%s/%s", REDIS_HOST, REDIS_PORT, REDIS_DB)
    except Exception as e:
        logger.warning("Redis unavailable, quota/cache degraded: %s", e)
        _client = None
    return _client
