"""管理端路由：内容审核 / 用户管理 / 数据维护 / 审计与采集日志 / 数据看板 / AI 知识库管理 / 模型管理"""
import logging

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, require_capability, invalidate_role_cache
from tyt.db.mysql import get_db
from tyt.models import (
    AuditLog, CollectLog, Company, DataSource, Lead, MerchantReview,
    Post, PostComment, Complaint, ReportRecord, RiskRecord, User,
)
from tyt.schemas import (
    ApiResponse, AuditActionRequest, ImportRequest,
    KbAddDocumentRequest, UserRoleUpdateRequest, UserStatusUpdateRequest,
    ViolationWordsUpdateRequest,
)
from tyt.services import ai_service, community_service, company_service, knowledge_sync_service
from tyt.services import import_service, model_config_service
from tyt.services import violation_service, kb_import_service
from tyt.services.audit_service import log_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["平台管理"])


# ==================== 内容审核 ====================

# ==================== 违规标准与违规扫描 ====================

@router.get("/audit/violation-words", response_model=ApiResponse)
def get_violation_words(principal: Principal = Depends(require_capability("admin.audit")),
                        db: Session = Depends(get_db)):
    """违规标准词库：当前启用词条（带分类）+ 第一版预设标准（供勾选）+ 分类列表"""
    items = violation_service.get_word_items(db)
    return ApiResponse(data={
        "words": [i["word"] for i in items],
        "items": items,
        "presets": violation_service.PRESET_WORDS,
        "categories": violation_service.CATEGORIES,
    })


@router.get("/audit/pending", response_model=ApiResponse)
def pending_overview(principal: Principal = Depends(require_capability("admin.audit")),
                     db: Session = Depends(get_db)):
    return ApiResponse(data=community_service.pending_audit_items(db))


