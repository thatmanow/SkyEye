"""进程内 API 冒烟（fakeredis 替代 Redis，复用 TestClient 启动真实应用）

目的：在缺乏独立 Redis/Neo4j/Ollama 服务的环境下，尽量多地实跑接口，发现运行时 bug。
- Redis 用 fakeredis 内存实现替换（get_redis 在所有引用模块中打补丁）
- Neo4j 关闭：图谱类接口标记为 ENV（基础设施缺失，非代码 bug）
- Ollama 视可用情况：嵌入/对话可能超时，相关写入类接口标记为 ENV

运行：conda base  python -m tests.api_smoke_fakeredis
"""
import os
import sys
import traceback

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

import fakeredis  # noqa: E402

# ---- 在所有引用 get_redis 的模块中替换为 fakeredis ----
_fake = fakeredis.FakeStrictRedis(decode_responses=True)


def fake_get_redis():
    return _fake


import tyt.db.redis_client as rc  # noqa: E402
rc.get_redis = fake_get_redis
rc._client = _fake
for _m in ("tyt.services.auth_service", "tyt.services.quota_service",
           "tyt.services.knowledge_sync_service", "tyt.main", "tyt.core.rbac"):
    __import__(_m).get_redis = fake_get_redis

from fastapi.testclient import TestClient  # noqa: E402
import tyt.main as main  # noqa: E402

DEMO_PASSWORD = "SkyEye@123456"
client = TestClient(main.app)
PASSED, FAILED, ERRORS, ENV = [], [], [], []

try:
    from tyt.main import app  # noqa
except Exception:
    pass


def call(method, path, token="", body=None, expect=200, record=True):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = client.request(method, path, json=body, headers=headers)
    except Exception as ex:
        if record:
            ERRORS.append(f"{method} {path} -> SERVER ERROR: {type(ex).__name__}: {ex}\n{traceback.format_exc()[-800:]}")
        return None, {}
    try:
        payload = r.json()
    except Exception:
        payload = {}
    if record:
        ok = r.status_code == expect and payload.get("code", 0) == 0
        if r.status_code >= 500:
            ERRORS.append(f"{method} {path} -> HTTP {r.status_code} (500 类服务端错误)")
        elif not ok:
            FAILED.append(f"{method} {path} -> HTTP {r.status_code} code={payload.get('code')} {str(payload.get('message'))[:50]}")
        else:
            PASSED.append(f"{method} {path}")
    return r, payload


def mark(name, cond, env=False):
    (ENV if env else (PASSED if cond else FAILED)).append(name)


# ---------- 1. 健康检查 ----------
r, h = call("GET", "/api/health")
deps = h.get("deps", {})
print("  [info] health deps =", deps)
mark("health.mysql", deps.get("mysql") is True)
mark("health.redis(fake)", deps.get("redis") is True)

# ---------- 2. 认证 ----------
_, reg = call("POST", "/api/v1/auth/register", body={
    "account": "e2e_test@tyt.test", "nickname": "E2E",
    "password": "E2E@12345", "confirm_password": "E2E@12345", "agree": True})
_, r = call("POST", "/api/v1/auth/login", body={"account": "demo@tyt.demo", "password": DEMO_PASSWORD})
user_token = r.get("data", {}).get("access_token", "")
mark("login.user", bool(user_token))
_, me = call("GET", "/api/v1/auth/me", token=user_token)
mark("me.role", me.get("data", {}).get("user", {}).get("role") == "user")
_, rf = call("POST", "/api/v1/auth/refresh", body={"refresh_token": r.get("data", {}).get("refresh_token", "")})
mark("refresh", bool(rf.get("data", {}).get("access_token")))
user_token = rf.get("data", {}).get("access_token", user_token)
_, pr = call("POST", "/api/v1/auth/login", body={"account": "premium@tyt.demo", "password": DEMO_PASSWORD})
premium_token = pr.get("data", {}).get("access_token", "")
_, am = call("POST", "/api/v1/auth/login", body={"account": "admin@tyt.demo", "password": DEMO_PASSWORD})
admin_token = am.get("data", {}).get("access_token", "")
mark("admin.login", bool(admin_token))
call("GET", "/api/v1/auth/guest-info")

# ---------- 3. 生活类 ----------
_, ms = call("GET", "/api/v1/life/merchants/search?keyword=%E5%B0%8F%E9%A6%86&page=1&page_size=5", token=user_token)
merchants = ms.get("data", {}).get("items", [])
mark("merchants.found", len(merchants) > 0)
mid = merchants[0]["id"] if merchants else 0
_, md = call("GET", f"/api/v1/life/merchants/{mid}", token=user_token)
mark("merchant.detail", md.get("data", {}).get("id") == mid)
_, rev = call("POST", f"/api/v1/life/merchants/{mid}/reviews", token=user_token,
              body={"rating": 5, "content": "E2E 测试评价，内容合规可过审。"})
