"""AI 问答模型：异步任务（ai_chat_tasks）+ 历史记录（ai_chat_histories，按用户隔离）"""
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from tyt.models.base import Base


class AIChatTask(Base):
    """AI 问答异步任务：POST /ai/chat 提交即返回 task_id，
    RAG 在后台执行，前端轮询 GET /ai/chat/tasks/{id} 获取结果"""
    __tablename__ = "ai_chat_tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="归属用户")
    question: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="queued", nullable=False,
                                        comment="queued/running/done/failed")
    result_json: Mapped[Optional[str]] = mapped_column(Text, comment="回答结果 JSON（answer/references/model 等）")
    error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class AIChatHistory(Base):
    __tablename__ = "ai_chat_histories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="归属用户")
    question: Mapped[str] = mapped_column(String(512), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    references_json: Mapped[Optional[str]] = mapped_column(Text, comment="参考来源 JSON")
    model: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        try:
            refs = json.loads(self.references_json) if self.references_json else []
        except (ValueError, TypeError):
            refs = []
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "references": refs,
            "model": self.model,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
