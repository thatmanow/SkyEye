"""数据治理模型：数据源登记、采集日志（合规溯源与审计）"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from tyt.models.base import Base


class DataSource(Base):
    """数据源登记表：所有入库数据必须可溯源到此处登记的合法来源"""
    __tablename__ = "data_sources"
    __table_args__ = (UniqueConstraint("code", name="uq_source_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), comment="official_web/official_sdk/ugc/seed/third_party_api")
    url: Mapped[Optional[str]] = mapped_column(String(512))
    license_note: Mapped[Optional[str]] = mapped_column(Text, comment="合法性说明")
    enabled: Mapped[bool] = mapped_column(default=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id, "code": self.code, "name": self.name, "type": self.type,
            "url": self.url, "license_note": self.license_note, "enabled": self.enabled,
            "last_synced_at": self.last_synced_at.strftime("%Y-%m-%d %H:%M:%S") if self.last_synced_at else None,
        }


class CollectLog(Base):
    """采集/导入日志：合规审计要求留存"""
    __tablename__ = "collect_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_code: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    task_type: Mapped[str] = mapped_column(String(32), comment="import/crawl/sdk/sync")
    params: Mapped[Optional[str]] = mapped_column(Text, comment="任务参数 JSON")
    status: Mapped[str] = mapped_column(String(16), default="success", comment="success/failed")
    records: Mapped[int] = mapped_column(default=0, comment="本次处理记录数")
    message: Mapped[Optional[str]] = mapped_column(Text)
    operator_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="操作管理员（人工导入时）")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def to_dict(self):
        return {
            "id": self.id, "source_code": self.source_code, "task_type": self.task_type,
            "params": self.params, "status": self.status, "records": self.records,
            "message": self.message,
            "started_at": self.started_at.strftime("%Y-%m-%d %H:%M:%S") if self.started_at else None,
            "finished_at": self.finished_at.strftime("%Y-%m-%d %H:%M:%S") if self.finished_at else None,
        }


class ViolationWord(Base):
    """内容审核违规标准词库：管理员可维护，加载待审内容时自动识别命中"""
    __tablename__ = "violation_words"
    __table_args__ = (UniqueConstraint("word", name="uq_violation_word"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="通用",
                                         server_default="通用", comment="词分类（第一版分类体系）")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
