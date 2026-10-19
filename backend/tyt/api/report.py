"""商业报告路由：一键尽调报告（API 进程内后台异步生成 + PDF/Excel 下载）"""
import logging
import mimetypes
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from tyt.config import REPORT_DIR
from tyt.core.rbac import Principal, get_current_user, require_capability
from tyt.db.mysql import get_db
from tyt.models import ReportTask
from tyt.schemas import ApiResponse, ReportCreate
from tyt.services import report_service, quota_service
from tyt.services.audit_service import log_action

router = APIRouter(prefix="/api/v1/biz/reports", tags=["商业报告"])


@router.post("", response_model=ApiResponse)
def create_report(
    req: ReportCreate,
    background_tasks: BackgroundTasks,
    principal: Principal = Depends(require_capability("biz.report")),
    db: Session = Depends(get_db),
):
    """创建报告任务：在 API 进程内以后台任务异步生成，不依赖独立 Celery worker"""
    from tyt.models import Company
    company = db.get(Company, req.company_id)
    if not company:
        return ApiResponse(code=404, message="企业不存在")

    allowed, used, limit = quota_service.check_and_consume("report", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日尽调报告次数已用完（限额 {limit} 篇/天），明日重置或升级会员")

    task = ReportTask(user_id=principal.user_id, company_id=req.company_id,
                      company_name=company.name, template=req.template, status="queued")
    db.add(task)
    db.commit()
    db.refresh(task)

    # 关键修复：原实现调用 generate_report_task.delay() 把任务投递到 Celery 队列，
    # 但若部署未启动 celery worker，任务会永久停留在 queued（前端一直显示「排队中」）。
    # 同步回退只在 broker 不可用时触发，Redis 在线但无 worker 时不会生效。
    # 改为在 API 进程内用 FastAPI BackgroundTasks 异步生成：提交即开始、前端轮询可见进度，
    # 不再依赖独立 Celery worker，保证「功能始终可用」。
    background_tasks.add_task(_run_report_in_process, task.id, req.company_id, req.template)

    log_action(db, principal, "biz.report.create", resource=f"company:{req.company_id}")
    return ApiResponse(message="报告任务已提交（后台生成）", data={"task_id": task.id})


def _run_report_in_process(task_id: int, company_id: int, template: str) -> None:
    """在 API 进程的后台线程中生成报告，推进状态 queued -> running -> done/failed。"""
    from datetime import datetime

    from tyt.db.mysql import SessionLocal
    from tyt.models import Notification, ReportTask

    logger = logging.getLogger(__name__)
    db = SessionLocal()
    try:
        task = db.get(ReportTask, task_id)
        if not task:
            return
        task.status, task.progress = "running", 10
        db.commit()
        try:
            pdf_path, xlsx_path = report_service.build_report_files(task.id, company_id, template)
            task.file_pdf, task.file_xlsx = str(pdf_path), str(xlsx_path)
            task.status, task.progress = "done", 100
            task.finished_at = datetime.now()
            db.add(Notification(
                user_id=task.user_id, type="report",
                title=f"尽调报告已生成：{task.company_name}",
                content="报告已就绪，可前往「商业报告」页面下载 PDF / Excel。",
            ))
            db.commit()
        except Exception as e:
            logger.exception("in-process report generation failed: task=%s", task_id)
            task.status, task.error = "failed", str(e)
            db.commit()
    finally:
        db.close()


@router.get("", response_model=ApiResponse)
def list_reports(principal: Principal = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    """查看「我的报告」历史：仅校验登录（按 user_id 隔离）。
    即使会员过期（role 降为 user）仍可查看自己曾生成的历史报告，符合「历史记录保留」规则；
    生成新报告仍由 create_report 的 biz.report 能力校验把关。"""
    rows = db.execute(
        select(ReportTask).where(ReportTask.user_id == principal.user_id)
        .order_by(ReportTask.created_at.desc()).limit(50)
    ).scalars().all()
    return ApiResponse(data={"items": [t.to_dict() for t in rows]})


@router.get("/{task_id}", response_model=ApiResponse)
def get_report(task_id: int, principal: Principal = Depends(get_current_user),
               db: Session = Depends(get_db)):
    t = db.get(ReportTask, task_id)
    if not t or t.user_id != principal.user_id:
        return ApiResponse(code=404, message="报告任务不存在")
    return ApiResponse(data=t.to_dict())


@router.get("/{task_id}/download", response_class=FileResponse)
def download_report(
    task_id: int,
    format: str = Query("pdf", pattern="^(pdf|xlsx)$"),
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    t = db.get(ReportTask, task_id)
    if not t or t.user_id != principal.user_id:
        raise HTTPException(status_code=404, detail="报告任务不存在")
    if t.status != "done":
        raise HTTPException(status_code=400, detail="报告尚未生成完成")

    path = Path(t.file_pdf if format == "pdf" else t.file_xlsx)
    if not path.exists():
        raise HTTPException(status_code=410, detail="报告文件已过期或被清理，请重新生成")

    media_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return FileResponse(
        path, media_type=media_type,
        filename=f"{t.company_name}_尽调报告.{format}",
    )
