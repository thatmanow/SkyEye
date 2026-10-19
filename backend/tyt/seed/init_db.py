"""数据库初始化：建表 + 种子数据

用法：cd backend && python -m tyt.seed.init_db
可重复执行（幂等）：已存在的数据自动跳过。
"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select, text

from tyt.config import DATA_SOURCES, DEMO_SOURCE
from tyt.core.security import hash_password
from tyt.db.mysql import engine, SessionLocal
from tyt.models import (
    Base, User, Notification, Company, CompanyPersonnel, CompanyShareholder,
    CompanyInvestment, CompanyBranch, CompanyChange, RiskRecord,
    Merchant, MerchantReview, HousingEstate, Complaint, Post, PostComment,
    WatchItem, WatchEvent, Lead, DataSource, CollectLog,
)
from tyt.seed import data_companies as DC, data_risks as DR, data_life as DL, data_leads as DLd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("seed")

DEMO_USERS = [
    ("admin@tyt.demo", "平台管理员", "platform_admin"),
    ("entadmin@tyt.demo", "企业管理员", "enterprise_admin"),
    ("premium@tyt.demo", "高级会员", "premium"),
    ("demo@tyt.demo", "普通用户", "user"),
]
DEMO_PASSWORD = "SkyEye@123456"


def create_tables():
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        # 中文全文检索（MySQL 8.0 ngram）
        try:
            conn.execute(text(
                "ALTER TABLE companies ADD FULLTEXT INDEX ft_companies_search "
                "(name, business_scope, industry) WITH PARSER ngram"))
            log.info("ngram FULLTEXT 索引已创建")
        except Exception as e:
            if "Duplicate" in str(e):
                log.info("FULLTEXT 索引已存在")
            else:
                log.warning("FULLTEXT 索引创建失败（搜索将走 LIKE 降级）: %s", e)
        # v2.4 会员订阅：users 表补加连续包月自动续费开关列
        # （create_all 只建新表，不会为已存在的表新增列）
        try:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN auto_renew TINYINT(1) NOT NULL DEFAULT 0 "
                "COMMENT '连续包月自动续费开关'"))
            log.info("users.auto_renew 列已创建")
        except Exception as e:
            if "Duplicate" in str(e):
                log.info("users.auto_renew 列已存在")
            else:
                log.warning("users.auto_renew 列创建失败: %s", e)


def seed_data_sources(db):
    for src in DATA_SOURCES:
        exists = db.execute(select(DataSource).where(DataSource.code == src["code"])).scalar_one_or_none()
        if not exists:
            db.add(DataSource(**src))
    db.commit()
    log.info("数据源登记完成（%d 项）", len(DATA_SOURCES))


def seed_users(db):
    for account, nickname, role in DEMO_USERS:
        exists = db.execute(select(User).where(User.account == account)).scalar_one_or_none()
        if exists:
            continue
        db.add(User(
            account=account, nickname=nickname, role=role,
            password_hash=hash_password(DEMO_PASSWORD),
            email_enc=None,
        ))
    db.commit()
    log.info("演示账号：admin/entadmin/premium/demo @tyt.demo，密码 %s", DEMO_PASSWORD)


def seed_companies(db) -> dict[str, int]:
    name_to_id: dict[str, int] = {}
    now = datetime.now()
    for row in DC.COMPANIES:
        (name, short, code, legal, status, cap, founded, ctype, industry,
         prov, city, addr, scope, authority, listed, scale) = row
        exists = db.execute(select(Company).where(Company.name == name)).scalar_one_or_none()
        if exists:
            name_to_id[name] = exists.id
            continue
        c = Company(
            name=name, short_name=short, credit_code=code, legal_person=legal,
            reg_status=status, reg_capital_wan=cap, paid_capital_wan=round(cap * 0.6, 2),
            founded_date=datetime.strptime(founded, "%Y-%m-%d").date() if founded else None,
            company_type=ctype, industry=industry, province=prov, city=city,
            address=addr, business_scope=scope, reg_authority=authority,
            listed_code=listed, employee_scale=scale,
            is_demo=True, source=DEMO_SOURCE,
            source_url="https://www.gsxt.gov.cn（演示数据：请通过官方渠道核实）",
            collected_at=now - timedelta(days=3),
        )
        db.add(c)
        db.flush()
        name_to_id[name] = c.id

    # 人员
    for company_name, people in DC.PERSONNEL.items():
        cid = name_to_id.get(company_name)
        if not cid:
            continue
        for pname, position, is_legal in people:
            if db.execute(select(CompanyPersonnel).where(
                    CompanyPersonnel.company_id == cid,
                    CompanyPersonnel.name == pname)).scalar_one_or_none():
                continue
            db.add(CompanyPersonnel(company_id=cid, name=pname, position=position,
                                    is_legal_person=is_legal, source=DEMO_SOURCE))

    # 股东
    for company_name, holders in DC.SHAREHOLDERS.items():
        cid = name_to_id.get(company_name)
        if not cid:
            continue
        for hname, htype, ratio, capital in holders:
            if db.execute(select(CompanyShareholder).where(
                    CompanyShareholder.company_id == cid,
                    CompanyShareholder.holder_name == hname)).scalar_one_or_none():
                continue
            db.add(CompanyShareholder(company_id=cid, holder_name=hname, holder_type=htype,
                                      share_ratio=ratio, subscribed_capital_wan=capital,
                                      source=DEMO_SOURCE))

    # 对外投资
    for investor_name, invests in DC.INVESTMENTS.items():
        iid = name_to_id.get(investor_name)
        if not iid:
            continue
        for iname, ratio, amount, istatus in invests:
            if db.execute(select(CompanyInvestment).where(
                    CompanyInvestment.investor_id == iid,
                    CompanyInvestment.investee_name == iname)).scalar_one_or_none():
                continue
            db.add(CompanyInvestment(investor_id=iid, investee_id=None,
                                     investee_name=iname, share_ratio=ratio,
                                     invested_amount_wan=amount,
                                     investee_reg_status=istatus, source=DEMO_SOURCE))

    # 分支机构
    for company_name, branches in DC.BRANCHES.items():
        cid = name_to_id.get(company_name)
        if not cid:
            continue
        for bname, bstatus, bcity in branches:
            if db.execute(select(CompanyBranch).where(
                    CompanyBranch.company_id == cid,
                    CompanyBranch.branch_name == bname)).scalar_one_or_none():
                continue
            db.add(CompanyBranch(company_id=cid, branch_name=bname,
                                 branch_status=bstatus, city=bcity, source=DEMO_SOURCE))

    # 变更记录
    for company_name, changes in DC.CHANGES.items():
        cid = name_to_id.get(company_name)
        if not cid:
            continue
        for ctype, before, after, cdate in changes:
            if db.execute(select(CompanyChange).where(
                    CompanyChange.company_id == cid,
                    CompanyChange.change_type == ctype,
                    CompanyChange.change_date == datetime.strptime(cdate, "%Y-%m-%d").date())
            ).scalar_one_or_none():
                continue
            db.add(CompanyChange(company_id=cid, change_type=ctype, before_value=before,
                                 after_value=after,
                                 change_date=datetime.strptime(cdate, "%Y-%m-%d").date(),
                                 source=DEMO_SOURCE))
    db.commit()
    log.info("企业种子数据完成（%d 家）", len(name_to_id))
    return name_to_id


def seed_risks(db, name_to_id: dict[str, int]):
    for (stype, sname, rtype, subtype, title, digest, amount, court,
         case_no, level, odate) in DR.COMPANY_RISKS:
        if stype != "company":
            continue
        cid = name_to_id.get(sname, 0)
        if db.execute(select(RiskRecord).where(
                RiskRecord.subject_type == "company",
                RiskRecord.subject_id == cid,
                RiskRecord.title == title)).scalar_one_or_none():
            continue
        db.add(RiskRecord(
            subject_type="company", subject_id=cid, subject_name=sname,
            risk_type=rtype, risk_subtype=subtype, title=title, content_digest=digest,
            amount_wan=amount, court=court, case_no=case_no, risk_level=level,
            occur_date=odate, publish_date=odate, source=DR.SD,
            source_url="https://wenshu.court.gov.cn（演示数据：请通过官方渠道核实）",
            is_demo=True))
    for (stype, masked, rtype, subtype, title, digest, amount, court,
         case_no, level, odate) in DR.PERSON_RISKS:
        if db.execute(select(RiskRecord).where(
                RiskRecord.subject_type == "person",
                RiskRecord.subject_name == masked,
                RiskRecord.title == title)).scalar_one_or_none():
            continue
        db.add(RiskRecord(
            subject_type="person", subject_id=0, subject_name=masked,
            risk_type=rtype, risk_subtype=subtype, title=title, content_digest=digest,
            amount_wan=amount, court=court, case_no=case_no, risk_level=level,
            occur_date=odate, publish_date=odate, source=DR.SD,
            source_url="http://zxgk.court.gov.cn（演示数据：请通过官方渠道核实）",
            is_demo=True))
    db.commit()
    log.info("风险种子数据完成")


def seed_life(db):
    now = datetime.now()
    demo_uid = db.execute(select(User).where(User.account == "demo@tyt.demo")).scalar_one_or_none()
    uid = demo_uid.id if demo_uid else 1

    for (name, cat, city, addr, status, scope, rating, rcount, ccount) in DL.MERCHANTS:
        if db.execute(select(Merchant).where(Merchant.name == name)).scalar_one_or_none():
            continue
        db.add(Merchant(name=name, category=cat, city=city, address=addr,
                        reg_status=status, business_scope=scope, credit_code=None,
                        rating_avg=rating, rating_count=rcount, complaint_count=ccount,
                        is_demo=True, source=DL.SL))
    db.flush()

    def mid(name):
        return db.execute(select(Merchant).where(Merchant.name == name)).scalar_one().id

    for (mname, rating, content) in DL.MERCHANT_REVIEWS_APPROVED:
        db.add(MerchantReview(merchant_id=mid(mname), user_id=uid, rating=rating,
                              content=content, status="approved",
                              audited_by=1, audited_at=now))
    for (mname, rating, content) in DL.MERCHANT_REVIEWS_PENDING:
        db.add(MerchantReview(merchant_id=mid(mname), user_id=uid, rating=rating,
                              content=content, status="pending"))

    for (name, city, district, addr, developer, prop, year) in DL.ESTATES:
        if db.execute(select(HousingEstate).where(HousingEstate.name == name)).scalar_one_or_none():
            continue
        db.add(HousingEstate(name=name, city=city, district=district, address=addr,
                             developer=developer, property_company=prop, build_year=year,
                             is_demo=True, source=DL.SL))
    db.flush()

    def eid(name):
        return db.execute(select(HousingEstate).where(HousingEstate.name == name)).scalar_one().id

    for (stype, label, cat, content) in DL.COMPLAINTS_APPROVED:
        sid = mid(label) if stype == "merchant" else (eid("阳光花园") if label == "阳光花园" else 0)
        db.add(Complaint(subject_type=stype, subject_id=sid, subject_label=label,
                         user_id=uid, content=content, category=cat,
                         status="approved", audited_by=1, audited_at=now))
    for (stype, label, cat, content) in DL.COMPLAINTS_PENDING:
        sid = mid(label) if stype == "merchant" else 0
        db.add(Complaint(subject_type=stype, subject_id=sid, subject_label=label,
                         user_id=uid, content=content, category=cat, status="pending"))

    for i, (cat, title, content, anon) in enumerate(DL.POSTS_APPROVED):
        if db.execute(select(Post).where(Post.title == title)).scalar_one_or_none():
            continue
        db.add(Post(user_id=uid, category=cat, title=title, content=content,
                    is_anonymous=anon, status="approved", audited_by=1, audited_at=now,
                    like_count=12 - i * 3, comment_count=0))
    db.flush()

    for (post_idx, content) in DL.COMMENTS_APPROVED:
        post = db.execute(select(Post).where(Post.status == "approved").offset(post_idx - 1).limit(1)).scalar_one_or_none()
        if post:
            db.add(PostComment(post_id=post.id, user_id=uid, content=content,
                               is_anonymous=True, status="approved", audited_by=1, audited_at=now))
            post.comment_count += 1
    for (cat, title, content, anon) in DL.POSTS_PENDING:
        if not db.execute(select(Post).where(Post.title == title)).scalar_one_or_none():
            db.add(Post(user_id=uid, category=cat, title=title, content=content,
                        is_anonymous=anon, status="pending"))
    db.commit()
    log.info("生活类种子数据完成")


def seed_leads(db, name_to_id: dict[str, int]):
    for (cname, sig, desc, delta, score, disc) in DLd.LEADS:
        cid = name_to_id.get(cname, 0)
        if db.execute(select(Lead).where(Lead.company_name == cname,
                                         Lead.signal_type == sig)).scalar_one_or_none():
            continue
        company = db.get(Company, cid) if cid else None
        db.add(Lead(company_id=cid, company_name=cname,
                    industry=company.industry if company else None,
                    province=company.province if company else None,
                    employee_scale=company.employee_scale if company else None,
                    signal_type=sig, signal_desc=desc, risk_delta=delta,
                    score=score, discovered_at=disc, is_demo=True))
    db.commit()
    log.info("商机线索种子数据完成")


def seed_watch_demo(db, name_to_id: dict[str, int]):
    """给高级会员演示号预置监控与事件"""
    premium_user = db.execute(select(User).where(User.account == "premium@tyt.demo")).scalar_one_or_none()
    if not premium_user:
        return
    for cname in ("宁德时代新能源科技股份有限公司", "比亚迪股份有限公司", "星辰贸易有限公司"):
        cid = name_to_id.get(cname)
        if not cid:
            continue
        if not db.execute(select(WatchItem).where(
                WatchItem.user_id == premium_user.id,
                WatchItem.company_id == cid)).scalar_one_or_none():
            db.add(WatchItem(user_id=premium_user.id, company_id=cid, company_name=cname))
    # 预置两条监控事件
    # 注意：运行期监控扫描会持续新增 watch_events，这里用 first() 判断是否存在，
    # 不能用 scalar_one_or_none()（多行时抛 MultipleResultsFound，破坏幂等）
    if not db.execute(select(WatchEvent).where(
            WatchEvent.company_id == name_to_id.get("星辰贸易有限公司", 0))).scalars().first():
        db.add(WatchEvent(
            company_id=name_to_id.get("星辰贸易有限公司", 0), company_name="星辰贸易有限公司",
            event_type="risk", title="新增被执行记录：执行标的 48.00 万元",
            detail="未履行生效法律文书确定的给付义务（演示事件）",
            risk_level="high", occurred_at=datetime.now() - timedelta(days=2)))
    db.commit()
    log.info("监控演示数据完成")


def seed_collect_log(db):
    if not db.execute(select(CollectLog).limit(1)).scalars().first():
        db.add(CollectLog(
            source_code="demo_seed", task_type="import",
            params='{"entity": "all"}', status="success", records=len(DC.COMPANIES),
            message="演示种子数据初始化（来源与合规说明见 data_sources 表）",
            started_at=datetime.now(), finished_at=datetime.now()))
        db.commit()


def run():
    log.info("=== 天眼通数据库初始化开始 ===")
    create_tables()
    db = SessionLocal()
    try:
        seed_data_sources(db)
        seed_users(db)
        name_to_id = seed_companies(db)
        seed_risks(db, name_to_id)
        seed_life(db)
        seed_leads(db, name_to_id)
        seed_watch_demo(db, name_to_id)
        seed_collect_log(db)
    finally:
        db.close()
    log.info("=== 初始化完成 ===")


if __name__ == "__main__":
    run()
