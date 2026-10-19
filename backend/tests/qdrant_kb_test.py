"""Qdrant 向量库迁移验证测试（替代原 Chroma 知识库）

不依赖任何外部服务（Ollama / Redis / Neo4j 均 mock 或绕过）：
- 用临时目录作为 Qdrant 本地持久化路径
- mock embed() 返回确定性向量，chat()/rerank() 返回占位值
覆盖：入库 / 已存在判定 / 统计 / 列表(筛选+分页) / 召回查询 / 删除 / 爬虫清空 / 手动录入

运行：conda base 环境下  python -m tests.qdrant_kb_test
"""
import hashlib
import os
import shutil
import sys
import tempfile

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

import tyt.services.ai_service as ai  # noqa: E402

_TMP = tempfile.mkdtemp(prefix="tyt_qdrant_test_")
ai.QDRANT_DIR = os.path.join(_TMP, "tyt_qdrant")
ai._QDRANT = None  # 强制使用新的临时客户端


def _fake_embed(text: str):
    """确定性 4 维向量（前 4 字节映射），保证相同文本向量一致、不同文本可区分"""
    h = hashlib.md5(text.encode("utf-8")).digest()
    return [(b / 255.0) - 0.5 for b in h[:4]]


ai.embed = _fake_embed
ai.rerank = lambda q, docs, top_n=3: []   # 走召回序降级分支
ai.chat = lambda prompt, context_docs=None: "（测试）这是一条模拟回答。"


def _reset():
    ai._QDRANT = None
    shutil.rmtree(ai.QDRANT_DIR, ignore_errors=True)
    os.makedirs(ai.QDRANT_DIR, exist_ok=True)


def test_upsert_and_existing():
    _reset()
    assert ai.upsert_knowledge("doc1", "人民网报道某公司风险事件",
                               {"kind": "people_article", "title": "风险报道",
                                "source": "人民网", "url": "http://x"})
    assert ai.upsert_knowledge("doc2", "baostock 行情 600000 收盘价",
                               {"kind": "baostock_quote", "title": "行情", "source": "baostock"})
    assert ai.upsert_knowledge("doc3", "企业卡片 测试科技有限公司",
                               {"kind": "company_card", "title": "企业卡片", "source": "演示"})
    ex = ai.existing_kb_ids(["doc1", "doc2", "docX"])
    assert ex == {"doc1", "doc2"}, f"existing_kb_ids 错误: {ex}"
    # 重复 upsert 应幂等（不报错、不重复计数）
    ai.upsert_knowledge("doc1", "人民网报道某公司风险事件（更新）",
                        {"kind": "people_article", "title": "风险报道", "source": "人民网"})
    assert ai.kb_stats()["total"] == 3


def test_stats_and_list():
    _reset()
    ai.upsert_knowledge("a", "人民网资讯一", {"kind": "people_article", "title": "资讯A", "source": "人民网"})
    ai.upsert_knowledge("b", "baostock 行情一", {"kind": "baostock_quote", "title": "行情B", "source": "baostock"})
    ai.upsert_knowledge("c", "企业卡片一", {"kind": "company_card", "title": "卡片C", "source": "演示"})
    st = ai.kb_stats()
    assert st["available"] and st["total"] == 3, st
    assert st["by_kind"].get("people_article") == 1

    # 全量列表
    lst = ai.list_knowledge()
    assert lst["total"] == 3 and len(lst["items"]) == 3
    # kind 筛选
    lst2 = ai.list_knowledge(kind="people_article")
    assert lst2["total"] == 1 and lst2["items"][0]["kind"] == "people_article"
    # 关键词筛选（命中正文）
    lst3 = ai.list_knowledge(keyword="行情")
    assert lst3["total"] == 1 and "行情" in lst3["items"][0]["excerpt"]
    # 分页
    lst4 = ai.list_knowledge(page=1, page_size=2)
    assert lst4["total"] == 3 and len(lst4["items"]) == 2
    # 稳定排序：按 kind 升序，第一条应为 baostock_quote
    assert lst4["items"][0]["kind"] == "baostock_quote"


