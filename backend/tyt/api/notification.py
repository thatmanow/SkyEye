"""通用站内通知接口（右上角消息中心）

所有登录用户可用：监控提醒、会员订阅、内容审核、社区互动（点赞/评论）等
通知统一在此读取；消息中心轮询未读数并支持单条/全部标记已读。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, get_current_user
from tyt.db.mysql import get_db
from tyt.schemas import ApiResponse
from tyt.services import notification_service

router = APIRouter(prefix="/api/v1/notifications", tags=["站内通知"])


@router.get("", response_model=ApiResponse)
def list_my_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(data=notification_service.list_notifications(
        db, principal.user_id, unread_only, page, page_size))


@router.get("/unread-count", response_model=ApiResponse)
def my_unread_count(principal: Principal = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    return ApiResponse(data={"count": notification_service.unread_count(db, principal.user_id)})


@router.post("/read-all", response_model=ApiResponse)
def read_all(principal: Principal = Depends(get_current_user),
             db: Session = Depends(get_db)):
    return ApiResponse(data={"updated": notification_service.mark_all_read(db, principal.user_id)})


@router.post("/{nid}/read", response_model=ApiResponse)
def read_one(nid: int, principal: Principal = Depends(get_current_user),
             db: Session = Depends(get_db)):
    ok = notification_service.mark_notification_read(db, principal.user_id, nid)
    if not ok:
        return ApiResponse(code=404, message="通知不存在")
    return ApiResponse(data={"id": nid})


@router.delete("/{nid}", response_model=ApiResponse)
def delete_one(nid: int, principal: Principal = Depends(get_current_user),
               db: Session = Depends(get_db)):
    """移除单条通知：消息中心中已读消息再次点击时调用"""
    ok = notification_service.delete_notification(db, principal.user_id, nid)
    if not ok:
        return ApiResponse(code=404, message="通知不存在")
    return ApiResponse(data={"id": nid})
