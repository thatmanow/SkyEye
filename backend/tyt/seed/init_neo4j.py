"""Neo4j 图谱初始化：从 MySQL 种子数据同步企业与人员关系

用法：cd backend && python -m tyt.seed.init_neo4j
幂等：MERGE 语义，可重复执行。
"""
import logging
from datetime import datetime

from sqlalchemy import select

from tyt.db.mysql import SessionLocal
from tyt.db.neo4j_client import neo4j_session
from tyt.models import (
    Company, CompanyPersonnel, CompanyShareholder, CompanyInvestment,
)
from tyt.seed.data_companies import INVESTMENTS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("neo4j-seed")

PERSON_ID_BASE = 1_000_000_000


def run():
    db = SessionLocal()
    try:
        companies = db.execute(select(Company)).scalars().all()
        cid_to_company = {c.id: c for c in companies}
        name_to_id = {c.name: c.id for c in companies}

        with neo4j_session() as s:
            # 约束（幂等）
            for label in ("Company", "Person"):
                s.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.tyt_id IS UNIQUE")

            # 1) 企业节点
            for c in companies:
                s.run("""
                    MERGE (co:Company {tyt_id: $id})
                    SET co.name = $name, co.credit_code = $code, co.status = $status,
                        co.short_name = $short
                """, {"id": c.id, "name": c.name, "code": c.credit_code,
                      "status": c.reg_status, "short": c.short_name or ""})

            # 2) 人员节点 + 任职/法代关系
            person_ids: dict[str, int] = {}
            next_pid = PERSON_ID_BASE + 1
            personnel_rows = db.execute(select(CompanyPersonnel)).scalars().all()
            for p in personnel_rows:
                if p.name not in person_ids:
                    person_ids[p.name] = next_pid
                    next_pid += 1
            for name, pid in person_ids.items():
                s.run("MERGE (pe:Person {tyt_id: $id}) SET pe.name = $name",
                      {"id": pid, "name": name})
            for p in personnel_rows:
                pid = person_ids[p.name]
                if p.is_legal_person:
                    s.run("""
                        MATCH (pe:Person {tyt_id: $pid}), (co:Company {tyt_id: $cid})
                        MERGE (co)-[:HAS_LEGAL_REP]->(pe)
                    """, {"pid": pid, "cid": p.company_id})
                s.run("""
                    MATCH (pe:Person {tyt_id: $pid}), (co:Company {tyt_id: $cid})
                    MERGE (pe)-[r:EXECUTIVE_OF]->(co)
                    SET r.position = $pos
                """, {"pid": pid, "cid": p.company_id, "pos": p.position or ""})

            # 3) 股东关系（机构股东若已入库建 Company 节点引用；自然人建 Person）
            holders = db.execute(select(CompanyShareholder)).scalars().all()
            for h in holders:
                ratio = float(h.share_ratio) if h.share_ratio else None
                if h.holder_type == "person":
                    if h.holder_name not in person_ids:
                        person_ids[h.holder_name] = next_pid
                        next_pid += 1
                        s.run("MERGE (pe:Person {tyt_id: $id}) SET pe.name = $name",
                              {"id": person_ids[h.holder_name], "name": h.holder_name})
                    s.run("""
                        MATCH (pe:Person {tyt_id: $pid}), (co:Company {tyt_id: $cid})
                        MERGE (pe)-[r:SHAREHOLDER_OF]->(co)
                        SET r.ratio = $ratio, r.amount = $amount
                    """, {"pid": person_ids[h.holder_name], "cid": h.company_id,
                          "ratio": ratio, "amount": float(h.subscribed_capital_wan or 0)})
                else:
                    # 机构股东：若名称与库内企业匹配则关联，否则建占位 Company 节点
                    org_id = name_to_id.get(h.holder_name)
                    if org_id is None:
                        org_id = 900_000_000 + h.id
                        s.run("""
                            MERGE (co:Company {tyt_id: $id})
                            SET co.name = $name, co.status = '外部机构'
                        """, {"id": org_id, "name": h.holder_name})
                    s.run("""
                        MATCH (a:Company {tyt_id: $aid}), (b:Company {tyt_id: $cid})
                        MERGE (a)-[r:SHAREHOLDER_OF]->(b)
                        SET r.ratio = $ratio, r.amount = $amount
                    """, {"aid": org_id, "cid": h.company_id,
                          "ratio": ratio, "amount": float(h.subscribed_capital_wan or 0)})

            # 4) 对外投资（MySQL company_investments：被投企业建占位 Company）
            invests = db.execute(select(CompanyInvestment)).scalars().all()
            for inv in invests:
                investee_id = inv.investee_id
                if investee_id is None:
                    investee_id = 910_000_000 + inv.id
                    s.run("""
                        MERGE (co:Company {tyt_id: $id})
                        SET co.name = $name, co.status = $status
                    """, {"id": investee_id, "name": inv.investee_name,
                          "status": inv.investee_reg_status or ""})
                s.run("""
                    MATCH (a:Company {tyt_id: $aid}), (b:Company {tyt_id: $iid})
                    MERGE (a)-[r:INVESTS_IN]->(b)
                    SET r.ratio = $ratio, r.amount = $amount
                """, {"aid": inv.investor_id, "iid": investee_id,
                      "ratio": float(inv.share_ratio) if inv.share_ratio else None,
                      "amount": float(inv.invested_amount_wan or 0)})

            # 5) 演示供应链关系（公开报道整理，标注演示）
            supply_pairs = [
                ("宁德时代新能源科技股份有限公司", "特斯拉（上海）有限公司", "电池供应（演示）"),
                ("弗迪电池有限公司", "比亚迪股份有限公司", "电池供应（演示）"),
                ("宁德邦普循环科技有限公司", "宁德时代新能源科技股份有限公司", "电池回收（演示）"),
            ]
            for src_name, dst_name, note in supply_pairs:
                sid = name_to_id.get(src_name)
                did = name_to_id.get(dst_name)
                if did is None:
                    did = 920_000_000 + abs(hash(dst_name)) % 100000
                    s.run("MERGE (co:Company {tyt_id: $id}) SET co.name = $name, co.status='外部企业'",
                          {"id": did, "name": dst_name})
                if sid:
                    s.run("""
                        MATCH (a:Company {tyt_id: $aid}), (b:Company {tyt_id: $bid})
                        MERGE (a)-[r:SUPPLIES_TO]->(b) SET r.note = $note
                    """, {"aid": sid, "bid": did, "note": note})

            # 6) 个人-个人关系（共同投资人，公开工商推导）
            co_investors = [("王传福", "吕向阳"), ("曾毓群", "黄世霖")]
            for a, b in co_investors:
                if a in person_ids and b in person_ids:
                    s.run("""
                        MATCH (a:Person {tyt_id: $aid}), (b:Person {tyt_id: $bid})
                        MERGE (a)-[r:CO_INVESTOR_WITH]->(b) SET r.note = '共同投资（公开工商推导）'
                    """, {"aid": person_ids[a], "bid": person_ids[b]})

            # 统计
            stats = s.run(
                "MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt").data()
            rels = s.run(
                "MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS cnt").data()
        log.info("Neo4j 图谱初始化完成: %s / %s", stats, rels)
    finally:
        db.close()


if __name__ == "__main__":
    run()
