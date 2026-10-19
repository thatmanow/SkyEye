"""数据导入服务（管理端）：来自官方公开渠道人工查询结果的 CSV 导入

合规设计：
- 导入来源必须是 data_sources 登记的合法 source_code
- 每次导入写入 collect_logs 审计（操作人、参数、记录数）
- 个人相关数据（如失信被执行人）导入时强制脱敏姓名
"""
import csv
import io
import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from tyt.core.security import mask_name
from tyt.models import (
    Company, DataSource, CollectLog, CompanyPersonnel,
    CompanyShareholder, RiskRecord,
)

logger = logging.getLogger(__name__)


def _log(db: Session, source_code: str, task_type: str, params: dict,
         status: str, records: int, message: str, operator_id: int | None):
    db.add(CollectLog(
        source_code=source_code, task_type=task_type,
        params=json.dumps(params, ensure_ascii=False)[:2000],
        status=status, records=records, message=message[:1000],
        operator_id=operator_id,
        started_at=datetime.now(), finished_at=datetime.now(),
    ))


def import_csv(db: Session, admin_id: int, source_code: str, entity: str,
               csv_content: str) -> tuple[bool, str, int]:
    """CSV 导入：companies / personnel / shareholders / risks"""
    source = db.execute(
        select(DataSource).where(DataSource.code == source_code)
    ).scalar_one_or_none()
    if not source or not source.enabled:
        return False, f"数据源 {source_code} 未登记或已禁用（合规红线：来源必须可溯源）", 0

    reader = csv.DictReader(io.StringIO(csv_content))
    rows = list(reader)
    if not rows:
        return False, "CSV 无数据行", 0

    inserted = 0
    errors: list[str] = []
    now = datetime.now()

    try:
        if entity == "companies":
            for row in rows:
                name = (row.get("name") or "").strip()
                if not name:
                    continue
                exists = db.execute(
                    select(Company).where(Company.name == name)
                ).scalar_one_or_none()
                if exists:
                    continue
                db.add(Company(
                    name=name,
                    credit_code=(row.get("credit_code") or "").strip() or None,
                    legal_person=(row.get("legal_person") or "").strip() or None,
                    reg_status=row.get("reg_status") or None,
                    industry=row.get("industry") or None,
                    province=row.get("province") or None,
                    city=row.get("city") or None,
                    address=row.get("address") or None,
                    business_scope=row.get("business_scope") or None,
                    reg_authority=row.get("reg_authority") or None,
                    source=source_code, source_url=source.url,
                    collected_at=now, is_demo=False,
                ))
                inserted += 1

        elif entity == "personnel":
            for row in rows:
                company_name = (row.get("company_name") or "").strip()
                person = (row.get("name") or "").strip()
                if not company_name or not person:
                    continue
                company = db.execute(
                    select(Company).where(Company.name == company_name)
                ).scalar_one_or_none()
                if not company:
                    errors.append(f"企业不存在：{company_name}")
                    continue
                db.add(CompanyPersonnel(
                    company_id=company.id, name=person,
                    position=row.get("position") or None,
                    is_legal_person=row.get("is_legal_person") == "是",
                    source=source_code,
                ))
                inserted += 1

        elif entity == "shareholders":
            for row in rows:
                company_name = (row.get("company_name") or "").strip()
                holder = (row.get("holder_name") or "").strip()
                if not company_name or not holder:
                    continue
                company = db.execute(
                    select(Company).where(Company.name == company_name)
                ).scalar_one_or_none()
                if not company:
                    errors.append(f"企业不存在：{company_name}")
                    continue
                ratio = None
                if row.get("share_ratio"):
                    try:
                        ratio = float(row["share_ratio"])
                    except ValueError:
                        pass
                db.add(CompanyShareholder(
                    company_id=company.id, holder_name=holder,
                    holder_type=row.get("holder_type") or "person",
                    share_ratio=ratio, source=source_code,
                ))
                inserted += 1

        elif entity == "risks":
            for row in rows:
                subject_name = (row.get("subject_name") or "").strip()
                risk_type = (row.get("risk_type") or "").strip()
                title = (row.get("title") or "").strip()
                if not subject_name or risk_type not in (
                        "judicial", "business", "finance", "public_opinion", "admin_penalty") or not title:
                    continue
                subject_type = row.get("subject_type") or "company"
                subject_id = 0
                display_name = subject_name
                if subject_type == "company":
                    company = db.execute(
                        select(Company).where(Company.name == subject_name)
                    ).scalar_one_or_none()
                    if not company:
                        errors.append(f"企业不存在：{subject_name}")
                        continue
                    subject_id, display_name = company.id, company.name
                else:
                    # 个人风险：强制脱敏后入库，原始姓名不留存
                    display_name = mask_name(subject_name)
                db.add(RiskRecord(
                    subject_type=subject_type, subject_id=subject_id,
                    subject_name=display_name, risk_type=risk_type,
                    risk_subtype=row.get("risk_subtype") or None,
                    title=title, content_digest=row.get("content_digest") or None,
                    court=row.get("court") or None, case_no=row.get("case_no") or None,
                    risk_level=row.get("risk_level") or "medium",
                    source=source_code, source_url=row.get("source_url") or source.url,
                    is_demo=False,
                ))
                inserted += 1

        db.commit()
        _log(db, source_code, "import", {"entity": entity, "rows": len(rows)},
             "success", inserted,
             f"导入 {inserted} 条" + (f"；跳过：{';'.join(errors[:5])}" if errors else ""),
             admin_id)
        source.last_synced_at = now
        db.commit()
        return True, f"成功导入 {inserted} 条记录（来源：{source.name}），已写入采集审计日志", inserted

    except Exception as e:
        db.rollback()
        _log(db, source_code, "import", {"entity": entity}, "failed", inserted, str(e), admin_id)
        db.commit()
        return False, f"导入失败：{e}", inserted
