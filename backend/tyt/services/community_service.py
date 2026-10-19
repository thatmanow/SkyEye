"""生活圈与 UGC 审核：先审后发、敏感词防护、举报处理"""
import json
import logging

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from tyt.config import SENSITIVE_WORDS
from tyt.models import (
    Post, PostComment, PostLike, ReportRecord,
    Merchant, MerchantReview, Complaint, HousingEstate, Notification, User,
)

logger = logging.getLogger(__name__)


def sensitive_check(text: str) -> tuple[bool, str | None]:
    """敏感词命中即拒审（造谣诽谤/违法/隐私猎取类词）"""
    for w in SENSITIVE_WORDS:
        if w in text:
            return False, w
    return True, None


# ==================== 帖子 ====================

# 帖子话题分类：按标题+正文关键词命中数自动识别（命中最多者胜出，无命中归为其他）
TOPIC_RULES: dict[str, list[str]] = {
    "餐饮美食": ["餐厅", "饭店", "外卖", "奶茶", "咖啡", "火锅", "烧烤", "小吃", "食品", "零食",
               "吃", "菜单", "厨师", "堂食", "团购餐", "烘焙", "蛋糕", "饮品"],
    "租房住房": ["租房", "房东", "中介", "小区", "押金", "合租", "搬家", "水电", "房屋", "出租",
               "物业", "邻居", "房贷", "装修"],
    "消费购物": ["购物", "网购", "电商", "退货", "退款", "假货", "商家", "超市", "商场", "打折",
               "优惠", "直播间", "二手", "闲鱼", "买", "客服", "发货"],
    "交通出行": ["打车", "网约车", "公交", "地铁", "停车", "高铁", "机票", "火车", "出行", "驾照",
               "堵车", "导航", "租车", "旅行", "景区"],
    "求职职场": ["招聘", "面试", "工作", "公司", "加班", "工资", "offer", "入职", "离职", "职场",
               "简历", "试用期", "裁员", "老板"],
    "教育培训": ["培训", "课程", "辅导", "学习", "机构", "考证", "考试", "老师", "学费", "孩子",
               "学校", "幼儿园", "留学", "考研"],
    "医疗健康": ["医院", "看病", "医生", "体检", "牙", "中医", "健康", "医美", "美容", "药房",
               "挂号", "手术", "疫苗", "养生"],
    "金融服务": ["银行", "贷款", "保险", "理财", "信用卡", "利息", "分期", "投资", "支付", "基金",
               "股票", "汇率", "手续费", "扣费"],
    "生活服务": ["快递", "维修", "保洁", "家政", "理发", "宽带", "健身", "宠物", "洗衣", "开锁",
               "搬家", "燃气", "暖气", "装修", "办卡", "会员卡", "预付", "闭店", "跑路"],
}
TOPICS = list(TOPIC_RULES.keys()) + ["其他"]


def detect_topic(title: str, content: str) -> str:
    """根据标题+正文自动识别话题分类：统计各话题关键词命中数，取最高者"""
    text = f"{title or ''} {content or ''}"
    if not text.strip():
        return "其他"
    best, best_hits = "其他", 0
    for topic, words in TOPIC_RULES.items():
        hits = sum(1 for w in words if w in text)
        if hits > best_hits:
            best, best_hits = topic, hits
    return best


def create_post(db: Session, user_id: int, data: dict) -> tuple[bool, str, int | None]:
    ok, word = sensitive_check(data["title"] + data["content"])
    if not ok:
        return False, f"内容包含敏感词「{word}」，未通过初审；请修改后重试（平台禁止造谣诽谤与隐私猎取）", None
    data = dict(data)
    data["topic"] = detect_topic(data.get("title", ""), data.get("content", ""))
    images = data.pop("images", None) or []
    post = Post(user_id=user_id, **data, status="pending",
                images=json.dumps(images, ensure_ascii=False) if images else None)
    db.add(post)
    db.commit()
    return True, "发布成功，内容进入先审后发队列，审核通过后对外可见", post.id


