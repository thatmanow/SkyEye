"""AI 问答服务（RAG 多路召回）：Ollama qwen2.5:1.5b / 百炼 qwen-plus 对话 + bge-large-zh 嵌入
+ Qdrant 向量库 + jieba 关键词 + bge-reranker 重排

召回链路（多路召回 + RRF 融合）：
  路径1  向量语义召回：问题 -> bge 嵌入 -> Qdrant COSINE 检索 Top8
  路径2  关键词召回：问题 -> jieba 分词 -> 知识库全文本地关键词评分 Top8（60s 语料缓存）
  融合   RRF（Reciprocal Rank Fusion，k=60）合并去重 -> 融合 Top8
  精排   bge-reranker-v2-m3 精排 Top5 -> 相似度过滤(≥0.6)
  生成   百炼 qwen-plus（会员，失败降级）或 本地 qwen2.5:1.5b

降级策略：无 jieba/关键词为空 -> 仅向量路；无 rerank -> 按 RRF 融合序直出；
无 Qdrant -> 纯模型问答；百炼不可用 -> 本地 qwen2.5:1.5b。
"""
import json
import logging
import math
import time
import uuid
from datetime import datetime

import httpx

from tyt.config import (
    OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, OLLAMA_EMBED_MODEL,
    RERANK_URL, QDRANT_DIR, QDRANT_COLLECTION,
    BAILIAN_API_KEY, BAILIAN_BASE_URL, BAILIAN_MODEL,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是「天眼通」平台的智能助理，帮助用户查询企业工商信息、风险信息与生活避坑建议。"
    "回答必须基于提供的参考资料；若资料不足，明确说明并建议用户使用平台查询功能。"
    "你不得编造企业数据、风险记录或司法文书；涉及个人隐私的信息一律拒绝提供。"
    "回答使用简体中文，条理清晰，使用 Markdown 格式组织内容："
    "关键信息用 **加粗** 强调，多条内容用要点列表分条陈述，最多分 2-4 个小节。"
    "回答保持简洁（300 字以内），严禁重复相同或相近的内容。"
)


