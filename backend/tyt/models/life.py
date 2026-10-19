"""生活类模型：商家、房源、投诉、生活圈 UGC（全部先审后发）"""
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, DateTime, Enum, ForeignKey, Index, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from tyt.models.base import Base, TimestampMixin

UGC_STATUS = ("pending", "approved", "rejected", "offline")


class Merchant(Base, TimestampMixin):
    """商家（公开工商基础信息 + 评价聚合）"""
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(32), comment="餐饮/零售/教培/美容/健身等")
    address: Mapped[Optional[str]] = mapped_column(String(512))
    city: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    credit_code: Mapped[Optional[str]] = mapped_column(String(32), comment="统一社会信用代码（演示值）")
    reg_status: Mapped[Optional[str]] = mapped_column(String(32))
    business_scope: Mapped[Optional[str]] = mapped_column(Text)
    rating_avg: Mapped[float] = mapped_column(default=0.0, comment="评价聚合均分（仅统计过审评价）")
    rating_count: Mapped[int] = mapped_column(default=0)
    complaint_count: Mapped[int] = mapped_column(default=0, comment="过审投诉数")
    is_demo: Mapped[bool] = mapped_column(default=False)
    source: Mapped[Optional[str]] = mapped_column(String(64))

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "category": self.category,
            "address": self.address, "city": self.city,
            "credit_code": self.credit_code, "reg_status": self.reg_status,
            "business_scope": self.business_scope,
            "rating_avg": round(self.rating_avg or 0, 1),
            "rating_count": self.rating_count,
            "complaint_count": self.complaint_count,
            "is_demo": self.is_demo, "source": self.source,
        }


class MerchantReview(Base):
    """商家评价（UGC，先审后发）"""
    __tablename__ = "merchant_reviews"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rating: Mapped[int] = mapped_column(comment="1-5 星")
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    audit_reason: Mapped[Optional[str]] = mapped_column(String(256))
    audited_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    audited_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class HousingEstate(Base, TimestampMixin):
    """小区（房源查询主体）"""
    __tablename__ = "housing_estates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    city: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    district: Mapped[Optional[str]] = mapped_column(String(64))
    address: Mapped[Optional[str]] = mapped_column(String(512))
    developer: Mapped[Optional[str]] = mapped_column(String(256), comment="开发商（企业名，公开信息）")
    property_company: Mapped[Optional[str]] = mapped_column(String(256), comment="物业公司")
    build_year: Mapped[Optional[int]] = mapped_column()
    complaint_count: Mapped[int] = mapped_column(default=0)
    is_demo: Mapped[bool] = mapped_column(default=False)
    source: Mapped[Optional[str]] = mapped_column(String(64))

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "city": self.city,
            "district": self.district, "address": self.address,
            "developer": self.developer, "property_company": self.property_company,
            "build_year": self.build_year, "complaint_count": self.complaint_count,
            "is_demo": self.is_demo, "source": self.source,
        }


class Complaint(Base):
    """投诉/纠纷记录（UGC 先审后发；司法类脱敏引用见 risk_records）"""
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    subject_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True,
                                              comment="merchant/estate/landlord/agency/company")
    subject_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="关联主体ID；landlord/agency 无实体时为0")
    subject_label: Mapped[str] = mapped_column(String(256), nullable=False, comment="主体展示名（房东/中介为脱敏名）")
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    content: Mapped[str] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(32), comment="押金纠纷/虚假宣传/服务态度/质量等")
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True, comment="仅 approved 对外可见")
    audit_reason: Mapped[Optional[str]] = mapped_column(String(256))
    audited_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    audited_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id, "subject_type": self.subject_type, "subject_label": self.subject_label,
            "content": self.content, "category": self.category,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }


class Post(Base):
    """生活圈帖子（UGC，先审后发；可匿名）"""
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category: Mapped[str] = mapped_column(String(16), default="avoid_pit", comment="avoid_pit避雷/recommend推荐")
    topic: Mapped[str] = mapped_column(String(32), default="其他", comment="话题分类（发帖时按内容自动识别）")
    title: Mapped[str] = mapped_column(String(256))
    content: Mapped[str] = mapped_column(Text)
    is_anonymous: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    audit_reason: Mapped[Optional[str]] = mapped_column(String(256))
    audited_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    audited_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    like_count: Mapped[int] = mapped_column(default=0)
    comment_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    images: Mapped[Optional[str]] = mapped_column(Text, comment="帖子配图 URL 列表（JSON 数组）")

    def to_dict(self, viewer_user_id: int | None = None, liked: bool = False):
        try:
            images = json.loads(self.images) if self.images else []
        except (ValueError, TypeError):
            images = []
        return {
            "id": self.id, "category": self.category, "topic": self.topic or "其他",
            "title": self.title,
            "content": self.content, "is_anonymous": self.is_anonymous,
            "like_count": self.like_count, "comment_count": self.comment_count,
            "author_nickname": "匿名用户" if self.is_anonymous else (getattr(self, "_author_nickname", None) or "用户"),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
            "liked": liked,
            "images": [u for u in images if isinstance(u, str)],
        }


class PostComment(Base):
    __tablename__ = "post_comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text)
    is_anonymous: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    audit_reason: Mapped[Optional[str]] = mapped_column(String(256))
    audited_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    audited_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_post_like"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ReportRecord(Base):
    """举报（帖子/评论/评价/商家投诉均可达）"""
    __tablename__ = "report_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    target_type: Mapped[str] = mapped_column(String(16), nullable=False, comment="post/comment/review/complaint")
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    reporter_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    reporter_ip_hash: Mapped[Optional[str]] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(String(32))
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True, comment="pending/handled/dismissed")
    handled_by: Mapped[Optional[int]] = mapped_column(BigInteger)
    handle_result: Mapped[Optional[str]] = mapped_column(String(256))
    handled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
