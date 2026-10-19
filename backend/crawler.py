#!/usr/bin/env python3
"""
Sky Eye - 人民网资讯爬虫
遵守 robots.txt，Crawl-delay 120s，增量抓取
数据源：人民网官方 Sitemap（sitemap_index.xml -> 各频道 sitemap）
输出：SQLite 资讯库 data/skyeye.db + articles.pkl
"""

import os
import re
import time
import pickle
import sqlite3
import hashlib
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Optional

import requests
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "skyeye.db")
PKL_PATH = os.path.join(BASE_DIR, "data", "articles.pkl")

PEOPLE_URL = "http://www.people.com.cn"
SITEMAP_INDEX = "http://www.people.com.cn/sitemap.xml"
ROBOTS_URL = "http://www.people.com.cn/robots.txt"

CHANNEL_WHITELIST = [
    "politics", "international", "finance", "sports",
    "legal", "culture", "society", "media",
]
CHANNEL_MAP = {
    "politics": "时政", "international": "国际", "finance": "财经",
    "sports": "体育", "legal": "法治", "culture": "文化",
    "society": "社会", "media": "传媒",
}

CRAWL_DELAY = 120
REQUEST_TIMEOUT = 30
USER_AGENT = "SkyEyeBot/1.0 (+https://github.com/sky-eye)"
BATCH_SIZE = 50

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("crawler")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            channel TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            content_len INTEGER DEFAULT 0,
            source TEXT,
            pub_time TEXT,
            crawl_time TEXT NOT NULL,
            status TEXT DEFAULT 'normal',
            url_hash TEXT UNIQUE
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_channel ON articles(channel)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_pub_time ON articles(pub_time DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status)")
    conn.commit()
    conn.close()
    logger.info(f"数据库初始化完成: {DB_PATH}")


def fetch_robots_rules() -> set:
    try:
        resp = requests.get(ROBOTS_URL, timeout=REQUEST_TIMEOUT,
                            headers={"User-Agent": USER_AGENT})
        resp.encoding = resp.apparent_encoding
        disallowed = set()
        for line in resp.text.splitlines():
            line = line.strip()
            if line.lower().startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    disallowed.add(path)
        logger.info(f"robots.txt 加载完成，禁止路径 {len(disallowed)} 条")
        return disallowed
    except Exception as e:
        logger.warning(f"robots.txt 获取失败: {e}，默认全允许")
        return set()


def is_allowed(url: str, disallowed: set) -> bool:
    parsed = urlparse(url)
    path = parsed.path
    for dis in disallowed:
        if path.startswith(dis):
            return False
    return True


def fetch_sitemap_urls() -> list:
    """从人民网 sitemap 获取文章 URL 列表"""
    try:
        resp = requests.get(SITEMAP_INDEX, timeout=REQUEST_TIMEOUT,
                            headers={"User-Agent": USER_AGENT})
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "xml")
        sitemaps = [loc.text for loc in soup.find_all("loc")]
        logger.info(f"发现 {len(sitemaps)} 个子 sitemap")
        all_urls = []
        for sm_url in sitemaps:
            channel = _detect_channel(sm_url)
            if channel and channel not in CHANNEL_WHITELIST:
                continue
            if not channel and not any(ch in sm_url for ch in CHANNEL_WHITELIST):
                continue
            try:
                sub_resp = requests.get(sm_url, timeout=REQUEST_TIMEOUT,
                                        headers={"User-Agent": USER_AGENT})
                sub_resp.encoding = sub_resp.apparent_encoding
                sub_soup = BeautifulSoup(sub_resp.text, "xml")
                urls = [loc.text for loc in sub_soup.find_all("loc")]
                for u in urls:
                    ch = channel or _detect_channel(u)
                    if ch and ch in CHANNEL_WHITELIST:
                        all_urls.append((u, ch))
            except Exception as e:
                logger.warning(f"子 sitemap {sm_url} 获取失败: {e}")
            time.sleep(2)
        logger.info(f"共获取 {len(all_urls)} 个待抓取 URL")
        return all_urls
    except Exception as e:
        logger.error(f"Sitemap 获取失败: {e}")
        return []


def _detect_channel(url: str) -> Optional[str]:
    for ch in CHANNEL_WHITELIST:
        if ch in url:
            return ch
    return None


def get_existing_urls() -> set:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT url FROM articles").fetchall()
    conn.close()
    return {r[0] for r in rows}


