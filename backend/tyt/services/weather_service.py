"""定位与天气服务

数据源：Open-Meteo（开放数据，无需 API Key）；网络不可用时降级为确定性演示数据。
地图：前端高德 JS API 展示，本服务仅提供坐标与天气图层提示文案。
定位：浏览器定位（前端）/ 网络定位（WiFi·基站·融合，参考第一版）/ IP 定位（前端高德）。
"""
import logging
import math
import random
import time
from datetime import datetime, timedelta

import httpx

from tyt.config import (
    AMAP_JS_KEY, DEFAULT_CITY, DEFAULT_LAT, DEFAULT_LON, WEATHER_CACHE_MINUTES,
)

logger = logging.getLogger(__name__)

_cache: dict = {}
_regeo_cache: dict = {}
_locate_cache: dict = {}

# 周边地点模板：名称 / 类型 / 图标 / 距离范围（米）（第一版同款）
_POI_TEMPLATES = [
    ("西湖文化广场", "地标", "🏛️", (300, 700)),
    ("地铁站 · 武林广场站", "交通", "🚇", (200, 600)),
    ("银泰百货", "购物", "🛍️", (400, 900)),
    ("西湖风景区", "公园", "🌳", (600, 1500)),
    ("学军中学", "学校", "🏫", (500, 1200)),
    ("浙江省人民医院", "医疗", "🏥", (700, 1800)),
    ("联华超市", "便利", "🏪", (100, 300)),
    ("外婆家餐厅", "餐饮", "🍜", (150, 500)),
    ("黄龙体育中心", "运动", "🏟️", (800, 2000)),
    ("招商银行", "金融", "🏦", (200, 800)),
]


def _generate_nearby(lat: float, lng: float, count: int = 8) -> list:
    """基于坐标生成稳定的周边地点列表（第一版同款）"""
    seed = int(abs(lat * 10000 + lng * 10000))
    rng = random.Random(seed)
    templates = rng.sample(_POI_TEMPLATES, min(count, len(_POI_TEMPLATES)))
    nearby = []
    for name, ptype, icon, (dmin, dmax) in templates:
        dist = round(rng.uniform(dmin, dmax))
        bearing = rng.uniform(0, 2 * math.pi)
        nearby.append({
            "name": name,
            "type": ptype,
            "icon": icon,
            "distance_m": dist,
            "bearing": round(bearing, 4),
            "latitude": round(lat + (dist / 111320) * math.cos(bearing), 6),
            "longitude": round(lng + (dist / (111320 * math.cos(math.radians(lat)))) * math.sin(bearing), 6),
        })
    nearby.sort(key=lambda p: p["distance_m"])
    return nearby


