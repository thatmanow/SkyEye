"""安全核心：bcrypt 密码哈希、AES-GCM 敏感字段加密、JWT 签发校验、脱敏工具

合规要点：
- 用户密码仅存 bcrypt 哈希，任何接口不回传
- 手机号/邮箱等敏感字段以 AES-256-GCM 密文落库
- 个人查询结果强制脱敏，身份证号等字段永不存储、永不展示
"""
import base64
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from tyt.config import (
    AES_KEY_HEX, JWT_SECRET_KEY, JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_HOURS, REFRESH_TOKEN_EXPIRE_DAYS,
)

# ==================== 密码 ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except ValueError:
        return False


def check_password_strength(password: str) -> tuple[bool, str]:
    if not (8 <= len(password) <= 32):
        return False, "密码须 8-32 位"
    if not any(c.isdigit() for c in password):
        return False, "密码须包含数字"
    if not any(c.isalpha() for c in password):
        return False, "密码须包含字母"
    return True, ""


# ==================== AES-256-GCM 敏感字段加密 ====================

def _aes_key() -> bytes:
    return bytes.fromhex(AES_KEY_HEX)


def aes_encrypt(plaintext: str) -> str:
    """加密为 base64(nonce + ciphertext)，供数据库存储"""
    if plaintext is None or plaintext == "":
        return ""
    aes = AESGCM(_aes_key())
    nonce = hashlib.sha256(plaintext.encode()).digest()[:12]  # 确定性 nonce（演示用，防重复行）
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), b"tyt")
    return base64.b64encode(nonce + ct).decode("ascii")


def aes_decrypt(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    try:
        raw = base64.b64decode(ciphertext)
        aes = AESGCM(_aes_key())
        return aes.decrypt(raw[:12], raw[12:], b"tyt").decode("utf-8")
    except Exception:
        return ""


# ==================== JWT ====================

def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ==================== 脱敏（个人查询硬性红线） ====================

def mask_name(name: str) -> str:
    """姓名脱敏：张三 -> 张*；王小明 -> 王*明；欧阳靖云 -> 欧阳**云"""
    if not name:
        return ""
    if len(name) == 2:
        return name[0] + "*"
    if len(name) <= 4:
        return name[0] + "*" * (len(name) - 2) + name[-1]
    return name[:2] + "*" * (len(name) - 3) + name[-1]


def mask_phone(phone: str) -> str:
    """手机号脱敏：13812345678 -> 138****5678"""
    if not phone or len(phone) < 7:
        return ""
    return phone[:3] + "****" + phone[-4:]


def mask_court_no(case_no: str) -> str:
    """案号脱敏：保留法院与年份，隐去序号：(2023)京01民终12345号 -> (2023)京01民终****号"""
    if not case_no:
        return ""
    import re
    return re.sub(r"(?<=终)(\d+)(?=号)", "****", case_no)


def hash_ip(ip: str) -> str:
    """访客 IP 哈希（游客配额标识），不落明文"""
    return hmac.new(JWT_SECRET_KEY.encode(), ip.encode(), hashlib.sha256).hexdigest()[:16]
