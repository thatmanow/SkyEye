"""仪表盘路由：第一版两爬虫（人民网资讯 / baostock 证券）流式实时窗口"""
import logging

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from tyt.core.rbac import Principal, get_principal
from tyt.schemas import ApiResponse
from tyt.services import crawler_stream_service as svc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["仪表盘"])


@router.get("/crawler-stream")
async def crawler_stream(
    limit: int = Query(20, ge=1, le=500),
    source: str = Query("all", pattern="^(all|people|baostock)$"),
    principal: Principal = Depends(get_principal),
):
    """SSE 流式输出两个爬虫数据源的最新采集记录（游客可访问）"""
    return StreamingResponse(
        svc.stream_events(limit, source),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/crawler-stats", response_model=ApiResponse)
def crawler_stats():
    """两个爬虫库的采集统计"""
    return ApiResponse(data=svc.get_stats())