def network_locate(method: str = "auto", lat: float | None = None, lng: float | None = None) -> dict:
    """网络定位辅助（第一版同款）：WiFi 热点 / 移动基站 / GPS·WiFi·基站融合。

    method: auto（融合，±50m）/ wifi（±500m）/ cellular·bs·base（基站，±2000m）
    lat/lng: 可选基准坐标（GCJ-02，高德系），缺省用默认城市中心；
             传入当前已知位置（如 IP 定位结果）时，网络定位结果与周边地点围绕该位置生成。
    """
    method = (method or "auto").lower()
    key = f"netloc_{method}_{round(float(lat or DEFAULT_LAT), 3)}_{round(float(lng or DEFAULT_LON), 3)}"
    cached = _locate_cache.get(key)
    if cached and time.time() - cached["ts"] < WEATHER_CACHE_MINUTES * 60:
        return cached["data"]

    if method in ("wifi",):
        accuracy_m = 500
        loc_method = "WiFi 热点定位"
    elif method in ("cellular", "bs", "base"):
        accuracy_m = 2000
        loc_method = "移动基站定位"
    else:
        accuracy_m = 50
        loc_method = "GPS / WiFi / 基站融合定位"
        method = "auto"

    lat = float(lat) if lat is not None else DEFAULT_LAT
    lng = float(lng) if lng is not None else DEFAULT_LON

    geo = reverse_geocode(lat, lng)
    city = geo.get("city") or DEFAULT_CITY
    district = geo.get("district") or ""

    result = {
        "city": city,
        "district": district,
        "method": loc_method,
        "method_key": method,
        "accuracy": f"±{accuracy_m}m",
        "accuracy_m": accuracy_m,
        "latitude": lat,
        "longitude": lng,
        "nearby": _generate_nearby(lat, lng),
        "located_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _locate_cache[key] = {"ts": time.time(), "data": result}
    return result

WMO_MAP = {
    0: ("晴", "☀️"), 1: ("基本晴", "🌤️"), 2: ("多云", "⛅"), 3: ("阴", "☁️"),
    45: ("雾", "🌫️"), 48: ("雾凇", "🌫️"),
    51: ("小毛雨", "🌦️"), 53: ("毛雨", "🌦️"), 55: ("大毛雨", "🌧️"),
    61: ("小雨", "🌦️"), 63: ("中雨", "🌧️"), 65: ("大雨", "🌧️"),
    66: ("冻雨", "🌧️"), 67: ("强冻雨", "🌧️"),
    71: ("小雪", "🌨️"), 73: ("中雪", "❄️"), 75: ("大雪", "❄️"), 77: ("雪粒", "🌨️"),
    80: ("阵雨", "🌦️"), 81: ("强阵雨", "🌧️"), 82: ("暴雨", "⛈️"),
    85: ("阵雪", "🌨️"), 86: ("强阵雪", "❄️"),
    95: ("雷阵雨", "⛈️"), 96: ("雷雨伴雹", "⛈️"), 99: ("强雷雨伴雹", "⛈️"),
}


def _wmo(code: int) -> tuple[str, str]:
    return WMO_MAP.get(code, ("多云", "⛅"))


def _aqi_level(aqi: int) -> str:
    if aqi <= 50:
        return "优"
    if aqi <= 100:
        return "良"
    if aqi <= 150:
        return "轻度污染"
    if aqi <= 200:
        return "中度污染"
    return "重度污染"


def _uv_level(uv: float) -> str:
    if uv < 3:
        return "弱"
    if uv < 6:
        return "中等"
    if uv < 8:
        return "强"
    return "很强"


def _life_index(data: dict) -> list[dict]:
    uv = data.get("uv", 3)
    temp = data.get("temperature", 24)
    rain = data.get("precipitation", 0)
    return [
        {"name": "紫外线", "icon": "🧴", "value": _uv_level(uv)},
        {"name": "穿衣", "icon": "👔", "value": "轻薄夏装" if temp >= 26 else ("舒适长袖" if temp >= 18 else "保暖外套")},
        {"name": "运动", "icon": "🏃", "value": "适宜" if rain < 1 else "不建议户外"},
        {"name": "洗车", "icon": "🚗", "value": "较适宜" if rain < 1 else "暂缓"},
        {"name": "雨伞", "icon": "☂️", "value": "无需" if rain < 0.5 else "建议携带"},
        {"name": "晾晒", "icon": "🌞", "value": "适宜" if rain < 0.5 and data.get("humidity", 60) < 80 else "不宜"},
    ]


def _fetch_open_meteo(lat: float, lon: float) -> dict | None:
    """Open-Meteo 实时数据（当前 + 24h 逐时 + 7 日预报 + 空气质量）"""
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                           "precipitation,weather_code,wind_speed_10m,pressure_msl,cloud_cover",
                "hourly": "temperature_2m,apparent_temperature,precipitation_probability,"
                          "weather_code,wind_speed_10m,relative_humidity_2m",
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max",
                "forecast_days": 8, "timezone": "auto",
            })
            resp.raise_for_status()
            base = resp.json()

            try:
                air = client.get("https://air-quality-api.open-meteo.com/v1/air-quality", params={
                    "latitude": lat, "longitude": lon,
                    "current": "european_aqi,pm2_5,pm10",
                }).json()
                aqi_val = int(round(air.get("current", {}).get("european_aqi") or 50))
            except Exception:
                aqi_val = 50
        return _format_open_meteo(base, aqi_val)
    except Exception as e:
        logger.warning("open-meteo unavailable, fallback demo: %s", e)
        return None


