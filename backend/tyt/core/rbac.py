"""RBAC 权限核心：角色层级、能力矩阵、FastAPI 依赖

角色（5 级）：
guest < user < premium < enterprise_admin < platform_admin
权限分两层：
1. 能力（布尔）：是否可执行某类操作
2. 配额（每日次数，-1 不限）：通过 Redis 计数，见 services/quota_service.py
"""
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from tyt.config import QUOTA_MATRIX, ROLE_NAMES
from tyt.core.security import decode_token, hash_ip
from tyt.db.mysql import get_db
from tyt.db.redis_client import get_redis
from tyt.models import User

ROLE_LEVEL = {
    "guest": 0, "user": 1, "premium": 2,
    "enterprise_admin": 3, "platform_admin": 4,
}

# 能力矩阵：角色 -> 允许的权限点
CAPABILITY_MATRIX = {
    "guest": {"life.query", "biz.company.basic", "life.weather"},
    "user": {"life.query", "life.post", "biz.company.basic", "biz.risk", "biz.graph",
             "life.vision", "life.weather", "biz.stock", "ai.chat"},
    "premium": {"life.query", "life.post", "biz.company.basic", "biz.risk", "biz.graph",
                "biz.report", "biz.monitor", "ai.chat", "life.vision", "life.weather", "biz.stock"},
    "enterprise_admin": {"life.query", "life.post", "biz.company.basic", "biz.risk", "biz.graph",
                         "biz.report", "biz.monitor", "ai.chat", "biz.dashboard",
                         "life.vision", "life.weather", "biz.stock"},
    "platform_admin": {"life.query", "life.post", "biz.company.basic", "biz.risk", "biz.graph",
                       "biz.report", "biz.monitor", "ai.chat", "biz.dashboard",
                       "admin.audit", "admin.users", "admin.dataops", "admin.billing",
                       "admin.kb", "admin.models", "life.vision", "life.weather", "biz.stock"},
}

_bearer = HTTPBearer(auto_error=False)


class Principal:
    """请求主体：已登录用户或游客"""

    def __init__(self, user_id: int | None, role: str, nickname: str = "", ip_hash: str = ""):
        self.user_id = user_id          # 游客为 None
        self.role = role
        self.nickname = nickname
        self.ip_hash = ip_hash          # 游客配额标识
        self.is_authenticated = user_id is not None

    @property
    def quota_key(self) -> str:
        return f"u:{self.user_id}" if self.is_authenticated else f"g:{self.ip_hash}"

    def quota_limit(self, quota_type: str) -> int:
        return QUOTA_MATRIX.get(self.role, {}).get(quota_type, 0)

    def has_capability(self, perm: str) -> bool:
        return perm in CAPABILITY_MATRIX.get(self.role, set())

    def has_role_at_least(self, role: str) -> bool:
        return ROLE_LEVEL.get(self.role, -1) >= ROLE_LEVEL.get(role, 99)


def require_capability(perm: str):
    """能力校验依赖工厂：require_capability('biz.report')"""
    def checker(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_capability(perm):
            raise HTTPException(
                status_code=403,
                detail=f"当前角色（{ROLE_NAMES.get(principal.role, principal.role)}）无权执行该操作",
            )
        return principal
    return checker


def require_role(min_role: str):
    """角色下限依赖工厂：require_role('platform_admin')"""
    def checker(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_role_at_least(min_role):
            raise HTTPException(
                status_code=403,
                detail=f"需要 {ROLE_NAMES.get(min_role, min_role)} 及以上角色",
            )
        return principal
    return checker


def get_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Principal:
    """从请求解析主体（游客也可通过，role=guest）。

    角色以**数据库实时角色**为准（而非 JWT 中的 role 声明）：
    这样无论是自助订阅升级、后台管理员改角色、还是 Celery 到期自动降级，
    下一次请求即生效，无需用户重新登录。JWT 仅用于身份认证（sub）。
    """
    ip = request.client.host if request.client else "0.0.0.0"
    ip_hash = hash_ip(ip)

    if credentials is None:
        return Principal(None, "guest", ip_hash=ip_hash)

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return Principal(None, "guest", ip_hash=ip_hash)

    # Redis 黑名单（登出吊销）
    r = get_redis()
    if r is not None and r.exists(f"bl:{credentials.credentials}"):
        return Principal(None, "guest", ip_hash=ip_hash)

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError, TypeError):
        return Principal(None, "guest", ip_hash=ip_hash)

    role = get_live_role(db, user_id)
    if role is None:
        # 用户记录不存在：视作游客
        return Principal(None, "guest", ip_hash=ip_hash)
    return Principal(user_id, role, ip_hash=ip_hash)


_ROLE_CACHE_TTL = 15  # 秒；角色变更通过 invalidate_role_cache 立即失效


def _role_cache_key(user_id: int) -> str:
    return f"role:{user_id}"


def get_live_role(db: Session, user_id: int) -> str | None:
    """返回用户实时角色（DB 为准，Redis 短缓存降低查询压力）。

    返回 None 表示用户不存在。
    """
    r = get_redis()
    key = _role_cache_key(user_id)
    if r is not None:
        try:
            cached = r.get(key)
            if cached is not None:
                # Redis 客户端已配置 decode_responses=True，返回即为 str
                return cached
        except Exception:
            pass
    user = db.get(User, user_id)
    if user is None:
        return None
    role = user.role
    if r is not None:
        try:
            r.set(key, role, ex=_ROLE_CACHE_TTL)
        except Exception:
            pass
    return role


def invalidate_role_cache(user_id: int) -> None:
    """角色/状态变更后立即使缓存失效，确保下一次请求即时读取新角色。"""
    r = get_redis()
    if r is None:
        return
    try:
        r.delete(_role_cache_key(user_id))
    except Exception:
        pass


def get_current_user(principal: Principal = Depends(get_principal)) -> Principal:
    """强制登录依赖"""
    if not principal.is_authenticated:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return principal
