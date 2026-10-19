"""会员订阅服务：方案查询 / 下单 / 模拟支付 / 自动续费

演示环境说明：不接入真实支付渠道，「扫码支付」为模拟流程——
创建订单（pending）后由用户在页面上确认支付（模拟支付回调），
订单置为 paid 并开通/续期高级会员。
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from tyt.config import (
    MEMBER_DAYS_PER_PERIOD, MEMBER_FIRST_AUTO, MEMBER_FIRST_MONTHLY,
    MEMBER_PRICE_AUTO, MEMBER_PRICE_MONTHLY,
)
from tyt.core.rbac import invalidate_role_cache
from tyt.models import MembershipOrder, Notification, User

logger = logging.getLogger(__name__)

# 前端会员权益介绍（与 QUOTA_MATRIX 对齐：普通用户 -> 高级会员的提升）
MEMBER_BENEFITS = [
    {"icon": "shield", "title": "风险查询不限次",
     "desc": "司法/经营/财务/舆情/行政处罚五类企业风险敞开查（普通用户 10 次/日）"},
    {"icon": "graph", "title": "关系图谱不限次",
     "desc": "Neo4j 股权任职关系图谱任意探索（普通用户 5 次/日）"},
    {"icon": "report", "title": "尽调报告 10 篇/日",
     "desc": "多维数据自动汇总生成尽调报告，支持 PDF/Excel 导出（普通用户不可用）"},
    {"icon": "monitor", "title": "商业监控不限次",
     "desc": "关注企业风险变更实时预警，支持日报/周报摘要（普通用户不可用）"},
    {"icon": "chat", "title": "AI 问答不限次",
     "desc": "本地 RAG 智能问答，回答附可溯源引用（普通用户 20 次/日）"},
    {"icon": "eye", "title": "AI 识图不限次",
     "desc": "MiniCPM-V 图像识别，支持连续追问（普通用户 5 次/日）"},
    {"icon": "edit", "title": "生活圈发帖不限次",
     "desc": "社区分享避坑经验无限制（普通用户 10 次/日）"},
    {"icon": "user", "title": "个人查询 10 次/日",
     "desc": "个人公开背景查询额度提升至 3 倍（普通用户 3 次/日）"},
    {"icon": "stock", "title": "股票分析 10 次/日",
     "desc": "多智能体协作股票/指数分析额度提升至 3 倍（普通用户 3 次/日）"},
]


def get_plans() -> list[dict]:
    """订阅方案（单一会员类型：高级会员；两种方案：包月 / 连续包月）"""
    return [
        {"plan": "monthly", "name": "包月", "price": MEMBER_PRICE_MONTHLY,
         "first_price": MEMBER_FIRST_MONTHLY, "auto_renew": False,
         "badge": "首月优惠", "recommended": False,
         "note": "首月 ¥25，之后 ¥35/月，到期不自动扣费"},
        {"plan": "auto_monthly", "name": "连续包月", "price": MEMBER_PRICE_AUTO,
         "first_price": MEMBER_FIRST_AUTO, "auto_renew": True,
         "badge": "首月优惠 · 每月省 ¥6", "recommended": True,
         "note": "首月 ¥19，之后 ¥29/月自动续费，可随时取消"},
    ]


def _is_first_purchase(db: Session, user_id: int) -> bool:
    """是否首次订阅（无任何已支付订单）——首月优惠资格"""
    return db.execute(
        select(MembershipOrder.id).where(
            MembershipOrder.user_id == user_id,
            MembershipOrder.status == "paid").limit(1)
    ).first() is None


def get_status(db: Session, user: User) -> dict:
    """当前会员状态"""
    return {
        "role": user.role,
        "vip_expire_at": user.vip_expire_at.strftime("%Y-%m-%d") if user.vip_expire_at else None,
        "auto_renew": bool(user.auto_renew),
        "is_first": _is_first_purchase(db, user.id),
    }


def create_order(db: Session, user: User, plan: str, pay_channel: str) -> tuple[bool, str, dict | None]:
    """创建订阅订单（pending，待支付）"""
    if user.role not in ("user", "premium"):
        return False, "当前角色无需购买会员", None
    plans = {p["plan"]: p for p in get_plans()}
    if plan not in plans:
        return False, "无效的订阅方案", None
    if pay_channel not in ("alipay", "wechat"):
        return False, "无效的支付渠道", None

    is_first = _is_first_purchase(db, user.id)
    amount = plans[plan]["first_price"] if is_first else plans[plan]["price"]
    order = MembershipOrder(
        user_id=user.id, plan=plan, amount=amount, pay_channel=pay_channel,
        status="pending", auto_renew=(plan == "auto_monthly"), is_first=is_first,
    )
    db.add(order)
    db.commit()
    return True, "订单创建成功", {
        "order": order.to_dict(),
        # 模拟扫码内容：真实环境为支付网关返回的二维码链接
        "qr_payload": f"tyt://demo-pay/order/{order.id}?amount={amount}&channel={pay_channel}",
        "pay_note": "演示环境模拟支付，点击「模拟支付成功」即可开通",
    }


def pay_order(db: Session, user: User, order_id: int) -> tuple[bool, str, dict | None]:
    """模拟支付回调：订单置为 paid，开通/续期高级会员 30 天"""
    order = db.execute(
        select(MembershipOrder).where(
            MembershipOrder.id == order_id,
            MembershipOrder.user_id == user.id)
    ).scalar_one_or_none()
    if not order:
        return False, "订单不存在", None
    if order.status != "pending":
        return False, f"订单状态异常（{order.status}），无法支付", None

    now = datetime.now()
    # 未到期则顺延续期，已到期（或新购）从现在起算
    base = max(now, user.vip_expire_at) if user.vip_expire_at else now
    period_end = base + timedelta(days=MEMBER_DAYS_PER_PERIOD)

    order.status = "paid"
    order.period_start, order.period_end, order.paid_at = base, period_end, now

    user.role = "premium"
    user.vip_expire_at = period_end
    user.auto_renew = bool(order.auto_renew)
    db.commit()
    invalidate_role_cache(user.id)

    plan_name = "连续包月" if order.auto_renew else "包月"
    db.add(Notification(
        user_id=user.id, type="membership",
        title="高级会员已开通",
        content=f"您已成功订阅{plan_name}（{order.amount:.0f} 元），会员有效期至 "
                f"{period_end.strftime('%Y-%m-%d')}。"
                + ("到期将自动续费，可随时在「会员权益」页取消。" if order.auto_renew
                   else "到期后自动恢复为普通用户。"),
    ))
    db.commit()
    logger.info("membership paid: user=%s order=%s plan=%s until=%s",
                user.id, order.id, order.plan, period_end)
    return True, "支付成功，高级会员已开通", {
        "order": order.to_dict(),
        "membership": get_status(db, user),
    }


def cancel_auto_renew(db: Session, user: User) -> tuple[bool, str]:
    """取消连续包月自动续费（会员期内权益保留至到期）"""
    if not user.auto_renew:
        return False, "当前未开启自动续费"
    user.auto_renew = False
    db.commit()
    db.add(Notification(
        user_id=user.id, type="membership",
        title="已取消自动续费",
        content="连续包月自动续费已关闭，会员权益保留至到期日，到期后恢复为普通用户。",
    ))
    db.commit()
    return True, "已取消自动续费"


def list_orders(db: Session, user_id: int, limit: int = 20) -> list[dict]:
    orders = db.execute(
        select(MembershipOrder).where(MembershipOrder.user_id == user_id)
        .order_by(MembershipOrder.id.desc()).limit(limit)
    ).scalars().all()
    return [o.to_dict() for o in orders]


def manage_expired_memberships(db: Session) -> dict:
    """会员到期每日处理（Celery 任务）：

    1. 连续包月到期：自动续费（模拟扣款，生成订单 + 通知）；
    2. 到期且未开启自动续费：自动降级为普通用户（user）并通知，
       不依赖用户下次登录才降级。
    """
    now = datetime.now()
    # --- 1. 连续包月：自动续费 ---
    expired_auto = db.execute(
        select(User).where(
            User.role == "premium",
            User.auto_renew.is_(True),
            User.vip_expire_at < now,
        )
    ).scalars().all()
    renewed = 0
    for user in expired_auto:
        period_end = now + timedelta(days=MEMBER_DAYS_PER_PERIOD)
        db.add(MembershipOrder(
            user_id=user.id, plan="auto_monthly", amount=MEMBER_PRICE_AUTO,
            pay_channel="auto", status="paid", auto_renew=True, is_first=False,
            period_start=now, period_end=period_end, paid_at=now,
        ))
        user.vip_expire_at = period_end
        invalidate_role_cache(user.id)
        db.add(Notification(
            user_id=user.id, type="membership",
            title="会员自动续费成功",
            content=f"连续包月已自动续费（{MEMBER_PRICE_AUTO:.0f} 元），会员服务持续有效。"
                    f"如需取消，请在「会员权益」弹窗中操作。",
        ))
        renewed += 1

    # --- 2. 到期未续费：自动降级为普通用户 ---
    expired_plain = db.execute(
        select(User).where(
            User.role == "premium",
            User.auto_renew.is_(False),
            User.vip_expire_at < now,
        )
    ).scalars().all()
    downgraded = 0
    for user in expired_plain:
        user.role = "user"
        user.vip_expire_at = None
        invalidate_role_cache(user.id)
        db.add(Notification(
            user_id=user.id, type="membership",
            title="会员已到期",
            content="您的会员有效期已结束，已自动恢复为普通用户。如需继续使用高级权益，"
                    "可随时在「会员权益」中再次开通。",
        ))
        downgraded += 1

    if renewed or downgraded:
        db.commit()
    logger.info("membership expiry handled: renewed=%s downgraded=%s", renewed, downgraded)
    return {"renewed": renewed, "downgraded": downgraded}
