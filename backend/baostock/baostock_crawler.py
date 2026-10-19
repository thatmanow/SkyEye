#!/usr/bin/env python3
"""
Sky Eye - baostock 证券数据采集器
通过 baostock 官方 SDK 以 TCP 协议登录查询，非网页抓取
采集：全市场证券列表、行业分类、日K线（3指数 + 10重点个股）
输出：SQLite 证券库 data/stocks.db + stocks_kline.pkl
"""

import os
import time
import pickle
import sqlite3
import logging
from datetime import datetime, timedelta

try:
    import baostock as bs
    BAOSTOCK_AVAILABLE = True
except ImportError:
    BAOSTOCK_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # backend/baostock/
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))  # Sky Eye/
DB_PATH = os.path.join(ROOT_DIR, "database", "stocks", "stocks.db")
PKL_PATH = os.path.join(ROOT_DIR, "database", "stocks", "stocks_kline.pkl")

START_DATE = "2024-01-01"
QUERY_INTERVAL = 0.3

INDEX_CODES = [
    "sh.000001",
    "sz.399001",
    "sz.399006",
]

STOCK_CODES = [
    "sh.600519",
    "sh.601398",
    "sh.600036",
    "sh.600900",
    "sh.601318",
    "sz.000001",
    "sz.000002",
    "sz.300750",
    "sz.002594",
    "sz.688981",
]

