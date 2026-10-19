"""审计日志服务：敏感操作全量留痕"""
import json
import logging

from sqlalchemy.orm import Session

from tyt.core.rbac import Principal
from tyt.models import AuditLog

logger = logging.getLogger(__name__)


def log_action(db: Session, principal: Principal, action: str,
               resource: str = None, detail: dict = None):
    """写审计日志（失败不阻断业务）"""
    try:
        db.add(AuditLog(
            user_id=principal.user_id,
            role=principal.role,
            action=action,
            resource=resource,
            detail=json.dumps(detail, ensure_ascii=False)[:2000] if detail else None,
            ip_hash=principal.ip_hash,
        ))
        db.commit()
    except Exception as e:
        logger.error("audit log failed: %s", e)
        db.rollback()
