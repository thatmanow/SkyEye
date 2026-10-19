"""商机线索服务：筛选、收藏、跟进"""
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from tyt.models import Lead, LeadFavorite, LeadFollow


def list_leads(db: Session, user_id: int, industry: str | None, province: str | None,
               scale: str | None, risk_delta: str | None,
               page: int = 1, page_size: int = 10) -> dict:
    """线索筛选：行业 / 地域 / 规模 / 风险变化（改善 or 恶化）"""
    base = select(Lead)
    if industry:
        base = base.where(Lead.industry == industry)
    if province:
        base = base.where(Lead.province == province)
    if scale:
        base = base.where(Lead.employee_scale == scale)
    if risk_delta == "improved":
        base = base.where(Lead.risk_delta < 0)
    elif risk_delta == "worsened":
        base = base.where(Lead.risk_delta > 0)

    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = db.execute(
        base.order_by(Lead.score.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    fav_ids = set(db.execute(
        select(LeadFavorite.lead_id).where(LeadFavorite.user_id == user_id)
    ).scalars().all()) if user_id else set()

    items = []
    for l in rows:
        d = l.to_dict()
        d["favorited"] = l.id in fav_ids
        follow = db.execute(
            select(LeadFollow).where(LeadFollow.lead_id == l.id, LeadFollow.user_id == user_id)
        ).scalar_one_or_none() if user_id else None
        d["follow_status"] = follow.status if follow else "new"
        items.append(d)
    return {"total": total, "items": items}


def toggle_favorite(db: Session, user_id: int, lead_id: int) -> tuple[bool, bool]:
    lead = db.get(Lead, lead_id)
    if not lead:
        return False, False
    fav = db.execute(
        select(LeadFavorite).where(LeadFavorite.lead_id == lead_id, LeadFavorite.user_id == user_id)
    ).scalar_one_or_none()
    if fav:
        db.delete(fav)
        db.commit()
        return True, False
    db.add(LeadFavorite(lead_id=lead_id, user_id=user_id))
    db.commit()
    return True, True


def update_follow(db: Session, user_id: int, lead_id: int, status: str,
                  note: str, next_action: str) -> tuple[bool, str]:
    lead = db.get(Lead, lead_id)
    if not lead:
        return False, "线索不存在"
    follow = db.execute(
        select(LeadFollow).where(LeadFollow.lead_id == lead_id, LeadFollow.user_id == user_id)
    ).scalar_one_or_none()
    if follow is None:
        follow = LeadFollow(lead_id=lead_id, user_id=user_id)
        db.add(follow)
    follow.status = status
    if note:
        follow.note = note
    if next_action:
        follow.next_action = next_action
    db.commit()
    return True, "跟进记录已更新"


def list_favorites(db: Session, user_id: int) -> list[dict]:
    favs = db.execute(
        select(LeadFavorite).where(LeadFavorite.user_id == user_id)
        .order_by(LeadFavorite.created_at.desc())
    ).scalars().all()
    out = []
    for f in favs:
        lead = db.get(Lead, f.lead_id)
        if lead:
            d = lead.to_dict()
            d["favorited"] = True
            d["favorited_at"] = f.created_at.strftime("%Y-%m-%d") if f.created_at else None
            out.append(d)
    return out


def lead_filter_options(db: Session) -> dict:
    industries = db.execute(
        select(Lead.industry).where(Lead.industry.is_not(None)).distinct()
    ).scalars().all()
    provinces = db.execute(
        select(Lead.province).where(Lead.province.is_not(None)).distinct()
    ).scalars().all()
    scales = db.execute(
        select(Lead.employee_scale).where(Lead.employee_scale.is_not(None)).distinct()
    ).scalars().all()
    return {"industries": sorted(industries), "provinces": sorted(provinces), "scales": sorted(scales)}
