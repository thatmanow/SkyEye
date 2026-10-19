"""Elasticsearch 客户端（可选组件）

设计：ES 默认关闭（TYT_ES_ENABLED=0）。开启时企业搜索走 ES（standard 分词），
未开启或连接失败时自动降级为 MySQL FULLTEXT(ngram) —— 搜索功能始终可用。
"""
import logging
from typing import Any, Optional

from tyt.config import ES_ENABLED, ES_URL, ES_INDEX_COMPANY

logger = logging.getLogger(__name__)

_es = None
_checked = False


def get_es():
    global _es, _checked
    if _checked:
        return _es
    _checked = True
    if not ES_ENABLED:
        return None
    try:
        from elasticsearch import Elasticsearch
        _es = Elasticsearch(ES_URL, request_timeout=3)
        if not _es.ping():
            _es = None
    except Exception as e:
        logger.warning("Elasticsearch unavailable (%s), fallback to MySQL FULLTEXT", e)
        _es = None
    return _es


def es_available() -> bool:
    return get_es() is not None


def index_company(company: dict[str, Any]) -> bool:
    es = get_es()
    if es is None:
        return False
    try:
        es.index(index=ES_INDEX_COMPANY, id=company["id"],
                 document={"name": company["name"], "business_scope": company.get("business_scope") or "",
                           "industry": company.get("industry") or ""})
        return True
    except Exception as e:
        logger.warning("ES index failed: %s", e)
        return False


def search_company(keyword: str, size: int = 20) -> Optional[list[dict[str, Any]]]:
    """返回 None 表示 ES 不可用（调用方降级 MySQL）；返回列表为命中"""
    es = get_es()
    if es is None:
        return None
    try:
        resp = es.search(index=ES_INDEX_COMPANY, body={
            "query": {
                "multi_match": {
                    "query": keyword,
                    "fields": ["name^3", "business_scope", "industry"],
                    "type": "best_fields",
                }
            },
            "size": size,
        })
        return [hit["_source"] | {"id": hit["_id"]} for hit in resp["hits"]["hits"]]
    except Exception as e:
        logger.warning("ES search failed: %s", e)
        return None
