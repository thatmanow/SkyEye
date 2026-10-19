"""站内通知服务：面向右上角消息中心与各业务通知的统一读写入口

所有登录用户可用（无能力限制）；通知来源包括：商业监控（monitor）、
会员订阅（membership）、内容审核（audit）、社区互动（social：点赞/评论）等。
"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tyt.models.biz import Notification


def list_notifications(db: Session, user_id: int, unread_only: bool = False,
                       page: int = 1, page_size: int = 20) -> dict:
    base = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        base = base.where(Notification.is_read.is_(False))
    total = db.execute(select(func.count()).select_from(base.subquery())).scalar() or 0
    rows = db.execute(
        base.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return {"total": total, "items": [n.to_dict() for n in rows]}


def unread_count(db: Session, user_id: int) -> int:
    return db.execute(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id, Notification.is_read.is_(False))
    ).scalar() or 0


def mark_notification_read(db: Session, user_id: int, notification_id: int) -> bool:
    n = db.get(Notification, notification_id)
    if not n or n.user_id != user_id:
        return False
    n.is_read = True
    db.commit()
    return True


def mark_all_read(db: Session, user_id: int) -> int:
    """全部已读，返回更新条数"""
    rows = db.execute(
        select(Notification).where(Notification.user_id == user_id, Notification.is_read.is_(False))
    ).scalars().all()
    for n in rows:
        n.is_read = True
    db.commit()
    return len(rows)


def delete_notification(db: Session, user_id: int, notification_id: int) -> bool:
    """删除单条通知（仅限本人）：消息中心中已读消息再次点击时移除"""
    n = db.get(Notification, notification_id)
    if not n or n.user_id != user_id:
        return False
    db.delete(n)
    db.commit()
    return True
