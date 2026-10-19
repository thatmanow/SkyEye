"""商业监控服务：关注、事件、通知、日报周报订阅"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from tyt.models import (
    WatchItem, WatchEvent, Notification, MonitorSchedule,
    CompanyChange, RiskRecord, Company,
)

logger = logging.getLogger(__name__)


def add_watch(db: Session, user_id: int, company_id: int) -> tuple[bool, str]:
    company = db.get(Company, company_id)
    if not company:
        return False, "企业不存在"
    exists = db.execute(
        select(WatchItem).where(WatchItem.user_id == user_id, WatchItem.company_id == company_id)
    ).scalar_one_or_none()
    if exists:
        return False, "已在监控列表中"
    db.add(WatchItem(user_id=user_id, company_id=company_id, company_name=company.name))
    db.commit()
    return True, f"已开始监控「{company.name}」，风险与变更动态将实时提醒"


def remove_watch(db: Session, user_id: int, watch_id: int) -> bool:
    w = db.get(WatchItem, watch_id)
    if not w or w.user_id != user_id:
        return False
    db.delete(w)
    db.commit()
    return True


def list_watches(db: Session, user_id: int) -> list[dict]:
    rows = db.execute(
        select(WatchItem).where(WatchItem.user_id == user_id, WatchItem.enabled.is_(True))
        .order_by(WatchItem.created_at.desc())
    ).scalars().all()
    out = []
    for w in rows:
        latest = db.execute(
            select(WatchEvent).where(WatchEvent.company_id == w.company_id)
            .order_by(WatchEvent.occurred_at.desc()).limit(1)
        ).scalar_one_or_none()
        out.append({
            "watch_id": w.id, "company_id": w.company_id, "company_name": w.company_name,
            "created_at": w.created_at.strftime("%Y-%m-%d") if w.created_at else None,
            "latest_event": latest.to_dict() if latest else None,
        })
    return out


def list_events(db: Session, user_id: int, page: int = 1, page_size: int = 20) -> dict:
    """监控事件流：仅返回用户关注企业的事件"""
    watch_company_ids = db.execute(
        select(WatchItem.company_id).where(WatchItem.user_id == user_id)
    ).scalars().all()
    if not watch_company_ids:
        return {"total": 0, "items": []}
    base = select(WatchEvent).where(WatchEvent.company_id.in_(watch_company_ids))
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = db.execute(
        base.order_by(WatchEvent.occurred_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return {"total": total, "items": [e.to_dict() for e in rows]}


def scan_and_generate_events(db: Session, since_hours: int = 24) -> int:
    """扫描变更与风险记录，生成监控事件 + 站内通知（Celery 周期任务调用）

    事件生成规则：company_changes / risk_records 中 created_at 晚于扫描基线的记录，
    且其企业被至少一个用户关注。
    """
    baseline = datetime.now() - timedelta(hours=since_hours)
    watched = db.execute(select(WatchItem).where(WatchItem.enabled.is_(True))).scalars().all()
    if not watched:
        return 0

    company_watchers: dict[int, list[WatchItem]] = {}
    for w in watched:
        company_watchers.setdefault(w.company_id, []).append(w)

    created = 0
    # 1) 工商变更 -> 事件
    changes = db.execute(
        select(CompanyChange).where(CompanyChange.created_at >= baseline)
    ).scalars().all()
    for ch in changes:
        if ch.company_id not in company_watchers:
            continue
        exists = db.execute(
            select(WatchEvent).where(WatchEvent.event_type == "change",
                                     WatchEvent.event_ref_id == ch.id)
        ).scalar_one_or_none()
        if exists:
            continue
        company = db.get(Company, ch.company_id)
        ev = WatchEvent(
            company_id=ch.company_id,
            company_name=company.name if company else str(ch.company_id),
            event_type="change", event_ref_id=ch.id,
            title=f"工商变更：{ch.change_type}",
            detail=f"{ch.before_value or '—'} → {ch.after_value or '—'}",
            risk_level="info",
            occurred_at=ch.created_at,
        )
        db.add(ev)
        created += 1
        for w in company_watchers[ch.company_id]:
            db.add(Notification(
                user_id=w.user_id, type="monitor",
                title=f"【监控】{ev.company_name} {ch.change_type}",
                content=ev.detail, ref_url=f"/biz/company/{ch.company_id}",
            ))

    # 2) 新增风险 -> 事件（级别按 risk_level）
    risks = db.execute(
        select(RiskRecord).where(RiskRecord.created_at >= baseline)
    ).scalars().all()
    for r in risks:
        if r.subject_type != "company" or r.subject_id not in company_watchers:
            continue
        exists = db.execute(
            select(WatchEvent).where(WatchEvent.event_type == "risk",
                                     WatchEvent.event_ref_id == r.id)
        ).scalar_one_or_none()
        if exists:
            continue
        ev = WatchEvent(
            company_id=r.subject_id, company_name=r.subject_name,
            event_type="risk", event_ref_id=r.id,
            title=f"新增{r.risk_type}风险：{r.risk_subtype or r.title[:20]}",
            detail=r.title, risk_level=r.risk_level or "medium",
            occurred_at=r.created_at,
        )
        db.add(ev)
        created += 1
        for w in company_watchers[r.subject_id]:
            db.add(Notification(
                user_id=w.user_id, type="monitor",
                title=f"【风险提醒】{r.subject_name}",
                content=r.title, ref_url=f"/biz/company/{r.subject_id}",
            ))

    db.commit()
    return created


def upsert_schedule(db: Session, user_id: int, freq: str, scope: str, enabled: bool) -> dict:
    sch = db.execute(
        select(MonitorSchedule).where(MonitorSchedule.user_id == user_id)
    ).scalar_one_or_none()
    if sch is None:
        sch = MonitorSchedule(user_id=user_id, freq=freq, scope=scope, enabled=enabled)
        db.add(sch)
    else:
        sch.freq, sch.scope, sch.enabled = freq, scope, enabled
    db.commit()
    return {"freq": sch.freq, "scope": sch.scope, "enabled": sch.enabled}


def get_schedule(db: Session, user_id: int) -> dict:
    sch = db.execute(
        select(MonitorSchedule).where(MonitorSchedule.user_id == user_id)
    ).scalar_one_or_none()
    if not sch:
        return {"freq": "daily", "scope": "watched", "enabled": True}
    return {"freq": sch.freq, "scope": sch.scope, "enabled": sch.enabled}


def generate_digest(db: Session, user_id: int) -> dict:
    """生成日报/周报摘要（Celery 任务 + API 即时预览共用）"""
    sch = get_schedule(db, user_id)
    days = 7 if sch["freq"] == "weekly" else 1
    since = datetime.now() - timedelta(days=days)
    watches = db.execute(
        select(WatchItem).where(WatchItem.user_id == user_id)
    ).scalars().all()
    company_ids = [w.company_id for w in watches]
    events = []
    if company_ids:
        events = db.execute(
            select(WatchEvent).where(
                and_(WatchEvent.company_id.in_(company_ids), WatchEvent.occurred_at >= since)
            ).order_by(WatchEvent.occurred_at.desc()).limit(100)
        ).scalars().all()
    return {
        "freq": sch["freq"], "since": since.strftime("%Y-%m-%d %H:%M"),
        "watched_count": len(watches),
        "event_count": len(events),
        "events": [e.to_dict() for e in events[:30]],
    }
