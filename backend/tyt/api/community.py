"""生活圈路由：匿名发帖（先审后发）/ 评论 / 点赞 / 举报"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, get_current_user, get_principal
from tyt.db.mysql import get_db
from tyt.schemas import AbuseReportCreate, ApiResponse, CommentCreate, PostCreate
from tyt.services import community_service, quota_service
from tyt.services.audit_service import log_action

router = APIRouter(prefix="/api/v1/community", tags=["生活圈"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "posts"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
MAX_IMAGE_BYTES = 8 * 1024 * 1024


@router.post("/upload-image", response_model=ApiResponse)
async def upload_image(
    file: UploadFile = File(...),
    principal: Principal = Depends(get_current_user),
):
    """帖子配图上传（登录用户；仅限 jpg/png/webp/gif，单张 ≤ 8MB）"""
    ext = IMAGE_TYPES.get(file.content_type or "")
    if not ext:
        return ApiResponse(code=400, message="仅支持 jpg/png/webp/gif 格式图片")
    data = await file.read()
    if len(data) > MAX_IMAGE_BYTES:
        return ApiResponse(code=400, message="图片不能超过 8MB")
    if not data:
        return ApiResponse(code=400, message="图片内容为空")
    name = f"{uuid.uuid4().hex}.{ext}"
    (UPLOAD_DIR / name).write_bytes(data)
    return ApiResponse(data={"url": f"/uploads/posts/{name}"})


@router.get("/topics", response_model=ApiResponse)
def get_topics(principal: Principal = Depends(get_principal)):
    """话题分类及关键词规则（发帖实时预览用，规则以服务端为准）"""
    return ApiResponse(data={"topics": community_service.TOPICS,
                             "rules": community_service.TOPIC_RULES})


@router.get("/posts", response_model=ApiResponse)
def list_posts(
    category: str = Query("", pattern="^(|avoid_pit|recommend)$"),
    topic: str = Query("", max_length=32, description="话题分类筛选（自动识别）"),
    keyword: str = Query("", max_length=64, description="标题/正文关键词搜索"),
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    data = community_service.list_posts(
        db, page, page_size, category or None, principal.user_id,
        topic or None, keyword or None)
    data["topics"] = community_service.TOPICS
    return ApiResponse(data=data)


@router.post("/posts", response_model=ApiResponse)
def create_post(
    req: PostCreate,
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed, used, limit = quota_service.check_and_consume("post", principal)
    if not allowed:
        return ApiResponse(code=429, message=f"今日发帖次数已用完（限额 {limit} 次/天）")
    ok, msg, post_id = community_service.create_post(db, principal.user_id, req.model_dump())
    if ok:
        log_action(db, principal, "community.post.create", resource=f"post:{post_id}")
    return ApiResponse(code=0 if ok else 400, message=msg, data={"post_id": post_id})


@router.get("/posts/{post_id}", response_model=ApiResponse)
def get_post(
    post_id: int,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    data = community_service.get_post(db, post_id, principal.user_id)
    if not data:
        return ApiResponse(code=404, message="帖子不存在或未过审")
    return ApiResponse(data=data)


@router.post("/posts/{post_id}/like", response_model=ApiResponse)
def like_post(
    post_id: int,
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    liked, count = community_service.toggle_like(db, principal.user_id, post_id)
    if count == 0 and not liked:
        return ApiResponse(code=404, message="帖子不存在")
    return ApiResponse(data={"liked": liked, "like_count": count})


@router.post("/posts/{post_id}/comments", response_model=ApiResponse)
def add_comment(
    post_id: int,
    req: CommentCreate,
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok, msg = community_service.add_comment(db, principal.user_id, post_id, req.model_dump())
    return ApiResponse(code=0 if ok else 400, message=msg)


@router.post("/reports", response_model=ApiResponse)
async def create_report_endpoint(
    req: AbuseReportCreate,
    principal: Principal = Depends(get_principal),
    db: Session = Depends(get_db),
):
    """举报：登录用户与游客均可（游客以 IP 哈希留痕，不留明文）"""
    ok, msg = community_service.create_report(
        db, principal.user_id, principal.ip_hash, req.model_dump())
    if ok:
        log_action(db, principal, "community.report", resource=f"{req.target_type}:{req.target_id}")
    return ApiResponse(code=0 if ok else 400, message=msg)