def list_posts(db: Session, page: int, page_size: int, category: str | None,
               viewer_id: int | None, topic: str | None = None,
               keyword: str | None = None) -> dict:
    base = select(Post).where(Post.status == "approved")
    if category:
        base = base.where(Post.category == category)
    if topic:
        base = base.where(Post.topic == topic)
    if keyword:
        kw = f"%{keyword.strip()}%"
        base = base.where(or_(Post.title.like(kw), Post.content.like(kw)))
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = db.execute(
        base.order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    liked_ids: set[int] = set()
    if viewer_id and rows:
        ids = [p.id for p in rows]
        likes = db.execute(
            select(PostLike.post_id).where(PostLike.user_id == viewer_id, PostLike.post_id.in_(ids))
        ).scalars().all()
        liked_ids = set(likes)

    items = []
    for p in rows:
        d = p.to_dict()
        d["liked"] = p.id in liked_ids
        if not p.is_anonymous:
            author = db.get(User, p.user_id)
            d["author_nickname"] = author.nickname if author else "用户"
        items.append(d)
    return {"total": total, "items": items}


def get_post(db: Session, post_id: int, viewer_id: int | None) -> dict | None:
    p = db.get(Post, post_id)
    if not p or p.status != "approved":
        return None
    liked = False
    if viewer_id:
        liked = db.execute(
            select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == viewer_id)
        ).scalar_one_or_none() is not None
    d = p.to_dict(liked=liked)
    if not p.is_anonymous:
        author = db.get(User, p.user_id)
        d["author_nickname"] = author.nickname if author else "用户"
    d["comments"] = list_comments(db, post_id)
    return d


def list_comments(db: Session, post_id: int) -> list[dict]:
    rows = db.execute(
        select(PostComment).where(
            PostComment.post_id == post_id, PostComment.status == "approved"
        ).order_by(PostComment.created_at.asc())
    ).scalars().all()
    out = []
    for c in rows:
        nickname = "匿名用户"
        if not c.is_anonymous:
            u = db.get(User, c.user_id)
            nickname = u.nickname if u else "用户"
        out.append({
            "id": c.id, "content": c.content, "author_nickname": nickname,
            "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else None,
        })
    return out


def add_comment(db: Session, user_id: int, post_id: int, data: dict) -> tuple[bool, str]:
    post = db.get(Post, post_id)
    if not post or post.status != "approved":
        return False, "帖子不存在或未过审"
    ok, word = sensitive_check(data["content"])
    if not ok:
        return False, f"评论包含敏感词「{word}」，未通过初审"
    db.add(PostComment(post_id=post_id, user_id=user_id, **data, status="pending"))
    db.commit()
    return True, "评论已提交，先审后发"


def toggle_like(db: Session, user_id: int, post_id: int) -> tuple[bool, int]:
    post = db.get(Post, post_id)
    if not post or post.status != "approved":
        return False, 0
    existing = db.execute(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user_id)
    ).scalar_one_or_none()
    if existing:
        db.delete(existing)
        post.like_count = max(0, post.like_count - 1)
        liked = False
    else:
        db.add(PostLike(post_id=post_id, user_id=user_id))
        post.like_count += 1
        liked = True
        # 点赞提醒：他人点赞时通知帖子作者（自己赞自己不提醒）
        if post.user_id and post.user_id != user_id:
            nickname = db.execute(
                select(User.nickname).where(User.id == user_id)).scalar() or "社区用户"
            db.add(Notification(
                user_id=post.user_id, type="social",
                title="收到新点赞",
                content=f"「{nickname}」赞了你的帖子「{post.title}」",
                ref_url=f"/community/{post_id}",
            ))
    db.commit()
    return liked, post.like_count


# ==================== 举报 ====================

def create_report(db: Session, reporter_id: int | None, ip_hash: str, data: dict) -> tuple[bool, str]:
    db.add(ReportRecord(
        target_type=data["target_type"], target_id=data["target_id"],
        reporter_id=reporter_id, reporter_ip_hash=ip_hash,
        reason=data["reason"], description=data.get("description") or None,
    ))
    db.commit()
    return True, "举报已受理，平台将在 24 小时内核实处理"


