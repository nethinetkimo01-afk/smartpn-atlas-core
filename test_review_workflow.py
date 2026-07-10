# -*- coding: utf-8 -*-
"""
IE 送審審核 Workflow 驗證（隔離副本 DB + 隔離 server 5099）。

狀態機：編輯中→[送審]→待審(pending)→[經理確認]→已通過(approved)
                                    →[經理駁回+原因]→已駁回(rejected)
                                    →[編輯員取消審核]→已撤回(withdrawn)
關鍵：送審審核 ≠ 設鎖定版（送審在 ie_review；鎖定版在 ie_stage.is_approved），兩件獨立。

角色：de1(data_entry 編輯員)、mg1(manager 經理)、jim(admin)。
測試 header：1=通過流程(且事先鎖定→證明審核不動鎖定版)、2=撤回流程、3=駁回流程。

用法：隔離 server 起在 5099、已 seed de1/mg1，py test_review_workflow.py
"""
import sys, io, os, json, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5099"
DBP  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_backend", "data", "test_isolated", "atlas_test.db")
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_backend", "test_output", "review_shots")
os.makedirs(SHOT, exist_ok=True)
HA, HB, HC = 1, 2, 3  # approve / withdraw / reject

RESULTS = []
def rec(step, title, ok, detail=""):
    RESULTS.append((step, title, ok))
    print(f"\n[{step}] {'✅ PASS' if ok else '❌ FAIL'} — {title}")
    for ln in detail.splitlines():
        if ln.strip(): print("     " + ln)

def db(sql, params=(), one=False):
    c = sqlite3.connect(DBP, timeout=15); c.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]
        return (rows[0] if rows else None) if one else rows
    finally: c.close()
def dbexec(sql, params=()):
    c = sqlite3.connect(DBP, timeout=15)
    try: c.execute(sql, params); c.commit()
    finally: c.close()

