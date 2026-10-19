"""天眼通 - 全局配置

所有第三方服务地址均可通过环境变量覆盖；演示环境默认指向本机。
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent          # backend/tyt
BACKEND_DIR = BASE_DIR.parent                       # backend/
ROOT_DIR = BACKEND_DIR.parent                       # SkyEyev2.0/

# ==================== MySQL 8.0（业务库） ====================
MYSQL_HOST = os.getenv("TYT_MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("TYT_MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("TYT_MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("TYT_MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = os.getenv("TYT_MYSQL_DATABASE", "SkyEye2.0")

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    "?charset=utf8mb4"
)

# ==================== Redis 7（缓存 / 配额 / Celery Broker） ====================
REDIS_HOST = os.getenv("TYT_REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("TYT_REDIS_PORT", "6380"))
REDIS_PASSWORD = os.getenv("TYT_REDIS_PASSWORD", "")
REDIS_DB = int(os.getenv("TYT_REDIS_DB", "0"))

REDIS_URL = f"redis://{':' + REDIS_PASSWORD + '@' if REDIS_PASSWORD else ''}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# ==================== Neo4j 5（关系图谱） ====================
NEO4J_URI = os.getenv("TYT_NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = os.getenv("TYT_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("TYT_NEO4J_PASSWORD", "skyeye123456")

# ==================== Elasticsearch（全文检索，可选） ====================
# ES 未启动时自动降级为 MySQL FULLTEXT(ngram) 检索，不影响功能可用性
ES_ENABLED = os.getenv("TYT_ES_ENABLED", "0") == "1"
ES_URL = os.getenv("TYT_ES_URL", "http://127.0.0.1:9200")
ES_INDEX_COMPANY = "tyt_companies"

# ==================== Ollama（本地 AI） ====================
OLLAMA_BASE_URL = os.getenv("TYT_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_CHAT_MODEL = os.getenv("TYT_OLLAMA_CHAT_MODEL", "qwen2.5:1.5b")
OLLAMA_EMBED_MODEL = os.getenv("TYT_OLLAMA_EMBED_MODEL", "quentinz/bge-large-zh-v1.5:latest")
OLLAMA_VISION_MODEL = os.getenv("TYT_OLLAMA_VISION_MODEL", "minicpm-v4.6:latest")

# ==================== 百炼大模型（阿里云 DashScope，OpenAI 兼容模式） ====================
# 管理端「模型管理」开关打开后，高级会员及以上角色的 AI 问答走百炼；失败自动降级本地 qwen2.5
BAILIAN_ENABLED = os.getenv("TYT_BAILIAN_ENABLED", "0") == "1"   # 仅作默认值，运行态以 system_settings 表为准
BAILIAN_BASE_URL = os.getenv("TYT_BAILIAN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
BAILIAN_MODEL = os.getenv("TYT_BAILIAN_MODEL", "qwen-plus")
BAILIAN_API_KEY = os.getenv("TYT_BAILIAN_API_KEY",
                            "sk-ws-H.PEHMMEE.zm1V.MEQCIAbi0vQsVI8lHiyLhOAuMzbRbhAQJtlmsX75nPtlGS-HAiAuMeVne7CYI8pZrZSGnD-W1HNOmkYdCdmp4wrsq51o1w")
# 可使用百炼的最低角色（普通用户始终走本地 qwen2.5:1.5b）
BAILIAN_MIN_ROLE = os.getenv("TYT_BAILIAN_MIN_ROLE", "premium")

# ---- 百炼云端识图模型（AI 识图，OpenAI 兼容模式）----
# 管理端「模型管理-百炼识图」开关打开后，高级会员及以上角色的识图走百炼；
# 普通用户始终本地 minicpm-v；百炼调用失败自动降级本地 minicpm-v
BAILIAN_VISION_MODEL = os.getenv("TYT_BAILIAN_VISION_MODEL", "qwen-vl-ocr")
BAILIAN_VISION_API_KEY = os.getenv("TYT_BAILIAN_VISION_API_KEY",
                                   "sk-ws-H.PPHPREL.tDoh.MEQCICk2Modae5kvzK_U1y7Ggqn99Pz1jMtcW5cfNOYixXqmAiAlJRnBDjXWqfnftqcOM1KxQfIjb4rE0NEmFtsLw4RZhQ")

# ==================== 天气（Open-Meteo 开放数据，无需 Key） ====================
WEATHER_CACHE_MINUTES = 30
DEFAULT_CITY = "杭州市"
DEFAULT_LAT = 30.2741
DEFAULT_LON = 120.1551

# ==================== 高德地图 Web 端 Key（天气地图展示） ====================
AMAP_JS_KEY = os.getenv("TYT_AMAP_KEY", "554871e15a2759c608c6f00f41289ad5")

# ==================== Rerank 重排服务（bge-reranker-v2-m3） ====================
RERANK_URL = os.getenv("TYT_RERANK_URL", "http://127.0.0.1:9999")

# ==================== Qdrant 向量库 ====================
# 本地持久化模式（QdrantClient(path=...)），无需独立服务进程，
# 等价于原 Chroma PersistentClient，重启后数据保留于本地目录。
QDRANT_DIR = str(ROOT_DIR / "database" / "tyt_qdrant")
QDRANT_COLLECTION = "tyt_knowledge"

# ==================== JWT ====================
JWT_SECRET_KEY = os.getenv("TYT_JWT_SECRET", "tyt-skyeye2-secret-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
REFRESH_TOKEN_EXPIRE_DAYS = 7

# ==================== AES-GCM（敏感字段加密） ====================
# 生产环境必须通过环境变量注入 32 字节密钥
AES_KEY_HEX = os.getenv("TYT_AES_KEY", "6a5a7d3f2b8c4e1f9a0d6c3b7e2f5a48120a4b6c8d0e2f4a6b8c0d2e4f6a8b0c")

# ==================== 角色与配额 ====================
ROLES = ("guest", "user", "premium", "enterprise_admin", "platform_admin")
ROLE_NAMES = {
    "guest": "游客",
    "user": "普通用户",
    "premium": "高级会员",
    "enterprise_admin": "企业管理员",
    "platform_admin": "平台管理员",
}

# 每日配额：-1 表示不限次
QUOTA_MATRIX = {
    "guest": {
        "life_query": 3,       # 生活类查询（商家/房源/求职公司）
        "person_query": 0,     # 个人查询（游客禁止）
        "biz_basic": 3,        # 商业类基础工商查询
        "biz_risk": 0,         # 风险查询
        "biz_graph": 0,        # 图谱查询
        "report": 0,           # 尽调报告
        "monitor": 0,          # 商业监控
        "post": 0,             # 发帖
        "ai_chat": 0,          # AI 问答
        "vision": 0,           # AI 识图（游客禁止）
        "stock_analysis": 0,   # 多智能体股票分析（游客禁止）
    },
    "user": {
        "life_query": -1, "person_query": 3, "biz_basic": -1,
        "biz_risk": 10, "biz_graph": 5, "report": 0, "monitor": 0,
        "post": 10, "ai_chat": 20, "vision": 5, "stock_analysis": 3,
    },
    "premium": {
        "life_query": -1, "person_query": 10, "biz_basic": -1,
        "biz_risk": -1, "biz_graph": -1, "report": 10, "monitor": -1,
        "post": -1, "ai_chat": -1, "vision": -1, "stock_analysis": 10,
    },
    "enterprise_admin": {
        "life_query": -1, "person_query": 3, "biz_basic": -1,
        "biz_risk": -1, "biz_graph": 20, "report": 30, "monitor": -1,
        "post": 10, "ai_chat": 50, "vision": -1, "stock_analysis": 20,
    },
    "platform_admin": {
        "life_query": -1, "person_query": -1, "biz_basic": -1,
        "biz_risk": -1, "biz_graph": -1, "report": -1, "monitor": -1,
        "post": -1, "ai_chat": -1, "vision": -1, "stock_analysis": -1,
    },
}

# ==================== 会员订阅定价（元，演示环境模拟支付） ====================
# 单一会员类型：高级会员；两种订阅方案：包月 / 连续包月
MEMBER_PRICE_MONTHLY = 35.0          # 包月价
MEMBER_FIRST_MONTHLY = 25.0          # 包月首月优惠价（首次订阅）
MEMBER_PRICE_AUTO = 29.0             # 连续包月价（自动续费，可随时取消）
MEMBER_FIRST_AUTO = 19.0             # 连续包月首月优惠价（首次订阅）
MEMBER_DAYS_PER_PERIOD = 30          # 每期 30 天

# ==================== 业务常量 ====================
DEMO_SOURCE = "演示数据（整理自公开工商信息，仅供功能验证）"
RISK_TYPES = ("judicial", "business", "finance", "public_opinion", "admin_penalty")
RISK_TYPE_NAMES = {
    "judicial": "司法风险", "business": "经营风险",
    "finance": "财务风险", "public_opinion": "舆情风险",
    "admin_penalty": "行政处罚",
}

# UGC 先审后发：敏感词命中直接拒审
SENSITIVE_WORDS = [
    "诈骗", "赌博", "色情", "毒品", "传销", "非法集资", "洗钱",
    "人肉", "开盒", "身份证号", "手机号是", "住址是",
    "造谣", "诽谤", "去死", "辱骂",
]

# 举报理由
REPORT_REASONS = ["虚假信息", "侵犯隐私", "造谣诽谤", "辱骂攻击", "广告 spam", "其他"]

# 报告导出目录
REPORT_DIR = ROOT_DIR / "storage" / "reports"
UPLOAD_DIR = ROOT_DIR / "storage" / "uploads"

# 数据源登记（合规溯源，见 docs/06_数据来源合规说明.md）
DATA_SOURCES = [
    {"code": "gsxt", "name": "国家企业信用信息公示系统", "type": "official_web",
     "url": "https://www.gsxt.gov.cn", "license_note": "公开查询渠道；本平台通过管理端人工导入查询结果，不做自动化爬取"},
    {"code": "creditchina", "name": "信用中国", "type": "official_web",
     "url": "https://www.creditchina.gov.cn", "license_note": "公开查询渠道；行政许可/行政处罚信息人工导入"},
    {"code": "wenshu", "name": "中国裁判文书网", "type": "official_web",
     "url": "https://wenshu.court.gov.cn", "license_note": "公开司法文书；脱敏后人工导入"},
    {"code": "zxgk", "name": "中国执行信息公开网", "type": "official_web",
     "url": "http://zxgk.court.gov.cn", "license_note": "失信/被执行人公开信息；脱敏后人工导入"},
    {"code": "people_news", "name": "人民网资讯（舆情）", "type": "official_web",
     "url": "http://www.people.com.cn", "license_note": "遵守 robots.txt 与 Crawl-delay 的合规采集（crawler.py）"},
    {"code": "baostock", "name": "baostock 证券数据（财务）", "type": "official_sdk",
     "url": "http://www.baostock.com", "license_note": "官方 SDK 数据接口，公开证券行情"},
    {"code": "demo_seed", "name": "演示种子数据", "type": "seed",
     "url": "", "license_note": "本仓库内置演示数据，结构真实、内容标注演示，不可用于生产决策"},
    {"code": "third_party_api", "name": "第三方商业 API（天眼查/企查查等）", "type": "third_party_api",
     "url": "", "license_note": "需购买商用授权后由管理端配置；未配置时不提供该通道"},
]

