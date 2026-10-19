"""Neo4j 5 客户端（关系图谱）

图谱模型：
  (:Company {tyt_id, name, credit_code, status})
  (:Person   {tyt_id, name, masked_name})
  关系：
    (:Company)-[:HAS_LEGAL_REP {since}]->(:Person)      法定代表人
    (:Person)-[:EXECUTIVE_OF {position, since}]->(:Company)   主要人员任职
    (:Person)-[:SHAREHOLDER_OF {ratio, amount}]->(:Company)   自然人股东
    (:Company)-[:SHAREHOLDER_OF {ratio, amount}]->(:Company)  机构股东
    (:Company)-[:INVESTS_IN {ratio, amount}]->(:Company)      对外投资
    (:Company)-[:SUPPLIES_TO]->(:Company)                    供应链（演示）
    (:Person)-[:CO_INVESTOR_WITH]->(:Person)                 共同投资人（公开工商推导）
"""
import logging
from contextlib import contextmanager
from typing import Any, Optional

from tyt.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

logger = logging.getLogger(__name__)

try:
    from neo4j import GraphDatabase
    _HAS_NEO4J = True
except ImportError:
    _HAS_NEO4J = False
    logger.warning("neo4j driver not installed, graph features disabled")

_driver = None


def get_driver():
    global _driver
    if not _HAS_NEO4J:
        return None
    if _driver is not None:
        return _driver
    try:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        _driver.verify_connectivity()
        logger.info("Neo4j connected: %s", NEO4J_URI)
    except Exception as e:
        logger.warning("Neo4j unavailable: %s", e)
        _driver = None
    return _driver


@contextmanager
def neo4j_session():
    """会话上下文：with neo4j_session() as s: s.run(...)"""
    driver = get_driver()
    if driver is None:
        raise RuntimeError("Neo4j 不可用")
    with driver.session() as session:
        yield session


def run_cypher(cypher: str, params: dict | None = None) -> list[dict[str, Any]]:
    with neo4j_session() as s:
        result = s.run(cypher, params or {})
        return [record.data() for record in result]


def neo4j_available() -> bool:
    return get_driver() is not None
