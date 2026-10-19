"""爬虫实时流服务：整合第一版两个爬虫数据源的流式输出

数据源（第一版爬虫产物，只读复用）：
  1. 人民网资讯爬虫（backend/crawler.py）-> database/skyeye.db articles 表
  2. baostock 证券数据采集器（backend/baostock/baostock_crawler.py）-> database/stocks/stocks.db
     （baostock 为官方 SDK TCP 查询，非网页抓取）

输出：SSE 事件流（start -> item*N -> done），供仪表盘滚动窗口展示。
任一数据源缺失时自动降级为确定性演示数据。
"""
import asyncio
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[3]  # E:\SkyEyev2.0
SKYEYE_DB = _ROOT / "database" / "skyeye.db"
STOCKS_DB = _ROOT / "database" / "stocks" / "stocks.db"

# baostock 重点观测池（3 指数 + 10 个股，与第一版采集清单一致）
FOCUS_CODES = [
    "sh.000001", "sz.399001", "sz.399006",
    "sh.600519", "sh.601398", "sh.600036", "sh.600900", "sh.601318",
    "sz.000001", "sz.000002", "sz.300750", "sz.002594", "sz.688981",
]

CHANNEL_COLORS = {
    "时政": "#ef4444", "国际": "#0891b2", "财经": "#6366f1", "体育": "#10b981",
    "法治": "#8b5cf6", "文化": "#f59e0b", "社会": "#f97316", "传媒": "#14b8a6",
}


def _connect(db_path: Path) -> sqlite3.Connection | None:
    if not db_path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.warning("打开爬虫库失败 %s: %s", db_path, e)
        return None


def load_people_articles(limit: int = 20) -> list[dict]:
    """人民网爬虫最新资讯"""
    conn = _connect(SKYEYE_DB)
    if not conn:
        return []
    try:
        rows = conn.execute(
            "SELECT channel, title, source, pub_time, crawl_time FROM articles "
            "WHERE status = 'normal' ORDER BY crawl_time DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "source": "people",
            "source_name": "人民网爬虫",
            "badge": r["channel"] or "资讯",
            "badge_color": CHANNEL_COLORS.get(r["channel"], "#6366f1"),
            "title": r["title"],
            "meta": f"{r['source'] or '人民网'} · 发布 {r['pub_time'] or '--'}",
            "crawl_time": r["crawl_time"],
        }
        for r in rows
    ]


def load_baostock_records(limit: int = 20) -> list[dict]:
    """baostock 采集器最新证券行情（重点池：最新 K 线收盘 + 涨跌幅）"""
    conn = _connect(STOCKS_DB)
    if not conn:
        return []
    try:
        rows = conn.execute(
            "SELECT s.code, s.code_name FROM securities s WHERE s.code IN "
            f"({','.join('?' * len(FOCUS_CODES))}) ORDER BY s.code", FOCUS_CODES
        ).fetchall()
        items = []
        for r in rows:
            k = conn.execute(
                "SELECT date, open, close, crawl_time FROM kline WHERE code = ? "
                "ORDER BY date DESC LIMIT 2", (r["code"],)
            ).fetchall()
            if not k:
                continue
            latest, prev = k[0], (k[1] if len(k) > 1 else None)
            close = round(float(latest["close"] or 0), 2)
            if prev and prev["close"]:
                pct = round((close / float(prev["close"]) - 1) * 100, 2)
            else:
                pct = 0.0
            items.append({
                "source": "baostock",
                "source_name": "baostock 采集器",
                "badge": r["code"].split(".")[-1],
                "badge_color": "#0891b2",
                "title": f"{r['code_name']}（{r['code']}）",
                "meta": f"收盘 {close} · {pct:+.2f}% · K线日期 {latest['date']}",
                "crawl_time": latest["crawl_time"],
                "pct": pct,
            })
        # 按采集时间倒序
        items.sort(key=lambda x: x["crawl_time"] or "", reverse=True)
        return items[:limit]
    finally:
        conn.close()


def _demo_records(limit: int) -> list[dict]:
    """两个库都不可用时的确定性演示降级"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    demos = [
        {"source": "people", "source_name": "人民网爬虫", "badge": "时政", "badge_color": "#ef4444",
         "title": "推动督促修改废止规范性文件2.7万余件", "meta": "人民日报 · 演示数据", "crawl_time": now},
        {"source": "baostock", "source_name": "baostock 采集器", "badge": "600519",
         "badge_color": "#0891b2", "title": "贵州茅台（sh.600519）",
         "meta": "收盘 1756.50 · +2.35% · 演示数据", "crawl_time": now, "pct": 2.35},
        {"source": "people", "source_name": "人民网爬虫", "badge": "财经", "badge_color": "#6366f1",
         "title": "保险服务托举居家银发幸福", "meta": "人民网 · 演示数据", "crawl_time": now},
        {"source": "baostock", "source_name": "baostock 采集器", "badge": "300750",
         "badge_color": "#0891b2", "title": "宁德时代（sz.300750）",
         "meta": "收盘 215.80 · +1.87% · 演示数据", "crawl_time": now, "pct": 1.87},
        {"source": "people", "source_name": "人民网爬虫", "badge": "国际", "badge_color": "#0891b2",
         "title": "多国政要祝贺中国国庆", "meta": "新华社 · 演示数据", "crawl_time": now},
    ]
    out = []
    while len(out) < limit:
        out.extend(demos)
    return out[:limit]


def load_stream_items(limit: int = 20, source: str = "all") -> list[dict]:
    """合并两个爬虫源的记录（交替穿插，滚动窗口更有层次感）；limit 足够大时展示全部采集记录"""
    per = limit
    people = load_people_articles(per) if source in ("all", "people") else []
    stock = load_baostock_records(per) if source in ("all", "baostock") else []

    if not people and not stock:
        return _demo_records(limit)

    # 交替穿插
    merged: list[dict] = []
    i = j = 0
    while len(merged) < limit and (i < len(people) or j < len(stock)):
        if i < len(people):
            merged.append(people[i]); i += 1
        if j < len(stock) and len(merged) < limit:
            merged.append(stock[j]); j += 1
    return merged


def get_stats() -> dict:
    """两个爬虫库的采集统计"""
    stats = {"people_total": 0, "baostock_securities": 0, "baostock_kline": 0}
    conn = _connect(SKYEYE_DB)
    if conn:
        try:
            stats["people_total"] = conn.execute(
                "SELECT COUNT(*) FROM articles WHERE status='normal'").fetchone()[0]
        except sqlite3.Error:
            pass
        conn.close()
    conn = _connect(STOCKS_DB)
    if conn:
        try:
            stats["baostock_securities"] = conn.execute("SELECT COUNT(*) FROM securities").fetchone()[0]
            stats["baostock_kline"] = conn.execute("SELECT COUNT(*) FROM kline").fetchone()[0]
        except sqlite3.Error:
            pass
        conn.close()
    return stats


async def stream_events(limit: int = 20, source: str = "all"):
    """SSE 事件流：start -> item* -> done
    推送间隔与前端 streamSlideIn(0.55s) 滑入动画对齐，放缓节奏便于阅读"""
    items = load_stream_items(limit, source)
    stats = get_stats()
    delay = min(1.1, max(0.45, 36 / max(1, len(items))))
    yield ("data: " + json.dumps({
        "type": "start", "count": len(items),
        "stats": stats, "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }, ensure_ascii=False) + "\n\n")
    for item in items:
        yield ("data: " + json.dumps({"type": "item", "data": item}, ensure_ascii=False) + "\n\n")
        await asyncio.sleep(delay)
    yield 'data: {"type": "done"}\n\n'
