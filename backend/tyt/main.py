"""天眼通 FastAPI 应用入口

启动：cd backend && uvicorn tyt.main:app --host 0.0.0.0 --port 8000
文档：http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import update

from tyt.api import admin, ai, auth, biz, billing, community, graph, lead, life, monitor, notification, report
from tyt.api import dashboard, stock, vision, weather
from tyt.db.mysql import ping as mysql_ping, engine
from tyt.db.neo4j_client import neo4j_available
from tyt.db.redis_client import get_redis
from tyt.db import es_client
from tyt.models.ai import AIChatTask
from tyt.services import model_warmup
from tyt.services import knowledge_sync_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("tyt")

WEB_DIST = Path(__file__).resolve().parents[2] / "web" / "dist"

# 用户上传文件目录（生活圈帖子配图等）
UPLOADS_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    deps = {
        "mysql": mysql_ping(),
        "redis": get_redis() is not None,
        "neo4j": neo4j_available(),
        "elasticsearch": es_client.es_available(),
    }
    logger.info("服务依赖状态: %s", deps)
    if not deps["mysql"]:
        logger.error("MySQL 不可用！请先启动 MySQL（root/123456，库 SkyEye2.0）")
    # 重启兜底：上次服务停止时遗留的运行中 AI 问答任务标记为失败（前端轮询可感知）
    try:
        with engine.begin() as conn:
            conn.execute(update(AIChatTask).where(AIChatTask.status.in_(["queued", "running"]))
                         .values(status="failed", error="服务重启导致任务中断，请重新提问",
                                 finished_at=datetime.now()))
    except Exception as e:
        logger.warning("清理遗留 AI 问答任务失败（表未初始化时忽略）: %s", e)
    # 后台预热大模型（chat/embed/vision 顺序加载进内存，不阻塞启动）
    model_warmup.start()
    # 后台将爬虫资讯/证券行情向量化入 Qdrant 知识库（等嵌入模型就绪后执行）
    knowledge_sync_service.start()
    yield
    knowledge_sync_service.stop()
    model_warmup.stop()
    engine.dispose()


app = FastAPI(
    title="天眼通 API",
    description="Web 信息查询与风险洞察平台 —— 生活类帮普通人避坑，商业类帮企业做尽调；"
                "所有数据来源公开、合法、可溯源。",
    version="2.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 统一错误响应格式 {code, message}
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"code": exc.status_code, "message": str(exc.detail)})


# ===== API 路由 =====
# 上传静态资源须注册在 SPA 回退路由（下方 catch-all）之前
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.include_router(auth.router)
app.include_router(billing.router)
app.include_router(notification.router)
app.include_router(life.router)
app.include_router(community.router)
app.include_router(biz.router)
app.include_router(graph.router)
app.include_router(monitor.router)
app.include_router(report.router)
app.include_router(lead.router)
app.include_router(admin.router)
app.include_router(ai.router)
app.include_router(vision.router)
app.include_router(weather.router)
app.include_router(stock.router)
app.include_router(dashboard.router)


@app.get("/api/health", tags=["健康检查"])
async def health():
    return {
        "status": "ok", "app": "天眼通 TianYanTong",
        "deps": {
            "mysql": mysql_ping(),
            "redis": get_redis() is not None,
            "neo4j": neo4j_available(),
            "elasticsearch": es_client.es_available(),
        },
    }


# ===== 前端静态托管（Vue3 构建产物；开发期由 Vite 5173 端口代理） =====
if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="web-assets")

    # index.html 每次重新校验，避免重新构建后浏览器用缓存旧文档请求已删除的旧 chunk 导致白屏；
    # /assets 资源文件名带哈希，可放心长缓存
    NO_CACHE_HEADERS = {"Cache-Control": "no-cache"}

    @app.get("/", include_in_schema=False)
    async def spa_index():
        return FileResponse(WEB_DIST / "index.html", headers=NO_CACHE_HEADERS)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """SPA 路由回退：非 API、非静态文件的路径全部返回 index.html"""
        if full_path.startswith(("api/", "assets/", "docs", "openapi.json")):
            return JSONResponse(status_code=404, content={"code": 404, "message": "Not Found"})
        target = WEB_DIST / full_path
        if target.is_file():
            return FileResponse(target, headers=NO_CACHE_HEADERS)
        return FileResponse(WEB_DIST / "index.html", headers=NO_CACHE_HEADERS)
