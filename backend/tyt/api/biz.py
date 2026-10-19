"""商业类路由：企业信息查询 + 风险信息查询"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, get_principal, require_capability
from tyt.db.mysql import get_db
from tyt.schemas import ApiResponse
from tyt.services import company_service, risk_service, quota_service
from tyt.services.audit_service import log_action

router = APIRouter(prefix="/api/v1/biz", tags=["商业类"])


@router.get("/companies/search", response_model=ApiResponse)
def search_companies(
    keyword: str = Query(..., min_length=1, max_length=64),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """企业搜索（游客限基础信息、每日 3 次）"""
    allowed, used, limit = quota_service.check_and_consume("biz_basic", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日企业查询次数已用完（限额 {limit} 次/天），注册登录后不限次")
    data = company_service.search_companies(db, keyword, page, page_size)
    log_action(db, principal, "biz.company.search", detail={"keyword": keyword})
    return ApiResponse(data=data)


@router.get("/companies/{company_id}", response_model=ApiResponse)
def company_detail(
    company_id: int,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """企业工商详情：含数据来源与更新时间标注"""
    allowed, used, limit = quota_service.check_and_consume("biz_basic", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日企业查询次数已用完（限额 {limit} 次/天）")
    data = company_service.company_detail(db, company_id)
    if not data:
        return ApiResponse(code=404, message="企业不存在")
    return ApiResponse(data=data)


@router.get("/companies/{company_id}/shareholders", response_model=ApiResponse)
def shareholders(company_id: int, principal: Principal = Depends(get_principal),
                 db: Session = Depends(get_db)):
    allowed, _, _ = quota_service.check_and_consume("biz_basic", principal)
    if not allowed:
        return ApiResponse(code=429, message="查询次数已用完")
    return ApiResponse(data={"items": company_service.get_shareholders(db, company_id)})


@router.get("/companies/{company_id}/personnel", response_model=ApiResponse)
def personnel(company_id: int, principal: Principal = Depends(get_principal),
              db: Session = Depends(get_db)):
    allowed, _, _ = quota_service.check_and_consume("biz_basic", principal)
    if not allowed:
        return ApiResponse(code=429, message="查询次数已用完")
    return ApiResponse(data={"items": company_service.get_personnel(db, company_id)})


@router.get("/companies/{company_id}/investments", response_model=ApiResponse)
def investments(company_id: int, principal: Principal = Depends(get_principal),
                db: Session = Depends(get_db)):
    allowed, _, _ = quota_service.check_and_consume("biz_basic", principal)
    if not allowed:
        return ApiResponse(code=429, message="查询次数已用完")
    return ApiResponse(data={"items": company_service.get_investments(db, company_id)})


@router.get("/companies/{company_id}/branches", response_model=ApiResponse)
def branches(company_id: int, principal: Principal = Depends(get_principal),
             db: Session = Depends(get_db)):
    allowed, _, _ = quota_service.check_and_consume("biz_basic", principal)
    if not allowed:
        return ApiResponse(code=429, message="查询次数已用完")
    return ApiResponse(data={"items": company_service.get_branches(db, company_id)})


@router.get("/companies/{company_id}/changes", response_model=ApiResponse)
def changes(company_id: int, principal: Principal = Depends(get_principal),
            db: Session = Depends(get_db)):
    allowed, _, _ = quota_service.check_and_consume("biz_basic", principal)
    if not allowed:
        return ApiResponse(code=429, message="查询次数已用完")
    return ApiResponse(data={"items": company_service.get_changes(db, company_id)})


# ==================== 4.2 风险信息 ====================

@router.get("/companies/{company_id}/risks", response_model=ApiResponse)
def company_risks(
    company_id: int,
    risk_type: str = Query("", pattern="^(|judicial|business|finance|public_opinion|admin_penalty)$"),
    principal: Principal = Depends(require_capability("biz.risk")),
    db: Session = Depends(get_db),
):
    """企业风险：司法/经营/财务/舆情/行政处罚（普通用户每日 10 次）"""
    allowed, used, limit = quota_service.check_and_consume("biz_risk", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日风险查询次数已用完（限额 {limit} 次/天），高级会员不限次")
    data = risk_service.get_company_risks(db, company_id, risk_type or None)
    log_action(db, principal, "biz.risk.query", resource=f"company:{company_id}")
    return ApiResponse(data=data)