def _ollama(method: str, payload: dict, timeout: float = 60.0) -> dict:
    r = httpx.post(f"{OLLAMA_BASE_URL}{method}", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def embed(text: str) -> list[float] | None:
    try:
        resp = _ollama("/api/embeddings", {"model": OLLAMA_EMBED_MODEL, "prompt": text}, timeout=30)
        return resp.get("embedding")
    except Exception as e:
        logger.warning("embed failed: %s", e)
        return None


def chat(prompt: str, context_docs: list[str] | None = None) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context_docs:
        ctx = "\n\n".join(f"【参考资料{i+1}】{d}" for i, d in enumerate(context_docs))
        messages.append({"role": "system", "content": f"以下是与问题相关的平台数据参考资料：\n{ctx}"})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = _ollama("/api/chat", {
            "model": OLLAMA_CHAT_MODEL, "messages": messages, "stream": False,
            # repeat_penalty 抑制小模型复读循环；num_predict 限制篇幅防止失控
            "options": {"temperature": 0.4, "repeat_penalty": 1.15, "num_predict": 600},
        })
        return resp["message"]["content"]
    except Exception as e:
        logger.error("ollama chat failed: %s", e)
        return f"AI 服务暂时不可用：{e}"


def chat_bailian(prompt: str, context_docs: list[str] | None = None) -> str:
    """调用阿里云百炼大模型（DashScope OpenAI 兼容模式）生成回答。

    失败时抛异常，由调用方降级本地 qwen2.5:1.5b，保证问答始终可用。
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context_docs:
        ctx = "\n\n".join(f"【参考资料{i+1}】{d}" for i, d in enumerate(context_docs))
        messages.append({"role": "system", "content": f"以下是与问题相关的平台数据参考资料：\n{ctx}"})
    messages.append({"role": "user", "content": prompt})
    try:
        resp = httpx.post(
            f"{BAILIAN_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {BAILIAN_API_KEY}"},
            json={"model": BAILIAN_MODEL, "messages": messages,
                  "temperature": 0.4, "max_tokens": 1024},
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error("bailian chat failed: %s", e)
        raise


def rerank(query: str, documents: list[str], top_n: int = 3) -> list[tuple[int, float]]:
    """调用 bge-reranker-v2-m3 重排服务（127.0.0.1:9999，接口经 openapi.json 验证）。
    分数为 sigmoid 归一化的 0-1 相似度；服务不可用时返回空列表，由调用方降级。"""
    if not documents:
        return []
    try:
        r = httpx.post(f"{RERANK_URL}/rerank", json={
            "query": query, "documents": documents, "top_n": min(top_n, len(documents)),
        }, timeout=30)
        r.raise_for_status()
        results = r.json().get("results", [])
        return [(item["index"], float(item["score"])) for item in results]
    except Exception as e:
        logger.warning("rerank unavailable, fallback to recall order: %s", e)
        return []


# ==================== Qdrant 知识库 ====================
# 本地持久化模式：QdrantClient(path=QDRANT_DIR)，数据落盘于 database/tyt_qdrant，
# 无需独立 Qdrant 服务进程。向量以 COSINE 距离检索，与原 Chroma 召回语义一致。
# Qdrant 点位 id 仅支持 uint / UUID，故将字符串 doc_id 经 uuid5 确定性映射为 UUID，
# 并在 payload 中保留原始 _id 以便反向定位。

_QDRANT = None
_UUID_NS = uuid.UUID("a1b2c3d4-e5f6-4789-8abc-def012345678")


def _to_point_id(doc_id: str) -> str:
    return str(uuid.uuid5(_UUID_NS, doc_id))


def _get_client():
    global _QDRANT
    if _QDRANT is not None:
        return _QDRANT
    try:
        from qdrant_client import QdrantClient
        _QDRANT = QdrantClient(path=QDRANT_DIR)
        return _QDRANT
    except Exception as e:
        logger.warning("qdrant unavailable: %s", e)
        return None


def _collection_ready(client) -> bool:
    try:
        return client.collection_exists(QDRANT_COLLECTION)
    except Exception:
        return False


def _ensure_collection(client, vector_size: int) -> bool:
    """首次入库时按真实向量维度创建集合（bge-large-zh-v1.5 = 1024 维）"""
    try:
        if client.collection_exists(QDRANT_COLLECTION):
            return True
        from qdrant_client.models import Distance, VectorParams
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        return True
    except Exception as e:
        logger.warning("qdrant create collection failed: %s", e)
        return False


def _scroll_all(client, scroll_filter=None, with_payload: bool = True):
    """分页拉取集合内全部点位（绕过单次上限），返回点位列表"""
    points = []
    offset = None
    while True:
        batch, offset = client.scroll(
            collection_name=QDRANT_COLLECTION, scroll_filter=scroll_filter,
            limit=500, offset=offset, with_payload=with_payload, with_vectors=False,
        )
        points.extend(batch)
        if offset is None:
            break
    return points


def upsert_knowledge(doc_id: str, text: str, metadata: dict | None = None) -> bool:
    """知识入库（爬虫资讯/证券行情/企业卡片向量化）

    将文本、元数据与向量一并写入 Qdrant；payload 中额外保存 _id 以保留原始文档标识。
    """
    client = _get_client()
    if client is None:
        return False
    vec = embed(text)
    if not vec:
        return False
    try:
        if not _ensure_collection(client, len(vec)):
            return False
        from qdrant_client.models import PointStruct
        payload = {"_id": doc_id, "text": text}
        payload.update(metadata or {})
        client.upsert(collection_name=QDRANT_COLLECTION, points=[
            PointStruct(id=_to_point_id(doc_id), vector=vec, payload=payload)
        ])
        _invalidate_kb_cache()
        return True
    except Exception as e:
        logger.warning("qdrant upsert failed: %s", e)
        return False


def existing_kb_ids(ids: list[str]) -> set[str]:
    """查询知识库中已存在的文档 id（增量入库用）"""
    client = _get_client()
    if client is None or not ids:
        return set()
    if not _collection_ready(client):
        return set()
    try:
        point_ids = [_to_point_id(i) for i in ids]
        points = client.retrieve(
            collection_name=QDRANT_COLLECTION, ids=point_ids,
            with_payload=True, with_vectors=False,
        )
        return {p.payload.get("_id") for p in points if p.payload}
    except Exception as e:
        logger.warning("qdrant get failed: %s", e)
        return set()


CRAWLER_KINDS = ("people_article", "baostock_quote")
MANUAL_KIND = "manual"


def purge_crawler_knowledge() -> int:
    """清空爬虫来源的知识文档（人民网资讯 / baostock 行情），返回删除条数。

    爬虫数据每日更新、文章可能撤稿下架；旧文档留在向量库会被 RAG 检索到，
    导致 AI 引用失效链接或过期行情，因此每日一清后重新入库最新数据。

    关键约束（白名单 + 防御性过滤，双重保险）：
    仅删除 kind ∈ CRAWLER_KINDS 的文档；手动录入（kind=manual）、
    企业卡片（kind=company_card）以及任何未识别 kind（含缺失）的文档一律保留，
    绝不允许日切清理误删管理员手动录入的知识。
    """
    client = _get_client()
    if client is None or not _collection_ready(client):
        return 0
    try:
        from qdrant_client.models import (
            Filter, FieldCondition, MatchAny, PointIdsList,
        )
        f = Filter(must=[FieldCondition(
            key="kind", match=MatchAny(any=list(CRAWLER_KINDS)))])
        pts = _scroll_all(client, scroll_filter=f, with_payload=True)
        # 防御性再过滤：仅当 payload.kind 确实属于爬虫来源才删除，
        # 杜绝过滤边界 case / 未来新增加密或非爬虫 kind 被误删
        delete_ids = [p.id for p in pts
                      if (p.payload or {}).get("kind") in CRAWLER_KINDS]
        if delete_ids:
            client.delete(collection_name=QDRANT_COLLECTION,
                          points_selector=PointIdsList(points=delete_ids))
            _invalidate_kb_cache()
        logger.info("知识库日切清理：删除爬虫文档 %d 条（手动录入/企业卡片等保留）",
                    len(delete_ids))
        return len(delete_ids)
    except Exception as e:
        logger.warning("qdrant purge failed: %s", e)
        return 0


def count_knowledge(kind: str | None = None) -> int:
    """统计知识库文档数（按 kind 过滤），用于日切清理后汇报保留项"""
    client = _get_client()
    if client is None or not _collection_ready(client):
        return 0
    try:
        total = 0
        for p in _scroll_all(client, with_payload=True):
            k = (p.payload or {}).get("kind")
            if kind is None or k == kind:
                total += 1
        return total
    except Exception as e:
        logger.warning("qdrant count failed: %s", e)
        return 0


def kb_stats() -> dict:
    """知识库文档统计（按 kind 分组）"""
    client = _get_client()
    if client is None or not _collection_ready(client):
        return {"total": 0, "by_kind": {}, "available": False}
    try:
        by_kind: dict[str, int] = {}
        total = 0
        for p in _scroll_all(client, with_payload=True):
            kind = (p.payload or {}).get("kind", "other")
            by_kind[kind] = by_kind.get(kind, 0) + 1
            total += 1
        return {"total": total, "by_kind": by_kind, "available": True}
    except Exception as e:
        logger.warning("qdrant stats failed: %s", e)
        return {"total": 0, "by_kind": {}, "available": False}


KIND_NAMES = {
    "people_article": "人民网资讯",
    "baostock_quote": "baostock 行情",
    "company_card": "企业卡片",
    "manual": "手动录入",
}


def list_knowledge(kind: str | None = None, keyword: str | None = None,
                   page: int = 1, page_size: int = 10) -> dict:
    """管理端知识库文档列表：kind 筛选 + 标题/正文关键词 + 分页（按类型/标题稳定排序）

    Qdrant 本地模式不依赖服务端全文索引，关键词检索在 Python 端对 text/title 做包含判断，
    知识库规模小（数百~数千条），全量拉取过滤开销可忽略。
    """
    client = _get_client()
    if client is None or not _collection_ready(client):
        return {"items": [], "total": 0, "available": False}
    try:
        entries = []
        for p in _scroll_all(client, with_payload=True):
            meta = p.payload or {}
            k = meta.get("kind", "other")
            if kind and k != kind:
                continue
            text = meta.get("text", "")
            title = meta.get("title") or ""
            if keyword and keyword not in text and keyword not in title:
                continue
            entries.append((k, title, p.id, meta, text))
        entries.sort(key=lambda e: (e[0], e[1]))
        total = len(entries)
        start = (page - 1) * page_size
        items: list[dict] = []
        for k, title, pid, meta, text in entries[start:start + page_size]:
            items.append({
                "id": meta.get("_id") or str(pid),
                "kind": k,
                "kind_name": KIND_NAMES.get(k, k),
                "title": title or text[:40],
                "source": meta.get("source") or "--",
                "url": meta.get("url"),
                "excerpt": text[:160],
            })
        return {"items": items, "total": total, "available": True}
    except Exception as e:
        logger.warning("qdrant list failed: %s", e)
        return {"items": [], "total": 0, "available": False}


def delete_knowledge(doc_id: str) -> bool:
    """删除单条知识文档（爬虫来源文档会在下次同步时按最新数据重建）"""
    client = _get_client()
    if client is None or not _collection_ready(client):
        return False
    try:
        from qdrant_client.models import PointIdsList
        client.delete(collection_name=QDRANT_COLLECTION,
                      points_selector=PointIdsList(points=[_to_point_id(doc_id)]))
        _invalidate_kb_cache()
        return True
    except Exception as e:
        logger.warning("qdrant delete failed: %s", e)
        return False


def add_manual_knowledge(title: str, text: str, url: str | None = None) -> str | None:
    """管理员手动录入知识文档（kind=manual，不参与每日自动清理）"""
    import hashlib
    doc_id = "manual:" + hashlib.md5(f"{title}|{text}".encode("utf-8")).hexdigest()[:16]
    meta = {"kind": "manual", "title": title, "source": "管理员手动录入"}
    if url:
        meta["url"] = url
    if upsert_knowledge(doc_id, text, meta):
        return doc_id
    return None


# 参考来源相似度阈值：低于该值的召回文档不进入生成上下文与来源展示
SIM_THRESHOLD = 0.6

# 关键词召回语料缓存 TTL（秒）：知识库规模小（数百~数千条），全量拉取后本地评分
_KB_CACHE_TTL = 60.0
_KB_CACHE: list[dict] | None = None
_KB_CACHE_AT: float = 0.0

# RRF 融合常数（标准值 60）：rank 越靠前贡献越大，两路命中同一文档分数叠加
RRF_K = 60


def _invalidate_kb_cache():
    """知识库写入/删除/清空后失效关键词召回语料缓存"""
    global _KB_CACHE
    _KB_CACHE = None


def _load_kb_corpus() -> list[dict]:
    """全量拉取知识库语料（带 60s 缓存），供关键词召回路径评分使用"""
    global _KB_CACHE, _KB_CACHE_AT
    now = time.monotonic()
    if _KB_CACHE is not None and now - _KB_CACHE_AT < _KB_CACHE_TTL:
        return _KB_CACHE
    corpus: list[dict] = []
    client = _get_client()
    if client is not None and _collection_ready(client):
        try:
            for p in _scroll_all(client, with_payload=True):
                meta = p.payload or {}
                corpus.append({
                    "id": meta.get("_id") or str(p.id),
                    "text": meta.get("text", ""),
                    "title": meta.get("title") or "",
                    "meta": {k: v for k, v in meta.items() if k not in ("text", "_id")},
                })
        except Exception as e:
            logger.warning("kb corpus load failed: %s", e)
    _KB_CACHE, _KB_CACHE_AT = corpus, now
    return corpus


def _keywords(question: str) -> list[str]:
    """jieba 分词提取关键词：去停用词/单字，去重保序"""
    import jieba
    jieba.setLogLevel(logging.WARNING)
    words = [w.strip() for w in jieba.lcut(question) if len(w.strip()) >= 2]
    return list(dict.fromkeys(words))


def _recall_vector(question: str, top_k: int = 8) -> list[dict]:
    """路径1 向量语义召回：bge 嵌入 + Qdrant COSINE 检索

    返回 [{"id", "text", "meta", "vec_sim"}, ...]，vec_sim 为召回阶段余弦相似度。
    """
    client = _get_client()
    out: list[dict] = []
    if client is None or not _collection_ready(client):
        return out
    qvec = embed(question)
    if not qvec:
        return out
    try:
        res = client.query_points(collection_name=QDRANT_COLLECTION,
                                  query=qvec, limit=top_k,
                                  with_payload=True, with_vectors=True)
        for p in (res.points or []):
            payload = p.payload or {}
            vec = p.vector
            out.append({
                "id": payload.get("_id") or str(p.id),
                "text": payload.get("text", ""),
                "meta": {k: v for k, v in payload.items() if k not in ("text", "_id")},
                "vec_sim": _cosine(qvec, vec) if vec else 0.0,
            })
    except Exception as e:
        logger.warning("qdrant query failed: %s", e)
    return out


def _recall_keyword(question: str, top_k: int = 8) -> list[tuple[int, dict]]:
    """路径2 关键词召回：jieba 分词 -> 语料关键词命中数评分

    返回 [(命中次数, {"id", "text", "meta"}), ...]，按命中数降序。
    jieba 不可用时返回空列表（仅向量路召回）。
    """
    try:
        kws = _keywords(question)
    except Exception as e:
        logger.warning("jieba unavailable, keyword recall skipped: %s", e)
        return []
    if not kws:
        return []
    scored: list[tuple[int, dict]] = []
    for doc in _load_kb_corpus():
        hay = f"{doc['title']}\n{doc['text']}"
        hits = sum(hay.count(k) for k in kws)
        if hits > 0:
            scored.append((hits, doc))
    scored.sort(key=lambda x: -x[0])
    return scored[:top_k]


def _fuse(vector_hits: list[dict], keyword_hits: list[tuple[int, dict]],
          top_k: int = 8) -> list[dict]:
    """RRF 融合两路召回并去重：score = Σ 1/(k + rank)，k=60

    双路同时命中的文档分数叠加，天然偏向"语义相似且关键词命中"的高置信文档。
    返回融合排序后的候选列表（附 rrf 分数与 kw_hits 命中次数）。
    """
    scores: dict[str, float] = {}
    cands: dict[str, dict] = {}
    for rank, h in enumerate(vector_hits):
        scores[h["id"]] = scores.get(h["id"], 0.0) + 1.0 / (RRF_K + rank + 1)
        cands[h["id"]] = h
    for rank, (hits, doc) in enumerate(keyword_hits):
        cid = doc["id"]
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + rank + 1)
        if cid not in cands:
            cands[cid] = {"id": cid, "text": doc["text"], "meta": doc["meta"],
                          "vec_sim": None, "kw_hits": hits}
        else:
            cands[cid]["kw_hits"] = hits
    ranked_ids = sorted(scores, key=lambda i: -scores[i])[:top_k]
    return [{**cands[i], "rrf": round(scores[i], 6)} for i in ranked_ids]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def rag_answer(question: str, use_bailian: bool = False) -> dict:
    """RAG 多路召回主链路：向量召回 + 关键词召回 -> RRF 融合 Top8 -> 精排 Top5
    -> 相似度过滤(≥0.6) -> 生成，引用带相似度与原文链接。

    use_bailian=True 时（百炼开关开启且用户角色达标）走百炼生成，失败自动降级本地 qwen2.5:1.5b。
    降级链：无 jieba/无关键词 -> 仅向量路；无 rerank -> 按 RRF 融合序直出（关键词独有命中
    无精排分数，similarity 置空不参与阈值过滤）；无 Qdrant -> 纯模型问答。
    """
    # ---- 多路召回（并行语义：两路独立打分，互不依赖） ----
    vector_hits = _recall_vector(question, top_k=8)
    keyword_hits = _recall_keyword(question, top_k=8)
    fused = _fuse(vector_hits, keyword_hits, top_k=8)

    docs = [f["text"] for f in fused]
    metas = [f["meta"] for f in fused]

    # ---- 精排 + 相似度过滤 ----
    context_docs: list[str] = []
    references: list[dict] = []
    if docs:
        ranked = rerank(question, docs, top_n=5)
        if ranked:
            scored = [(i, score) for i, score in ranked]  # 精排分数（sigmoid 0-1）
            scored.sort(key=lambda x: x[1], reverse=True)
        else:
            # 降级：RRF 融合序直出；向量路有真实相似度，关键词独有命中置 None
            scored = [(i, fused[i].get("vec_sim")) for i in range(len(docs))]
        for i, score in scored:
            if score is not None and score < SIM_THRESHOLD:
                continue
            meta = metas[i] if i < len(metas) else {}
            context_docs.append(docs[i])
            references.append({
                "title": meta.get("title") or docs[i][:60],
                "url": meta.get("url"),
                "source": meta.get("source") or "平台知识库",
                "similarity": round(score, 4) if score is not None else None,
            })

    # ---- 生成（百炼失败自动降级本地） ----
    used_model = OLLAMA_CHAT_MODEL
    if use_bailian:
        try:
            answer = chat_bailian(question, context_docs=context_docs or None)
            used_model = f"bailian:{BAILIAN_MODEL}"
        except Exception:
            # 百炼不可用，降级本地 qwen2.5:1.5b
            answer = chat(question, context_docs=context_docs or None)
            used_model = f"{OLLAMA_CHAT_MODEL}(bailian降级)"
    else:
        answer = chat(question, context_docs=context_docs or None)
    return {
        "answer": answer,
        "references": references,
        "model": used_model,
        "recall": {
            "paths": ["vector", "keyword"],
            "vector": len(vector_hits),
            "keyword": len(keyword_hits),
            "fused": len(fused),
        },
        "reranker": "bge-reranker-v2-m3",
        "similarity_threshold": SIM_THRESHOLD,
        "answered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