def parse_article(html: str, url: str, channel: str) -> Optional[dict]:
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("h1") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "未知标题"

    content_parts = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text and len(text) > 10:
            content_parts.append(text)
    content = "\n".join(content_parts)
    if not content:
        return None

    source_tag = soup.find("a", string=re.compile(r"来源"))
    source = source_tag.get_text(strip=True) if source_tag else "人民网"

    pub_time = None
    time_patterns = [
        r"(\d{4}年\d{1,2}月\d{1,2}日\s*\d{1,2}:\d{2})",
        r"(\d{4}-\d{1,2}-\d{1,2}\s*\d{1,2}:\d{2})",
        r"(\d{4}/\d{1,2}/\d{1,2})",
    ]
    page_text = soup.get_text()
    for pattern in time_patterns:
        match = re.search(pattern, page_text)
        if match:
            pub_time = match.group(1)
            break

    url_hash = hashlib.md5(url.encode()).hexdigest()

    return {
        "url": url,
        "url_hash": url_hash,
        "channel": channel,
        "channel_name": CHANNEL_MAP.get(channel, channel),
        "title": title,
        "content": content,
        "content_len": len(content),
        "source": source,
        "pub_time": pub_time or datetime.now().strftime("%Y-%m-%d %H:%M"),
        "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "normal",
    }


def save_article(conn: sqlite3.Connection, article: dict):
    conn.execute("""
        INSERT OR IGNORE INTO articles
            (url, url_hash, channel, title, content, content_len,
             source, pub_time, crawl_time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        article["url"], article["url_hash"], article["channel_name"],
        article["title"], article["content"], article["content_len"],
        article["source"], article["pub_time"], article["crawl_time"],
        article["status"],
    ))


def export_pkl():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT url, channel, title, content, content_len, source,
               pub_time, crawl_time, status
        FROM articles WHERE status = 'normal'
    """).fetchall()
    conn.close()

    articles = []
    for r in rows:
        articles.append({
            "url": r[0], "channel": r[1], "title": r[2],
            "content": r[3], "content_len": r[4], "source": r[5],
            "pub_time": r[6], "crawl_time": r[7], "status": r[8],
        })

    with open(PKL_PATH, "wb") as f:
        pickle.dump(articles, f)
    logger.info(f"已导出 {len(articles)} 条到 {PKL_PATH}")
    return len(articles)


def run_crawl(max_articles: int = None):
    logger.info("=" * 60)
    logger.info("Sky Eye 人民网爬虫启动")
    logger.info(f"数据库: {DB_PATH}")
    logger.info(f"采集频道: {', '.join(CHANNEL_MAP.values())}")
    logger.info(f"Crawl-delay: {CRAWL_DELAY}s")
    logger.info("=" * 60)

    init_db()
    disallowed = fetch_robots_rules()
    existing = get_existing_urls()
    logger.info(f"数据库已有 {len(existing)} 条记录")

    all_urls = fetch_sitemap_urls()
    new_urls = [(u, ch) for u, ch in all_urls if u not in existing]
    logger.info(f"过滤后新增待抓取: {len(new_urls)} 条")

    if max_articles:
        new_urls = new_urls[:max_articles]

    conn = sqlite3.connect(DB_PATH)
    success = 0
    for i, (url, channel) in enumerate(new_urls):
        if not is_allowed(url, disallowed):
            logger.info(f"[跳过-robots] {url}")
            continue
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT,
                                headers={"User-Agent": USER_AGENT})
            resp.encoding = resp.apparent_encoding
            if resp.status_code != 200:
                logger.warning(f"[{resp.status_code}] {url}")
                continue

            article = parse_article(resp.text, url, channel)
            if article:
                save_article(conn, article)
                success += 1
                logger.info(f"[{i+1}/{len(new_urls)}] {article['title'][:40]}")
            else:
                logger.warning(f"[解析失败] {url}")
        except Exception as e:
            logger.error(f"[异常] {url}: {e}")

        if (i + 1) % BATCH_SIZE == 0:
            conn.commit()
            logger.info(f"已提交 {i+1} 条，暂停 {CRAWL_DELAY}s (Crawl-delay)")
            time.sleep(CRAWL_DELAY)

    conn.commit()
    conn.close()

    total = export_pkl()
    logger.info(f"采集完成: 新增 {success} 条，总计 {total} 条")
    return success


if __name__ == "__main__":
    run_crawl(max_articles=100)
