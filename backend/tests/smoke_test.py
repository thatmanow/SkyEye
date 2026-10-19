"""全链路 API 冒烟测试：认证 / 生活类 / 生活圈 / 商业类 / 图谱 / 监控 / 报告 / 线索 / 管理端 / AI

运行：python -m tests.smoke_test [base_url]
"""
import json
import sys
import time
import urllib.request
import urllib.error

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
DEMO_PASSWORD = "SkyEye@123456"

PASSED, FAILED = [], []


def call(method: str, path: str, token: str = "", body=None, expect: int = 200, record: bool = True):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            code, raw = resp.status, resp.read()
    except urllib.error.HTTPError as e:
        try:
            code, raw = e.code, e.read()
        except Exception:
            code, raw = e.code, b""
    try:
        payload = json.loads(raw.decode())
    except Exception:
        payload = {"__binary__": len(raw)}
    if record:
        ok = code == expect and payload.get("code", 0) == 0
        (PASSED if ok else FAILED).append(f"{method} {path} -> HTTP {code} code={payload.get('code')} {str(payload.get('message'))[:60]}")
    return code, payload


def check(name: str, cond: bool):
    (PASSED if cond else FAILED).append(f"ASSERT {name}: {'ok' if cond else 'FAIL'}")


def main():
    ts = int(time.time())

    # ---------- 1. 健康检查 ----------
    _, h = call("GET", "/api/health")
    deps = h.get("deps", {})
    print(f"    [info] health deps = {deps}")
    check("health.mysql", deps.get("mysql") is True)
    check("health.redis", deps.get("redis") is True)
    check("health.neo4j", deps.get("neo4j") is True)

    # ---------- 2. 认证 ----------
    account = f"tester{ts % 100000}@tyt.test"
    call("POST", "/api/v1/auth/register", body={
        "account": account, "nickname": f"测试{ts % 1000}", "password": "Test@12345",
        "confirm_password": "Test@12345", "agree": True,
    })
    _, r = call("POST", "/api/v1/auth/login", body={"account": account, "password": "Test@12345"})
    d = r.get("data", {})
    user_token = d.get("access_token", "")
    check("login.token", bool(user_token))

    _, me = call("GET", "/api/v1/auth/me", token=user_token)
    check("me.role", me.get("data", {}).get("user", {}).get("role") == "user")
    new_uid = me.get("data", {}).get("id") or me.get("data", {}).get("user_id")

    _, rf = call("POST", "/api/v1/auth/refresh", body={"refresh_token": d.get("refresh_token", "")})
    check("refresh.token", bool(rf.get("data", {}).get("access_token")))
    user_token = rf["data"]["access_token"]

    _, ad = call("POST", "/api/v1/auth/login", body={"account": "demo@tyt.demo", "password": DEMO_PASSWORD})
    demo_token = ad["data"]["access_token"]
    _, pr = call("POST", "/api/v1/auth/login", body={"account": "premium@tyt.demo", "password": DEMO_PASSWORD})
    premium_token = pr["data"]["access_token"]
    _, am = call("POST", "/api/v1/auth/login", body={"account": "admin@tyt.demo", "password": DEMO_PASSWORD})
    admin_token = am["data"]["access_token"]
    check("admin.login", bool(admin_token))
    call("GET", "/api/v1/auth/guest-info")

    # ---------- 3. 生活类 ----------
    _, ms = call("GET", "/api/v1/life/merchants/search?keyword=%E5%B0%8F%E9%A6%86&page=1&page_size=5", token=user_token)
    merchants = ms.get("data", {}).get("items", [])
    check("merchants.found", len(merchants) > 0)
    mid = merchants[0]["id"] if merchants else 0

    _, md = call("GET", f"/api/v1/life/merchants/{mid}", token=user_token)
    check("merchant.detail", md.get("data", {}).get("id") == mid)

    _, rev = call("POST", f"/api/v1/life/merchants/{mid}/reviews", token=user_token,
                  body={"rating": 5, "content": f"环境不错服务到位（冒烟测试 {ts}），值得推荐。"})
    check("review.submitted", rev.get("code") == 0)

    _, he = call("GET", "/api/v1/life/housing/estates/search?keyword=%E7%BF%A0%E6%B9%96", token=user_token)
    estates = he.get("data", {}).get("items", [])
    check("estates.found", len(estates) > 0)
    estate_id = estates[0]["id"] if estates else 0

    _, hr = call("GET", "/api/v1/life/housing/records?subject_type=estate&keyword=%E9%98%B3%E5%85%89%E8%8A%B1%E5%9B%AD", token=user_token)
    check("housing.records", hr.get("code") == 0 and hr.get("data", {}).get("estate") is not None)

    _, hc = call("POST", "/api/v1/life/housing/complaints", token=user_token,
                 body={"subject_type": "estate", "subject_id": estate_id,
                       "subject_label": "翠湖天地",
                       "content": f"地下车库渗水长期未修（冒烟测试 {ts}）", "category": "物业纠纷"})
    check("complaint.submitted", hc.get("code") == 0)

    _, jc = call("GET", "/api/v1/life/jobs/companies?name=%E7%A7%91%E6%8A%80", token=user_token)
    check("jobs.found", jc.get("code") == 0 and jc.get("data", {}).get("total", 0) > 0)

    _, ps = call("POST", "/api/v1/life/person/search", token=user_token, body={"name": "张小三"})
    pd_ = ps.get("data", {})
    check("person.masked", pd_.get("masked_name") == "张*三")
    check("person.records", pd_.get("total", 0) > 0)

    # ---------- 4. 生活圈 ----------
    _, posts = call("GET", "/api/v1/community/posts?page=1&page_size=5", token=user_token)
    items = posts.get("data", {}).get("items", [])
    check("posts.visible", len(items) > 0)

    _, np = call("POST", "/api/v1/community/posts", token=demo_token,
                 body={"category": "avoid_pit", "title": f"冒烟测试帖 {ts}",
                       "content": "先审后发流程验证帖，内容超过十个字。", "is_anonymous": True})
    check("post.pending", np.get("code") == 0)

    # 管理员待审列表里找到该帖并审核通过
    _, pl = call("GET", "/api/v1/admin/audit/post?page=1&page_size=50", token=admin_token)
    pending_posts = pl.get("data", {}).get("items", [])
    mine = next((p for p in pending_posts if str(ts) in (p.get("title") or "")), None)
    check("post.in_pending", mine is not None)
    if mine:
        call("POST", f"/api/v1/admin/audit/post/{mine['id']}", token=admin_token,
             body={"action": "approve", "reason": "冒烟测试通过"})
        _, pt = call("GET", f"/api/v1/community/posts/{mine['id']}", token=user_token)
        check("post.approved", pt.get("code") == 0 and pt.get("data", {}).get("id") == mine["id"])
        call("POST", f"/api/v1/community/posts/{mine['id']}/like", token=user_token)
        _, cm = call("POST", f"/api/v1/community/posts/{mine['id']}/comments", token=user_token,
                     body={"content": f"评论冒烟 {ts}", "is_anonymous": True})
        check("comment.submitted", cm.get("code") == 0)
        # 待审评论 -> 通过
        _, cl = call("GET", "/api/v1/admin/audit/comment?page=1&page_size=50", token=admin_token)
        pending_comments = cl.get("data", {}).get("items", [])
        mcm = next((c for c in pending_comments if str(ts) in (c.get("content") or "")), None)
        if mcm:
            call("POST", f"/api/v1/admin/audit/comment/{mcm['id']}", token=admin_token,
                 body={"action": "approve", "reason": "冒烟"})
            call("POST", "/api/v1/community/reports", token=demo_token,
                 body={"target_type": "comment", "target_id": mcm["id"], "reason": "虚假信息",
                       "description": "冒烟测试举报内容"})

    # ---------- 5. 商业类：企业查询 ----------
    _, cs = call("GET", "/api/v1/biz/companies/search?keyword=%E8%85%BE%E8%AE%AF&page=1&page_size=5", token=user_token)
    companies = cs.get("data", {}).get("items", [])
    check("companies.found", len(companies) > 0)
    cid = companies[0]["id"] if companies else 0

    _, cd = call("GET", f"/api/v1/biz/companies/{cid}", token=user_token)
    check("company.detail", cd.get("data", {}).get("id") == cid)

    for sub in ("shareholders", "personnel", "investments", "branches", "changes", "risks"):
        _, sub_r = call("GET", f"/api/v1/biz/companies/{cid}/{sub}", token=user_token)
        check(f"company.{sub}", sub_r.get("code") == 0)

    # ---------- 6. 图谱（Neo4j） ----------
    _, gs = call("GET", "/api/v1/biz/graph/status", token=user_token)
    check("graph.status", gs.get("code") == 0)

    _, ge = call("GET", f"/api/v1/biz/graph/nodes/{cid}/expand?limit=30", token=user_token)
    check("graph.expand", ge.get("code") == 0 and len(ge.get("data", {}).get("nodes", [])) > 0)

    _, gc = call("GET", f"/api/v1/biz/graph/companies/{cid}", token=user_token)
    check("graph.company", gc.get("code") == 0)

    _, gp = call("GET", f"/api/v1/biz/graph/path?from_id={cid}&to_id={cid}", token=user_token)
    check("graph.path", gp.get("code") == 0)

    _, ct = call("GET", f"/api/v1/biz/graph/companies/{cid}/controller", token=user_token)
    check("graph.controller", ct.get("code") == 0)

    # ---------- 7. 监控 ----------
    _, wl0 = call("GET", "/api/v1/biz/monitor/watches", token=premium_token)
    for w in (wl0.get("data", {}) or {}).get("items", wl0.get("data") or []):
        call("DELETE", f"/api/v1/biz/monitor/watches/{w.get('watch_id') or w.get('id')}", token=premium_token)

    _, wc = call("POST", "/api/v1/biz/monitor/watches", token=premium_token,
                 body={"company_id": cid})
    watch_id = wc.get("data", {}).get("id", 0) if isinstance(wc.get("data"), dict) else 0
    check("watch.created", wc.get("code") == 0)

    _, wl = call("GET", "/api/v1/biz/monitor/watches", token=premium_token)
    check("watch.listed", wl.get("code") == 0)

    _, sc = call("POST", "/api/v1/biz/monitor/scan", token=admin_token)
    check("scan.done", sc.get("code") == 0)

    _, ev = call("GET", "/api/v1/biz/monitor/events", token=premium_token)
    check("events.listed", ev.get("code") == 0)

    _, nt = call("GET", "/api/v1/biz/monitor/notifications", token=premium_token)
    check("notifications.listed", nt.get("code") == 0)

    call("GET", "/api/v1/biz/monitor/schedule", token=premium_token)
    call("GET", "/api/v1/biz/monitor/digest", token=premium_token)

    # ---------- 8. 报告 ----------
    _, rc = call("POST", "/api/v1/biz/reports", token=premium_token,
                 body={"company_id": cid, "template": "standard"})
    task_id = rc.get("data", {}).get("task_id", "")
    check("report.created", bool(task_id))

    status = ""
    for _ in range(60):
        _, rs = call("GET", f"/api/v1/biz/reports/{task_id}", token=premium_token)
        status = rs.get("data", {}).get("status", "")
        if status in ("done", "failed"):
            break
        time.sleep(1)
    check("report.done", status == "done")
    print(f"    [info] report status = {status}")

    pdf_code, dl = call("GET", f"/api/v1/biz/reports/{task_id}/download?format=pdf", token=premium_token)
    check("report.pdf", pdf_code == 200 and dl.get("__binary__", 0) > 0)
    xlsx_code, dl2 = call("GET", f"/api/v1/biz/reports/{task_id}/download?format=xlsx", token=premium_token)
    check("report.excel", xlsx_code == 200 and dl2.get("__binary__", 0) > 0)

    # ---------- 9. 线索 ----------
    _, lo = call("GET", "/api/v1/biz/leads?page=1&page_size=5", token=user_token)
    leads = lo.get("data", {}).get("items", [])
    check("leads.found", len(leads) > 0)
    if leads:
        lid = leads[0]["id"]
        _, fv = call("POST", f"/api/v1/biz/leads/{lid}/favorite", token=user_token)
        check("lead.favorite", fv.get("code") == 0)
        _, fu = call("PUT", f"/api/v1/biz/leads/{lid}/follow", token=user_token,
                     body={"status": "following", "note": "冒烟测试跟进",
                           "next_action": "下周电话联系"})
        check("lead.follow", fu.get("code") == 0)
    call("GET", "/api/v1/biz/leads/options", token=user_token)
    call("GET", "/api/v1/biz/leads/favorites", token=user_token)

    # ---------- 10. 管理端 ----------
    _, ap = call("GET", "/api/v1/admin/audit/pending", token=admin_token)
    check("admin.pending", ap.get("code") == 0)

    # 审核此前产生的评价（从待审列表找我们提交的那条）
    _, rl = call("GET", "/api/v1/admin/audit/review?page=1&page_size=50", token=admin_token)
    pending_reviews = rl.get("data", {}).get("items", [])
    mrv = next((x for x in pending_reviews if str(ts) in (x.get("content") or "")), None)
    if mrv:
        _, ra = call("POST", f"/api/v1/admin/audit/review/{mrv['id']}", token=admin_token,
                     body={"action": "approve", "reason": "冒烟"})
        check("review.audited", ra.get("code") == 0)

    _, ul = call("GET", "/api/v1/admin/users?page=1&page_size=20", token=admin_token)
    check("admin.users", ul.get("code") == 0)
    users = ul.get("data", {}).get("items", [])
    target = next((u for u in users if u.get("account") == account), None)

    _, ds = call("GET", "/api/v1/admin/data/sources", token=admin_token)
    check("admin.sources", ds.get("code") == 0)

    _, db_ = call("GET", "/api/v1/admin/dashboard", token=admin_token)
    check("admin.dashboard", db_.get("code") == 0)
    print(f"    [info] dashboard = {json.dumps(db_.get('data', {}), ensure_ascii=False)[:300]}")

    call("GET", "/api/v1/admin/audit-logs?page=1&page_size=5", token=admin_token)
    call("GET", "/api/v1/admin/data/collect-logs?page=1&page_size=5", token=admin_token)

    # 数据导入（CSV）
    csv_content = f"name,city,reg_status\n冒烟测试公司{ts},上海,存续\n"
    _, imp = call("POST", "/api/v1/admin/data/import", token=admin_token,
                  body={"source_code": "gsxt", "entity": "companies", "csv_content": csv_content})
    check("admin.import", imp.get("code") == 0)

    # 用户角色/状态管理
    if target:
        _, ur = call("PUT", f"/api/v1/admin/users/{target['id']}/role", token=admin_token,
                     body={"role": "premium"})
        check("admin.role", ur.get("code") == 0)
        _, st = call("PUT", f"/api/v1/admin/users/{target['id']}/status", token=admin_token,
                     body={"status": "banned"})
        check("admin.status", st.get("code") == 0)
        # banned 用户登录应被拒
        _, bl = call("POST", "/api/v1/auth/login", body={"account": account, "password": "Test@12345"},
                     expect=200, record=False)
        check("banned.login_rejected", bl.get("code") != 0)

    # RBAC：普通用户访问管理端被拒
    _, denied = call("GET", "/api/v1/admin/users", token=user_token, expect=403, record=False)
    check("rbac.denied", denied.get("code") != 0)

    # ---------- 11. AI ----------
    _, as_ = call("GET", "/api/v1/ai/status", token=premium_token)
    ai_data = as_.get("data", as_)
    print(f"    [info] ai.status = {json.dumps(ai_data, ensure_ascii=False)[:200]}")
    if ai_data and ai_data.get("ollama"):
        _, ac = call("POST", "/api/v1/ai/chat", token=premium_token,
                     body={"question": "用一句话说明什么是企业尽职调查"})
        print(f"    [info] ai.chat = {json.dumps(ac.get('data', {}), ensure_ascii=False)[:200]}")

    # ---------- 汇总 ----------
    print("\n========== 结果汇总 ==========")
    print(f"通过: {len(PASSED)}  失败: {len(FAILED)}")
    for f in FAILED:
        print("  FAIL:", f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
