"""关系图谱服务（Neo4j 5）：懒加载展开、路径查询、图谱快照

节点：(:Company {tyt_id, name, credit_code, status}) (:Person {tyt_id, name})
关系：HAS_LEGAL_REP / EXECUTIVE_OF / SHAREHOLDER_OF / INVESTS_IN / SUPPLIES_TO / CO_INVESTOR_WITH
"""
import logging
from typing import Optional

from tyt.db.neo4j_client import neo4j_session, neo4j_available

logger = logging.getLogger(__name__)

EXPAND_LIMIT = 60  # 每次懒加载展开的邻居上限


def _node_label(tyt_id: int) -> str:
    """节点 ID 规则：企业 1..1e9；人员 1e9+（seed 分配）"""
    return "Person" if tyt_id >= 1_000_000_000 else "Company"


def expand_node(tyt_id: int, limit: int = EXPAND_LIMIT) -> dict:
    """懒加载：展开单个节点的直接关系（一度），前端按需逐层加载"""
    label = _node_label(tyt_id)
    with neo4j_session() as s:
        center = s.run(
            f"MATCH (n:{label} {{tyt_id: $id}}) RETURN n.tyt_id AS id, n.name AS name, labels(n) AS labels",
            {"id": tyt_id}).single()
        if center is None:
            return {"nodes": [], "edges": [], "not_found": True}

        result = s.run(f"""
            MATCH (n:{label} {{tyt_id: $id}})-[r]-(m)
            RETURN n.tyt_id AS src, m.tyt_id AS dst, m.name AS name, labels(m) AS labels,
                   type(r) AS rel, properties(r) AS props
            LIMIT $limit
        """, {"id": tyt_id, "limit": limit})
        nodes, edges = {}, []
        nodes[tyt_id] = {"id": tyt_id, "name": center["name"],
                         "type": "person" if label == "Person" else "company"}
        for rec in result:
            nid, nname = rec["dst"], rec["name"]
            ntype = "person" if "Person" in rec["labels"] else "company"
            if nid not in nodes:
                nodes[nid] = {"id": nid, "name": nname, "type": ntype}
            props = rec["props"] or {}
            edges.append({
                "source": tyt_id, "target": nid,
                "rel": rec["rel"],
                "label": _rel_label(rec["rel"], props),
            })
        return {"nodes": list(nodes.values()), "edges": edges}


def company_graph(company_id: int) -> dict:
    """企业详情页图谱快照：中心企业 + 一度邻居"""
    return expand_node(company_id)


def find_path(from_id: int, to_id: int, max_hops: int = 4) -> dict:
    """两节点间最短路径（穿透查询，如实控人链路）"""
    from_label = _node_label(from_id)
    to_label = _node_label(to_id)
    with neo4j_session() as s:
        if from_id == to_id:
            node = s.run(
                f"MATCH (n:{from_label} {{tyt_id: $id}}) RETURN n.tyt_id AS id, n.name AS name",
                {"id": from_id}).single()
            if node is None:
                return {"found": False, "hops": 0, "nodes": [], "edges": []}
            ntype = "person" if from_label == "Person" else "company"
            return {"found": True, "hops": 0,
                    "nodes": [{"id": node["id"], "name": node["name"], "type": ntype}],
                    "edges": []}
        result = s.run(f"""
            MATCH p = shortestPath((a:{from_label} {{tyt_id: $a}})-[*..{max_hops}]-(b:{to_label} {{tyt_id: $b}}))
            RETURN [n IN nodes(p) | {{id: n.tyt_id, name: n.name,
                     type: CASE 'Person' IN labels(n) WHEN true THEN 'person' ELSE 'company' END}}] AS nodes,
                   [r IN relationships(p) | {{source: startNode(r).tyt_id, target: endNode(r).tyt_id,
                     rel: type(r), props: properties(r)}}] AS edges,
                   length(p) AS hops
        """, {"a": from_id, "b": to_id}).single()
        if result is None:
            return {"found": False, "hops": 0, "nodes": [], "edges": []}
        edges = [{
            "source": e["source"], "target": e["target"], "rel": e["rel"],
            "label": _rel_label(e["rel"], e["props"] or {}),
        } for e in result["edges"]]
        return {"found": True, "hops": result["hops"],
                "nodes": result["nodes"], "edges": edges}


def actual_controller(company_id: int) -> dict:
    """股权穿透：自然人最大持股链路（公开工商信息推导）"""
    with neo4j_session() as s:
        result = s.run("""
            MATCH p = (n:Person)-[:SHAREHOLDER_OF|INVESTS_IN*1..4]->(c:Company {tyt_id: $id})
            WITH p, n, reduce(total = 1.0, r IN relationships(p) |
                     total * CASE WHEN r.ratio IS NULL THEN 1.0 ELSE r.ratio / 100.0 END) AS effective
            RETURN n.name AS person, n.tyt_id AS person_id, effective,
                   [r IN relationships(p) | {src: startNode(r).name, dst: endNode(r).name, rel: type(r), ratio: r.ratio}] AS chain
            ORDER BY effective DESC LIMIT 3
        """, {"id": company_id}).data()
        return {"controllers": result}


def _rel_label(rel: str, props: dict) -> str:
    names = {
        "HAS_LEGAL_REP": "法定代表人", "EXECUTIVE_OF": "任职", "SHAREHOLDER_OF": "持股",
        "INVESTS_IN": "投资", "SUPPLIES_TO": "供应", "CO_INVESTOR_WITH": "共同投资",
    }
    base = names.get(rel, rel)
    if props.get("ratio") is not None:
        base += f" {props['ratio']}%"
    elif props.get("position"):
        base += f"·{props['position']}"
    return base


def graph_ready() -> bool:
    return neo4j_available()
