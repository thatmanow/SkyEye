"""企业查询服务：搜索（ES 优先 / MySQL ngram FULLTEXT 降级）、工商详情、股权、人员、投资、分支、变更"""
import logging
from datetime import datetime

from sqlalchemy import select, func, or_, text, bindparam, String
from sqlalchemy.orm import Session

from tyt.db import es_client
from tyt.models import (
    Company, CompanyPersonnel, CompanyShareholder,
    CompanyInvestment, CompanyBranch, CompanyChange,
)

logger = logging.getLogger(__name__)


def search_companies(db: Session, keyword: str, page: int = 1, page_size: int = 10) -> dict:
    """企业搜索：ES（如启用）→ MySQL FULLTEXT(ngram) → LIKE 兜底"""
    # 1) Elasticsearch
    if es_client.es_available():
        hits = es_client.search_company(keyword, size=page_size)
        if hits is not None:
            ids = [int(h["id"]) for h in hits]
            if not ids:
                return {"total": 0, "items": []}
            rows = db.execute(select(Company).where(Company.id.in_(ids))).scalars().all()
            rows.sort(key=lambda c: ids.index(c.id))
            return {"total": len(rows), "items": [company_card(c) for c in rows]}

    # 2) MySQL FULLTEXT(ngram)
    # 说明：sqlalchemy 2.x 顶层没有 match/Match 构造器，func.match(...).against(...)
    # 在 2.0.x 会抛 AttributeError（Function 无 .against 方法）。
    # 故用 text() + bindparam 直接生成 MATCH(col) AGAINST (:kw)，
    # 并把 keyword 值烘焙进 bindparam，使后续 execute 无需显式传参。
    total = 0
    rows: list[Company] = []
    try:
        match_clause = text(
            "MATCH(name, business_scope, industry) AGAINST (:kw)"
        ).bindparams(bindparam("kw", type_=String, value=keyword))
        base = select(Company).where(match_clause)
        total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
        rows = db.execute(
            base.order_by(Company.reg_status.desc()).offset((page - 1) * page_size).limit(page_size)
        ).scalars().all()
    except Exception as e:
        logger.warning("FULLTEXT search failed, fallback LIKE: %s", e)

    # 3) LIKE 兜底（FULLTEXT 未建索引或分词不命中）
    if not rows:
        like = f"%{keyword}%"
        base = select(Company).where(or_(
            Company.name.like(like),
            Company.short_name.like(like),
            Company.listed_code == keyword.strip(),
        ))
        total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
        rows = db.execute(
            base.offset((page - 1) * page_size).limit(page_size)
        ).scalars().all()

    return {"total": total, "items": [company_card(c) for c in rows]}


def company_card(c: Company) -> dict:
    return {
        "id": c.id, "name": c.name, "short_name": c.short_name,
        "legal_person": c.legal_person, "reg_status": c.reg_status,
        "reg_capital_wan": float(c.reg_capital_wan) if c.reg_capital_wan else None,
        "founded_date": c.founded_date.isoformat() if c.founded_date else None,
        "industry": c.industry, "province": c.province, "city": c.city,
        "listed_code": c.listed_code, "is_demo": c.is_demo,
        "source": c.source,
        "collected_at": c.collected_at.strftime("%Y-%m-%d") if c.collected_at else None,
        "updated_at": c.updated_at.strftime("%Y-%m-%d") if c.updated_at else None,
    }


def company_detail(db: Session, company_id: int) -> dict | None:
    c = db.get(Company, company_id)
    if not c:
        return None
    d = company_card(c)
    d.update({
        "credit_code": c.credit_code,
        "paid_capital_wan": float(c.paid_capital_wan) if c.paid_capital_wan else None,
        "company_type": c.company_type,
        "address": c.address,
        "business_scope": c.business_scope,
        "reg_authority": c.reg_authority,
        "employee_scale": c.employee_scale,
        "source_url": c.source_url,
    })
    return d


def get_shareholders(db: Session, company_id: int) -> list[dict]:
    rows = db.execute(
        select(CompanyShareholder).where(CompanyShareholder.company_id == company_id)
        .order_by(CompanyShareholder.share_ratio.desc())
    ).scalars().all()
    return [{
        "holder_name": s.holder_name, "holder_type": s.holder_type,
        "share_ratio": float(s.share_ratio) if s.share_ratio else None,
        "subscribed_capital_wan": float(s.subscribed_capital_wan) if s.subscribed_capital_wan else None,
        "source": s.source,
    } for s in rows]


def get_personnel(db: Session, company_id: int) -> list[dict]:
    rows = db.execute(
        select(CompanyPersonnel).where(CompanyPersonnel.company_id == company_id)
    ).scalars().all()
    return [{
        "name": p.name, "position": p.position,
        "is_legal_person": p.is_legal_person, "source": p.source,
    } for p in rows]


def get_investments(db: Session, company_id: int) -> list[dict]:
    rows = db.execute(
        select(CompanyInvestment).where(CompanyInvestment.investor_id == company_id)
        .order_by(CompanyInvestment.share_ratio.desc())
    ).scalars().all()
    return [{
        "investee_id": i.investee_id, "investee_name": i.investee_name,
        "share_ratio": float(i.share_ratio) if i.share_ratio else None,
        "invested_amount_wan": float(i.invested_amount_wan) if i.invested_amount_wan else None,
        "investee_reg_status": i.investee_reg_status, "source": i.source,
    } for i in rows]


def get_branches(db: Session, company_id: int) -> list[dict]:
    rows = db.execute(
        select(CompanyBranch).where(CompanyBranch.company_id == company_id)
    ).scalars().all()
    return [{
        "branch_name": b.branch_name, "branch_status": b.branch_status,
        "branch_person": b.branch_person, "province": b.province, "city": b.city,
    } for b in rows]


def get_changes(db: Session, company_id: int, limit: int = 50) -> list[dict]:
    rows = db.execute(
        select(CompanyChange).where(CompanyChange.company_id == company_id)
        .order_by(CompanyChange.change_date.desc()).limit(limit)
    ).scalars().all()
    return [{
        "change_type": ch.change_type, "before_value": ch.before_value,
        "after_value": ch.after_value,
        "change_date": ch.change_date.isoformat() if ch.change_date else None,
        "source": ch.source,
    } for ch in rows]


def get_stats(db: Session) -> dict:
    """平台数据看板统计"""
    total_companies = db.execute(select(func.count()).select_from(Company)).scalar() or 0
    today = datetime.now().strftime("%Y-%m-%d")
    return {
        "total_companies": total_companies,
        "stat_date": today,
    }
