"""系统设置模型：平台级键值配置（如模型开关），管理员可在后台动态修改"""
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from tyt.models.base import Base


class SystemSetting(Base):
    """键值型系统设置（值统一存字符串，由使用方解析）"""
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[str] = mapped_column(String(255), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (UniqueConstraint("key", name="uq_system_settings_key"),)

    def __repr__(self) -> str:
        return f"<SystemSetting {self.key}={self.value}>"
