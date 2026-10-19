"""模型管理服务：百炼大模型开关（问答 + 识图，管理端可动态切换）+ 模型说明文案

开关状态持久化在 MySQL system_settings 表（key=bailian_enabled / bailian_vision_enabled），
重启不丢失；读取带 5 秒 Redis 缓存，降低每次 AI 问答/识图的查询开销。

路由规则（管理员在平台管理-模型管理中控制）：
- 问答开关关闭：所有用户 AI 问答走本地 qwen2.5:1.5b
- 问答开关开启：角色 >= premium 的用户走百炼 qwen-plus，普通用户始终本地
- 识图开关关闭：所有用户 AI 识图走本地 minicpm-v4.6
- 识图开关开启：角色 >= premium 的用户走百炼 qwen-vl-ocr，普通用户始终本地
- 百炼调用失败：自动降级对应本地模型，保证功能始终可用
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from tyt.config import (
    BAILIAN_MODEL, BAILIAN_BASE_URL, OLLAMA_CHAT_MODEL,
    BAILIAN_VISION_MODEL, OLLAMA_VISION_MODEL, ROLE_NAMES,
)
from tyt.db.redis_client import get_redis
from tyt.models.setting import SystemSetting

logger = logging.getLogger(__name__)

_CACHE_TTL = 5  # 秒；切换开关后最多 5 秒内全局生效

# 普通用户角色集合（永不走百炼）
_NORMAL_ROLES = {"guest", "user"}


def _read_switch(key: str, cache_key: str) -> bool:
    """读取开关（Redis 5s 缓存 -> DB system_settings）"""
    r = get_redis()
    if r is not None:
        try:
            cached = r.get(cache_key)
            if cached is not None:
                return cached == "1"
        except Exception:
            pass
    value = None
    try:
        from tyt.db.mysql import SessionLocal
        with SessionLocal() as db:
            row = db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            ).scalar_one_or_none()
            value = row.value if row else "0"
    except Exception as e:
        logger.warning("read switch %s failed: %s", key, e)
        return False
    enabled = value == "1"
    if r is not None:
        try:
            r.set(cache_key, "1" if enabled else "0", ex=_CACHE_TTL)
        except Exception:
            pass
    return enabled


def _write_switch(key: str, cache_key: str, enabled: bool, label: str) -> None:
    """写入开关（upsert）并立即失效缓存"""
    from tyt.db.mysql import SessionLocal
    with SessionLocal() as db:
        row = db.execute(
            select(SystemSetting).where(SystemSetting.key == key)
        ).scalar_one_or_none()
        if row is None:
            db.add(SystemSetting(key=key, value="1" if enabled else "0"))
        else:
            row.value = "1" if enabled else "0"
        db.commit()
    r = get_redis()
    if r is not None:
        try:
            r.delete(cache_key)
        except Exception:
            pass
    logger.info("%s开关已切换为 %s", label, enabled)


# ==================== 百炼问答开关 ====================

_KEY_BAILIAN = "bailian_enabled"
_CACHE_KEY = "sys:bailian_enabled"


def get_bailian_enabled() -> bool:
    """读取百炼问答开关"""
    return _read_switch(_KEY_BAILIAN, _CACHE_KEY)


def set_bailian_enabled(enabled: bool) -> None:
    """写入百炼问答开关"""
    _write_switch(_KEY_BAILIAN, _CACHE_KEY, enabled, "百炼大模型")


def should_use_bailian(role: str | None) -> bool:
    """该角色本次问答是否走百炼：开关开启 且 角色达到门槛（普通用户始终本地）"""
    if not get_bailian_enabled():
        return False
    if role in _NORMAL_ROLES or role is None:
        return False
    return True


# ==================== 百炼识图开关 ====================

_KEY_BAILIAN_VISION = "bailian_vision_enabled"
_CACHE_KEY_VISION = "sys:bailian_vision_enabled"


def get_bailian_vision_enabled() -> bool:
    """读取百炼识图开关"""
    return _read_switch(_KEY_BAILIAN_VISION, _CACHE_KEY_VISION)


def set_bailian_vision_enabled(enabled: bool) -> None:
    """写入百炼识图开关"""
    _write_switch(_KEY_BAILIAN_VISION, _CACHE_KEY_VISION, enabled, "百炼识图模型")


def should_use_bailian_vision(role: str | None) -> bool:
    """该角色本次识图是否走百炼：开关开启 且 角色达到门槛（普通用户始终本地）"""
    if not get_bailian_vision_enabled():
        return False
    if role in _NORMAL_ROLES or role is None:
        return False
    return True


# ==================== 模型说明文案（管理端展示 + 问答返回的 model 元信息） ====================

BAILIAN_NAME = f"百炼 {BAILIAN_MODEL}"
LOCAL_NAME = f"本地 {OLLAMA_CHAT_MODEL}"

MODEL_INTRO = {
    "bailian": {
        "name": BAILIAN_NAME,
        "provider": "阿里云百炼（DashScope）",
        "model": BAILIAN_MODEL,
        "endpoint": BAILIAN_BASE_URL,
        "title": "百炼大模型（云端）",
        "intro": "阿里云百炼平台的大语言模型，通过 OpenAI 兼容接口接入，"
                 "参数规模与知识容量远超本地模型，理解与生成质量更高，适合对回答质量要求高的会员用户。",
        "pros": [
            "中文理解与长文本能力强，回答更准确、更有条理",
            "支持联网知识与时事内容，不受本地知识截止限制",
            "云端弹性算力，推理速度快且稳定，不受本机负载影响",
            "平台统一管控 API Key，数据经脱敏后上传，隐私字段不外传",
        ],
        "cons": ["依赖外部网络与百炼服务可用性", "按调用量计费（平台承担）"],
        "apply_scope": "开关开启后：高级会员 / 企业管理员 / 平台管理员的 AI 问答",
    },
    "local": {
        "name": LOCAL_NAME,
        "provider": "本地 Ollama",
        "model": OLLAMA_CHAT_MODEL,
        "endpoint": "本机 Ollama 服务",
        "title": "本地大模型 qwen2.5:1.5b（默认）",
        "intro": "部署在本机 Ollama 上的通义千问 1.5B 轻量模型，是平台的默认问答引擎。"
                 "数据全程不出本机，零调用成本，作为百炼不可用时的自动降级兜底。",
        "pros": [
            "数据全程本地推理，隐私与合规性最好",
            "零 API 成本，不依赖外部网络",
            "1.5B 轻量参数，CPU 即可运行，启动快占用低",
            "配合 RAG（bge 向量召回 + rerank 精排）弥补小模型知识不足",
        ],
        "cons": ["参数规模小，复杂推理与长文生成能力弱于云端大模型", "受本机算力影响，高峰期可能变慢"],
        "apply_scope": "所有用户的默认引擎；普通用户 AI 问答仅使用该模型",
    },
}


def get_model_config() -> dict:
    """管理端模型配置总览（问答/识图开关状态 + 各模型讲解 + 生效规则）"""
    enabled = get_bailian_enabled()
    vision_enabled = get_bailian_vision_enabled()
    return {
        "bailian_enabled": enabled,
        "bailian_vision_enabled": vision_enabled,
        "min_role": "premium",
        "min_role_name": ROLE_NAMES.get("premium", "高级会员"),
        "models": MODEL_INTRO,
        "vision_models": VISION_MODEL_INTRO,
        "rule": (
            "开关开启：高级会员及以上角色的 AI 问答使用百炼大模型，"
            "百炼不可用时自动降级本地模型；普通用户无论开关状态，始终使用本地 qwen2.5:1.5b。"
            "开关关闭：所有用户均使用本地模型。"
        ),
        "vision_rule": (
            "识图开关开启：高级会员及以上角色的 AI 识图使用百炼云端 qwen-vl-ocr，"
            "百炼不可用或返回不可解析时自动降级本地 minicpm-v4.6；"
            "普通用户无论开关状态，始终使用本地 minicpm-v4.6:latest。识图开关关闭：所有用户均使用本地识图模型。"
        ),
    }


# ==================== AI 识图模型说明文案 ====================

VISION_MODEL_INTRO = {
    "bailian_vision": {
        "name": f"百炼 {BAILIAN_VISION_MODEL}",
        "provider": "阿里云百炼（DashScope）",
        "model": BAILIAN_VISION_MODEL,
        "endpoint": BAILIAN_BASE_URL,
        "title": "百炼云端识图 qwen-vl-ocr",
        "intro": "阿里云百炼平台的视觉语言模型，专注图像文字识别（OCR）与视觉理解，"
                 "通过 OpenAI 兼容多模态接口接入，对票据、文档、截图中文字的识别精度显著优于本地小模型。",
        "pros": [
            "OCR 能力强：票据 / 证照 / 文档 / 截图中的文字识别精度高",
            "云端大参数视觉模型，复杂场景与低质量图片理解更好",
            "云端弹性算力，识别速度快且稳定，不受本机负载影响",
            "识别失败或返回不可解析时自动降级本地模型，功能始终可用",
        ],
        "cons": ["图片需上传至百炼云端处理", "依赖外部网络与百炼服务可用性", "按调用量计费（平台承担）"],
        "apply_scope": "识图开关开启后：高级会员 / 企业管理员 / 平台管理员的 AI 识图",
    },
    "local_vision": {
        "name": f"本地 {OLLAMA_VISION_MODEL}",
        "provider": "本地 Ollama",
        "model": OLLAMA_VISION_MODEL,
        "endpoint": "本机 Ollama 服务",
        "title": "本地识图模型 minicpm-v4.6:latest（默认）",
        "intro": "部署在本机 Ollama 上的 MiniCPM-V 多模态模型，是平台的默认识图引擎。"
                 "图片全程不出本机，零调用成本，作为百炼识图不可用时的自动降级兜底。",
        "pros": [
            "图片全程本地推理，不离开设备，隐私与合规性最好",
            "零 API 成本，不依赖外部网络",
            "支持识别结果多轮追问（流式），体验连贯",
            "JSON 结构化输出 + 残缺结果自动修复，识别稳定",
        ],
        "cons": ["小参数模型，复杂票据 / 模糊图片识别精度弱于云端", "受本机算力影响，高峰期可能变慢"],
        "apply_scope": "所有用户的默认识图引擎；普通用户 AI 识图仅使用该模型",
    },
}
