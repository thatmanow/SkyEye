"""启动预热：后台将本地 Ollama 大模型加载进内存/显存

背景：Ollama 默认在模型空闲 5 分钟后自动卸载，首次调用需现场加载（可达数十秒）。
本模块在服务启动时后台顺序预热全部业务模型（空 prompt + keep_alive 触发加载），
并周期性刷新，保证模型常驻内存、首次请求即达热态。

【预热范围约定】
- 仅预热本地 Ollama 模型（chat / embed / vision），与百炼开关状态无关：
  即使管理员开启百炼（会员走云端生成），本地模型仍保持预热常驻，
  保证百炼不可用降级、普通用户问答、嵌入召回等链路始终热态。
- 百炼云端模型（bailian:qwen-plus）【不做预热】——云端推理无本地加载成本，
  按需 HTTP 调用即可，禁止加入 WARMUP_MODELS。

- 不阻塞 FastAPI 启动：lifespan 中 asyncio.create_task 异步执行
- 顺序加载（chat -> embed -> vision），避免并发加载争抢内存/显存
- Ollama 不可达或模型未安装仅记录告警，下一轮自动重试，绝不影响服务
- 状态可通过 /api/v1/ai/status 的 models 字段观测
"""
import asyncio
import logging
import os
import time
from datetime import datetime

import httpx

from tyt.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL, OLLAMA_VISION_MODEL

logger = logging.getLogger("model-warmup")

KEEP_ALIVE = os.getenv("TYT_OLLAMA_KEEP_ALIVE", "12h")
REFRESH_MINUTES = float(os.getenv("TYT_MODEL_REFRESH_MINUTES", "10"))
LOAD_TIMEOUT = float(os.getenv("TYT_MODEL_LOAD_TIMEOUT", "600"))

# 仅本地模型常驻预热；百炼为云端按需调用，不在此列（见模块 docstring 约定）
WARMUP_MODELS = [
    ("chat", OLLAMA_CHAT_MODEL),
    ("embed", OLLAMA_EMBED_MODEL),
    ("vision", OLLAMA_VISION_MODEL),
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


status: dict = {
    "keep_alive": KEEP_ALIVE,
    "refresh_minutes": REFRESH_MINUTES,
    "started_at": None,
    "last_cycle": None,
    "models": {kind: {"model": model, "state": "pending"} for kind, model in WARMUP_MODELS},
}

_task: asyncio.Task | None = None


def _set(kind: str, state: str, **extra):
    status["models"][kind].update({"state": state, **extra})


async def _installed_models() -> set[str]:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        r.raise_for_status()
        return {m["name"] for m in r.json().get("models", [])}


async def _warmup(kind: str, model: str):
    """空 prompt 请求触发加载；keep_alive 使模型常驻"""
    if kind == "embed":
        method, payload = "/api/embeddings", {"model": model, "prompt": "预热", "keep_alive": KEEP_ALIVE}
    else:
        method, payload = "/api/generate", {"model": model, "prompt": "", "keep_alive": KEEP_ALIVE}
    async with httpx.AsyncClient(timeout=LOAD_TIMEOUT) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}{method}", json=payload)
        r.raise_for_status()


async def _run_cycle():
    try:
        installed = await _installed_models()
    except Exception as e:
        logger.warning("Ollama 不可达，本轮预热跳过（下轮重试）: %s", e)
        for kind, _ in WARMUP_MODELS:
            _set(kind, "unreachable", error=str(e)[:120])
        return

    for kind, model in WARMUP_MODELS:
        if model not in installed:
            _set(kind, "missing")
            logger.warning("模型未安装，跳过预热: %s", model)
            continue
        t0 = time.monotonic()
        try:
            await _warmup(kind, model)
            dt = round(time.monotonic() - t0, 1)
            _set(kind, "loaded", seconds=dt, at=_now())
            logger.info("模型已加载驻留: %s（%.1fs，keep_alive=%s）", model, dt, KEEP_ALIVE)
        except Exception as e:
            _set(kind, "failed", error=str(e)[:200], at=_now())
            logger.warning("模型预热失败 %s: %s", model, e)


async def _loop():
    status["started_at"] = _now()
    logger.info(
        "大模型后台预热启动：%s（刷新周期 %g 分钟）",
        "、".join(m for _, m in WARMUP_MODELS), REFRESH_MINUTES,
    )
    while True:
        await _run_cycle()
        status["last_cycle"] = _now()
        if REFRESH_MINUTES <= 0:
            logger.info("周期刷新已关闭（TYT_MODEL_REFRESH_MINUTES<=0），预热任务退出")
            return
        await asyncio.sleep(REFRESH_MINUTES * 60)


def start() -> asyncio.Task | None:
    """启动后台预热任务（幂等，需在事件循环内调用）"""
    global _task
    if _task and not _task.done():
        return _task
    try:
        _task = asyncio.create_task(_loop())
        logger.info("模型预热任务已提交后台执行")
        return _task
    except RuntimeError:
        logger.warning("无事件循环，跳过模型预热")
        return None


def stop():
    """服务关停时取消预热任务"""
    global _task
    if _task and not _task.done():
        _task.cancel()
    _task = None


def get_status() -> dict:
    import copy
    return copy.deepcopy(status)
