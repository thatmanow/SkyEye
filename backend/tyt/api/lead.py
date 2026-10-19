"""商机线索路由：筛选 / 收藏 / 跟进"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, require_capability
from tyt.db.mysql import get_db
from tyt.schemas import ApiResponse, LeadFollowUpdate
from tyt.services import lead_service
from tyt.services.audit_service import log_action

router = APIRouter(prefix="/api/v1/biz/leads", tags=["商机线索"])


@router.get("", response_model=ApiResponse)
def list_leads(
    industry: str = Query(""), province: str = Query(""), scale: str = Query(""),
    risk_delta: str = Query("", pattern="^(|improved|worsened)$"),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
    principal: Principal = Depends(require_capability("biz.company.basic")),
    db: Session = Depends(get_db),
):
    data = lead_service.list_leads(db, principal.user_id, industry or None,
                                   province or None, scale or None, risk_delta or None,
                                   page, page_size)
    return ApiResponse(data=data)


@router.get("/options", response_model=ApiResponse)
def filter_options(principal: Principal = Depends(require_capability("biz.company.basic")),
                   db: Session = Depends(get_db)):
    return ApiResponse(data=lead_service.lead_filter_options(db))


@router.get("/favorites", response_model=ApiResponse)
def list_favorites(principal: Principal = Depends(require_capability("biz.company.basic")),
                   db: Session = Depends(get_db)):
    return ApiResponse(data={"items": lead_service.list_favorites(db, principal.user_id)})


@router.post("/{lead_id}/favorite", response_model=ApiResponse)
def toggle_favorite(lead_id: int, principal: Principal = Depends(require_capability("biz.company.basic")),
                    db: Session = Depends(get_db)):
    ok, favorited = lead_service.toggle_favorite(db, principal.user_id, lead_id)
    if not ok:
        return ApiResponse(code=404, message="线索不存在")
    return ApiResponse(message="已收藏" if favorited else "已取消收藏", data={"favorited": favorited})


@router.put("/{lead_id}/follow", response_model=ApiResponse)
def update_follow(lead_id: int, req: LeadFollowUpdate,
                  principal: Principal = Depends(require_capability("biz.company.basic")),
                  db: Session = Depends(get_db)):
    ok, msg = lead_service.update_follow(db, principal.user_id, lead_id,
                                         req.status, req.note, req.next_action)
    if ok:
        log_action(db, principal, "biz.lead.follow", resource=f"lead:{lead_id}")
    return ApiResponse(code=0 if ok else 404, message=msg)
