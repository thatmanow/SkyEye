"""生活类路由：商家查询 / 房源查询 / 求职公司查询 / 个人查询（严格受限）"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, get_current_user, get_principal
from tyt.db.mysql import get_db
from tyt.models import Merchant, MerchantReview, HousingEstate, Complaint, RiskRecord, Company
from tyt.schemas import (
    ApiResponse, ComplaintCreate, MerchantReviewCreate, PersonQueryRequest,
)
from tyt.services import community_service, risk_service, quota_service
from tyt.services.audit_service import log_action

router = APIRouter(prefix="/api/v1/life", tags=["生活类"])


def _consume(db: Session, principal: Principal, quota_type: str):
    """配额检查：超限时返回错误响应"""
    allowed, used, limit = quota_service.check_and_consume(quota_type, principal)
    if not allowed:
        remaining = max(0, limit - used)
        return ApiResponse(
            code=429,
            message=f"今日{quota_type}查询次数已用完（限额 {limit} 次/天，剩余 {remaining}）。"
                    f"升级高级会员可获得不限次查询。",
        )
    return None


# ==================== 3.1 商家查询 ====================

@router.get("/merchants/search", response_model=ApiResponse)
def search_merchants(
    keyword: str = Query(..., min_length=1, max_length=64),
    city: str = Query(""),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    blocked = _consume(db, principal, "life_query")
    if blocked:
        return blocked
    base = select(Merchant)
    cond = or_(Merchant.name.like(f"%{keyword}%"),
               Merchant.address.like(f"%{keyword}%"),
               Merchant.business_scope.like(f"%{keyword}%"))
    base = base.where(cond)
    if city:
        base = base.where(Merchant.city == city)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = db.execute(
        base.order_by(Merchant.rating_avg.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return ApiResponse(data={"total": total, "items": [m.to_dict() for m in rows]})


@router.get("/merchants/{merchant_id}", response_model=ApiResponse)
def merchant_detail(
    merchant_id: int,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    blocked = _consume(db, principal, "life_query")
    if blocked:
        return blocked
    m = db.get(Merchant, merchant_id)
    if not m:
        return ApiResponse(code=404, message="商家不存在")
    data = m.to_dict()
    data["complaints"] = community_service.list_visible_complaints(db, "merchant", merchant_id)
    reviews = db.execute(
        select(MerchantReview)
        .where(MerchantReview.merchant_id == merchant_id, MerchantReview.status == "approved")
        .order_by(MerchantReview.created_at.desc()).limit(20)
    ).scalars().all()
    data["reviews"] = [{
        "rating": r.rating, "content": r.content,
        "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else None,
    } for r in reviews]
    return ApiResponse(data=data)


@router.post("/merchants/{merchant_id}/reviews", response_model=ApiResponse)
def create_merchant_review(
    merchant_id: int,
    req: MerchantReviewCreate,
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok, msg = community_service.create_merchant_review(
        db, principal.user_id, merchant_id, req.rating, req.content)
    if ok:
        log_action(db, principal, "life.merchant.review", resource=f"merchant:{merchant_id}")
    return ApiResponse(code=0 if ok else 400, message=msg)


# ==================== 3.2 房源查询 ====================

@router.get("/housing/estates/search", response_model=ApiResponse)
def search_estates(
    keyword: str = Query(..., min_length=1, max_length=64),
    city: str = Query(""),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    blocked = _consume(db, principal, "life_query")
    if blocked:
        return blocked
    base = select(HousingEstate).where(HousingEstate.name.like(f"%{keyword}%"))
    if city:
        base = base.where(HousingEstate.city == city)
    rows = db.execute(base.limit(20)).scalars().all()
    return ApiResponse(data={"total": len(rows), "items": [e.to_dict() for e in rows]})


@router.get("/housing/records", response_model=ApiResponse)
def housing_records(
    subject_type: str = Query("estate", pattern="^(estate|landlord|agency)$"),
    keyword: str = Query(..., min_length=1, max_length=64),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """房源投诉/纠纷查询：小区（精确名）/ 房东 / 中介（脱敏名匹配）"""
    blocked = _consume(db, principal, "life_query")
    if blocked:
        return blocked
    if subject_type == "estate":
        estate = db.execute(
            select(HousingEstate).where(HousingEstate.name.like(f"%{keyword}%")).limit(1)
        ).scalar_one_or_none()
        if not estate:
            return ApiResponse(data={"total": 0, "estate": None, "complaints": [],
                                     "judicial_records": []})
        complaints = community_service.list_visible_complaints(db, "estate", estate.id)
        judicial = [r.to_dict() for r in db.execute(
            select(RiskRecord).where(
                RiskRecord.subject_type == "company",
                RiskRecord.title.like(f"%{estate.name}%"),
            ).limit(10)
        ).scalars().all()]
        estate_dict = estate.to_dict()
        # complaint_count 为种子静态列，以过审投诉实时数量为准
        estate_dict["complaint_count"] = len(complaints)
        return ApiResponse(data={"total": len(complaints), "estate": estate_dict,
                                 "complaints": complaints, "judicial_records": judicial})
    # landlord / agency：投诉记录按脱敏名检索
    rows = db.execute(
        select(Complaint).where(
            Complaint.subject_type == subject_type,
            Complaint.subject_label.like(f"%{keyword}%"),
            Complaint.status == "approved",
        ).order_by(Complaint.created_at.desc()).limit(50)
    ).scalars().all()
    return ApiResponse(data={"total": len(rows), "complaints": [c.to_dict() for c in rows]})


@router.post("/housing/complaints", response_model=ApiResponse)
def create_housing_complaint(
    req: ComplaintCreate,
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.subject_type not in ("estate", "landlord", "agency"):
        return ApiResponse(code=400, message="subject_type 须为 estate/landlord/agency")
    ok, msg = community_service.create_complaint(db, principal.user_id, req.model_dump())
    if ok:
        log_action(db, principal, "life.housing.complaint", resource=req.subject_type)
    return ApiResponse(code=0 if ok else 400, message=msg)


# ==================== 3.3 公司查询（求职向） ====================

@router.get("/jobs/companies", response_model=ApiResponse)
def job_company_search(
    name: str = Query(..., min_length=2, max_length=64),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """求职向公司查询：经营状态 + 欠薪/劳动仲裁公开记录"""
    blocked = _consume(db, principal, "life_query")
    if blocked:
        return blocked
    companies = db.execute(
        select(Company).where(Company.name.like(f"%{name}%")).limit(10)
    ).scalars().all()
    if not companies:
        return ApiResponse(data={"total": 0, "items": []})
    items = []
    for c in companies:
        data = risk_service.job_company_risks(db, c.id)
        items.append(data)
    return ApiResponse(data={"total": len(items), "items": items})


# ==================== 3.4 个人查询（严格受限） ====================

@router.post("/person/search", response_model=ApiResponse)
def person_search(
    req: PersonQueryRequest,
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """个人查询：仅公开合法的失信/涉诉/行政处罚，强制脱敏，游客禁用

    合规说明：
    - 本接口不提供身份证号/手机号/住址等任何非公开信息检索
    - 姓名仅为检索条件，返回结果全部脱敏
    - 查询行为全量写入审计日志
    """
    allowed, used, limit = quota_service.check_and_consume("person_query", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日个人查询次数已用完（限额 {limit} 次/天）")
    data = risk_service.search_person_risks(db, req.name)
    log_action(db, principal, "life.person.search",
               detail={"masked": data["masked_name"], "results": data["total"]})
    return ApiResponse(data=data)