mark("review.submitted", rev.get("code") == 0)
_, he = call("GET", "/api/v1/life/housing/estates/search?keyword=%E7%BF%A0%E6%B9%96", token=user_token)
estates = he.get("data", {}).get("items", [])
mark("estates.found", len(estates) > 0)
estate_id = estates[0]["id"] if estates else 0
_, hr = call("GET", "/api/v1/life/housing/records?subject_type=estate&keyword=%E9%98%B3%E5%85%89", token=user_token)
mark("housing.records", hr.get("code") == 0)
_, hc = call("POST", "/api/v1/life/housing/complaints", token=user_token,
             body={"subject_type": "estate", "subject_id": estate_id, "subject_label": "测试小区",
                   "content": "E2E 投诉测试内容。", "category": "物业纠纷"})
mark("complaint.submitted", hc.get("code") == 0)
_, jc = call("GET", "/api/v1/life/jobs/companies?name=%E7%A7%91%E6%8A%80", token=user_token)
mark("jobs.found", jc.get("code") == 0 and jc.get("data", {}).get("total", 0) > 0)
_, ps = call("POST", "/api/v1/life/person/search", token=user_token, body={"name": "张小三"})
pd_ = ps.get("data", {})
mark("person.masked", pd_.get("masked_name") == "张*三")
mark("person.records", pd_.get("total", 0) > 0)

# ---------- 4. 生活圈 ----------
_, posts = call("GET", "/api/v1/community/posts?page=1&page_size=5", token=user_token)
mark("posts.visible", len(posts.get("data", {}).get("items", [])) > 0)
_, np = call("POST", "/api/v1/community/posts", token=user_token,
             body={"category": "avoid_pit", "title": "E2E 测试帖", "content": "先审后发流程验证帖，内容超过十个字。", "is_anonymous": True})
mark("post.pending", np.get("code") == 0)
pid = np.get("data", {}).get("id")
if pid:
    _, pl = call("GET", "/api/v1/admin/audit/post?page=1&page_size=50", token=admin_token)
    mine = next((p for p in pl.get("data", {}).get("items", []) if p.get("id") == pid), None)
    mark("post.in_pending", mine is not None)
    if mine:
        call("POST", f"/api/v1/admin/audit/post/{pid}", token=admin_token, body={"action": "approve", "reason": "E2E"})
        _, pt = call("GET", f"/api/v1/community/posts/{pid}", token=user_token)
        mark("post.approved", pt.get("code") == 0 and pt.get("data", {}).get("id") == pid)
        call("POST", f"/api/v1/community/posts/{pid}/like", token=user_token)
        _, cm = call("POST", f"/api/v1/community/posts/{pid}/comments", token=user_token,
                     body={"content": "E2E 评论测试。", "is_anonymous": True})
        mark("comment.submitted", cm.get("code") == 0)
        cid = cm.get("data", {}).get("id")
        if cid:
            _, cl = call("GET", "/api/v1/admin/audit/comment?page=1&page_size=50", token=admin_token)
            mcm = next((c for c in cl.get("data", {}).get("items", []) if c.get("id") == cid), None)
            if mcm:
                call("POST", f"/api/v1/admin/audit/comment/{cid}", token=admin_token, body={"action": "approve", "reason": "E2E"})

# ---------- 5. 商业类：企业查询 ----------
_, cs = call("GET", "/api/v1/biz/companies/search?keyword=%E8%85%BE%E8%AE%AF&page=1&page_size=5", token=user_token)
companies = cs.get("data", {}).get("items", [])
mark("companies.found", len(companies) > 0)
cid = companies[0]["id"] if companies else 0
_, cd = call("GET", f"/api/v1/biz/companies/{cid}", token=user_token)
mark("company.detail", cd.get("data", {}).get("id") == cid)
for sub in ("shareholders", "personnel", "investments", "branches", "changes", "risks"):
    _, sub_r = call("GET", f"/api/v1/biz/companies/{cid}/{sub}", token=user_token)
    mark(f"company.{sub}", sub_r.get("code") == 0)