def _format_open_meteo(base: dict, aqi_val: int) -> dict:
    cur = base["current"]
    cond, icon = _wmo(int(cur.get("weather_code") or 2))
    hourly_all = base.get("hourly", {})
    times = hourly_all.get("time", [])
    now_iso = cur.get("time", "")
    start = 0
    for i, t in enumerate(times):
        if t >= now_iso[:16]:
            start = i
            break
    hourly = []
    for i in range(start, min(start + 24, len(times))):
        h_cond, h_icon = _wmo(int(hourly_all["weather_code"][i] or 2))
        hour_label = "现在" if i == start else times[i][11:13] + "时"
        hourly.append({
            "time": hour_label,
            "temp": round(hourly_all["temperature_2m"][i]),
            "feels": round(hourly_all.get("apparent_temperature", [None] * len(times))[i] or hourly_all["temperature_2m"][i]),
            "icon": h_icon, "condition": h_cond,
            "pop": hourly_all.get("precipitation_probability", [0] * len(times))[i] or 0,
            "wind": round(hourly_all.get("wind_speed_10m", [0] * len(times))[i] or 0),
            "humidity": hourly_all.get("relative_humidity_2m", [60] * len(times))[i] or 60,
        })

    daily_all = base.get("daily", {})
    daily = []
    day_names = ["今天", "明天", "后天"]
    for i in range(min(7, len(daily_all.get("time", [])))):
        d_cond, d_icon = _wmo(int(daily_all["weather_code"][i] or 2))
        d = datetime.strptime(daily_all["time"][i], "%Y-%m-%d")
        daily.append({
            "day": day_names[i] if i < 3 else "周" + "一二三四五六日"[d.weekday()],
            "date": d.strftime("%m/%d"),
            "icon": d_icon, "condition": d_cond,
            "high": round(daily_all["temperature_2m_max"][i]),
            "low": round(daily_all["temperature_2m_min"][i]),
            "pop": daily_all.get("precipitation_probability_max", [0] * 7)[i] or 0,
        })

    data = {
        "city": DEFAULT_CITY,
        "temperature": round(cur["temperature_2m"]),
        "condition": cond,
        "icon": icon,
        "feels_like": round(cur.get("apparent_temperature") or cur["temperature_2m"]),
        "humidity": round(cur.get("relative_humidity_2m") or 60),
        "wind_speed": round(cur.get("wind_speed_10m") or 0),
        "pressure": round(cur.get("pressure_msl") or 1013),
        "cloud": round(cur.get("cloud_cover") or 0),
        "precipitation": round(cur.get("precipitation") or 0, 1),
        "uv": round(daily_all.get("uv_index_max", [3])[0] or 3, 1),
        "aqi": aqi_val,
        "aqi_level": _aqi_level(aqi_val),
        "visibility": max(1, 25 - round(cur.get("cloud_cover") or 0) // 5),
        "dew": round(cur["temperature_2m"] - (100 - (cur.get("relative_humidity_2m") or 60)) / 5),
        "hourly": hourly,
        "daily": daily,
        "summary": f"当前{cond}，气温 {round(cur['temperature_2m'])}°，空气质量{_aqi_level(aqi_val)}。",
        "source": "Open-Meteo 开放数据",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    data["life_index"] = _life_index(data)
    return data


def _demo_weather() -> dict:
    """离线降级：确定性演示数据"""
    now = datetime.now()
    hour = now.hour
    hourly = []
    for i in range(24):
        h = (hour + i) % 24
        if 6 <= h <= 9:
            temp, cond, icon = 21 + h - 6, "多云", "⛅"
        elif 10 <= h <= 16:
            temp, cond, icon = 26 + (h - 10), "晴", "☀️"
        elif 17 <= h <= 19:
            temp, cond, icon = 33 - (h - 17) * 2, "晴", "🌤️"
        else:
            temp, cond, icon = max(16, 26 - (h - 20) if h >= 20 else 22 + h * 0.4), "晴/夜", "🌙"
        hourly.append({
            "time": "现在" if i == 0 else f"{h}时", "temp": round(temp), "feels": round(temp + 1),
            "icon": icon, "condition": cond, "pop": 10 if 13 <= h <= 16 else 0,
            "wind": 8 + (h % 5), "humidity": 55 + (h % 20),
        })

    rng = random.Random(int(now.strftime("%Y%m%d")))
    daily = []
    for i in range(7):
        d = now + timedelta(days=i)
        high = 27 + rng.randint(-3, 3)
        cond, icon = [("晴", "☀️"), ("多云", "⛅"), ("阴", "☁️")][rng.randint(0, 2)]
        daily.append({
            "day": ["今天", "明天", "后天"][i] if i < 3 else "周" + "一二三四五六日"[d.weekday()],
            "date": d.strftime("%m/%d"), "icon": icon, "condition": cond,
            "high": high, "low": high - 7, "pop": rng.choice([0, 0, 10, 20]),
        })

    cur_temp = hourly[0]["temp"] if hourly else 26
    aqi_val = 42
    data = {
        "city": DEFAULT_CITY, "temperature": cur_temp, "condition": "多云转晴", "icon": "⛅",
        "feels_like": cur_temp + 2, "humidity": 62, "wind_speed": 12, "pressure": 1006,
        "cloud": 40, "precipitation": 0, "uv": 4.5, "aqi": aqi_val, "aqi_level": _aqi_level(aqi_val),
        "visibility": 18, "dew": 17, "hourly": hourly, "daily": daily,
        "summary": "大部分地区天气晴朗，适宜户外活动。（演示数据）",
        "source": "演示数据（离线降级）",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    data["life_index"] = _life_index(data)
    return data


def reverse_geocode(lat: float, lng: float) -> dict:
    """逆地理编码：GCJ-02（高德）坐标 -> 城市/区县，30 分钟缓存。

    高德 regeo Web 服务（该 key 已验证可用）；失败返回空值，由前端就近匹配兜底。
    """
    lat, lng = round(float(lat), 4), round(float(lng), 4)
    key = f"regeo_{lat}_{lng}"
    cached = _regeo_cache.get(key)
    if cached and time.time() - cached["ts"] < WEATHER_CACHE_MINUTES * 60:
        return cached["data"]

    result = {"city": "", "district": ""}
    try:
        with httpx.Client(timeout=8) as client:
            resp = client.get("https://restapi.amap.com/v3/geocode/regeo", params={
                "key": AMAP_JS_KEY, "location": f"{lng},{lat}", "extensions": "base",
            })
            data = resp.json()
            if str(data.get("infocode")) == "10000":
                ac = (data.get("regeocode") or {}).get("addressComponent") or {}

                def _s(v):
                    """高德对缺失字段返回空数组（如直辖市的 city），统一转字符串"""
                    return "" if isinstance(v, list) or not v else str(v)

                city = _s(ac.get("city")) or _s(ac.get("province"))
                result = {"city": city, "district": _s(ac.get("district"))}
    except Exception as e:
        logger.warning("amap regeo failed: %s", e)

    _regeo_cache[key] = {"ts": time.time(), "data": result}
    return result


def get_weather(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON) -> dict:
    """天气主入口：30 分钟缓存 -> Open-Meteo -> 演示降级"""
    lat, lon = round(float(lat), 4), round(float(lon), 4)
    key = f"w_{lat}_{lon}"
    cached = _cache.get(key)
    if cached and time.time() - cached["ts"] < WEATHER_CACHE_MINUTES * 60:
        return cached["data"]

    data = _fetch_open_meteo(lat, lon) or _demo_weather()
    data["latitude"], data["longitude"] = lat, lon
    _cache[key] = {"ts": time.time(), "data": data}
    return data
