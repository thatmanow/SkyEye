"""认证服务：注册 / 登录 / 刷新 / 登出（JWT + Redis 黑名单）"""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tyt.core.security import (
    aes_encrypt, aes_decrypt, check_password_strength,
    create_access_token, create_refresh_token, decode_token,
    hash_password, verify_password,
)
from tyt.db.redis_client import get_redis
from tyt.models import User, Notification

logger = logging.getLogger(__name__)

ACCESS_TTL = 24 * 3600          # 秒
REFRESH_TTL = 7 * 24 * 3600


def _is_phone(account: str) -> bool:
    return account.isdigit() and len(account) == 11


def register(db: Session, account: str, nickname: str, password: str) -> tuple[bool, str, dict | None]:
    ok, msg = check_password_strength(password)
    if not ok:
        return False, msg, None
    exists = db.execute(select(User).where(User.account == account)).scalar_one_or_none()
    if exists:
        return False, "该账号已注册", None

    user = User(
        account=account,
        nickname=nickname,
        password_hash=hash_password(password),
        role="user",
        phone_enc=aes_encrypt(account) if _is_phone(account) else None,
        email_enc=aes_encrypt(account) if not _is_phone(account) else None,
    )
    db.add(user)
    db.flush()
    db.add(Notification(
        user_id=user.id, type="system", title="欢迎注册天眼通",
        content="生活类帮您避坑，商业类助您尽调。所有数据来源公开合法、可溯源。",
    ))
    db.commit()
    return True, "注册成功", {"user_id": user.id}


def login(db: Session, account: str, password: str) -> tuple[bool, str, dict | None]:
    user = db.execute(select(User).where(User.account == account)).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return False, "账号或密码错误", None
    if user.status == "banned":
        return False, "该账号已被封禁，请联系平台管理员", None

    # 高级会员到期自动降级
    if user.role == "premium" and user.vip_expire_at and user.vip_expire_at < datetime.now():
        user.role = "user"

    user.last_login_at = datetime.now()
    db.commit()

    tokens = issue_tokens(user)
    return True, "登录成功", {
        **tokens,
        "role": user.role,
        "nickname": user.nickname,
        "user_id": user.id,
    }


def issue_tokens(user: User) -> dict:
    return {
        "access_token": create_access_token(user.id, user.role),
        "refresh_token": create_refresh_token(user.id, user.role),
        "token_type": "bearer",
    }


def refresh(db: Session, refresh_token: str) -> tuple[bool, str, dict | None]:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return False, "refresh_token 无效或已过期", None
    r = get_redis()
    if r is not None and r.exists(f"bl:{refresh_token}"):
        return False, "该凭证已吊销", None
    user = db.get(User, int(payload["sub"]))
    if not user or user.status == "banned":
        return False, "账号不可用", None
    return True, "刷新成功", {
        **issue_tokens(user),
        "role": user.role, "nickname": user.nickname, "user_id": user.id,
    }


def logout(token: str, refresh_token: str | None = None) -> bool:
    """JWT 黑名单吊销（Redis 不可用时静默失败——令牌自然过期兜底）"""
    r = get_redis()
    if r is None:
        return False
    try:
        if token:
            r.set(f"bl:{token}", "1", ex=ACCESS_TTL)
        if refresh_token:
            r.set(f"bl:{refresh_token}", "1", ex=REFRESH_TTL)
        return True
    except Exception as e:
        logger.warning("logout blacklist failed: %s", e)
        return False


def get_user_info(db: Session, user_id: int) -> dict | None:
    user = db.get(User, user_id)
    if not user:
        return None
    return {
        "id": user.id,
        "account": _mask_account(user.account),
        "nickname": user.nickname,
        "avatar": user.avatar,
        "role": user.role,
        "status": user.status,
        "vip_expire_at": user.vip_expire_at.strftime("%Y-%m-%d") if user.vip_expire_at else None,
        "created_at": user.created_at.strftime("%Y-%m-%d") if user.created_at else None,
        "phone": _mask_phone_acc(user.account) if _is_phone(user.account) else None,
        "email": _mask_email_acc(user.account) if not _is_phone(user.account) else None,
        "last_login_at": user.last_login_at.strftime("%Y-%m-%d %H:%M") if user.last_login_at else None,
    }


def _mask_account(account: str) -> str:
    if _is_phone(account):
        return account[:3] + "****" + account[-4:]
    if "@" in account:
        name, _, domain = account.partition("@")
        return (name[:2] + "***") + "@" + domain
    return account[:2] + "***"


def _mask_phone_acc(phone: str) -> str:
    return phone[:3] + "****" + phone[-4:]


def _mask_email_acc(email: str) -> str:
    name, _, domain = email.partition("@")
    return (name[:2] + "***@" + domain) if len(name) > 2 else email


def change_password(db: Session, user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    user = db.get(User, user_id)
    if not user or not verify_password(old_password, user.password_hash):
        return False, "原密码错误"
    ok, msg = check_password_strength(new_password)
    if not ok:
        return False, msg
    user.password_hash = hash_password(new_password)
    db.commit()
    return True, "密码修改成功"
