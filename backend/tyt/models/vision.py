"""AI 识图模型：识别记录（本地 MiniCPM-V 推理，图片不离开设备）"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Index, String, Text, func
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from tyt.models.base import Base


class VisionRecord(Base):
    """识图记录：图片 base64 + 结构化结果 + 追问多轮对话历史"""
    __tablename__ = "vision_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    # MEDIUMTEXT：TEXT 上限 64KB，普通照片 base64 轻松超过（约 20 万+ 字符），曾触发 1406 Data too long
    image_b64: Mapped[str] = mapped_column(MEDIUMTEXT, comment="图片 base64（追问多模态复用）")
    result_name: Mapped[str] = mapped_column(String(128), default="")
    category: Mapped[str] = mapped_column(String(32), default="")
    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    key_elements_json: Mapped[str] = mapped_column(Text, default="[]")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    description: Mapped[str] = mapped_column(Text, default="")
    # 同样改 MEDIUMTEXT：多轮追问的对话 JSON 累积也可能超 64KB
    chat_history: Mapped[str] = mapped_column(MEDIUMTEXT, default="[]", comment="追问多轮对话 JSON")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    __table_args__ = (Index("ix_vision_user_time", "user_id", "created_at"),)

    def to_dict(self, with_image: bool = False) -> dict:
        import json
        d = {
            "id": self.id,
            "name": self.result_name,
            "category": self.category,
            "tags": json.loads(self.tags_json or "[]"),
            "key_elements": json.loads(self.key_elements_json or "[]"),
            "confidence": round(self.confidence or 0, 3),
            "description": self.description,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
        }
        if with_image:
            d["image_b64"] = self.image_b64
        return d
