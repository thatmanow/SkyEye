"""会员订阅模型：订单（包月 / 连续包月）"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from tyt.models.base import Base, TimestampMixin


class MembershipOrder(Base, TimestampMixin):
    """会员订阅订单（演示环境为模拟支付，不接入真实支付渠道）"""
    __tablename__ = "membership_orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    plan: Mapped[str] = mapped_column(
        Enum("monthly", "auto_monthly", name="member_plan_enum"),
        nullable=False, comment="包月 monthly / 连续包月 auto_monthly")
    amount: Mapped[float] = mapped_column(nullable=False, comment="实付金额（元）")
    pay_channel: Mapped[str] = mapped_column(String(16), default="alipay", comment="alipay/wechat/auto（演示模拟）")
    status: Mapped[str] = mapped_column(
        Enum("pending", "paid", "cancelled", name="member_order_status_enum"),
        default="pending", nullable=False)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False, comment="本单是否开启自动续费")
    is_first: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否享首月优惠")
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="本期会员起始时间")
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="本期会员到期时间")
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def to_dict(self):
        return {
            "id": self.id, "plan": self.plan, "plan_name": {"monthly": "包月", "auto_monthly": "连续包月"}.get(self.plan, self.plan),
            "amount": self.amount, "pay_channel": self.pay_channel, "status": self.status,
            "auto_renew": self.auto_renew, "is_first": self.is_first,
            "period_start": self.period_start.strftime("%Y-%m-%d") if self.period_start else None,
            "period_end": self.period_end.strftime("%Y-%m-%d") if self.period_end else None,
            "paid_at": self.paid_at.strftime("%Y-%m-%d %H:%M") if self.paid_at else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }
