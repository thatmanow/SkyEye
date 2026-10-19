"""爬虫知识入库：第一版两个爬虫库的采集内容向量化进 Qdrant，供 AI 问答 RAG 检索

- 人民网资讯：标题 + 正文摘录（350 字）入库，metadata.url 指向人民网原文（可点击跳转）
- baostock 重点池：最新行情快照入库，metadata.url 指向 baostock 官网
- 启动后台执行：等 bge 嵌入模型预热完成后再同步；按文档 id 幂等，已入库条目跳过
- 每日一清（Redis 日切标记 tyt:ai:kb:purge_date）：仅清空爬虫来源文档（人民网资讯 /
  baostock 行情）后重新入库最新数据，防止爬虫信息更新/撤稿后 AI 引用失效内容产生错误问答。
  手动录入（kind=manual）与企业卡片（kind=company_card）等管理员维护的知识不参与清理，
  始终保留，避免人工知识被误删。
- 向量存储后端为 Qdrant（本地持久化），详见 tyt/services/ai_service.py
"""
import asyncio
import hashlib
import logging
import threading
import time
from datetime import date, datetime

from tyt.db.redis_client import get_redis
from tyt.services import ai_service, model_warmup
from tyt.services.crawler_stream_service import FOCUS_CODES, SKYEYE_DB, STOCKS_DB, _connect

logger = logging.getLogger("knowledge-sync")

BAOSTOCK_HOME = "http://www.baostock.com"
EXCERPT = 350
PURGE_DATE_KEY = "tyt:ai:kb:purge_date"
DAILY_CHECK_INTERVAL = 3600  # 常驻任务每小时检查一次是否跨天

status: dict = {"state": "pending", "indexed": 0, "skipped": 0, "last_run": None, "error": None,
                "last_purged": None, "purged_count": 0, "preserved_manual": 0,
                "preserved_company": 0, "kb_stats": {}}
_task: asyncio.Task | None = None
_timer_task: asyncio.Task | None = None
_mem_purge_date: str | None = None  # Redis 不可用时的进程内降级标记


def _today() -> str:
    return date.today().isoformat()


def _get_purge_date() -> str | None:
    r = get_redis()
    if r is not None:
        try:
            return r.get(PURGE_DATE_KEY)
        except Exception as e:
            logger.warning("读取日切标记失败: %s", e)
    return _mem_purge_date


def _set_purge_date(day: str):
    global _mem_purge_date
    _mem_purge_date = day
    r = get_redis()
    if r is not None:
        try:
            # 标记保留 2 天自动过期，历史标记无需长存
            r.set(PURGE_DATE_KEY, day, ex=2 * 24 * 3600)
        except Exception as e:
            logger.warning("写入日切标记失败: %s", e)


def daily_purge_and_resync() -> dict:
    """每日一清：清空爬虫来源知识文档 -> 从爬虫库重新入库最新数据。

    解决两类过期问题：
    1. 人民网文章撤稿/下架后，旧文档仍留在向量库被 AI 引用（失效链接）
    2. baostock 行情快照只在启动时入库一次，长期运行后行情过期

    先写 Redis 日切标记再执行，防止多进程（--reload 重叠窗口）并发清理交错删除。
    仅清理爬虫数据（people_article / baostock_quote），手动录入（manual）与企业卡片
    （company_card）始终保留，不参与每日清理，避免管理员人工维护的知识被误删。
    """
    _set_purge_date(_today())
    purged = ai_service.purge_crawler_knowledge()
    preserved_manual = ai_service.count_knowledge(ai_service.MANUAL_KIND)
    preserved_company = ai_service.count_knowledge("company_card")
    status["purged_count"] = purged
    status["preserved_manual"] = preserved_manual
    status["preserved_company"] = preserved_company
    status["last_purged"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info("AI 知识库日切：清理爬虫文档 %d 条；保留手动录入 %d 条、企业卡片 %d 条，开始重新同步最新数据",
                purged, preserved_manual, preserved_company)
    return sync()


def _md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def _people_docs() -> list[dict]:
    conn = _connect(SKYEYE_DB)
    if not conn:
        return []
    try:
        rows = conn.execute(
            "SELECT url, channel, title, content, source, pub_time FROM articles "
            "WHERE status = 'normal' ORDER BY crawl_time DESC"
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "id": "people:" + _md5(r["url"]),
            "text": (f"【人民网·{r['channel']}】{r['title']}"
                     f"（{r['source']}，发布于 {r['pub_time'] or '未知时间'}）\n"
                     f"{(r['content'] or '').strip()[:EXCERPT]}"),
            "meta": {
                "kind": "people_article",
                "title": r["title"],
                "url": r["url"],
                "source": f"人民网爬虫 · {r['channel']}频道",
            },
        }
        for r in rows
    ]


