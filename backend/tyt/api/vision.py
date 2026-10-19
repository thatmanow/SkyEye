"""AI 识图路由：识别 / 追问（SSE 流式）/ 历史"""
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, get_current_user, require_capability
from tyt.db.mysql import get_db
from tyt.schemas import ApiResponse
from tyt.services import vision_service
from tyt.services import quota_service
from tyt.services.audit_service import log_action

router = APIRouter(prefix="/api/v1/vision", tags=["AI 识图"])


class RecognizeRequest(BaseModel):
    image_base64: str = Field(..., min_length=64, max_length=12_000_000)


class FollowupRequest(BaseModel):
    record_id: int
    question: str = Field(..., min_length=1, max_length=500)


@router.post("/recognize", response_model=ApiResponse)
async def recognize(req: RecognizeRequest, principal: Principal = Depends(require_capability("life.vision")),
                    db: Session = Depends(get_db)):
    allowed, used, limit = quota_service.check_and_consume("vision", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日识图次数已用完（限额 {limit} 次/天）")
    # 模型路由：百炼识图开关开启且用户角色达标（高级会员及以上）走百炼 qwen-vl-ocr；
    # 普通用户始终本地 minicpm-v4.6；百炼失败自动降级本地
    from tyt.core.rbac import get_live_role
    from tyt.services import model_config_service
    role = get_live_role(db, principal.user_id)
    use_bailian = model_config_service.should_use_bailian_vision(role)
    result = await vision_service.recognize(principal.user_id, req.image_base64, use_bailian)
    if not result.get("success"):
        return ApiResponse(code=503, message=result.get("message", "识别失败"))
    log_action(db, principal, "vision.recognize",
               detail={"record_id": result["record_id"], "model": result.get("model")})
    usage = quota_service.get_usage("vision", principal)
    result["quota"] = usage
    return ApiResponse(data=result)


@router.post("/followup")
async def followup(req: FollowupRequest, principal: Principal = Depends(get_current_user)):
    record = vision_service.get_record(req.record_id, principal.user_id)
    if not record:
        return ApiResponse(code=404, message="记录不存在")

    async def stream():
        async for chunk in vision_service.followup(req.record_id, principal.user_id, req.question):
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield 'data: {"done": true}\n\n'

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/records", response_model=ApiResponse)
def records(principal: Principal = Depends(get_current_user)):
    return ApiResponse(data=vision_service.list_records(principal.user_id))


@router.get("/records/{record_id}", response_model=ApiResponse)
def record_detail(record_id: int, principal: Principal = Depends(get_current_user)):
    record = vision_service.get_record(record_id, principal.user_id)
    if not record:
        return ApiResponse(code=404, message="记录不存在")
    return ApiResponse(data=record)


@router.delete("/records/{record_id}", response_model=ApiResponse)
def record_delete(record_id: int, principal: Principal = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    vision_service.delete_record(record_id, principal.user_id)
    log_action(db, principal, "vision.delete", detail={"record_id": record_id})
    return ApiResponse(message="记录已删除")
