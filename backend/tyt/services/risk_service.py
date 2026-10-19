"""风险信息服务 + 个人查询（严格受限、强制脱敏）"""
import logging

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from tyt.core.security import mask_name
from tyt.models import RiskRecord, Company

logger = logging.getLogger(__name__)


def get_company_risks(db: Session, company_id: int, risk_type: str | None = None) -> dict:
    """企业风险：按类型分组返回 + 统计"""
    stmt = select(RiskRecord).where(
        RiskRecord.subject_type == "company", RiskRecord.subject_id == company_id)
    if risk_type:
        stmt = stmt.where(RiskRecord.risk_type == risk_type)
    rows = db.execute(stmt.order_by(RiskRecord.occur_date.desc())).scalars().all()

    by_type: dict[str, list] = {}
    for r in rows:
        by_type.setdefault(r.risk_type, []).append(r.to_dict())

    counts = {k: len(v) for k, v in by_type.items()}
    risk_score = compute_risk_score(counts)
    return {"total": len(rows), "by_type": by_type, "counts": counts, "risk_score": risk_score}


def compute_risk_score(counts: dict[str, int]) -> int:
    """综合风险分 0-100：司法/行政处罚权重高"""
    weights = {"judicial": 12, "admin_penalty": 10, "business": 6, "finance": 8, "public_opinion": 3}
    score = sum(counts.get(t, 0) * w for t, w in weights.items())
    return min(100, score)


def search_person_risks(db: Session, name: str) -> dict:
    """个人查询：仅失信/涉诉/行政处罚公开记录，姓名脱敏展示

    合规红线：
    - 原始姓名永不出现在返回中（subject_name 本身即脱敏名）
    - 不返回身份证号、手机号、住址等任何隐私字段
    - 查询不建立"姓名->档案"聚合页，仅逐条展示公开风险记录
    """
    masked = mask_name(name)
    rows = db.execute(
        select(RiskRecord).where(
            RiskRecord.subject_type == "person",
            RiskRecord.subject_name == masked,
            RiskRecord.risk_type.in_(["judicial", "admin_penalty"]),
        ).order_by(RiskRecord.occur_date.desc())
    ).scalars().all()

    return {
        "masked_name": masked,
        "total": len(rows),
        "records": [r.to_dict() for r in rows],
        "compliance_note": "结果仅含公开合法渠道（执行信息公开网/裁判文书网/信用中国）的脱敏记录；平台不提供任何非公开个人信息。",
    }


def job_company_risks(db: Session, company_id: int) -> dict:
    """求职向公司风险：经营状态 + 欠薪/劳动仲裁公开记录"""
    company = db.get(Company, company_id)
    if not company:
        return {}
    rows = db.execute(
        select(RiskRecord).where(
            RiskRecord.subject_type == "company",
            RiskRecord.subject_id == company_id,
            RiskRecord.risk_subtype.like("%劳动%") | RiskRecord.risk_subtype.like("%欠薪%")
            | RiskRecord.risk_type.in_(["business", "judicial"]),
        ).order_by(RiskRecord.occur_date.desc())
    ).scalars().all()
    labor = [r.to_dict() for r in rows if r.risk_subtype and ("劳动" in r.risk_subtype or "欠薪" in r.risk_subtype)]
    others = [r.to_dict() for r in rows if r not in [] and not (r.risk_subtype and ("劳动" in r.risk_subtype or "欠薪" in r.risk_subtype))]
    return {
        "company": {"id": company.id, "name": company.name, "reg_status": company.reg_status,
                    "legal_person": company.legal_person, "industry": company.industry,
                    "is_demo": company.is_demo},
        "labor_records": labor,
        "other_records": others[:10],
    }