def test_rag_query_recall():
    _reset()
    text1 = "人民网报道某公司风险事件"
    ai.upsert_knowledge("q1", text1, {"kind": "people_article", "title": "风险报道", "source": "人民网", "url": "http://x"})
    ai.upsert_knowledge("q2", "完全不相关的天气数据内容", {"kind": "company_card", "title": "其他", "source": "演示"})
    # 用与 doc1 完全相同的文本作为问题 -> 向量一致 -> 余弦=1.0 -> 必进引用
    res = ai.rag_answer(text1)
    assert "answer" in res and isinstance(res["references"], list)
    refs = res["references"]
    assert any(r.get("similarity", 0) >= 0.6 for r in refs), f"未召回高相似文档: {refs}"
    assert refs[0]["title"] == "风险报道"


def test_delete_and_purge():
    _reset()
    ai.upsert_knowledge("d1", "人民网资讯待删", {"kind": "people_article", "title": "待删", "source": "人民网"})
    ai.upsert_knowledge("d2", "baostock 行情待清", {"kind": "baostock_quote", "title": "待清", "source": "baostock"})
    ai.upsert_knowledge("d3", "企业卡片保留", {"kind": "company_card", "title": "保留", "source": "演示"})
    assert ai.delete_knowledge("d1")
    assert ai.list_knowledge()["total"] == 2
    # 清空爬虫来源（people_article + baostock_quote）
    n = ai.purge_crawler_knowledge()
    assert n == 1, f"purge 删除数应为 1（d2），实际 {n}"
    assert ai.list_knowledge()["total"] == 1  # 仅剩 d3


def test_purge_only_crawler_keeps_manual():
    """日切清理策略校验：仅删除爬虫来源，手动录入/企业卡片/未知 kind 全部保留"""
    _reset()
    # 爬虫来源（应被清）
    ai.upsert_knowledge("p1", "人民网资讯", {"kind": "people_article", "title": "资讯", "source": "人民网"})
    ai.upsert_knowledge("p2", "baostock 行情", {"kind": "baostock_quote", "title": "行情", "source": "baostock"})
    # 管理员手动录入（应保留）
    ai.upsert_knowledge("m1", "手动维护的行业规则", {"kind": "manual", "title": "手动规则", "source": "管理员手动录入"})
    # 企业卡片（应保留）
    ai.upsert_knowledge("c1", "企业卡片 某某公司", {"kind": "company_card", "title": "卡片", "source": "演示"})
    # 未知 kind（防御性：任何非白名单 kind 都不能被误删）
    ai.upsert_knowledge("u1", "未来新增的某种来源", {"kind": "future_src", "title": "未知", "source": "其它"})
    # 缺失 kind 的脏数据（同样不能误删）
    ai.upsert_knowledge("u2", "缺 kind 的文档", {"title": "无 kind", "source": "其它"})

    assert ai.kb_stats()["total"] == 6
    n = ai.purge_crawler_knowledge()
    assert n == 2, f"应只删除 2 条爬虫文档，实际 {n}"

    remain = ai.list_knowledge()
    assert remain["total"] == 4, f"应保留 4 条非爬虫文档，实际 {remain['total']}"
    kinds = {it["kind"] for it in remain["items"]}
    assert kinds == {"manual", "company_card", "future_src", "other"}, kinds
    # 确认手动录入文案完整保留
    manual = [it for it in remain["items"] if it["kind"] == "manual"][0]
    assert manual["title"] == "手动规则"


def test_add_manual():
    _reset()
    mid = ai.add_manual_knowledge("手动知识标题", "手动录入的知识正文内容", "http://manual")
    assert mid and mid.startswith("manual:"), mid
    st = ai.kb_stats()
    assert st["by_kind"].get("manual") == 1
    # 手动知识不被每日爬虫清空影响
    assert ai.purge_crawler_knowledge() == 0
    assert ai.list_knowledge()["total"] == 1


def test_empty_collection_graceful():
    _reset()
    # 集合尚未创建时，各读操作应优雅降级而非抛错
    assert ai.kb_stats()["available"] is False
    assert ai.list_knowledge()["total"] == 0
    assert ai.existing_kb_ids(["x"]) == set()
    assert ai.purge_crawler_knowledge() == 0
    res = ai.rag_answer("任意问题")
    assert "answer" in res and res["references"] == []


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  FAIL  {t.__name__}: {e}")
        except Exception as e:  # noqa
            failed += 1
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
    shutil.rmtree(_TMP, ignore_errors=True)
    print(f"\n结果：通过 {len(tests)-failed}/{len(tests)}")
    sys.exit(1 if failed else 0)