_n = {"i": 0}
def shot(pg, name):
    _n["i"] += 1
    try: pg.screenshot(path=os.path.join(SHOT, f"{_n['i']:02d}_{name}.png"))
    except Exception as e: print("  (shot fail", e, ")")


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        def new_sess(user, pw_):
            ctx = browser.new_context(viewport={"width": 1500, "height": 950})
            page = ctx.new_page()
            box = {"prompt": None, "alerts": []}
            def on_d(d):
                if d.type != "prompt": box["alerts"].append(d.message)
                d.accept(box["prompt"] or "") if d.type == "prompt" else d.accept()
            page.on("dialog", on_d)
            page.goto(f"{BASE}/login", wait_until="domcontentloaded")
            page.fill("#username", user); page.fill("#password", pw_)
            page.click("#btnLogin"); page.wait_for_timeout(1200)
            return ctx, page, box

        # 事先把 header 1 的版本設為鎖定版(is_approved=1) → 證明「審核通過不動鎖定版」
        dbexec("UPDATE ie_stage SET is_approved=1 WHERE id=(SELECT id FROM ie_stage WHERE header_id=? ORDER BY id LIMIT 1)", (HA,))
        ha_sid = db("SELECT id FROM ie_stage WHERE header_id=? ORDER BY id LIMIT 1", (HA,), one=True)["id"]
        locked_before = db("SELECT is_approved FROM ie_stage WHERE id=?", (ha_sid,), one=True)["is_approved"]

        ctx_de, de, de_box = new_sess("de1", "de123")   # 編輯員
        ctx_mg, mg, mg_box = new_sess("mg1", "mg123")    # 經理

        def open_detail(page, hid):
            page.goto(f"{BASE}/ie/{hid}/detail", wait_until="domcontentloaded")
            page.wait_for_timeout(1800)

        def click_submit(page):
            # 送審按鈕(btn-submit-review)可見就點，否則直接呼叫 submitForReview()
            el = page.query_selector("#btn-submit-review")
            if el and el.is_visible(): el.click()
            else: page.evaluate("()=>submitForReview()")
            page.wait_for_timeout(1500)

        # ══════ Flow A：編輯員送審 → 經理確認通過 ══════
        # Step 1: de1 送審 header 1
        open_detail(de, HA)
        submit_btn_visible = de.evaluate("()=>{const b=document.getElementById('btn-submit-review');return b?getComputedStyle(b).display!=='none':false;}")
        click_submit(de)
        shot(de, "de_submit_A")
        qA = db("SELECT id,status,stage_name,submitted_by FROM ie_review WHERE header_id=? AND status='pending'", (HA,), one=True)
        d1 = [f"de1 送審按鈕可見={submit_btn_visible}", f"DB pending={qA}"]
        ok1 = bool(qA) and qA["submitted_by"] == "de1"
        rec(1, "編輯員(de1)送審 header1 某版 → 出現在待審(pending)", ok1, "\n".join(d1))

        # Step 2: 經理界面只顯示 pending
        mg.goto(f"{BASE}/ie/reviews", wait_until="domcontentloaded"); mg.wait_for_timeout(1500)
        shot(mg, "mg_queue")
        qcards = mg.evaluate("""()=>[...document.querySelectorAll('#panel-queue .qcard')].map(c=>({
            id:c.dataset.id, txt:c.querySelector('.meta').innerText.replace(/\\s+/g,' ')}))""")
        qapi = json.loads(mg.evaluate("async()=>JSON.stringify(await (await fetch('/api/ie/review/queue')).json())"))
        d2 = [f"經理待審佇列卡片數={len(qcards)}", f"卡片={[c['id'] for c in qcards]}"]
        # 只有 pending：queue API 每筆 status 應皆 pending
        allp = all(r["status"] == "pending" for r in qapi.get("reviews", []))
        in_queue = any(str(qA["id"]) == c["id"] for c in qcards)
        d2.append(f"佇列全為 pending={allp}; header1 那筆在佇列={in_queue}")
        ok2 = allp and in_queue
        rec(2, "經理界面只顯示 pending → header1 那筆在", ok2, "\n".join(d2))

        # Step 3: 經理確認通過
        mg.evaluate("(id)=>approve(id)", qA["id"])
        mg.wait_for_timeout(1600)
        shot(mg, "mg_approved")
        a_db = db("SELECT status,reviewed_by,reviewed_at FROM ie_review WHERE id=?", (qA["id"],), one=True)
        still_in_q = mg.evaluate("(id)=>[...document.querySelectorAll('#panel-queue .qcard')].some(c=>c.dataset.id==String(id))", qA["id"])
        hist_has = db("SELECT COUNT(*) n FROM ie_review WHERE id=? AND status='approved'", (qA["id"],), one=True)["n"]
        d3 = [f"DB={a_db}", f"仍在待審清單={still_in_q}", f"歷史有approved記錄={hist_has}"]
        ok3 = a_db and a_db["status"] == "approved" and a_db["reviewed_by"] == "mg1" and not still_in_q and hist_has == 1
        rec(3, "經理「確認通過」→ 離開待審、status=approved、歷史有記錄", ok3, "\n".join(d3))

        # ══════ Flow B：編輯員送審 → 編輯員取消審核 ══════
        open_detail(de, HB)
        click_submit(de)
        qB = db("SELECT id FROM ie_review WHERE header_id=? AND status='pending'", (HB,), one=True)
        # 重整後應出現「取消審核」按鈕
        open_detail(de, HB)
        wd_visible = de.evaluate("()=>{const b=document.getElementById('btn-withdraw-review');return b?getComputedStyle(b).display!=='none':false;}")
        shot(de, "de_withdraw_before")
        el = de.query_selector("#btn-withdraw-review")
        if el and el.is_visible(): el.click()
        else: de.evaluate("()=>withdrawReview()")
        de.wait_for_timeout(1500)
        shot(de, "de_withdrawn")
        b_db = db("SELECT status FROM ie_review WHERE id=?", (qB["id"],), one=True) if qB else None
        in_q_b = json.loads(mg.evaluate("async()=>JSON.stringify(await (await fetch('/api/ie/review/queue')).json())"))
        b_in_queue = any(r["id"] == (qB["id"] if qB else -1) for r in in_q_b.get("reviews", []))
        d4 = [f"送審→取消審核按鈕可見={wd_visible}", f"DB status={b_db}", f"仍在待審佇列={b_in_queue}"]
        ok4 = b_db and b_db["status"] == "withdrawn" and not b_in_queue
        rec(4, "編輯員送審 → 「取消審核」→ 離開清單、status=withdrawn", ok4, "\n".join(d4))

        # ══════ Flow C：編輯員送審 → 經理駁回+原因 ══════
        open_detail(de, HC)
        click_submit(de)
        qC = db("SELECT id FROM ie_review WHERE header_id=? AND status='pending'", (HC,), one=True)
        mg.goto(f"{BASE}/ie/reviews", wait_until="domcontentloaded"); mg.wait_for_timeout(1500)
        REASON = "標時未填齊，請補齊主流工序後重送"
        mg_box["prompt"] = REASON
        mg.evaluate("(id)=>reject(id)", qC["id"])
        mg.wait_for_timeout(1600)
        shot(mg, "mg_rejected")
        c_db = db("SELECT status,reject_reason,reviewed_by FROM ie_review WHERE id=?", (qC["id"],), one=True)
        c_in_queue = json.loads(mg.evaluate("async()=>JSON.stringify(await (await fetch('/api/ie/review/queue')).json())"))
        c_still = any(r["id"] == qC["id"] for r in c_in_queue.get("reviews", []))
        # 編輯員看得到駁回原因（badge）
        open_detail(de, HC)
        badge = de.evaluate("()=>{const b=document.getElementById('review-status-badge');return b&&getComputedStyle(b).display!=='none'?b.textContent:'';}")
        shot(de, "de_sees_reject")
        d5 = [f"DB={c_db}", f"仍在待審={c_still}", f"編輯員badge={badge!r}"]
        ok5 = (c_db and c_db["status"] == "rejected" and c_db["reject_reason"] == REASON
               and c_db["reviewed_by"] == "mg1" and not c_still and REASON in (badge or ""))
        rec(5, "經理「駁回+原因」→ 離開清單、status=rejected、原因記錄、編輯員看得到", ok5, "\n".join(d5))

        # ══════ Step 6：審核歷史三筆齊全 ══════
        mg.goto(f"{BASE}/ie/reviews", wait_until="domcontentloaded"); mg.wait_for_timeout(1200)
        mg.evaluate("()=>showTab('hist')"); mg.wait_for_timeout(600)
        shot(mg, "mg_history")
        hist = json.loads(mg.evaluate("async()=>JSON.stringify(await (await fetch('/api/ie/review/history')).json())"))["reviews"]
        by_id = {r["id"]: r for r in hist}
        got = {}
        for label, rid, want in [("approved", qA["id"], "approved"), ("withdrawn", qB["id"], "withdrawn"), ("rejected", qC["id"], "rejected")]:
            r = by_id.get(rid)
            got[label] = r["status"] if r else None
        d6 = [f"歷史筆數={len(hist)}",
              f"approved({qA['id']})={got['approved']} withdrawn({qB['id']})={got['withdrawn']} rejected({qC['id']})={got['rejected']}"]
        # 資訊完整：approved 有 reviewed_by；rejected 有 reject_reason；每筆有 submitted_by/submitted_at/stage_name
        appr_r, rej_r = by_id.get(qA["id"]), by_id.get(qC["id"])
        full = (appr_r and appr_r["reviewed_by"] and rej_r and rej_r["reject_reason"]
                and all(by_id.get(i) and by_id[i]["submitted_by"] and by_id[i]["submitted_at"] and by_id[i]["stage_name"]
                        for i in (qA["id"], qB["id"], qC["id"])))
        d6.append(f"資訊完整(送審人/時間/版本 + 審核人/原因)={bool(full)}")
        ok6 = got["approved"] == "approved" and got["withdrawn"] == "withdrawn" and got["rejected"] == "rejected" and bool(full)
        rec(6, "審核歷史：approved/withdrawn/rejected 三筆都查得到、資訊完整", ok6, "\n".join(d6))

        # ══════ Step 7：送審審核 ≠ 鎖定版（獨立）══════
        locked_after = db("SELECT is_approved FROM ie_stage WHERE id=?", (ha_sid,), one=True)["is_approved"]
        # 全庫檢查：任何 review 動作都沒改 is_approved 分佈（header1 事先鎖定，approve 後仍鎖定）
        d7 = [f"header1 版本 is_approved：審核前={locked_before} 審核通過後={locked_after}（應不變=1）"]
        # 反向：ie_review 的 approve 只碰 ie_review，不碰 ie_stage
        n_locked = db("SELECT COUNT(*) n FROM ie_stage WHERE header_id=? AND is_approved=1", (HA,), one=True)["n"]
        d7.append(f"header1 鎖定版數={n_locked}(仍=1)")
        ok7 = locked_before == 1 and locked_after == 1 and n_locked == 1
        rec(7, "送審通過後該版 is_approved 不變（送審審核 ≠ 鎖定版，兩者獨立）", ok7, "\n".join(d7))

        # ══════ Step 8：權限 ══════
        d8 = []; ok8 = True
        # data_entry(de1) 不能確認/駁回（manager-only）
        de_appr = int(de.evaluate("async(id)=>(await fetch(`/api/ie/review/${id}/approve`,{method:'POST'})).status", qC["id"]))
        de_rej = int(de.evaluate("async(id)=>(await fetch(`/api/ie/review/${id}/reject`,{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})).status", qC["id"]))
        de_hist = int(de.evaluate("async()=>(await fetch('/api/ie/review/history')).status"))
        d8.append(f"de1(data_entry) approve→{de_appr} reject→{de_rej} history→{de_hist} (皆應 403)")
        # manager(mg1) 不能送審（editor-only）
        mg_sub = int(mg.evaluate("async()=>(await fetch('/api/ie/review/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({header_id:4,stage_id:4})})).status"))
        mg_wd = int(mg.evaluate("async()=>(await fetch('/api/ie/review/withdraw',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({header_id:4})})).status"))
        d8.append(f"mg1(manager) submit→{mg_sub} withdraw→{mg_wd} (皆應 403)")
        # UI：de1 有送審佇列鈕嗎？(不應)；mg1 有？(應)
        de_has_queue = de.evaluate("()=>{const b=document.getElementById('btn-review-queue');return b?getComputedStyle(b).display!=='none':false;}")
        d8.append(f"de1 detail 顯示『審核佇列』鈕={de_has_queue}(應 False)")
        ok8 = de_appr == 403 and de_rej == 403 and de_hist == 403 and mg_sub == 403 and mg_wd == 403 and not de_has_queue
        # 確認越權沒有生效：header4 沒被 mg1 送出
        h4 = db("SELECT COUNT(*) n FROM ie_review WHERE header_id=4", one=True)["n"]
        if h4: ok8 = False; d8.append("  ✗ manager 越權送審竟生效")
        rec(8, "權限：data_entry不能審核、manager不能送審（越權 403 被擋）", ok8, "\n".join(d8))
        shot(de, "de_final")

        print("\n" + "=" * 66)
        print("送審審核 Workflow — 驗證總結")
        print("=" * 66)
        npass = sum(1 for _, _, ok in RESULTS if ok); nfail = sum(1 for _, _, ok in RESULTS if not ok)
        for s, t, ok in RESULTS: print(f"  [{s}] {'PASS' if ok else 'FAIL'} — {t}")
        print(f"\n  合計 {npass} PASS / {nfail} FAIL")
        print(f"  截圖: {SHOT}")
        ctx_de.close(); ctx_mg.close(); browser.close()
        return nfail

if __name__ == "__main__":
    sys.exit(1 if main() else 0)
