"""会员订阅路由：方案查询 / 下单 / 模拟支付 / 自动续费管理

单一会员类型（高级会员），两种方案：包月 / 连续包月。
演示环境为模拟支付（不接入真实支付渠道）。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, get_current_user
from tyt.db.mysql import get_db
from tyt.models import User
from tyt.schemas import ApiResponse, MemberOrderCreate
from tyt.services import billing_service
from tyt.services.audit_service import log_action

router = APIRouter(prefix="/api/v1/billing", tags=["会员订阅"])


def _current_user(db: Session, principal: Principal) -> User | None:
    return db.get(User, principal.user_id)


@router.get("/plans", response_model=ApiResponse)
def plans(principal: Principal = Depends(get_current_user), db: Session = Depends(get_db)):
    """会员方案 + 权益介绍 + 当前会员状态"""
    user = _current_user(db, principal)
    if not user:
        return ApiResponse(code=401, message="用户不存在")
    return ApiResponse(data={
        "plans": billing_service.get_plans(),
        "benefits": billing_service.MEMBER_BENEFITS,
        "membership": billing_service.get_status(db, user),
    })


@router.post("/orders", response_model=ApiResponse)
def create_order(req: MemberOrderCreate,
                 principal: Principal = Depends(get_current_user), db: Session = Depends(get_db)):
    """创建订阅订单（pending 待支付；演示环境返回模拟扫码内容）"""
    user = _current_user(db, principal)
    if not user:
        return ApiResponse(code=401, message="用户不存在")
    ok, msg, data = billing_service.create_order(db, user, req.plan, req.pay_channel)
    if ok:
        log_action(db, principal, "billing.order.create",
                   resource=f"order:{data['order']['id']}",
                   detail={"plan": req.plan, "amount": data["order"]["amount"]})
    return ApiResponse(code=0 if ok else 400, message=msg, data=data)


@router.post("/orders/{order_id}/pay", response_model=ApiResponse)
def pay_order(order_id: int, principal: Principal = Depends(get_current_user),
              db: Session = Depends(get_db)):
    """模拟支付完成：开通/续期高级会员 30 天（连续包月开启自动续费）"""
    user = _current_user(db, principal)
    if not user:
        return ApiResponse(code=401, message="用户不存在")
    ok, msg, data = billing_service.pay_order(db, user, order_id)
    if ok:
        log_action(db, principal, "billing.order.pay",
                   resource=f"order:{order_id}",
                   detail={"plan": data["order"]["plan"], "amount": data["order"]["amount"]})
    return ApiResponse(code=0 if ok else 400, message=msg, data=data)


@router.post("/cancel-auto-renew", response_model=ApiResponse)
def cancel_auto_renew(principal: Principal = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    """取消连续包月自动续费（会员期内权益保留至到期）"""
    user = _current_user(db, principal)
    if not user:
        return ApiResponse(code=401, message="用户不存在")
    ok, msg = billing_service.cancel_auto_renew(db, user)
    if ok:
        log_action(db, principal, "billing.auto_renew.cancel", resource=f"user:{user.id}")
    return ApiResponse(code=0 if ok else 400, message=msg)


@router.get("/orders", response_model=ApiResponse)
def orders(principal: Principal = Depends(get_current_user), db: Session = Depends(get_db)):
    """我的订阅订单记录"""
    return ApiResponse(data={"orders": billing_service.list_orders(db, principal.user_id)})