@router.get("/audit/{content_type}", response_model=ApiResponse)
def list_pending(content_type: str,
                 principal: Principal = Depends(require_capability("admin.audit")),
                 db: Session = Depends(get_db),
                 page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    if content_type not in ("post", "comment", "review", "complaint", "report"):
        return ApiResponse(code=400, message="content_type 非法")
    return ApiResponse(data=community_service.list_pending(db, content_type, page, page_size))


@router.post("/audit/{content_type}/{item_id}", response_model=ApiResponse)
def audit_item(content_type: str, item_id: int, req: AuditActionRequest,
               principal: Principal = Depends(require_capability("admin.audit")),
               db: Session = Depends(get_db)):
    if content_type not in ("post", "comment", "review", "complaint", "report"):
        return ApiResponse(code=400, message="content_type 非法")
    ok, msg = community_service.audit_action(
        db, principal.user_id, content_type, item_id, req.action, req.reason)
    if ok:
        log_action(db, principal, f"admin.audit.{req.action}",
                   resource=f"{content_type}:{item_id}", detail={"reason": req.reason})
    return ApiResponse(code=0 if ok else 400, message=msg)


# ==================== 违规标准与违规扫描 ====================

@router.put("/audit/violation-words", response_model=ApiResponse)
def update_violation_words(req: ViolationWordsUpdateRequest,
                           principal: Principal = Depends(require_capability("admin.audit")),
                           db: Session = Depends(get_db)):
    """更新违规标准词库（全量替换），立即对后续待审列表生效；items 带分类，words 兼容旧格式"""
    items = [i.model_dump() for i in req.items] if req.items else list(req.words)
    if not items:
        return ApiResponse(code=400, message="违规标准不能为空，至少保留一个词")
    count = violation_service.set_words(db, items)
    log_action(db, principal, "admin.audit.violation_words",
               detail={"count": count, "words": [i["word"] for i in items[:50]]
                       if req.items else req.words[:50]})
    return ApiResponse(message=f"违规标准已更新（{count} 个词）", data={"count": count})


@router.post("/audit/violation-scan", response_model=ApiResponse)
def violation_scan(principal: Principal = Depends(require_capability("admin.audit")),
                   db: Session = Depends(get_db)):
    """违规扫描：对 5 类全部待审内容按当前违规标准检测，返回统计与命中明细"""
    return ApiResponse(data=violation_service.scan_pending(db))


# ==================== 用户管理 ====================

@router.get("/users", response_model=ApiResponse)
def list_users(
    keyword: str = Query(""), role: str = Query(""), status: str = Query(""),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    principal: Principal = Depends(require_capability("admin.users")),
    db: Session = Depends(get_db),
):
    base = select(User)
    if keyword:
        base = base.where(User.account.like(f"%{keyword}%") | User.nickname.like(f"%{keyword}%"))
    if role:
        base = base.where(User.role == role)
    if status:
        base = base.where(User.status == status)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = db.execute(
        base.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    items = [{
        "id": u.id, "account": u.account[:3] + "****" + u.account[-4:] if u.account.isdigit() else u.account,
        "nickname": u.nickname, "role": u.role, "status": u.status,
        "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else None,
        "last_login_at": u.last_login_at.strftime("%Y-%m-%d %H:%M") if u.last_login_at else None,
    } for u in rows]
    return ApiResponse(data={"total": total, "items": items})


@router.put("/users/{user_id}/role", response_model=ApiResponse)
def update_role(user_id: int, req: UserRoleUpdateRequest,
                principal: Principal = Depends(require_capability("admin.users")),
                db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        return ApiResponse(code=404, message="用户不存在")
    if u.id == principal.user_id:
        return ApiResponse(code=400, message="不能修改自己的角色")
    u.role = req.role
    db.commit()
    invalidate_role_cache(u.id)
    log_action(db, principal, "admin.user.role", resource=f"user:{user_id}",
               detail={"role": req.role})
    return ApiResponse(message=f"已将用户角色调整为 {req.role}")


@router.put("/users/{user_id}/status", response_model=ApiResponse)
def update_status(user_id: int, req: UserStatusUpdateRequest,
                  principal: Principal = Depends(require_capability("admin.users")),
                  db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        return ApiResponse(code=404, message="用户不存在")
    if u.id == principal.user_id:
        return ApiResponse(code=400, message="不能封禁自己")
    u.status = req.status
    db.commit()
    invalidate_role_cache(u.id)
    log_action(db, principal, "admin.user.status", resource=f"user:{user_id}",
               detail={"status": req.status})
    return ApiResponse(message="已封禁该账号" if req.status == "banned" else "已解封该账号")


# ==================== 数据维护（导入 / 数据源 / 采集日志） ====================

@router.get("/data/sources", response_model=ApiResponse)
def list_sources(principal: Principal = Depends(require_capability("admin.dataops")),
                 db: Session = Depends(get_db)):
    rows = db.execute(select(DataSource).order_by(DataSource.id)).scalars().all()
    return ApiResponse(data={"items": [s.to_dict() for s in rows]})


@router.post("/data/import", response_model=ApiResponse)
def import_data(req: ImportRequest,
                principal: Principal = Depends(require_capability("admin.dataops")),
                db: Session = Depends(get_db)):
    """CSV 导入（先审后入库；来源必须为已登记合法渠道）"""
    ok, msg, count = import_service.import_csv(
        db, principal.user_id, req.source_code, req.entity, req.csv_content)
    return ApiResponse(code=0 if ok else 400, message=msg, data={"imported": count})


@router.get("/data/collect-logs", response_model=ApiResponse)
def collect_logs(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    principal: Principal = Depends(require_capability("admin.dataops")),
    db: Session = Depends(get_db),
):
    base = select(CollectLog)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = db.execute(
        base.order_by(CollectLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return ApiResponse(data={"total": total, "items": [r.to_dict() for r in rows]})


@router.get("/audit-logs", response_model=ApiResponse)
def audit_logs(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    principal: Principal = Depends(require_capability("admin.users")),
    db: Session = Depends(get_db),
):
    base = select(AuditLog)
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = db.execute(
        base.order_by(AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return ApiResponse(data={"total": total, "items": [r.to_dict() for r in rows]})


# ==================== 数据看板（企业管理员 / 平台管理员） ====================

@router.get("/dashboard", response_model=ApiResponse)
def dashboard(principal: Principal = Depends(require_capability("biz.dashboard")),
              db: Session = Depends(get_db)):
    """数据看板：平台统计 + 风险分布 + 待办"""
    stats = {
        "total_companies": db.execute(select(func.count()).select_from(Company)).scalar() or 0,
        "total_users": db.execute(select(func.count()).select_from(User)).scalar() or 0,
        "total_risks": db.execute(select(func.count()).select_from(RiskRecord)).scalar() or 0,
        "total_leads": db.execute(select(func.count()).select_from(Lead)).scalar() or 0,
        "pending_posts": db.execute(
            select(func.count()).select_from(Post).where(Post.status == "pending")).scalar() or 0,
        "pending_reviews": db.execute(
            select(func.count()).select_from(MerchantReview).where(MerchantReview.status == "pending")).scalar() or 0,
        "pending_complaints": db.execute(
            select(func.count()).select_from(Complaint).where(Complaint.status == "pending")).scalar() or 0,
        "pending_abuse_reports": db.execute(
            select(func.count()).select_from(ReportRecord).where(ReportRecord.status == "pending")).scalar() or 0,
        "pending_comments": db.execute(
            select(func.count()).select_from(PostComment).where(PostComment.status == "pending")).scalar() or 0,
    }
    risk_dist = dict(db.execute(
        select(RiskRecord.risk_type, func.count()).group_by(RiskRecord.risk_type)
    ).all())
    role_dist = dict(db.execute(
        select(User.role, func.count()).group_by(User.role)
    ).all())
    return ApiResponse(data={"stats": stats, "risk_dist": risk_dist, "role_dist": role_dist})


# ==================== AI 知识库管理（平台管理员） ====================

@router.get("/kb/documents", response_model=ApiResponse)
def kb_documents(
    kind: str = Query("", description="空=全部 / people_article / baostock_quote / manual"),
    keyword: str = Query(""),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100),
    principal: Principal = Depends(require_capability("admin.kb")),
):
    """AI 问答知识库文档列表（分页）"""
    data = ai_service.list_knowledge(kind or None, keyword or None, page, page_size)
    data["stats"] = ai_service.kb_stats()
    data["sync"] = knowledge_sync_service.get_status()
    return ApiResponse(data=data)


@router.post("/kb/documents", response_model=ApiResponse)
def kb_add_document(
    req: KbAddDocumentRequest,
    principal: Principal = Depends(require_capability("admin.kb")),
    db: Session = Depends(get_db),
):
    """手动录入知识文档（向量化后立即生效，不参与每日自动清理）"""
    doc_id = ai_service.add_manual_knowledge(req.title, req.content, req.url or None)
    if not doc_id:
        return ApiResponse(code=500, message="入库失败：嵌入模型或向量库不可用")
    log_action(db, principal, "admin.kb.add", resource=doc_id, detail={"title": req.title})
    return ApiResponse(message="知识文档已入库", data={"doc_id": doc_id})


@router.delete("/kb/documents/{doc_id}", response_model=ApiResponse)
def kb_delete_document(
    doc_id: str,
    principal: Principal = Depends(require_capability("admin.kb")),
    db: Session = Depends(get_db),
):
    """删除单条知识文档（爬虫来源文档会在下次同步时按最新数据重建）"""
    if not ai_service.delete_knowledge(doc_id):
        return ApiResponse(code=400, message="删除失败：文档不存在或向量库不可用")
    log_action(db, principal, "admin.kb.delete", resource=doc_id)
    return ApiResponse(message="已删除")


@router.post("/kb/resync", response_model=ApiResponse)
async def kb_resync(principal: Principal = Depends(require_capability("admin.kb"))):
    """手动触发：清空爬虫来源知识 -> 重新同步最新采集数据（后台执行）"""
    if not knowledge_sync_service.start_manual_resync():
        return ApiResponse(code=409, message="同步任务正在执行中，请稍后再试")
    return ApiResponse(message="已开始后台同步，稍后刷新列表查看进度")


@router.post("/kb/documents/import", response_model=ApiResponse)
async def kb_import_document(
    file: UploadFile = File(...),
    title: str = Form(""),
    principal: Principal = Depends(require_capability("admin.kb")),
    db: Session = Depends(get_db),
):
    """导入文档（txt/md/csv/docx/pdf/xlsx/html）自动提取文本并切分入库（kind=manual）

    服务端按扩展名解析文本（利用已装 pypdf/python-docx/openpyxl/bs4，无需额外依赖），
    按段落/句子切分为若干片段，每段作为一条手动知识入库；手动知识不参与每日爬虫清理。
    title 留空时自动识别（首行 / 文件名）。
    """
    data = await file.read()
    if not data:
        return ApiResponse(code=400, message="文件内容为空")
    if len(data) > kb_import_service.MAX_BYTES:
        return ApiResponse(code=400, message="文件不能超过 20MB")
    try:
        result = kb_import_service.import_document(
            file.filename or "未命名文档", data, title_hint=title or None)
    except ValueError as e:
        return ApiResponse(code=400, message=str(e))
    except Exception as e:
        logger.warning("文档导入失败: %s", e)
        return ApiResponse(code=500, message=f"文档解析失败：{e}")
    if result.get("imported", 0) == 0:
        return ApiResponse(code=400, message="未能从文档中提取到有效文本，请检查文件内容")
    log_action(db, principal, "admin.kb.import",
               detail={"filename": file.filename, "imported": result["imported"]})
    return ApiResponse(
        message=(f"已导入 {result['imported']} 条知识（切分 {result['chunks']} 段，"
                 f"来源：{file.filename}）"),
        data=result,
    )


class ModelConfigUpdateRequest(BaseModel):
    bailian_enabled: bool | None = Field(None, description="百炼问答大模型开关")
    bailian_vision_enabled: bool | None = Field(None, description="百炼识图模型开关（qwen-vl-ocr）")


@router.get("/ai/model-config", response_model=ApiResponse)
def get_model_config(principal: Principal = Depends(require_capability("admin.models"))):
    """模型管理总览：问答/识图百炼开关状态 + 各模型讲解 + 生效规则"""
    return ApiResponse(data=model_config_service.get_model_config())


@router.put("/ai/model-config", response_model=ApiResponse)
def update_model_config(req: ModelConfigUpdateRequest,
                        principal: Principal = Depends(require_capability("admin.models")),
                        db: Session = Depends(get_db)):
    """切换百炼问答 / 识图开关（即时全局生效，普通用户不受影响始终走本地模型）"""
    if req.bailian_enabled is None and req.bailian_vision_enabled is None:
        return ApiResponse(code=400, message="至少提供一个开关字段（bailian_enabled / bailian_vision_enabled）")
    messages = []
    details = {"action": "bailian_toggle"}
    if req.bailian_enabled is not None:
        model_config_service.set_bailian_enabled(req.bailian_enabled)
        messages.append(f"百炼大模型已{'开启' if req.bailian_enabled else '关闭'}")
        details["bailian_enabled"] = req.bailian_enabled
    if req.bailian_vision_enabled is not None:
        model_config_service.set_bailian_vision_enabled(req.bailian_vision_enabled)
        messages.append(f"百炼识图模型（{model_config_service.VISION_MODEL_INTRO['bailian_vision']['model']}）"
                        f"已{'开启' if req.bailian_vision_enabled else '关闭'}")
        details["bailian_vision_enabled"] = req.bailian_vision_enabled
    log_action(db, principal, "admin.models", detail=details)
    return ApiResponse(message="；".join(messages),
                       data=model_config_service.get_model_config())
