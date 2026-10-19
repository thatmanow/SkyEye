"""企业主数据模型：工商、人员、股权、投资、分支、变更"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger, Date, DateTime, Numeric, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from tyt.models.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    """企业工商主表（来源：公开工商数据，演示库为整理的公开信息）

    中文全文检索：建表后由 seed/init_db.py 执行
      ALTER TABLE companies ADD FULLTEXT INDEX ft_companies_search (name, business_scope, industry) WITH PARSER ngram;
    """
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, index=True)
    short_name: Mapped[Optional[str]] = mapped_column(String(128), comment="常用简称")
    credit_code: Mapped[Optional[str]] = mapped_column(String(32), unique=True, comment="统一社会信用代码（演示库为 SEED- 前缀演示值）")
    legal_person: Mapped[Optional[str]] = mapped_column(String(128), comment="法定代表人（公开工商信息）")
    reg_status: Mapped[Optional[str]] = mapped_column(String(32), comment="存续/在业/注销/吊销/迁出")
    reg_capital_wan: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), comment="注册资本（万元）")
    paid_capital_wan: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), comment="实缴资本（万元）")
    founded_date: Mapped[Optional[date]] = mapped_column(Date)
    company_type: Mapped[Optional[str]] = mapped_column(String(64), comment="有限责任公司/股份有限公司等")
    industry: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    province: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    city: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    address: Mapped[Optional[str]] = mapped_column(String(512))
    business_scope: Mapped[Optional[str]] = mapped_column(Text)
    reg_authority: Mapped[Optional[str]] = mapped_column(String(128), comment="登记机关")
    listed_code: Mapped[Optional[str]] = mapped_column(String(12), comment="证券代码（上市公司）")
    employee_scale: Mapped[Optional[str]] = mapped_column(String(32), comment="人员规模档位：0-50/50-150/150-500/500-1000/1000+")
    is_demo: Mapped[bool] = mapped_column(default=False, comment="演示数据标记")
    source: Mapped[Optional[str]] = mapped_column(String(64), comment="数据来源标识")
    source_url: Mapped[Optional[str]] = mapped_column(String(512), comment="来源可溯源链接")
    collected_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="采集时间")


class CompanyPersonnel(Base):
    """主要人员（公开工商信息）"""
    __tablename__ = "company_personnel"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    position: Mapped[Optional[str]] = mapped_column(String(64), comment="董事长/总经理/董事/监事等")
    is_legal_person: Mapped[bool] = mapped_column(default=False)
    source: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CompanyShareholder(Base):
    """股东及出资（公开工商信息；自然人姓名在商业尽调场景为公开工商公示信息）"""
    __tablename__ = "company_shareholders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    holder_name: Mapped[str] = mapped_column(String(256), nullable=False)
    holder_type: Mapped[str] = mapped_column(String(16), comment="person/company")
    holder_credit_code: Mapped[Optional[str]] = mapped_column(String(32), comment="机构股东信用代码")
    share_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4), comment="持股比例(%)")
    subscribed_capital_wan: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), comment="认缴出资（万元）")
    source: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CompanyInvestment(Base):
    """对外投资（企业 -> 企业）"""
    __tablename__ = "company_investments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investor_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False, comment="投资方企业 ID")
    investee_id: Mapped[Optional[int]] = mapped_column(BigInteger, index=True, comment="被投企业 ID（可能未入库）")
    investee_name: Mapped[str] = mapped_column(String(256), nullable=False)
    investee_credit_code: Mapped[Optional[str]] = mapped_column(String(32))
    share_ratio: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    invested_amount_wan: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), comment="投资金额（万元）")
    investee_reg_status: Mapped[Optional[str]] = mapped_column(String(32))
    source: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CompanyBranch(Base):
    """分支机构"""
    __tablename__ = "company_branches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    branch_name: Mapped[str] = mapped_column(String(256), nullable=False)
    branch_status: Mapped[Optional[str]] = mapped_column(String(32))
    branch_person: Mapped[Optional[str]] = mapped_column(String(128), comment="分支机构负责人")
    province: Mapped[Optional[str]] = mapped_column(String(32))
    city: Mapped[Optional[str]] = mapped_column(String(64))
    source: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CompanyChange(Base):
    """工商变更记录（商业监控事件源）"""
    __tablename__ = "company_changes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    change_type: Mapped[str] = mapped_column(String(32), comment="法定代表人变更/注册资本变更/股东变更/经营范围变更/注销备案等")
    before_value: Mapped[Optional[str]] = mapped_column(String(512))
    after_value: Mapped[Optional[str]] = mapped_column(String(512))
    change_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    source: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