# ---------- 6. 监控（可能依赖 Neo4j，ENV 容忍） ----------
_, wl0 = call("GET", "/api/v1/biz/monitor/watches", token=premium_token)
if wl0 and wl0.get("code") == 0:
    for w in wl0.get("data", {}).get("items", []):
        call("DELETE", f"/api/v1/biz/monitor/watches/{w.get('watch_id') or w.get('id')}", token=premium_token)
_, wc = call("POST", "/api/v1/biz/monitor/watches", token=premium_token, body={"company_id": cid})
mark("watch.created", wc.get("code") == 0)
_, wl = call("GET", "/api/v1/biz/monitor/watches", token=premium_token)
mark("watch.listed", wl.get("code") == 0)
_, ev = call("GET", "/api/v1/biz/monitor/events", token=premium_token)
mark("events.listed", ev.get("code") == 0)
_, nt = call("GET", "/api/v1/biz/monitor/notifications", token=premium_token)
mark("monitor.notifications", nt.get("code") == 0)

# ---------- 7. 报告（进程内后台任务，MySQL+reportlab，不依赖 Neo4j） ----------
_, rc2 = call("POST", "/api/v1/biz/reports", token=premium_token, body={"company_id": cid, "template": "standard"})
task_id = rc2.get("data", {}).get("task_id", "")
mark("report.created", bool(task_id))
status = ""
import time
for _ in range(40):
    _, rs = call("GET", f"/api/v1/biz/reports/{task_id}", token=premium_token, record=False)
    status = (rs or {}).get("data", {}).get("status", "")
    if status in ("done", "failed"):
        break
    time.sleep(0.5)
mark("report.status_terminal", status in ("done", "failed"), env=(status == ""))
print("  [info] report status =", status)
if status == "done":
    dl_resp, dl = call("GET", f"/api/v1/biz/reports/{task_id}/download?format=pdf", token=premium_token)
    mark("report.pdf", dl_resp is not None and dl_resp.status_code == 200)

# ---------- 8. 线索 ----------
_, lo = call("GET", "/api/v1/biz/leads?page=1&page_size=5", token=user_token)
leads = lo.get("data", {}).get("items", [])
mark("leads.found", len(leads) > 0)
if leads:
    lid = leads[0]["id"]
    call("POST", f"/api/v1/biz/leads/{lid}/favorite", token=user_token)
    call("PUT", f"/api/v1/biz/leads/{lid}/follow", token=user_token,
         body={"status": "following", "note": "E2E 跟进", "next_action": "电话"})

# ---------- 9. 管理端 ----------
_, ap = call("GET", "/api/v1/admin/audit/pending", token=admin_token)
mark("admin.pending", ap.get("code") == 0)
_, ul = call("GET", "/api/v1/admin/users?page=1&page_size=20", token=admin_token)
mark("admin.users", ul.get("code") == 0)
_, ds = call("GET", "/api/v1/admin/data/sources", token=admin_token)
mark("admin.sources", ds.get("code") == 0)
_, db_ = call("GET", "/api/v1/admin/dashboard", token=admin_token)
mark("admin.dashboard", db_.get("code") == 0)
call("GET", "/api/v1/admin/audit-logs?page=1&page_size=5", token=admin_token)
call("GET", "/api/v1/admin/data/collect-logs?page=1&page_size=5", token=admin_token)

# ---------- 10. 会员 / 通知 / AI 状态 ----------
_, bp = call("GET", "/api/v1/billing/me", token=premium_token)
mark("billing.me", bp.get("code") == 0)
_, nf = call("GET", "/api/v1/notifications", token=user_token)
mark("notifications.listed", nf.get("code") == 0)
_, as_ = call("GET", "/api/v1/ai/status", token=premium_token)
mark("ai.status", as_.get("code") == 0)
ai_data = as_.get("data", as_)
print("  [info] ai.status =", {k: ai_data.get(k) for k in ("ollama", "rerank")} if isinstance(ai_data, dict) else ai_data)

# ---------- 11. 知识库管理（手动录入依赖 Ollama 嵌入，ENV 容忍） ----------
_, kbl = call("GET", "/api/v1/admin/kb/documents?page=1&page_size=10", token=admin_token)
mark("kb.list", kbl.get("code") == 0)

# ---------- 汇总 ----------
print("\n========== 进程内 API 冒烟结果 ==========")
print(f"通过: {len(PASSED)}  逻辑失败(FAILED): {len(FAILED)}  服务端错误(ERRORS): {len(ERRORS)}")
print("\n-- FAILED --")
for f in FAILED:
    print("  FAIL:", f)
print("\n-- ERRORS (500/异常，需关注) --")
for e in ERRORS:
    print("  ERR :", e)
PY = None
