"""商业类模型：监控、通知、报告任务、商机线索"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Date, DateTime, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from tyt.models.base import Base, TimestampMixin


class WatchItem(Base, TimestampMixin):
    """商业监控：关注企业"""
    __tablename__ = "watch_items"
    __table_args__ = (UniqueConstraint("user_id", "company_id", name="uq_watch"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True)


class WatchEvent(Base):
    """监控事件（由 company_changes / risk_records 新增触发，Celery 扫描生成）"""
    __tablename__ = "watch_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(256))
    event_type: Mapped[str] = mapped_column(String(32), comment="change/risk")
    event_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment="关联 company_changes/risk_records 的 id")
    title: Mapped[str] = mapped_column(String(512))
    detail: Mapped[Optional[str]] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(8), default="info", comment="info/low/medium/high")
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id, "company_id": self.company_id, "company_name": self.company_name,
            "event_type": self.event_type, "title": self.title, "detail": self.detail,
            "risk_level": self.risk_level,
            "occurred_at": self.occurred_at.strftime("%Y-%m-%d %H:%M") if self.occurred_at else None,
        }


class Notification(Base):
    """站内通知（监控提醒 / 报告完成 / 审核结果）"""
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    type: Mapped[str] = mapped_column(String(32), default="monitor", comment="monitor/report/audit/system")
    title: Mapped[str] = mapped_column(String(256))
    content: Mapped[Optional[str]] = mapped_column(Text)
    ref_url: Mapped[Optional[str]] = mapped_column(String(256))
    is_read: Mapped[bool] = mapped_column(default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id, "type": self.type, "title": self.title,
            "content": self.content, "ref_url": self.ref_url, "is_read": self.is_read,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }


class MonitorSchedule(Base, TimestampMixin):
    """定制日报/周报订阅"""
    __tablename__ = "monitor_schedules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    freq: Mapped[str] = mapped_column(String(16), default="daily", comment="daily/weekly")
    scope: Mapped[str] = mapped_column(String(16), default="watched", comment="watched=关注企业/all=全部监控")
    enabled: Mapped[bool] = mapped_column(default=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class ReportTask(Base):
    """尽调报告生成任务（Celery 异步）"""
    __tablename__ = "report_tasks"

    id: Mapped[str] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    company_name: Mapped[str] = mapped_column(String(256))
    template: Mapped[str] = mapped_column(String(16), default="standard", comment="standard/deep")
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True, comment="queued/running/done/failed")
    progress: Mapped[int] = mapped_column(default=0, comment="0-100")
    file_pdf: Mapped[Optional[str]] = mapped_column(String(512))
    file_xlsx: Mapped[Optional[str]] = mapped_column(String(512))
    error: Mapped[Optional[str]] = mapped_column(Text)
    params: Mapped[Optional[str]] = mapped_column(Text, comment="生成参数 JSON")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def to_dict(self):
        return {
            "id": self.id, "company_id": self.company_id, "company_name": self.company_name,
            "template": self.template, "status": self.status, "progress": self.progress,
            "file_pdf": self.file_pdf, "file_xlsx": self.file_xlsx, "error": self.error,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "finished_at": self.finished_at.strftime("%Y-%m-%d %H:%M:%S") if self.finished_at else None,
        }


class Lead(Base):
    """商机线索（基于公开工商+风险变化推导）"""
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    company_name: Mapped[str] = mapped_column(String(256), nullable=False)
    industry: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    province: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    employee_scale: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    signal_type: Mapped[Optional[str]] = mapped_column(String(64), comment="线索信号：新注册/扩张/中标/融资/风险缓解等")
    signal_desc: Mapped[Optional[str]] = mapped_column(String(512))
    risk_delta: Mapped[int] = mapped_column(default=0, comment="风险分变化（正=恶化，负=改善）")
    score: Mapped[int] = mapped_column(default=50, comment="线索价值分 0-100")
    discovered_at: Mapped[Optional[date]] = mapped_column(Date)
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id, "company_id": self.company_id, "company_name": self.company_name,
            "industry": self.industry, "province": self.province,
            "employee_scale": self.employee_scale, "signal_type": self.signal_type,
            "signal_desc": self.signal_desc, "risk_delta": self.risk_delta,
            "score": self.score,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
        }


class LeadFollow(Base, TimestampMixin):
    """线索跟进记录"""
    __tablename__ = "lead_follows"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="new", comment="new/following/won/lost")
    note: Mapped[Optional[str]] = mapped_column(Text)
    next_action: Mapped[Optional[str]] = mapped_column(String(256))


class LeadFavorite(Base):
    """线索收藏"""
    __tablename__ = "lead_favorites"
    __table_args__ = (UniqueConstraint("lead_id", "user_id", name="uq_lead_fav"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    lead_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