ALL_CODES = INDEX_CODES + STOCK_CODES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("baostock_crawler")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS securities (
            code TEXT PRIMARY KEY,
            code_name TEXT NOT NULL,
            ipo_date TEXT,
            out_date TEXT,
            type TEXT,
            status TEXT,
            industry TEXT,
            industry_classification TEXT,
            crawl_time TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS kline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            preclose REAL,
            volume REAL,
            amount REAL,
            turn REAL,
            pctChg REAL,
            isST TEXT,
            crawl_time TEXT NOT NULL,
            UNIQUE(code, date)
        );

        CREATE TABLE IF NOT EXISTS industries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            industry TEXT UNIQUE NOT NULL,
            stock_count INTEGER DEFAULT 0,
            crawl_time TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_kline_code ON kline(code);
        CREATE INDEX IF NOT EXISTS idx_kline_date ON kline(date DESC);
        CREATE INDEX IF NOT EXISTS idx_kline_code_date ON kline(code, date DESC);
    """)
    conn.commit()
    conn.close()
    logger.info(f"证券库初始化完成: {DB_PATH}")


def get_latest_date(conn: sqlite3.Connection, code: str) -> str:
    row = conn.execute(
        "SELECT MAX(date) FROM kline WHERE code = ?", (code,)
    ).fetchone()
    if row and row[0]:
        dt = datetime.strptime(row[0], "%Y-%m-%d")
        return (dt + timedelta(days=1)).strftime("%Y-%m-%d")
    return START_DATE


def crawl_securities_list():
    """采集全市场证券列表"""
    logger.info("开始采集证券列表...")
    lg = bs.login()
    if lg.error_code != "0":
        logger.error(f"baostock 登录失败: {lg.error_msg}")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    rs = bs.query_all_stock(day=today)
    if rs.error_code != "0":
        logger.error(f"查询证券列表失败: {rs.error_msg}")
        return

    conn = sqlite3.connect(DB_PATH)
    count = 0
    while rs.error_code == "0" and rs.next():
        row = rs.get_row_data()
        code, code_name = row[0], row[1]
        ipo_date = row[2] if len(row) > 2 else None
        out_date = row[3] if len(row) > 3 else None
        stype = row[4] if len(row) > 4 else None
        status = row[5] if len(row) > 5 else None

        conn.execute("""
            INSERT OR REPLACE INTO securities
                (code, code_name, ipo_date, out_date, type, status, crawl_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (code, code_name, ipo_date, out_date, stype, status,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        count += 1
        time.sleep(QUERY_INTERVAL)

    conn.commit()
    conn.close()
    bs.logout()
    logger.info(f"证券列表采集完成: {count} 条")


def crawl_industries():
    """采集行业分类"""
    logger.info("开始采集行业分类...")
    lg = bs.login()
    if lg.error_code != "0":
        logger.error(f"baostock 登录失败: {lg.error_msg}")
        return

    rs = bs.query_stock_industry()
    if rs.error_code != "0":
        logger.error(f"查询行业分类失败: {rs.error_msg}")
        bs.logout()
        return

    conn = sqlite3.connect(DB_PATH)
    industry_map = {}

    while rs.error_code == "0" and rs.next():
        row = rs.get_row_data()
        code, code_name = row[0], row[1]
        industry = row[2] if len(row) > 2 else "未知"
        classification = row[3] if len(row) > 3 else None

        conn.execute("""
            UPDATE securities SET industry = ?, industry_classification = ?
            WHERE code = ?
        """, (industry, classification, code))

        if industry not in industry_map:
            industry_map[industry] = 0
        industry_map[industry] += 1
        time.sleep(QUERY_INTERVAL)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for ind, cnt in industry_map.items():
        conn.execute("""
            INSERT OR REPLACE INTO industries (industry, stock_count, crawl_time)
            VALUES (?, ?, ?)
        """, (ind, cnt, now))

    conn.commit()
    conn.close()
    bs.logout()
    logger.info(f"行业分类采集完成: {len(industry_map)} 个行业")


def crawl_kline(code: str, start_date: str, end_date: str):
    """采集单只证券的日K线"""
    conn = sqlite3.connect(DB_PATH)
    existing_dates = {
        r[0] for r in conn.execute(
            "SELECT date FROM kline WHERE code = ?", (code,)
        ).fetchall()
    }
    conn.close()

    rs = bs.query_history_k_data_plus(
        code,
        "date,code,open,high,low,close,preclose,volume,amount,turn,pctChg,isST",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="2",
    )
    if rs.error_code != "0":
        logger.error(f"K线查询失败 {code}: {rs.error_msg}")
        return 0

    conn = sqlite3.connect(DB_PATH)
    count = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    while rs.error_code == "0" and rs.next():
        row = rs.get_row_data()
        date_str = row[0]
        if date_str in existing_dates:
            continue

        try:
            conn.execute("""
                INSERT OR IGNORE INTO kline
                    (code, date, open, high, low, close, preclose,
                     volume, amount, turn, pctChg, isST, crawl_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row[1], date_str,
                float(row[2]) if row[2] else None,
                float(row[3]) if row[3] else None,
                float(row[4]) if row[4] else None,
                float(row[5]) if row[5] else None,
                float(row[6]) if row[6] else None,
                float(row[7]) if row[7] else None,
                float(row[8]) if row[8] else None,
                float(row[9]) if row[9] else None,
                float(row[10]) if row[10] else None,
                row[11] if len(row) > 11 else "0",
                now,
            ))
            count += 1
        except (ValueError, IndexError) as e:
            logger.warning(f"K线数据解析失败 {code} {date_str}: {e}")
        time.sleep(QUERY_INTERVAL)

    conn.commit()
    conn.close()
    return count


def crawl_all_klines():
    """采集全部标的的K线"""
    logger.info(f"开始采集K线，标的 {len(ALL_CODES)} 只")
    lg = bs.login()
    if lg.error_code != "0":
        logger.error(f"baostock 登录失败: {lg.error_msg}")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    total = 0
    for code in ALL_CODES:
        start = get_latest_date(sqlite3.connect(DB_PATH), code)
        if start > today:
            logger.info(f"[跳过] {code} 已是最新数据")
            continue

        count = crawl_kline(code, start, today)
        total += count
        logger.info(f"[{code}] 新增 {count} 条K线 (起 {start} 至 {today})")

    bs.logout()
    logger.info(f"K线采集完成，共新增 {total} 条")


def export_pkl():
    conn = sqlite3.connect(DB_PATH)
    kline_rows = conn.execute("""
        SELECT code, date, open, high, low, close, preclose,
               volume, amount, turn, pctChg, isST
        FROM kline ORDER BY code, date
    """).fetchall()
    stock_rows = conn.execute("""
        SELECT code, code_name, industry, industry_classification, status
        FROM securities
    """).fetchall()
    conn.close()

    kline_data = []
    for r in kline_rows:
        kline_data.append({
            "code": r[0], "date": r[1], "open": r[2], "high": r[3],
            "low": r[4], "close": r[5], "preclose": r[6],
            "volume": r[7], "amount": r[8], "turn": r[9],
            "pctChg": r[10], "isST": r[11],
        })

    stock_data = []
    for r in stock_rows:
        stock_data.append({
            "code": r[0], "code_name": r[1], "industry": r[2],
            "classification": r[3], "status": r[4],
        })

    with open(PKL_PATH, "wb") as f:
        pickle.dump({"stocks": stock_data, "kline": kline_data}, f)
    logger.info(f"已导出 {len(kline_data)} 条K线到 {PKL_PATH}")
    return len(kline_data)


def run_crawl():
    logger.info("=" * 60)
    logger.info("Sky Eye baostock 证券采集器启动")
    logger.info(f"数据库: {DB_PATH}")
    logger.info(f"起始日期: {START_DATE}")
    logger.info(f"标的: {len(ALL_CODES)} 只 ({len(INDEX_CODES)} 指数 + {len(STOCK_CODES)} 个股)")
    logger.info("=" * 60)

    if not BAOSTOCK_AVAILABLE:
        logger.error("baostock SDK 未安装，请运行: pip install baostock")
        return

    init_db()

    crawl_securities_list()
    crawl_industries()
    crawl_all_klines()

    total = export_pkl()
    logger.info(f"采集完成，K线总计 {total} 条")


if __name__ == "__main__":
    run_crawl()
