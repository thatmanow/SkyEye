"""AI 识图服务：百炼云端 qwen-vl-ocr（会员） / 本地 Ollama MiniCPM-V 推理

链路：图片 base64 -> 模型生成 -> 结构化 JSON 解析（多级兜底）
- 百炼开关开启且角色达标：走云端 qwen-vl-ocr（OpenAI 兼容多模态），
  调用失败或解析失败自动降级本地 minicpm-v4.6
- 普通用户 / 开关关闭：始终本地 minicpm-v4.6:latest（图片不离开设备）
追问：图片 + 识别结果 + 多轮历史 -> /api/chat 流式输出（始终本地）
"""
import json
import logging
import re
from datetime import datetime
from typing import AsyncGenerator

import httpx
from sqlalchemy import delete, select

from tyt.config import (
    OLLAMA_BASE_URL, OLLAMA_VISION_MODEL,
    BAILIAN_BASE_URL, BAILIAN_VISION_API_KEY, BAILIAN_VISION_MODEL,
)
from tyt.db.mysql import SessionLocal
from tyt.models.vision import VisionRecord

logger = logging.getLogger(__name__)

RECOGNIZE_PROMPT = (
    "请仔细识别这张图片，输出结构化 JSON 结果。字段如下：\n"
    '- "name": 图片主体/场景的精炼中文名称（1-15字，必须中文）\n'
    '- "category": 所属类别，必须从以下列表中选择一个：'
    '动物|植物|食物|风景|建筑|人物|商品|文档|截图|艺术|交通工具|电子产品|服饰|其他\n'
    '- "tags": 3-8 个关键特征标签（中文字符串数组）\n'
    '- "key_elements": 图片中的关键元素/细节描述（字符串数组，每项一句话，中文）\n'
    '- "confidence": 你对识别结果的整体置信度（0-1 的小数）\n'
    '- "description": 100-250 字的综合中文描述，涵盖主体、环境、色彩、构图等\n'
    "务必包含所有字段。category 必须从给定列表选择，不得自创。只输出 JSON。"
)


def _iter_json_objects(text: str):
    """按花括号配对扫描文本中的所有顶层 JSON 对象（跳过字符串内的花括号）"""
    depth = 0
    start = None
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    yield text[start:i + 1]


def _repair_json_text(text: str) -> str:
    """修复模型常见的残缺 JSON：键名缺左引号（如 {name": ...）、全角引号、尾逗号等"""
    # {"name": 缺失左引号 -> {"name":   （兼容 ,key": 形式）
    text = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*":)', r'\1"\2\3', text)
    # 全角引号转半角
    text = text.replace("“", '"').replace("”", '"')
    # 去掉对象/数组末尾的悬挂逗号
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text


def _parse_recognize_result(raw: str) -> dict:
    """从模型返回文本解析结构化结果，兼容代码块/前后杂文/思考文本中夹杂的多段 JSON"""
    if not raw:
        return {}
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        body = text[start:end + 1]
        for candidate in (body, _repair_json_text(body)):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
    # 兜底：思考型模型可能先输出多段不完整 JSON 再给最终结果，从后往前取第一个可解析对象
    for candidate in reversed(list(_iter_json_objects(text))):
        for fixed in (candidate, _repair_json_text(candidate)):
            try:
                parsed = json.loads(fixed)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and any(k in parsed for k in ("name", "category", "description")):
                return parsed
    return {}


async def _vision_generate(prompt: str, image_b64: str) -> str:
    """调用本地 Ollama 视觉模型（非流式）；think=False 关闭思考模式，避免推理文本混入结果。

    format="json" 强制 Ollama 以合法 JSON 约束输出——MiniCPM-V 偶发输出残缺 JSON
    （如 {name": 少引号），曾导致识别结果全部落入默认值（前端表现为"没有输出"）。
    """
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json={
            "model": OLLAMA_VISION_MODEL,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "think": False,
            "format": "json",
            "options": {"temperature": 0.3},
        })
        resp.raise_for_status()
        return resp.json().get("response", "")


