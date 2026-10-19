"""商业监控路由：关注管理 / 事件流 / 通知 / 日报周报"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, get_current_user, require_capability
from tyt.db.mysql import get_db
from tyt.schemas import ApiResponse, MonitorScheduleUpdate, WatchCreate
from tyt.services import monitor_service, notification_service, quota_service
from tyt.services.audit_service import log_action

router = APIRouter(prefix="/api/v1/biz/monitor", tags=["商业监控"])


@router.get("/watches", response_model=ApiResponse)
def list_watches(principal: Principal = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """查看「我的监控列表」：仅校验登录（按 user_id 隔离）。
    会员过期后仍可查看自己曾关注的企业与历史，符合「历史记录保留」规则。"""
    return ApiResponse(data={"items": monitor_service.list_watches(db, principal.user_id)})


@router.post("/watches", response_model=ApiResponse)
def add_watch(req: WatchCreate, principal: Principal = Depends(require_capability("biz.monitor")),
              db: Session = Depends(get_db)):
    ok, msg = monitor_service.add_watch(db, principal.user_id, req.company_id)
    if ok:
        log_action(db, principal, "biz.monitor.watch", resource=f"company:{req.company_id}")
    return ApiResponse(code=0 if ok else 400, message=msg)


@router.delete("/watches/{watch_id}", response_model=ApiResponse)
def remove_watch(watch_id: int, principal: Principal = Depends(require_capability("biz.monitor")),
                 db: Session = Depends(get_db)):
    ok = monitor_service.remove_watch(db, principal.user_id, watch_id)
    return ApiResponse(code=0 if ok else 404, message="已取消监控" if ok else "监控项不存在")


@router.get("/events", response_model=ApiResponse)
def list_events(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查看「风险事件流」：仅校验登录（按 user_id 隔离）；会员过期后仍可查看历史事件。"""
    return ApiResponse(data=monitor_service.list_events(db, principal.user_id, page, page_size))


@router.post("/scan", response_model=ApiResponse)
def trigger_scan(principal: Principal = Depends(require_capability("biz.monitor")),
                 db: Session = Depends(get_db)):
    """手动触发一次监控扫描（管理员/演示用；正常由 Celery 周期任务执行）"""
    if not principal.has_role_at_least("platform_admin"):
        return ApiResponse(code=403, message="仅平台管理员可手动触发全量扫描")
    created = monitor_service.scan_and_generate_events(db)
    return ApiResponse(data={"events_created": created})


@router.get("/notifications", response_model=ApiResponse)
def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查看「监控站内通知」：仅校验登录（按 user_id 隔离）；会员过期后仍可查看历史通知。"""
    return ApiResponse(data=notification_service.list_notifications(
        db, principal.user_id, unread_only, page, page_size))


@router.post("/notifications/{nid}/read", response_model=ApiResponse)
def mark_read(nid: int, principal: Principal = Depends(require_capability("biz.monitor")),
              db: Session = Depends(get_db)):
    ok = notification_service.mark_notification_read(db, principal.user_id, nid)
    return ApiResponse(code=0 if ok else 404, message="已标记已读" if ok else "通知不存在")


@router.get("/schedule", response_model=ApiResponse)
def get_schedule(principal: Principal = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """查看「我的订阅设置」：仅校验登录；会员过期后仍可查看自己曾经的订阅配置。"""
    return ApiResponse(data=monitor_service.get_schedule(db, principal.user_id))


@router.put("/schedule", response_model=ApiResponse)
def update_schedule(req: MonitorScheduleUpdate,
                    principal: Principal = Depends(require_capability("biz.monitor")),
                    db: Session = Depends(get_db)):
    return ApiResponse(data=monitor_service.upsert_schedule(
        db, principal.user_id, req.freq, req.scope, req.enabled))


@router.get("/digest", response_model=ApiResponse)
def digest_preview(principal: Principal = Depends(require_capability("biz.monitor")),
                   db: Session = Depends(get_db)):
    """日报/周报即时预览（定时投递由 Celery 任务执行）"""
    return ApiResponse(data=monitor_service.generate_digest(db, principal.user_id))
