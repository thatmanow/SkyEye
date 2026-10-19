"""风险信息模型

subject_type = 'company' 时 subject_id 关联 companies.id；
subject_type = 'person' 时 subject_id 为 0，subject_name 为脱敏姓名 —— 个人风险仅存脱敏名，
原始姓名不入库（合规红线：不建人肉索引）。
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, Numeric, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from tyt.models.base import Base


class RiskRecord(Base):
    __tablename__ = "risk_records"
    __table_args__ = (
        Index("idx_risk_subject", "subject_type", "subject_id"),
        Index("idx_risk_type_date", "risk_type", "occur_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    subject_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="company/person")
    subject_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="企业ID；个人固定0")
    subject_name: Mapped[str] = mapped_column(String(256), nullable=False, comment="企业名 或 个人脱敏名")
    risk_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="judicial/business/finance/public_opinion/admin_penalty")
    risk_subtype: Mapped[Optional[str]] = mapped_column(String(64), comment="如 买卖合同纠纷/欠税公告/被执行人/失信被执行人")
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content_digest: Mapped[Optional[str]] = mapped_column(Text, comment="摘要（脱敏后）")
    amount_wan: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), comment="涉案/执行金额（万元）")
    court: Mapped[Optional[str]] = mapped_column(String(128), comment="审理法院")
    case_no: Mapped[Optional[str]] = mapped_column(String(64), comment="案号（脱敏）")
    risk_level: Mapped[str] = mapped_column(String(8), default="medium", comment="low/medium/high")
    occur_date: Mapped[Optional[date]] = mapped_column(Date)
    publish_date: Mapped[Optional[date]] = mapped_column(Date)
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=False, comment="数据来源标识（可溯源）")
    source_url: Mapped[Optional[str]] = mapped_column(String(512))
    is_demo: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self, with_content: bool = True):
        d = {
            "id": self.id, "subject_name": self.subject_name,
            "risk_type": self.risk_type, "risk_subtype": self.risk_subtype,
            "title": self.title, "amount_wan": float(self.amount_wan) if self.amount_wan else None,
            "court": self.court, "case_no": self.case_no, "risk_level": self.risk_level,
            "occur_date": self.occur_date.isoformat() if self.occur_date else None,
            "publish_date": self.publish_date.isoformat() if self.publish_date else None,
            "source": self.source, "source_url": self.source_url,
        }
        if with_content:
            d["content_digest"] = self.content_digest
        return d