async def _vision_generate_bailian(prompt: str, image_b64: str) -> str:
    """调用百炼云端识图模型 qwen-vl-ocr（DashScope OpenAI 兼容多模态，实测支持自定义 Prompt 且可返回 JSON）。

    失败抛异常，由调用方降级本地 minicpm-v4.6；图片经 data URL 内联上传，不落地。
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{BAILIAN_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {BAILIAN_VISION_API_KEY}"},
            json={
                "model": BAILIAN_VISION_MODEL,
                "messages": [{"role": "user", "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                    {"type": "text", "text": prompt},
                ]}],
                "temperature": 0.3,
                "max_tokens": 1500,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


async def _recognize_with_local(prompt: str, raw_b64: str) -> tuple[str, dict]:
    """本地链路：生成 + 解析 + 解析失败自动重试一次。返回 (原始文本, 解析结果)"""
    raw_text = await _vision_generate(prompt, raw_b64)
    result = _parse_recognize_result(raw_text)
    if not result:
        # 解析失败（模型偶发输出非 JSON）自动重试一次，避免整次识别落入默认空结果
        logger.warning("vision parse failed, retry once; raw=%r", raw_text[:200])
        raw_text = await _vision_generate(prompt, raw_b64)
        result = _parse_recognize_result(raw_text)
    return raw_text, result


async def _recognize_with_bailian(prompt: str, raw_b64: str) -> tuple[str, dict]:
    """百炼链路：云端生成 + 解析；调用失败或解析为空抛异常，由调用方降级本地"""
    raw_text = await _vision_generate_bailian(prompt, raw_b64)
    result = _parse_recognize_result(raw_text)
    if not result and raw_text.strip():
        # qwen-vl-ocr 偏 OCR 场景，可能输出非 JSON 的纯文本识别结果——
        # 将文本整理为结构化结果（首行作名称，行内容作标签/描述），不粗暴降级
        lines = [ln.strip() for ln in raw_text.strip().splitlines() if ln.strip()]
        result = {
            "name": lines[0][:15] if lines else "",
            "tags": lines[1:6],
            "key_elements": lines[:5],
            "description": " ".join(lines)[:1200],
            "confidence": 0.8,
        }
    if not result:
        raise ValueError(f"百炼识图返回无法解析：{raw_text[:120]!r}")
    return raw_text, result


async def recognize(user_id: int, image_base64: str, use_bailian: bool = False) -> dict:
    """图片识别主入口：调用模型 + 解析 + 落库

    use_bailian=True（百炼识图开关开启且角色达标）走云端 qwen-vl-ocr，
    调用失败 / 解析失败自动降级本地 minicpm-v4.6:latest；普通用户始终本地。
    """
    raw_b64 = image_base64.split(",", 1)[1] if "," in image_base64 else image_base64

    used_model = OLLAMA_VISION_MODEL
    try:
        if use_bailian:
            try:
                raw_text, result = await _recognize_with_bailian(RECOGNIZE_PROMPT, raw_b64)
                used_model = f"bailian:{BAILIAN_VISION_MODEL}"
            except Exception as e:
                # 百炼不可用 / 返回不可解析：降级本地 minicpm-v4.6:latest
                logger.warning("bailian vision failed, fallback to local %s: %s", OLLAMA_VISION_MODEL, e)
                raw_text, result = await _recognize_with_local(RECOGNIZE_PROMPT, raw_b64)
                used_model = f"{OLLAMA_VISION_MODEL}(bailian降级)"
        else:
            raw_text, result = await _recognize_with_local(RECOGNIZE_PROMPT, raw_b64)
    except Exception as e:
        logger.error("vision generate failed: %s", e)
        return {"success": False, "message": f"识别引擎不可用：{e}"}

    name = str(result.get("name") or "").strip()[:120] or "识别完成"
    category = str(result.get("category") or "").strip()[:30]
    tags = result.get("tags") or []
    if isinstance(tags, str):
        # 模型可能把 tags 输出成 "几何|色彩|图案" 一类分隔字符串
        tags = [t.strip() for t in re.split(r"[|、,，;；/]", tags) if t.strip()]
    if not isinstance(tags, list):
        tags = [str(tags)]
    tags = [str(t)[:24] for t in tags[:8]]
    key_elements = result.get("key_elements") or []
    if not isinstance(key_elements, list):
        key_elements = [str(key_elements)]
    key_elements = [str(e)[:120] for e in key_elements[:6]]
    description = str(result.get("description") or "").strip()
    if not description and raw_text and not raw_text.lstrip().startswith(("{", "```")):
        description = raw_text.strip()[:1200]
    try:
        confidence = float(result.get("confidence", 0.7))
        if confidence > 1.0:
            # 模型偶发输出 0-100 制（如 9.0 表示 90%），归一到 0-1
            confidence = confidence / 100.0 if confidence > 10 else confidence / 10.0
        confidence = max(0.0, min(1.0, confidence))
    except (TypeError, ValueError):
        confidence = 0.7

    if not key_elements and description:
        sentences = re.split(r"[。；！？\n]", description)
        key_elements = [s.strip() for s in sentences if len(s.strip()) >= 5][:5]

    with SessionLocal() as db:
        record = VisionRecord(
            user_id=user_id, image_b64=raw_b64, result_name=name, category=category,
            tags_json=json.dumps(tags, ensure_ascii=False),
            key_elements_json=json.dumps(key_elements, ensure_ascii=False),
            confidence=confidence, description=description,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        record_id = record.id

    return {
        "success": True, "record_id": record_id, "name": name, "category": category,
        "tags": tags, "key_elements": key_elements, "confidence": confidence,
        "description": description, "image_url": f"data:image/jpeg;base64,{raw_b64}",
        "model": used_model,
    }


async def followup(record_id: int, user_id: int, question: str) -> AsyncGenerator[str, None]:
    """基于图片与识别结果的多轮追问（流式）"""
    with SessionLocal() as db:
        record = db.execute(
            select(VisionRecord).where(VisionRecord.id == record_id, VisionRecord.user_id == user_id)
        ).scalar_one_or_none()
        if not record:
            yield "未找到对应的识别记录"
            return
        image_b64 = record.image_b64
        context = (
            f"之前识别结果：{record.result_name}（置信度 {round(record.confidence, 2)}）。"
            f"描述：{record.description}。"
        )
        try:
            history = json.loads(record.chat_history or "[]")
        except (TypeError, json.JSONDecodeError):
            history = []

    messages = [
        {"role": "system", "content": "你是天眼通 AI 识图助手，擅长基于图片进行多轮中文问答，回答简洁准确。"},
        {"role": "user", "content": context, "images": [image_b64]},
        {"role": "assistant", "content": "好的，我已了解这张图片的内容，请提问。"},
    ]
    for msg in history[-16:]:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": question})

    full_answer = ""
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/chat", json={
                "model": OLLAMA_VISION_MODEL, "messages": messages, "stream": True, "think": False,
            }) as resp:
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        full_answer += content
                        yield content
                    if chunk.get("done"):
                        break
    except Exception as e:
        yield f"回答生成失败：{e}"
        return

    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": full_answer})
    with SessionLocal() as db:
        db.execute(
            VisionRecord.__table__.update()
            .where(VisionRecord.id == record_id)
            .values(chat_history=json.dumps(history[-40:], ensure_ascii=False))
        )
        db.commit()


def list_records(user_id: int, limit: int = 50) -> list[dict]:
    with SessionLocal() as db:
        rows = db.execute(
            select(VisionRecord).where(VisionRecord.user_id == user_id)
            .order_by(VisionRecord.created_at.desc()).limit(limit)
        ).scalars().all()
        return [r.to_dict() for r in rows]


def get_record(record_id: int, user_id: int) -> dict | None:
    with SessionLocal() as db:
        record = db.execute(
            select(VisionRecord).where(VisionRecord.id == record_id, VisionRecord.user_id == user_id)
        ).scalar_one_or_none()
        return record.to_dict(with_image=True) if record else None


def delete_record(record_id: int, user_id: int) -> bool:
    with SessionLocal() as db:
        db.execute(delete(VisionRecord).where(
            VisionRecord.id == record_id, VisionRecord.user_id == user_id))
        db.commit()
    return True
