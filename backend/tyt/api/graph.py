"""关系图谱路由：懒加载展开 / 路径查询 / 股权穿透（Neo4j + AntV G6 前端渲染）"""
from fastapi import APIRouter, Depends, Query

from tyt.core.rbac import Principal, require_capability
from tyt.schemas import ApiResponse
from tyt.services import graph_service, quota_service
from tyt.services.audit_service import log_action
from tyt.db.mysql import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/biz/graph", tags=["关系图谱"])


@router.get("/nodes/{tyt_id}/expand", response_model=ApiResponse)
def expand_node(
    tyt_id: int,
    limit: int = Query(30, ge=1, le=60),
    principal: Principal = Depends(require_capability("biz.graph")),
    db: Session = Depends(get_db),
):
    """懒加载：展开一个节点的直接关系（前端点击节点时按需加载下一层）"""
    allowed, used, limit_ = quota_service.check_and_consume("biz_graph", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日图谱查询次数已用完（限额 {limit_} 次/天）")
    try:
        data = graph_service.expand_node(tyt_id, limit)
        log_action(db, principal, "biz.graph.expand", detail={"node": tyt_id})
        return ApiResponse(data=data)
    except RuntimeError as e:
        return ApiResponse(code=503, message=f"图谱服务暂不可用：{e}（请稍后重试）")


@router.get("/companies/{company_id}", response_model=ApiResponse)
def company_graph(
    company_id: int,
    principal: Principal = Depends(require_capability("biz.graph")),
    db: Session = Depends(get_db),
):
    """企业一度关系图（详情页图谱快照）"""
    allowed, _, limit_ = quota_service.check_and_consume("biz_graph", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日图谱查询次数已用完（限额 {limit_} 次/天）")
    try:
        return ApiResponse(data=graph_service.company_graph(company_id))
    except RuntimeError as e:
        return ApiResponse(code=503, message=f"图谱服务暂不可用：{e}")


@router.get("/path", response_model=ApiResponse)
def find_path(
    from_id: int = Query(...), to_id: int = Query(...),
    principal: Principal = Depends(require_capability("biz.graph")),
    db: Session = Depends(get_db),
):
    """两节点最短路径（如穿透查询两企业关联）"""
    allowed, _, limit_ = quota_service.check_and_consume("biz_graph", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日图谱查询次数已用完（限额 {limit_} 次/天）")
    try:
        data = graph_service.find_path(from_id, to_id)
        log_action(db, principal, "biz.graph.path", detail={"from": from_id, "to": to_id})
        return ApiResponse(data=data)
    except RuntimeError as e:
        return ApiResponse(code=503, message=f"图谱服务暂不可用：{e}")


@router.get("/companies/{company_id}/controller", response_model=ApiResponse)
def actual_controller(
    company_id: int,
    principal: Principal = Depends(require_capability("biz.graph")),
    db: Session = Depends(get_db),
):
    """股权穿透：疑似实际控制人（有效持股链路推导）"""
    allowed, _, limit_ = quota_service.check_and_consume("biz_graph", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日图谱查询次数已用完（限额 {limit_} 次/天）")
    try:
        return ApiResponse(data=graph_service.actual_controller(company_id))
    except RuntimeError as e:
        return ApiResponse(code=503, message=f"图谱服务暂不可用：{e}")


@router.get("/status", response_model=ApiResponse)
def graph_status(principal: Principal = Depends(require_capability("biz.graph"))):
    return ApiResponse(data={"ready": graph_service.graph_ready()})
