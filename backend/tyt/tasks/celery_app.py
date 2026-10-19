"""Celery 应用：报告生成 / 监控扫描 / 日报周报

启动（Windows）：celery -A tyt.tasks.celery_app worker --pool=solo --loglevel=info
启动（Linux）：  celery -A tyt.tasks.celery_app worker --loglevel=info
"""
import logging
from datetime import datetime

from celery import Celery
from sqlalchemy import select

from tyt.config import REDIS_URL
from tyt.db.mysql import SessionLocal
from tyt.models import MonitorSchedule, Notification, ReportTask
from tyt.services import report_service, monitor_service, billing_service

logger = logging.getLogger(__name__)

celery_app = Celery(
    "tyt",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tyt.tasks.celery_app"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    beat_schedule={
        "scan-monitor-events": {
            "task": "tyt.scan_monitor_events",
            "schedule": 3600.0,  # 每小时扫描一次变更与风险
        },
        "send-digest": {
            "task": "tyt.send_monitor_digest",
            "schedule": 86400.0,  # 每日投递订阅摘要
        },
        "membership-expiry": {
            "task": "tyt.renew_membership",
            "schedule": 86400.0,  # 每日处理到期会员：连续包月自动续费 / 到期未续费自动降级
        },
    },
)


@celery_app.task(name="tyt.generate_report")
def generate_report_task(task_id: int):
    """异步生成尽调报告（PDF + Excel），更新任务状态与进度"""
    db = SessionLocal()
    try:
        task = db.get(ReportTask, task_id)
        if not task:
            logger.error("report task %s not found", task_id)
            return
        task.status, task.progress = "running", 10
        db.commit()
        try:
            pdf_path, xlsx_path = report_service.build_report_files(task.id, task.company_id, task.template)
            task.file_pdf, task.file_xlsx = str(pdf_path), str(xlsx_path)
            task.status, task.progress = "done", 100
            task.finished_at = datetime.now()
            db.commit()
            db.add(Notification(
                user_id=task.user_id, type="report",
                title=f"尽调报告已生成：{task.company_name}",
                content="报告已就绪，可前往「商业报告」页面下载 PDF / Excel。",
            ))
            db.commit()
        except Exception as e:
            logger.exception("report generation failed")
            task.status, task.error = "failed", str(e)
            db.commit()
    finally:
        db.close()


@celery_app.task(name="tyt.scan_monitor_events")
def scan_monitor_events():
    """周期扫描：变更/风险 -> 监控事件 + 实时提醒"""
    db = SessionLocal()
    try:
        created = monitor_service.scan_and_generate_events(db, since_hours=2)
        logger.info("monitor scan created %s events", created)
        return {"events_created": created}
    finally:
        db.close()


@celery_app.task(name="tyt.send_monitor_digest")
def send_monitor_digest():
    """日报/周报投递：生成摘要并写入站内通知"""
    db = SessionLocal()
    try:
        schedules = db.execute(
            select(MonitorSchedule).where(MonitorSchedule.enabled.is_(True))
        ).scalars().all()
        sent = 0
        for sch in schedules:
            digest = monitor_service.generate_digest(db, sch.user_id)
            freq_name = "日报" if sch.freq == "daily" else "周报"
            db.add(Notification(
                user_id=sch.user_id, type="monitor",
                title=f"【{freq_name}】监控摘要：{digest['watched_count']} 家企业，{digest['event_count']} 条动态",
                content="；".join(e["title"] for e in digest["events"][:5]) or "本期无新增动态",
            ))
            sch.last_run_at = datetime.now()
            sent += 1
        db.commit()
        return {"digests_sent": sent}
    finally:
        db.close()


@celery_app.task(name="tyt.renew_membership")
def renew_membership():
    """每日会员到期处理：连续包月自动续费（模拟扣款）+ 到期未续费自动降级普通用户"""
    db = SessionLocal()
    try:
        result = billing_service.manage_expired_memberships(db)
        return {"members_renewed": result["renewed"], "members_downgraded": result["downgraded"]}
    finally:
        db.close()
