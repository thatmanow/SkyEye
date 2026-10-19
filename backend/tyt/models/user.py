"""用户与审计模型"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from tyt.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="账号（手机号或邮箱明文唯一索引；手机/邮箱另有密文列）")
    nickname: Mapped[str] = mapped_column(String(64), nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), comment="头像 URL（/uploads/avatars/xxx）")
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False, comment="bcrypt")
    role: Mapped[str] = mapped_column(
        Enum("user", "premium", "enterprise_admin", "platform_admin", name="role_enum"),
        default="user", nullable=False)
    phone_enc: Mapped[Optional[str]] = mapped_column(String(256), comment="手机号 AES-GCM 密文")
    email_enc: Mapped[Optional[str]] = mapped_column(String(256), comment="邮箱 AES-GCM 密文")
    status: Mapped[str] = mapped_column(
        Enum("normal", "banned", name="user_status_enum"), default="normal", nullable=False)
    vip_expire_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="高级会员到期时间")
    auto_renew: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="0",
        comment="连续包月自动续费开关")
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_login_ip_hash: Mapped[Optional[str]] = mapped_column(String(32), comment="登录 IP 哈希（不留明文）")

    def is_vip_active(self) -> bool:
        if self.role in ("premium", "enterprise_admin", "platform_admin"):
            return True
        return self.vip_expire_at is not None and self.vip_expire_at > datetime.now()


class AuditLog(Base):
    """操作审计日志（留存 >= 180 天，支持审计追溯）"""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True)
    role: Mapped[Optional[str]] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(64), nullable=False, comment="如 biz.graph.expand / admin.audit.approve")
    resource: Mapped[Optional[str]] = mapped_column(String(128), comment="操作对象，如 company:12")
    detail: Mapped[Optional[str]] = mapped_column(Text, comment="参数摘要 JSON")
    ip_hash: Mapped[Optional[str]] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "role": self.role,
            "action": self.action, "resource": self.resource,
            "detail": self.detail, "ip_hash": self.ip_hash,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
