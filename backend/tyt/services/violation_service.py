"""内容审核违规标准：可维护词库 + 待审内容自动识别 + 全量违规扫描

第一版在知识编辑框输入时用固定词表实时检测；第二版将词库落到 MySQL（violation_words 表），
管理员可在内容审核页维护：从第一版预设标准中勾选启用，或手动添加自定义词。
词库带分类（第一版分类体系），加载待审列表时自动识别命中词，并提供跨 5 类待审内容的全量扫描。
"""
import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from tyt.models import (
    Complaint, MerchantReview, Post, PostComment, ReportRecord, ViolationWord,
)

logger = logging.getLogger(__name__)

# 第一版违规词库分类体系（dashboard.html 违规词库管理弹窗）
CATEGORIES = ["通用", "违法犯罪", "暴力恐怖", "网络安全", "造谣诽谤", "歧视仇恨", "灰黑产业"]

# 预设标准词库：第一版实时检测固定词表（frontend/assets/app.js badWords 18 词）按分类归位，
# 并按第一版各分类补充常见标准词，供管理员勾选启用
PRESET_WORDS: list[dict] = [
    {"word": "赌博", "category": "通用"},
    {"word": "色情", "category": "通用"},
    {"word": "毒品", "category": "通用"},
    {"word": "暴力", "category": "通用"},
    {"word": "诈骗", "category": "通用"},
    {"word": "传销", "category": "通用"},
    {"word": "洗钱", "category": "通用"},
    {"word": "枪支", "category": "违法犯罪"},
    {"word": "爆炸", "category": "违法犯罪"},
    {"word": "走私", "category": "违法犯罪"},
    {"word": "行贿", "category": "违法犯罪"},
    {"word": "恐怖", "category": "暴力恐怖"},
    {"word": "极端", "category": "暴力恐怖"},
    {"word": "袭击", "category": "暴力恐怖"},
    {"word": "自杀", "category": "暴力恐怖"},
    {"word": "黑客", "category": "网络安全"},
    {"word": "病毒", "category": "网络安全"},
    {"word": "木马", "category": "网络安全"},
    {"word": "勒索", "category": "网络安全"},
    {"word": "钓鱼", "category": "网络安全"},
    {"word": "谣言", "category": "造谣诽谤"},
    {"word": "诽谤", "category": "造谣诽谤"},
    {"word": "造谣", "category": "造谣诽谤"},
    {"word": "传谣", "category": "造谣诽谤"},
    {"word": "歧视", "category": "歧视仇恨"},
    {"word": "仇恨", "category": "歧视仇恨"},
    {"word": "辱骂", "category": "歧视仇恨"},
    {"word": "地域黑", "category": "歧视仇恨"},
    {"word": "刷单", "category": "灰黑产业"},
    {"word": "套现", "category": "灰黑产业"},
    {"word": "高利贷", "category": "灰黑产业"},
    {"word": "代开发票", "category": "灰黑产业"},
]

_PRESET_LOOKUP = {p["word"]: p["category"] for p in PRESET_WORDS}


def _preset_category(word: str) -> str:
    """已知预设词返回其分类，未知词归入通用"""
    return _PRESET_LOOKUP.get(word, "通用")


def _rows_to_items(rows) -> list[dict]:
    return [{"word": r.word, "category": r.category or "通用"} for r in rows]


def get_words(db: Session) -> list[str]:
    """读取违规标准词库（仅词，检测用）；空表时播种第一版默认 18 词"""
    return [i["word"] for i in get_word_items(db)]


def get_word_items(db: Session) -> list[dict]:
    """读取违规标准词库（词 + 分类）；空表时播种第一版默认 18 词"""
    rows = db.execute(select(ViolationWord).order_by(ViolationWord.id)).scalars().all()
    if not rows:
        seeded = [p for p in PRESET_WORDS if p["word"] in (
            "赌博", "色情", "毒品", "暴力", "诈骗", "传销", "恐怖", "极端",
            "枪支", "爆炸", "谣言", "诽谤", "歧视", "自杀", "黑客", "病毒", "木马", "勒索")]
        db.add_all([ViolationWord(word=p["word"], category=p["category"]) for p in seeded])
        db.commit()
        return list(seeded)
    return _rows_to_items(rows)


def set_words(db: Session, items: list) -> int:
    """全量替换违规标准词库（items 为 {word, category} 或纯字符串），返回更新后的词数"""
    cleaned: list[dict] = []
    seen: set[str] = set()
    for it in items:
        if isinstance(it, str):
            word, category = it.strip(), "通用"
        else:
            word = (it.get("word") or "").strip() if hasattr(it, "get") else str(it).strip()
            category = (it.get("category") or "").strip() if hasattr(it, "get") else "通用"
        if not word or word in seen or len(word) > 64:
            continue
        seen.add(word)
        cleaned.append({"word": word, "category": category if category in CATEGORIES else "通用"})
    if not cleaned:
        return 0
    db.execute(delete(ViolationWord))
    db.add_all([ViolationWord(word=i["word"], category=i["category"]) for i in cleaned])
    db.commit()
    logger.info("违规标准词库已更新：%d 个词", len(cleaned))
    return len(cleaned)


def check_text(text: str, words: list[str]) -> list[str]:
    """返回文本中命中的违规词（去重，保持词库顺序）"""
    if not text:
        return []
    return [w for w in words if w in text]


def _item_text(content_type: str, r) -> str:
    """拼接待审条目的可检文本"""
    if content_type == "post":
        return f"{r.title or ''} {r.content or ''}"
    if content_type == "report":
        return f"{r.reason or ''} {r.description or ''}"
    return r.content or ""


# 各内容类型的待审查询模型与展示名
PENDING_MODELS = {
    "post": (Post, "帖子"),
    "comment": (PostComment, "帖子评论"),
    "review": (MerchantReview, "商家评价"),
    "complaint": (Complaint, "投诉"),
    "report": (ReportRecord, "举报"),
}


def scan_pending(db: Session) -> dict:
    """违规扫描：对 5 类全部待审内容做命中检测，返回分类统计与命中明细"""
    words = get_words(db)
    stats = {}
    hits = []
    total_pending = 0
    total_hit = 0
    for ctype, (model, label) in PENDING_MODELS.items():
        rows = db.execute(select(model).where(model.status == "pending")).scalars().all()
        type_hits = []
        for r in rows:
            found = check_text(_item_text(ctype, r), words)
            if found:
                type_hits.append({
                    "type": ctype, "type_name": label, "id": r.id,
                    "preview": _item_text(ctype, r)[:60],
                    "violations": found,
                })
        stats[ctype] = {"type_name": label, "pending": len(rows), "hit": len(type_hits)}
        total_pending += len(rows)
        total_hit += len(type_hits)
        hits.extend(type_hits)
    return {
        "words": words, "total_pending": total_pending, "total_hit": total_hit,
        "stats": stats, "hits": hits,
    }