def _baostock_docs() -> list[dict]:
    conn = _connect(STOCKS_DB)
    if not conn:
        return []
    try:
        docs = []
        for code in FOCUS_CODES:
            s = conn.execute("SELECT code_name FROM securities WHERE code = ?", (code,)).fetchone()
            if not s:
                continue
            k = conn.execute(
                "SELECT date, close FROM kline WHERE code = ? ORDER BY date DESC LIMIT 2", (code,)
            ).fetchall()
            if not k:
                continue
            close = round(float(k[0]["close"] or 0), 2)
            pct = 0.0
            if len(k) > 1 and k[1]["close"]:
                pct = round((close / float(k[1]["close"]) - 1) * 100, 2)
            name, date = s["code_name"], k[0]["date"]
            docs.append({
                "id": f"stock:{code}",
                "text": (f"【baostock 证券行情】{name}（{code}）最新收盘价 {close} 元，"
                         f"涨跌幅 {pct:+.2f}%，K 线日期 {date}。数据来源：baostock 证券宝官方数据服务。"),
                "meta": {
                    "kind": "baostock_quote",
                    "title": f"{name}（{code}）最新行情",
                    "url": BAOSTOCK_HOME,
                    "source": "baostock 采集器",
                },
            })
        return docs
    finally:
        conn.close()


def sync() -> dict:
    docs = _people_docs() + _baostock_docs()
    if not docs:
        status.update({"state": "error", "error": "爬虫库不可读（skyeye.db / stocks.db）",
                       "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        return status

    existing = ai_service.existing_kb_ids([d["id"] for d in docs])
    todo = [d for d in docs if d["id"] not in existing]

    indexed = 0
    for d in todo:
        if not ai_service.upsert_knowledge(d["id"], d["text"], d["meta"]):
            logger.warning("知识入库中断（嵌入或向量库不可用），已完成 %d/%d", indexed, len(todo))
            break
        indexed += 1

    status.update({
        "state": "done" if indexed == len(todo) else ("partial" if indexed else "error"),
        "indexed": indexed,
        "skipped": len(docs) - indexed,
        "last_run": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    logger.info("爬虫知识入库完成：新增 %d 条，跳过已存在 %d 条", indexed, len(docs) - indexed)
    return status


async def _wait_embed_ready(timeout: float = 300) -> bool:
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if model_warmup.get_status()["models"].get("embed", {}).get("state") == "loaded":
            return True
        await asyncio.sleep(5)
    return False


async def _bg_job():
    for attempt in range(1, 6):
        if not await _wait_embed_ready():
            status["state"] = "waiting-model"
            logger.warning("等待嵌入模型预热超时（第 %d 次）", attempt)
            continue
        try:
            # 启动时检查日切：今天还没清理过（服务跨天运行/重启），先清空爬虫文档再同步
            if _get_purge_date() != _today():
                await asyncio.to_thread(daily_purge_and_resync)
            else:
                await asyncio.to_thread(sync)
            if status["state"] in ("done", "partial"):
                status["kb_stats"] = ai_service.kb_stats()
                return
        except Exception as e:
            status.update({"state": "error", "error": str(e)[:200]})
            logger.warning("知识入库异常: %s", e)
        await asyncio.sleep(30)


async def _daily_timer():
    """常驻日切任务：每小时检查 Redis 日期标记，跨天自动 清理+重同步。

    服务长期不重启时保证爬虫知识每日刷新，防止 AI 引用过期资讯/行情。
    """
    while True:
        await asyncio.sleep(DAILY_CHECK_INTERVAL)
        try:
            if _get_purge_date() != _today():
                if not await _wait_embed_ready(timeout=120):
                    logger.warning("日切清理：等待嵌入模型超时，下小时重试")
                    continue
                await asyncio.to_thread(daily_purge_and_resync)
                status["kb_stats"] = ai_service.kb_stats()
                logger.info("AI 知识库已完成每日清理与重同步: %s",
                            {k: status.get(k) for k in ("purged_count", "indexed", "skipped")})
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning("每日知识清理任务异常（下小时重试）: %s", e)


def start() -> asyncio.Task | None:
    global _task
    if _task and not _task.done():
        return _task
    try:
        _task = asyncio.create_task(_bg_job())
        _start_timer()
        return _task
    except RuntimeError:
        logger.warning("无事件循环，跳过知识入库")
        return None


def _start_timer():
    global _timer_task
    if _timer_task and not _timer_task.done():
        return
    _timer_task = asyncio.create_task(_daily_timer())


def stop():
    global _task, _timer_task
    if _task and not _task.done():
        _task.cancel()
    if _timer_task and not _timer_task.done():
        _timer_task.cancel()
    _task = None
    _timer_task = None


def get_status() -> dict:
    return dict(status)


_manual_lock = threading.Lock()


def start_manual_resync() -> bool:
    """管理端手动触发：后台线程执行 清理爬虫文档 + 重新同步；已有任务在跑时返回 False"""
    if not _manual_lock.acquire(blocking=False):
        return False

    def _job():
        try:
            status.update({"state": "syncing", "error": None})
            daily_purge_and_resync()
            status["kb_stats"] = ai_service.kb_stats()
            logger.info("管理端手动重同步完成")
        except Exception as e:
            status.update({"state": "error", "error": str(e)[:200]})
            logger.warning("管理端手动重同步异常: %s", e)
        finally:
            _manual_lock.release()

    threading.Thread(target=_job, daemon=True, name="kb-manual-resync").start()
    return True
