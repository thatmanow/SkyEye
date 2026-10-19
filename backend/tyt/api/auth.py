"""认证路由：注册 / 登录 / 刷新 / 登出 / 个人信息 / 头像"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Header, UploadFile, File
from sqlalchemy.orm import Session

from tyt.core.rbac import Principal, get_current_user, get_principal
from tyt.db.mysql import get_db
from tyt.models import User
from tyt.schemas import (
    ApiResponse, LoginRequest, PasswordChangeRequest, RegisterRequest, RefreshRequest,
)
from tyt.services import auth_service, quota_service
from tyt.services.audit_service import log_action

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

AVATAR_DIR = Path(__file__).resolve().parents[2] / "uploads" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
AVATAR_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
AVATAR_MAX_BYTES = 2 * 1024 * 1024  # 与第一版一致：头像 ≤ 2MB


@router.post("/register", response_model=ApiResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if req.password != req.confirm_password:
        return ApiResponse(code=400, message="两次输入的密码不一致")
    if not req.agree:
        return ApiResponse(code=400, message="请阅读并同意《用户协议》与《隐私政策》")
    ok, msg, data = auth_service.register(db, req.account, req.nickname, req.password)
    return ApiResponse(code=0 if ok else 400, message=msg, data=data)


@router.post("/login", response_model=ApiResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    ok, msg, data = auth_service.login(db, req.account, req.password)
    return ApiResponse(code=0 if ok else 401, message=msg, data=data)


@router.post("/refresh", response_model=ApiResponse)
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    ok, msg, data = auth_service.refresh(db, req.refresh_token)
    return ApiResponse(code=0 if ok else 401, message=msg, data=data)


@router.post("/logout", response_model=ApiResponse)
def logout(
    authorization: str = Header(default=""),
    refresh_token: str = Header(default="", alias="X-Refresh-Token"),
):
    token = authorization.replace("Bearer ", "")
    auth_service.logout(token, refresh_token or None)
    return ApiResponse(message="已退出登录")


@router.get("/me", response_model=ApiResponse)
def me(principal: Principal = Depends(get_current_user), db: Session = Depends(get_db)):
    info = auth_service.get_user_info(db, principal.user_id)
    if not info:
        return ApiResponse(code=401, message="用户不存在")
    quotas = {qt: quota_service.get_usage(qt, principal)
              for qt in ("life_query", "biz_basic", "biz_risk", "biz_graph", "report", "ai_chat", "post")}
    return ApiResponse(data={"user": info, "quotas": quotas})


@router.put("/avatar", response_model=ApiResponse)
async def update_avatar(
    file: UploadFile = File(...),
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改自己的头像（所有登录用户；仅限 jpg/png/webp/gif，≤ 2MB，保存后替换旧头像文件）"""
    ext = AVATAR_TYPES.get(file.content_type or "")
    if not ext:
        return ApiResponse(code=400, message="仅支持 jpg/png/webp/gif 格式图片")
    data = await file.read()
    if len(data) > AVATAR_MAX_BYTES:
        return ApiResponse(code=400, message="头像图片不能超过 2MB")
    if not data:
        return ApiResponse(code=400, message="头像图片内容为空")

    user = db.get(User, principal.user_id)
    if not user:
        return ApiResponse(code=401, message="用户不存在")

    # 保存新头像并替换数据库记录；旧头像文件属于本服务托管目录时同步清理
    old_avatar = user.avatar
    name = f"{uuid.uuid4().hex}.{ext}"
    (AVATAR_DIR / name).write_bytes(data)
    user.avatar = f"/uploads/avatars/{name}"
    db.commit()
    if old_avatar and old_avatar.startswith("/uploads/avatars/"):
        old_file = AVATAR_DIR / Path(old_avatar).name
        if old_file.exists() and old_file.name != name:
            old_file.unlink(missing_ok=True)
    log_action(db, principal, "auth.avatar.update")
    return ApiResponse(message="头像更新成功", data={"avatar": user.avatar})


@router.put("/password", response_model=ApiResponse)
def change_password(
    req: PasswordChangeRequest,
    principal: Principal = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ok, msg = auth_service.change_password(db, principal.user_id, req.old_password, req.new_password)
    if ok:
        log_action(db, principal, "auth.password.change")
    return ApiResponse(code=0 if ok else 400, message=msg)


@router.get("/guest-info", response_model=ApiResponse)
def guest_info(principal: Principal = Depends(get_principal)):
    """游客配额信息（未登录也可查看）"""
    quotas = {qt: quota_service.get_usage(qt, principal)
              for qt in ("life_query", "biz_basic", "biz_risk", "biz_graph")}
    return ApiResponse(data={"role": principal.role, "quotas": quotas})