# ==================== 商家评价（先审后发 + 聚合） ====================

def create_merchant_review(db: Session, user_id: int, merchant_id: int,
                           rating: int, content: str) -> tuple[bool, str]:
    merchant = db.get(Merchant, merchant_id)
    if not merchant:
        return False, "商家不存在"
    ok, word = sensitive_check(content)
    if not ok:
        return False, f"评价包含敏感词「{word}」，未通过初审"
    db.add(MerchantReview(merchant_id=merchant_id, user_id=user_id,
                          rating=rating, content=content, status="pending"))
    db.commit()
    return True, "评价已提交，审核通过后展示"


def refresh_merchant_rating(db: Session, merchant_id: int):
    """过审评价重算聚合分"""
    rows = db.execute(
        select(MerchantReview.rating).where(
            MerchantReview.merchant_id == merchant_id, MerchantReview.status == "approved")
    ).scalars().all()
    m = db.get(Merchant, merchant_id)
    if m and rows:
        m.rating_count = len(rows)
        m.rating_avg = round(sum(rows) / len(rows), 2)
    elif m:
        m.rating_count = 0
        m.rating_avg = 0.0
    db.commit()


# ==================== 投诉 ====================

def create_complaint(db: Session, user_id: int | None, data: dict) -> tuple[bool, str]:
    ok, word = sensitive_check(data["content"])
    if not ok:
        return False, f"投诉内容包含敏感词「{word}」，未通过初审"
    db.add(Complaint(user_id=user_id, **data, status="pending"))
    db.commit()
    return True, "投诉已提交，审核通过后对外可见（请勿包含个人隐私信息）"


def list_visible_complaints(db: Session, subject_type: str, subject_id: int) -> list[dict]:
    rows = db.execute(
        select(Complaint).where(
            Complaint.subject_type == subject_type,
            Complaint.subject_id == subject_id,
            Complaint.status == "approved",
        ).order_by(Complaint.created_at.desc()).limit(50)
    ).scalars().all()
    return [c.to_dict() for c in rows]


# ==================== 管理端审核 ====================

def pending_audit_items(db: Session) -> dict:
    def count(model, extra=None):
        stmt = select(func.count()).select_from(model).where(model.status == "pending")
        return db.execute(stmt).scalar() or 0
    return {
        "posts": count(Post), "comments": count(PostComment),
        "reviews": count(MerchantReview), "complaints": count(Complaint),
        "reports": count(ReportRecord),
    }


