"""多智能体股票分析服务

数据：演示证券宇宙 + 按代码种子确定性生成的 60 日 K 线（结构真实、内容标注演示）
智能体流水线：
  数据分析师(Python 确定性计算) -> [技术面/基本面/舆情分析师](并行 LLM) -> 风控经理(LLM) -> 首席分析师(LLM 汇总)
所有 LLM 调用走本地 Ollama qwen2.5，输出中文 Markdown，末尾附合规免责声明。
"""
import asyncio
import hashlib
import json
import logging
import random
from datetime import date, timedelta

import httpx

from tyt.config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL

logger = logging.getLogger(__name__)

# ==================== 演示证券宇宙 ====================
STOCKS = [
    {"code": "600519", "name": "贵州茅台", "industry": "白酒", "pe": 22.5, "pb": 7.8, "roe": 32.5},
    {"code": "000858", "name": "五粮液", "industry": "白酒", "pe": 15.2, "pb": 4.1, "roe": 24.8},
    {"code": "300750", "name": "宁德时代", "industry": "动力电池", "pe": 18.6, "pb": 4.5, "roe": 22.1},
    {"code": "002594", "name": "比亚迪", "industry": "新能源汽车", "pe": 20.3, "pb": 4.2, "roe": 21.5},
    {"code": "688981", "name": "中芯国际", "industry": "半导体", "pe": 88.4, "pb": 4.9, "roe": 4.2},
    {"code": "601318", "name": "中国平安", "industry": "保险", "pe": 8.9, "pb": 1.1, "roe": 11.6},
    {"code": "600036", "name": "招商银行", "industry": "银行", "pe": 6.2, "pb": 0.9, "roe": 15.3},
    {"code": "000333", "name": "美的集团", "industry": "家电", "pe": 12.8, "pb": 2.6, "roe": 22.4},
    {"code": "601899", "name": "紫金矿业", "industry": "有色金属", "pe": 14.6, "pb": 3.2, "roe": 20.8},
    {"code": "002415", "name": "海康威视", "industry": "安防设备", "pe": 25.4, "pb": 4.4, "roe": 18.9},
    {"code": "600276", "name": "恒瑞医药", "industry": "医药", "pe": 45.2, "pb": 6.1, "roe": 12.4},
    {"code": "601012", "name": "隆基绿能", "industry": "光伏", "pe": 28.9, "pb": 2.8, "roe": 9.6},
]

INDICES = [
    {"code": "000001", "name": "上证指数", "base": 3156},
    {"code": "399001", "name": "深证成指", "base": 10234},
    {"code": "399006", "name": "创业板指", "base": 2087},
    {"code": "000300", "name": "沪深300", "base": 3689},
]

# 多智能体定义（key, 名称, 角色, 图标, 描述）
AGENTS = [
    {"key": "data", "name": "数据分析师", "icon": "📊", "desc": "量化计算趋势/均线/波动率/量能"},
    {"key": "tech", "name": "技术面分析师", "icon": "📈", "desc": "K 线形态与技术指标解读"},
    {"key": "fundamental", "name": "基本面分析师", "icon": "🏢", "desc": "行业格局与估值水平评估"},
    {"key": "sentiment", "name": "舆情分析师", "icon": "📰", "desc": "公开资讯情绪与热度研判"},
    {"key": "risk", "name": "风控经理", "icon": "🛡️", "desc": "识别主要风险并给出约束"},
    {"key": "chief", "name": "首席分析师", "icon": "🎯", "desc": "汇总各方观点形成结论"},
]

DISCLAIMER = "\n\n> ⚠️ 免责声明：以上内容由本地大模型基于演示数据生成，仅供技术演示与研究学习，不构成任何投资建议。"


def search_stocks(keyword: str, limit: int = 10) -> list[dict]:
    kw = (keyword or "").strip().lower()
    if not kw:
        return [{"code": s["code"], "name": s["name"], "industry": s["industry"]} for s in STOCKS[:8]]
    hits = [s for s in STOCKS
            if kw in s["code"].lower() or kw in s["name"].lower() or kw in s["industry"].lower()]
    return [{"code": s["code"], "name": s["name"], "industry": s["industry"]} for s in hits[:limit]]


