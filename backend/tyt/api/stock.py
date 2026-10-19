"""多智能体股票分析路由：搜索 / 智能体定义 / 大盘指数 / 分析（SSE 流水线）"""
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, require_capability
from tyt.db.mysql import get_db
from tyt.schemas import ApiResponse
from tyt.services import quota_service, stock_service
from tyt.services.audit_service import log_action

router = APIRouter(prefix="/api/v1/biz/stock", tags=["多智能体股票分析"])


class AnalyzeRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=12)


@router.get("/search", response_model=ApiResponse)
def search(keyword: str = "", principal: Principal = Depends(require_capability("biz.stock"))):
    return ApiResponse(data=stock_service.search_stocks(keyword))


@router.get("/agents", response_model=ApiResponse)
def agents(principal: Principal = Depends(require_capability("biz.stock"))):
    return ApiResponse(data=stock_service.AGENTS)


@router.get("/indices", response_model=ApiResponse)
def indices(principal: Principal = Depends(require_capability("biz.stock"))):
    return ApiResponse(data=stock_service.get_indices())


@router.get("/quote/{code}", response_model=ApiResponse)
def quote(code: str, principal: Principal = Depends(require_capability("biz.stock"))):
    detail = stock_service.get_stock_detail(code)
    if not detail:
        return ApiResponse(code=404, message="未找到该证券")
    return ApiResponse(data=detail)


@router.post("/analyze")
async def analyze(req: AnalyzeRequest, principal: Principal = Depends(require_capability("biz.stock")),
                  db: Session = Depends(get_db)):
    if not stock_service.find_stock(req.code):
        return ApiResponse(code=404, message="未找到该证券（仅演示宇宙内代码）")
    allowed, used, limit = quota_service.check_and_consume("stock_analysis", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日多智能体分析次数已用完（限额 {limit} 次/天）")
    log_action(db, principal, "biz.stock.analyze", detail={"code": req.code})

    async def stream():
        try:
            async for event in stock_service.run_pipeline(req.code):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        yield "data: {\"type\": \"eof\"}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
