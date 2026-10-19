"""AI 问答路由（RAG 多路召回：bge 向量召回 + jieba 关键词召回 -> RRF 融合
-> bge-reranker 精排 -> 百炼 qwen-plus / 本地 qwen2.5:1.5b 生成）

问答为异步任务模式：POST /ai/chat 提交后立即返回 task_id，
RAG 全链路在后台线程池执行（不阻塞事件循环），前端轮询 GET /ai/chat/tasks/{id} 获取回答。
"""
import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, require_capability
from tyt.db.mysql import SessionLocal, get_db
from tyt.models.ai import AIChatHistory, AIChatTask
from tyt.schemas import ApiResponse
from tyt.services import ai_service, quota_service
from tyt.services import model_warmup, knowledge_sync_service
from tyt.services.audit_service import log_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI 问答"])


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=500)


# 后台问答协程的强引用（防止被 GC 中断）
_bg_tasks: set[asyncio.Task] = set()


async def _run_rag_task(task_id: int, question: str, user_id: int):
    """后台执行 RAG 问答：阻塞推理丢线程池跑，完成后更新任务状态并写入历史"""
    db = SessionLocal()
    try:
        task = db.get(AIChatTask, task_id)
        if not task:
            logger.error("ai chat task %s not found", task_id)
            return
        task.status = "running"
        db.commit()
        try:
            # 模型路由：百炼开关开启且用户角色达标（高级会员及以上）走百炼；普通用户始终本地 qwen2.5:1.5b
            from tyt.core.rbac import get_live_role
            from tyt.services import model_config_service
            role = get_live_role(db, user_id) if user_id is not None else None
            use_bailian = model_config_service.should_use_bailian(role)
            data = await asyncio.to_thread(ai_service.rag_answer, question, use_bailian)
            task.result_json = json.dumps(data, ensure_ascii=False)
            task.status, task.finished_at = "done", datetime.now()
            db.commit()
            # 完成后按用户落历史（与旧同步链路保持一致）
            if user_id is not None:
                db.add(AIChatHistory(
                    user_id=user_id,
                    question=question,
                    answer=data.get("answer", ""),
                    references_json=json.dumps(data.get("references") or [], ensure_ascii=False),
                    model=data.get("model"),
                ))
                db.commit()
        except Exception as e:
            logger.exception("ai chat task %s failed", task_id)
            task.status, task.error = "failed", str(e)
            task.finished_at = datetime.now()
            db.commit()
    finally:
        db.close()


@router.post("/chat", response_model=ApiResponse)
async def chat(req: ChatRequest, principal: Principal = Depends(require_capability("ai.chat")),
               db: Session = Depends(get_db)):
    """异步问答：提交问题立即返回 task_id，回答在后台生成，前端轮询获取"""
    allowed, used, limit = quota_service.check_and_consume("ai_chat", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日 AI 问答次数已用完（限额 {limit} 次/天）")
    task = AIChatTask(user_id=principal.user_id, question=req.question, status="queued")
    db.add(task)
    db.commit()
    log_action(db, principal, "ai.chat", detail={"q_len": len(req.question), "task_id": task.id})
    t = asyncio.create_task(_run_rag_task(task.id, req.question, principal.user_id))
    _bg_tasks.add(t)
    t.add_done_callback(_bg_tasks.discard)
    return ApiResponse(message="问题已提交，正在后台生成回答",
                       data={"task_id": task.id, "status": "queued"})


@router.get("/chat/tasks/{task_id}", response_model=ApiResponse)
def chat_task_status(task_id: int, principal: Principal = Depends(require_capability("ai.chat")),
                     db: Session = Depends(get_db)):
    """轮询问答任务状态：done 时返回完整回答（answer/references/模型/相似度阈值）"""
    task = db.get(AIChatTask, task_id)
    if not task or task.user_id != principal.user_id:
        return ApiResponse(code=404, message="任务不存在")
    data = {"task_id": task.id, "status": task.status, "question": task.question}
    if task.status == "done" and task.result_json:
        try:
            result = json.loads(task.result_json)
        except (ValueError, TypeError):
            result = None
        if isinstance(result, dict):
            data.update(result)
    if task.status == "failed":
        data["error"] = task.error
    return ApiResponse(data=data)


@router.get("/history", response_model=ApiResponse)
def chat_history(principal: Principal = Depends(require_capability("ai.chat")),
                 limit: int = Query(50, ge=1, le=200),
                 db: Session = Depends(get_db)):
    """当前用户的历史问答（按用户隔离，倒序）"""
    if principal.user_id is None:
        return ApiResponse(data={"items": []})
    rows = db.execute(
        select(AIChatHistory)
        .where(AIChatHistory.user_id == principal.user_id)
        .order_by(AIChatHistory.created_at.desc(), AIChatHistory.id.desc())
        .limit(limit)
    ).scalars().all()
    return ApiResponse(data={"items": [r.to_dict() for r in rows]})


@router.delete("/history/{history_id}", response_model=ApiResponse)
def delete_history(history_id: int, principal: Principal = Depends(require_capability("ai.chat")),
                   db: Session = Depends(get_db)):
    row = db.get(AIChatHistory, history_id)
    if row is None or row.user_id != principal.user_id:
        return ApiResponse(code=404, message="记录不存在")
    db.delete(row)
    db.commit()
    return ApiResponse(message="已删除")


@router.delete("/history", response_model=ApiResponse)
def clear_history(principal: Principal = Depends(require_capability("ai.chat")),
                  db: Session = Depends(get_db)):
    db.execute(delete(AIChatHistory).where(AIChatHistory.user_id == principal.user_id))
    db.commit()
    return ApiResponse(message="已清空历史")


@router.get("/status", response_model=ApiResponse)
def ai_status(principal: Principal = Depends(require_capability("ai.chat")),
              db: Session = Depends(get_db)):
    import httpx
    from tyt.config import OLLAMA_BASE_URL, RERANK_URL, OLLAMA_VISION_MODEL, BAILIAN_VISION_MODEL
    ollama_ok = False
    rerank_ok = False
    try:
        ollama_ok = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3).status_code == 200
    except Exception:
        pass
    try:
        rerank_ok = httpx.get(f"{RERANK_URL}/health", timeout=3).status_code == 200
    except Exception:
        pass
    # 与问答/识图链路同一路由规则：百炼开关开启且角色达标 -> 百炼，否则本地模型
    from tyt.core.rbac import get_live_role
    from tyt.services import model_config_service
    try:
        role = get_live_role(db, principal.user_id)
        use_bailian = model_config_service.should_use_bailian(role)
        use_bailian_vision = model_config_service.should_use_bailian_vision(role)
    except Exception:
        use_bailian = False
        use_bailian_vision = False
    effective_model = (f"bailian:{ai_service.BAILIAN_MODEL}" if use_bailian
                       else ai_service.OLLAMA_CHAT_MODEL)
    effective_vision_model = (f"bailian:{BAILIAN_VISION_MODEL}" if use_bailian_vision
                              else OLLAMA_VISION_MODEL)
    return ApiResponse(data={"ollama": ollama_ok, "rerank": rerank_ok,
                             "chat_model": effective_model,
                             "use_bailian": use_bailian,
                             "vision_model": effective_vision_model,
                             "use_bailian_vision": use_bailian_vision,
                             "models": model_warmup.get_status(),
                             "knowledge": knowledge_sync_service.get_status()})