def find_stock(code: str) -> dict | None:
    for s in STOCKS:
        if s["code"] == code:
            return s
    return None


def _gen_kline(code: str, base_price: float, days: int = 60) -> list[dict]:
    """按代码种子确定性生成日 K（同一代码每次结果一致）"""
    seed = int(hashlib.md5(code.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    price = base_price
    today = date.today()
    rows = []
    d = today
    traded = 0
    while traded < days:
        if d.weekday() < 5:  # 跳过周末
            pct = rng.gauss(0.03, 1.8)
            open_ = round(price * (1 + rng.gauss(0, 0.4) / 100), 2)
            close = round(price * (1 + pct / 100), 2)
            high = round(max(open_, close) * (1 + abs(rng.gauss(0, 0.7)) / 100), 2)
            low = round(min(open_, close) * (1 - abs(rng.gauss(0, 0.7)) / 100), 2)
            volume = int(rng.uniform(80, 320) * 10000)
            rows.append({
                "date": d.isoformat(), "open": open_, "high": high, "low": low,
                "close": close, "pct_chg": round(pct, 2), "volume": volume,
            })
            price = close
            traded += 1
        d -= timedelta(days=1)
    rows.reverse()
    return rows


def get_stock_detail(code: str) -> dict | None:
    stock = find_stock(code)
    if not stock:
        return None
    seed = int(hashlib.md5(code.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed + 7)
    base = round(rng.uniform(18, 320), 2)
    kline = _gen_kline(code, base)
    latest, prev = kline[-1], kline[-2]
    change = round(latest["close"] - prev["close"], 2)
    return {
        **{k: stock[k] for k in ("code", "name", "industry", "pe", "pb", "roe")},
        "price": latest["close"], "change": change,
        "pct_chg": round(change / prev["close"] * 100, 2),
        "open": latest["open"], "high": latest["high"], "low": latest["low"],
        "volume": latest["volume"], "date": latest["date"],
        "kline": kline, "is_demo": True,
    }


def get_indices() -> list[dict]:
    out = []
    today = date.today().isoformat()
    for idx in INDICES:
        seed = int(hashlib.md5(idx["code"].encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + int(today.replace("-", "")) % 97)
        pct = rng.gauss(0.1, 0.9)
        price = round(idx["base"] * (1 + rng.gauss(0, 1.2) / 100), 2)
        out.append({
            "name": idx["name"], "code": idx["code"], "price": price,
            "pct_chg": round(pct, 2), "direction": "up" if pct >= 0 else "down", "date": today,
        })
    return out


def get_demo_news(stock: dict) -> list[str]:
    """按代码确定性生成演示资讯标题（模拟公开资讯情绪）"""
    seed = int(hashlib.md5(stock["code"].encode()).hexdigest()[:8], 16)
    rng = random.Random(seed + 13)
    pool = [
        f"{stock['name']}发布三季度业绩预告，营收同比小幅增长",
        f"{stock['industry']}板块近期获机构调研密集关注",
        f"分析师：{stock['name']}估值处于行业中等水平",
        f"{stock['name']}拟加大研发投入，布局下一代产品",
        f"行业政策面回暖，{stock['industry']}产业链有望受益",
        f"市场震荡加剧，{stock['name']}成交量放大",
        f"多家券商维持{stock['name']}中性评级",
        f"北向资金连续净流入{stock['industry']}板块",
    ]
    picks = rng.sample(pool, k=5)
    return picks


# ==================== 数据分析师（确定性计算，无 LLM） ====================
def data_agent(stock: dict, kline: list[dict]) -> str:
    closes = [k["close"] for k in kline]
    vols = [k["volume"] for k in kline]
    n = len(closes)

    def ma(window: int) -> float:
        return round(sum(closes[-window:]) / window, 2)

    ma5, ma10, ma20 = ma(5), ma(10), ma(20)
    ret_5d = round((closes[-1] / closes[-6] - 1) * 100, 2)
    ret_20d = round((closes[-1] / closes[-21] - 1) * 100, 2)
    vol_20d = round((sum((c - sum(closes[-20:]) / 20) ** 2 for c in closes[-20:]) / 20) ** 0.5 / closes[-1] * 100, 2)

    gains = [c for c in (closes[i] - closes[i - 1] for i in range(max(1, n - 14), n)) if c > 0]
    losses = [abs(c) for c in (closes[i] - closes[i - 1] for i in range(max(1, n - 14), n)) if c < 0]
    rs = (sum(gains) / len(gains)) / (sum(losses) / len(losses)) if gains and losses else (100.0 if gains else 0.01)
    rsi14 = round(100 - 100 / (1 + rs), 1)

    vol_ratio = round(vols[-1] / (sum(vols[-5:]) / 5), 2)
    hi60, lo60 = max(closes), min(closes)
    pos = round((closes[-1] - lo60) / (hi60 - lo60) * 100, 1)

    trend = "多头排列（MA5>MA10>MA20）" if ma5 > ma10 > ma20 else ("空头排列（MA5<MA10<MA20）" if ma5 < ma10 < ma20 else "均线纠缠，方向不明")
    lines = [
        f"### 量化数据摘要 · {stock['name']}（{stock['code']}）",
        f"- **最新收盘**：{closes[-1]} 元（60 日区间 {lo60} ~ {hi60}，当前位置 {pos}% 分位）",
        f"- **均线**：MA5={ma5}，MA10={ma10}，MA20={ma20} —— {trend}",
        f"- **区间收益**：近 5 日 {ret_5d:+}%，近 20 日 {ret_20d:+}%",
        f"- **波动率**（20 日年化近似）：{vol_20d}%",
        f"- **RSI(14)**：{rsi14}（>70 超买区，<30 超卖区）",
        f"- **量能**：最新成交量 / 5 日均量 = {vol_ratio}",
    ]
    return "\n".join(lines)


# ==================== LLM 智能体 ====================
async def _llm(system: str, prompt: str, max_tokens: int = 480) -> str:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json={
                "model": OLLAMA_CHAT_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "options": {"temperature": 0.4, "num_predict": max_tokens},
            })
            resp.raise_for_status()
            return resp.json()["message"]["content"].strip()
    except Exception as e:
        logger.error("stock agent llm failed: %s", e)
        return f"（{e}）"


BASE_SYSTEM = "你是天眼通平台的证券分析智能体。基于给定的演示数据用简体中文输出简洁的 Markdown 分析（不超过 200 字），不得编造数据之外的事实，不做投资建议。"

AGENT_PROMPTS = {
    "tech": (
        "你是技术面分析师。基于以下量化数据，解读K线趋势、均线形态、RSI与量能信号，"
        "给出技术面偏多/偏空/中性的判断，2-4 条要点。\n\n{data}"
    ),
    "fundamental": (
        "你是基本面分析师。评估标的的行业地位与估值水平（PE/PB/ROE 已给出），"
        "指出估值优势与隐忧，2-4 条要点。\n\n标的：{name}（{code}），行业：{industry}，"
        "PE={pe}，PB={pb}，ROE={roe}%。最新价 {price} 元。"
    ),
    "sentiment": (
        "你是舆情分析师。以下为该标的近期公开资讯标题（演示数据），"
        "请研判市场情绪倾向（乐观/谨慎/分歧），2-4 条要点。\n\n资讯：\n{news}"
    ),
    "risk": (
        "你是风控经理。综合以下三位分析师的观点，识别 3-5 条主要风险"
        "（估值/技术/情绪/流动性等维度），并给出风控约束建议。\n\n"
        "技术面观点：\n{tech}\n\n基本面观点：\n{fundamental}\n\n舆情观点：\n{sentiment}"
    ),
}

CHIEF_PROMPT = (
    "你是首席分析师。请综合以下所有智能体的分析，输出一份结构化结论文报告，格式：\n"
    "## 综合结论\n（2-3 句总体判断：偏多/偏空/中性）\n"
    "## 多空要点\n（多方 2 条、空方 2 条）\n"
    "## 操作参考\n（1-2 条风险偏好提示，强调仅为演示）\n\n"
    "数据摘要：\n{data}\n\n技术面：\n{tech}\n\n基本面：\n{fundamental}\n"
    "舆情：\n{sentiment}\n\n风控：\n{risk}"
)


async def run_pipeline(code: str):
    """多智能体流水线：data(同步) -> [tech, fundamental, sentiment] 并行 -> risk -> chief(流式)"""
    stock = find_stock(code)
    if not stock:
        yield {"type": "error", "message": "未找到该证券（演示宇宙内代码）"}
        return

    detail = get_stock_detail(code)
    kline = detail["kline"]
    closes = [k["close"] for k in kline]
    kline_brief = "\n".join(
        f"{k['date']}: 开{k['open']} 高{k['high']} 低{k['low']} 收{k['close']} 涨跌{k['pct_chg']}%"
        for k in kline[-10:]
    )

    quote = {"name": stock["name"], "code": stock["code"], "price": closes[-1]}

    # ---- 数据分析师（确定性，先跑） ----
    yield {"type": "agent_start", "agent": "data"}
    data_out = data_agent(stock, kline)
    yield {"type": "agent_done", "agent": "data", "content": data_out}

    # ---- 三位分析师并行 ----
    news = get_demo_news(stock)
    news_text = "\n".join(f"- {n}" for n in news)
    yield {"type": "agent_start", "agent": "tech"}
    yield {"type": "agent_start", "agent": "fundamental"}
    yield {"type": "agent_start", "agent": "sentiment"}

    tech_task = _llm(BASE_SYSTEM, AGENT_PROMPTS["tech"].format(
        data=data_out + f"\n\n近10日K线：\n{kline_brief}"))
    fund_task = _llm(BASE_SYSTEM, AGENT_PROMPTS["fundamental"].format(
        name=stock["name"], code=stock["code"], industry=stock["industry"],
        pe=stock["pe"], pb=stock["pb"], roe=stock["roe"], price=closes[-1]))
    sent_task = _llm(BASE_SYSTEM, AGENT_PROMPTS["sentiment"].format(news=news_text))

    results = await asyncio.gather(tech_task, fund_task, sent_task)
    tech_out, fund_out, sent_out = results
    yield {"type": "agent_done", "agent": "tech", "content": tech_out}
    yield {"type": "agent_done", "agent": "fundamental", "content": fund_out}
    yield {"type": "agent_done", "agent": "sentiment", "content": sent_out}

    # ---- 风控经理 ----
    yield {"type": "agent_start", "agent": "risk"}
    risk_out = await _llm(BASE_SYSTEM, AGENT_PROMPTS["risk"].format(
        tech=tech_out, fundamental=fund_out, sentiment=sent_out), max_tokens=380)
    yield {"type": "agent_done", "agent": "risk", "content": risk_out}

    # ---- 首席分析师（流式输出） ----
    yield {"type": "agent_start", "agent": "chief"}
    chief_prompt = CHIEF_PROMPT.format(
        data=data_out, tech=tech_out, fundamental=fund_out, sentiment=sent_out, risk=risk_out)
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/chat", json={
                "model": OLLAMA_CHAT_MODEL,
                "messages": [
                    {"role": "system", "content": BASE_SYSTEM},
                    {"role": "user", "content": chief_prompt},
                ],
                "stream": True,
                "options": {"temperature": 0.4, "num_predict": 640},
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
                        yield {"type": "chief_chunk", "content": content}
                    if chunk.get("done"):
                        break
    except Exception as e:
        yield {"type": "chief_chunk", "content": f"（首席分析师生成失败：{e}）"}

    yield {"type": "done", "quote": quote, "news": news, "kline": kline[-30:],
           "agents": {a["key"]: a["name"] for a in AGENTS}}