def list_pending(db: Session, content_type: str, page: int, page_size: int) -> dict:
    model_map = {"post": Post, "comment": PostComment,
                 "review": MerchantReview, "complaint": Complaint,
                 "report": ReportRecord}
    model = model_map.get(content_type)
    if model is None:
        return {"total": 0, "items": []}
    base = select(model).where(model.status == "pending")
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = db.execute(
        base.order_by(model.created_at.asc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    items = [_pending_item_to_dict(db, r, content_type) for r in rows]

    # 第一版自动识别违规：加载待审列表时按管理员维护的违规标准检测命中词
    from tyt.services import violation_service
    words = violation_service.get_words(db)
    for d, r in zip(items, rows):
        text = d.get("title", "") + " " + (d.get("content") or d.get("description") or d.get("reason") or "")
        d["violations"] = violation_service.check_text(text, words)

    return {"total": total, "items": items}


def _pending_item_to_dict(db: Session, r, content_type: str) -> dict:
    d = {"id": r.id, "type": content_type,
         "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else None,
         "status": r.status}
    if content_type == "post":
        try:
            imgs = json.loads(r.images) if r.images else []
        except (ValueError, TypeError):
            imgs = []
        d.update({"title": r.title, "content": r.content, "category": r.category,
                  "is_anonymous": r.is_anonymous, "images": imgs})
    elif content_type == "comment":
        d.update({"post_id": r.post_id, "content": r.content})
    elif content_type == "review":
        m = db.get(Merchant, r.merchant_id)
        d.update({"merchant_id": r.merchant_id, "merchant_name": m.name if m else "",
                  "rating": r.rating, "content": r.content})
    elif content_type == "complaint":
        d.update({"subject_type": r.subject_type, "subject_label": r.subject_label,
                  "category": r.category, "content": r.content})
    elif content_type == "report":
        d.update({"target_type": r.target_type, "target_id": r.target_id,
                  "reason": r.reason, "description": r.description})
    return d


def audit_action(db: Session, admin_id: int, content_type: str, item_id: int,
                 action: str, reason: str) -> tuple[bool, str]:
    """审核动作：approve 通过 / reject 拒绝 / offline 下线"""
    model_map = {"post": Post, "comment": PostComment,
                 "review": MerchantReview, "complaint": Complaint}
    if content_type == "report":
        return _handle_report(db, admin_id, item_id, action, reason)
    model = model_map.get(content_type)
    if model is None:
        return False, "内容类型非法"
    item = db.get(model, item_id)
    if not item:
        return False, "内容不存在"

    status_map = {"approve": "approved", "reject": "rejected", "offline": "offline"}
    item.status = status_map[action]
    item.audit_reason = reason or None
    item.audited_by = admin_id
    from datetime import datetime
    item.audited_at = datetime.now()

    # 联动：评价过审 -> 重算商家聚合分；帖子过审 -> 通知作者；投诉过审 -> 计数
    if content_type == "review" and action == "approve":
        refresh_merchant_rating(db, item.merchant_id)
    elif content_type == "complaint" and action == "approve":
        if item.subject_type == "merchant" and item.subject_id:
            m = db.get(Merchant, item.subject_id)
            if m:
                m.complaint_count += 1
        elif item.subject_type == "estate" and item.subject_id:
            e = db.get(HousingEstate, item.subject_id)
            if e:
                e.complaint_count += 1
    elif content_type == "post" and action in ("approve", "reject"):
        db.add(Notification(
            user_id=item.user_id, type="audit",
            title="帖子审核通过" if action == "approve" else "帖子未通过审核",
            content=(reason or "感谢您的分享，内容已对外可见。") if action == "approve"
            else (f"未通过原因：{reason or '内容不符合社区规范'}。请勿发布不实信息。"),
        ))
    elif content_type == "comment" and action == "approve":
        # 评论提醒：评论过审后通知帖子作者（自己评论自己不提醒）
        post = db.get(Post, item.post_id)
        if post and post.user_id and post.user_id != item.user_id:
            nickname = db.execute(
                select(User.nickname).where(User.id == item.user_id)).scalar() or "社区用户"
            digest = (item.content or "")[:40]
            db.add(Notification(
                user_id=post.user_id, type="social",
                title="帖子收到新评论",
                content=f"「{nickname}」评论了你的帖子「{post.title}」：{digest}",
                ref_url=f"/community/{post.id}",
            ))
    db.commit()
    return True, "审核完成"


def _handle_report(db: Session, admin_id: int, report_id: int, action: str, reason: str) -> tuple[bool, str]:
    report = db.get(ReportRecord, report_id)
    if not report:
        return False, "举报不存在"
    if action == "approve":  # 举报成立 -> 下线目标内容
        target_map = {"post": Post, "comment": PostComment,
                      "review": MerchantReview, "complaint": Complaint}
        model = target_map.get(report.target_type)
        if model:
            target = db.get(model, report.target_id)
            if target:
                target.status = "offline"
                target.audit_reason = f"举报成立：{reason or report.reason}"
                target.audited_by = admin_id
                from datetime import datetime
                target.audited_at = datetime.now()
                if report.target_type == "review":
                    tr = db.get(MerchantReview, report.target_id)
                    if tr:
                        refresh_merchant_rating(db, tr.merchant_id)
        report.status = "handled"
        report.handle_result = "举报成立，内容已下线"
    else:
        report.status = "dismissed"
        report.handle_result = reason or "经核实不成立"
    report.handled_by = admin_id
    db.commit()
    return True, "举报处理完成"
