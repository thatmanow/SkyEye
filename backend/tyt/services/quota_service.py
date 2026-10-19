"""配额服务：Redis 计数（每日），Redis 不可用时降级 MySQL 累计

规则：-1 不限次；0 无权限；>0 每日限次
键格式：quota:{type}:{principal.quota_key}:{yyyymmdd}，自然日过期
"""
import logging
from datetime import date

from sqlalchemy import text

from tyt.core.rbac import Principal
from tyt.db.mysql import engine
from tyt.db.redis_client import get_redis

logger = logging.getLogger(__name__)


def _quota_key(quota_type: str, principal: Principal) -> str:
    return f"quota:{quota_type}:{principal.quota_key}:{date.today().strftime('%Y%m%d')}"


def check_and_consume(quota_type: str, principal: Principal, consume: int = 1) -> tuple[bool, int, int]:
    """返回 (是否允许, 已用次数, 限额)。限额 -1 表示不限。"""
    limit = principal.quota_limit(quota_type)
    if limit == -1:
        return True, 0, -1
    if limit == 0:
        return False, 0, 0

    r = get_redis()
    if r is not None:
        try:
            key = _quota_key(quota_type, principal)
            pipe = r.pipeline()
            pipe.incrby(key, consume)
            pipe.expire(key, 90000)  # 25h，覆盖自然日滚动
            used, _ = pipe.execute()
            used = int(used)
            if used > limit:
                return False, used - consume, limit
            return True, used, limit
        except Exception as e:
            logger.warning("Redis quota failed, fallback MySQL: %s", e)

    # MySQL 降级路径：quota_usage 表不存在时直接放行并告警（避免阻断业务）
    try:
        today = date.today().isoformat()
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS quota_usage (
                    id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    quota_key VARCHAR(64) NOT NULL,
                    quota_type VARCHAR(32) NOT NULL,
                    used_count INT NOT NULL DEFAULT 0,
                    usage_date DATE NOT NULL,
                    UNIQUE KEY uq_quota (quota_key, quota_type, usage_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            conn.execute(text("""
                INSERT INTO quota_usage (quota_key, quota_type, used_count, usage_date)
                VALUES (:k, :t, :n, :d)
                ON DUPLICATE KEY UPDATE used_count = used_count + :n
            """), {"k": principal.quota_key, "t": quota_type, "n": consume, "d": today})
            row = conn.execute(text("""
                SELECT used_count FROM quota_usage
                WHERE quota_key=:k AND quota_type=:t AND usage_date=:d
            """), {"k": principal.quota_key, "t": quota_type, "d": today}).fetchone()
            used = row[0] if row else 0
            if used > limit:
                return False, used - consume, limit
            return True, used, limit
    except Exception as e:
        logger.error("quota fallback failed, allowing request: %s", e)
        return True, 0, limit


def get_usage(quota_type: str, principal: Principal) -> dict:
    """查询当前已用/限额（不消耗）"""
    limit = principal.quota_limit(quota_type)
    if limit == -1:
        return {"limit": -1, "used": 0, "remaining": -1}
    if limit == 0:
        return {"limit": 0, "used": 0, "remaining": 0}
    r = get_redis()
    if r is not None:
        try:
            used = int(r.get(_quota_key(quota_type, principal)) or 0)
            return {"limit": limit, "used": used, "remaining": max(0, limit - used)}
        except Exception:
            pass
    return {"limit": limit, "used": 0, "remaining": limit}
