# -*- coding: utf-8 -*-
"""
Sky Eye · Baostock 股票数据导入 SQLite
读取 baostock/data/*.csv -> baostock/data/stocks.db
（独立于人民网库 E:\Sky Eye\data\skyeye.db，两库文件级分离）
  - stock_list     表：全市场证券列表（code 唯一键）
  - stock_industry 表：行业分类（code 唯一键）
  - kline_daily    表：日 K 线（code+date 唯一键）
可重复运行幂等更新；空字符串统一入库为 NULL。
"""

import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent  # backend/baostock/
ROOT_DIR = BASE_DIR.parent.parent  # Sky Eye/
STOCK_DIR = ROOT_DIR / "database" / "stocks"
KLINE_DIR = STOCK_DIR / "kline"
DB_PATH = STOCK_DIR / "stocks.db"

DDL = [
    """CREATE TABLE IF NOT EXISTS stock_list (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        code        TEXT NOT NULL UNIQUE,
        trade_status TEXT,
        code_name   TEXT,
        crawl_time  TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_stock_list_name ON stock_list(code_name)",
    """CREATE TABLE IF NOT EXISTS stock_industry (
        id                       INTEGER PRIMARY KEY AUTOINCREMENT,
        code                     TEXT NOT NULL UNIQUE,
        code_name                TEXT,
        industry                 TEXT,
        industry_classification  TEXT,
        update_date              TEXT
    )""",
    "CREATE INDEX IF NOT EXISTS idx_stock_industry_ind ON stock_industry(industry)",
    """CREATE TABLE IF NOT EXISTS kline_daily (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        code       TEXT NOT NULL,
        date       TEXT NOT NULL,
        open       REAL,
        high       REAL,
        low        REAL,
        close      REAL,
        preclose   REAL,
        volume     REAL,
        amount     REAL,
        turn       REAL,
        pct_chg    REAL,
        is_st      INTEGER,
        crawl_time TEXT,
        UNIQUE(code, date)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_kline_code ON kline_daily(code)",
    "CREATE INDEX IF NOT EXISTS idx_kline_date ON kline_daily(date)",
]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def to_num(v):
    """Baostock 缺失值是空串；可转数值则转，否则 NULL"""
    if v is None:
        return None
    v = str(v).strip()
    if not v:
        return None
    try:
        f = float(v)
        return int(f) if f == int(f) and "." not in v else f
    except ValueError:
        return None


def read_csv(path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def import_stock_list(conn):
    rows = read_csv(STOCK_DIR / "stock_list.csv")
    if not rows:
        log("stock_list.csv 不存在或为空，跳过")
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.executemany(
        """INSERT INTO stock_list (code, trade_status, code_name, crawl_time)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(code) DO UPDATE SET
             trade_status=excluded.trade_status, code_name=excluded.code_name,
             crawl_time=excluded.crawl_time""",
        [(r.get("code"), r.get("tradeStatus") or None, r.get("code_name") or None, now)
         for r in rows],
    )
    log(f"stock_list 写入 {len(rows)} 只证券")


def import_industry(conn):
    rows = read_csv(STOCK_DIR / "stock_industry.csv")
    if not rows:
        log("stock_industry.csv 不存在或为空，跳过")
        return
    conn.executemany(
        """INSERT INTO stock_industry
             (code, code_name, industry, industry_classification, update_date)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(code) DO UPDATE SET
             code_name=excluded.code_name, industry=excluded.industry,
             industry_classification=excluded.industry_classification,
             update_date=excluded.update_date""",
        [(r.get("code"), r.get("code_name") or None,
          r.get("industry") or None, r.get("industryClassification") or None,
          r.get("update_date") or None)
         for r in rows],
    )
    log(f"stock_industry 写入 {len(rows)} 条行业记录")


def import_kline(conn):
    files = sorted(KLINE_DIR.glob("*.csv"))
    if not files:
        log("kline/ 目录无 CSV，跳过")
        return
    total = 0
    for path in files:
        rows = read_csv(path)
        if not rows:
            continue
        conn.executemany(
            """INSERT INTO kline_daily
                 (code, date, open, high, low, close, preclose, volume, amount,
                  turn, pct_chg, is_st, crawl_time)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(code, date) DO UPDATE SET
                 open=excluded.open, high=excluded.high, low=excluded.low,
                 close=excluded.close, preclose=excluded.preclose, volume=excluded.volume,
                 amount=excluded.amount, turn=excluded.turn, pct_chg=excluded.pct_chg,
                 is_st=excluded.is_st, crawl_time=excluded.crawl_time""",
            [(r.get("code"), r.get("date"),
              to_num(r.get("open")), to_num(r.get("high")), to_num(r.get("low")),
              to_num(r.get("close")), to_num(r.get("preclose")), to_num(r.get("volume")),
              to_num(r.get("amount")), to_num(r.get("turn")), to_num(r.get("pctChg")),
              to_num(r.get("isST")), r.get("crawl_time") or None)
             for r in rows],
        )
        total += len(rows)
    log(f"kline_daily 写入 {total} 行（{len(files)} 个文件）")


def run():
    if not STOCK_DIR.exists():
        log(f"数据目录不存在: {STOCK_DIR}，请先运行 baostock_crawler.py")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(";".join(DDL))
        conn.execute("BEGIN")
        import_stock_list(conn)
        import_industry(conn)
        import_kline(conn)
        conn.commit()

        # 校验
        n_list = conn.execute("SELECT COUNT(*) FROM stock_list").fetchone()[0]
        n_ind = conn.execute("SELECT COUNT(*) FROM stock_industry").fetchone()[0]
        n_k = conn.execute("SELECT COUNT(*) FROM kline_daily").fetchone()[0]
        dmin, dmax = conn.execute(
            "SELECT MIN(date), MAX(date) FROM kline_daily").fetchone()
        log(f"校验: stock_list={n_list}, stock_industry={n_ind}, kline_daily={n_k}"
            f"（{dmin} ~ {dmax}）")
        log("证券分布：")
        for code, cnt, d0, d1 in conn.execute(
                """SELECT code, COUNT(*), MIN(date), MAX(date) FROM kline_daily
                   GROUP BY code ORDER BY code"""):
            print(f"    {code}: {cnt} 条（{d0} ~ {d1}）")
    finally:
        conn.close()
    log(f"SQLite 导入完成: {DB_PATH}")


if __name__ == "__main__":
    run()
