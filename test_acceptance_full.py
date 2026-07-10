# -*- coding: utf-8 -*-
"""
真實系統完整驗收測試（含送審 workflow）—— 對正在跑的正式系統 127.0.0.1:5000（正式 atlas.db）。
Jim 已授權可動正式資料。測試建鞋型 TEST-ACC-001 → ART → 工序 → 送審(通過/撤回/駁回) →
兩版本 + 鎖定/解鎖 → 設備種類/區塊總計/SUM_C2B → 刪 ART/鞋型 → 權限 → 編制表連動，
最後「完整清乾淨」，回報鞋型數不變、無殘留孤兒。headless=False（過程可見）。

前置：正式機已重啟載入新碼（送審 workflow 路由 + ie_review self-heal），jim/admin123。
"""
import sys, io, os, json, sqlite3, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5000"
DBP  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_backend", "data", "atlas.db")
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_backend", "test_output", "acc_full_shots")
os.makedirs(SHOT, exist_ok=True)
MODEL = "完整驗收"
ART1, ART2 = "TEST-ACC-001", "TEST-ACC-002"
DE_USER, DE_PW = "acc_de", "acc123"

RESULTS = []; findings = []
def rec(s, t, ok, d=""):
    RESULTS.append((s, t, ok))
    print(f"\n[{s}] {'✅ PASS' if ok else '❌ FAIL'} — {t}")
    for ln in d.splitlines():
        if ln.strip(): print("     " + ln)

def db(sql, p=(), one=False):
    c = sqlite3.connect(DBP, timeout=15); c.row_factory = sqlite3.Row
    try:
        c.execute("PRAGMA busy_timeout=15000")
        rows = [dict(r) for r in c.execute(sql, p).fetchall()]
        return (rows[0] if rows else None) if one else rows
    finally: c.close()
def dbexec(sql, p=()):
    c = sqlite3.connect(DBP, timeout=15)
    try: c.execute("PRAGMA busy_timeout=15000"); c.execute(sql, p); c.commit()
    finally: c.close()

_n = {"i": 0}
def shot(pg, name):
    _n["i"] += 1
    try: pg.screenshot(path=os.path.join(SHOT, f"{_n['i']:02d}_{name}.png"))
    except Exception as e: print("  (shot", e, ")")


def main():
    hid = None
    # 事先建 data_entry 帳號(權限測試用)，清理時刪除
    h = hashlib.sha256(DE_PW.encode()).hexdigest()
    dbexec("INSERT OR IGNORE INTO sys_users (username,display_name,role,password_hash,active,locked,created_at,updated_at) "
           "VALUES (?,?,?,?,1,0,datetime('now'),datetime('now'))", (DE_USER, "驗收編輯員", "data_entry", h))

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=300)
        ctx = browser.new_context(viewport={"width": 1600, "height": 950})
        page = ctx.new_page()
        alerts = []; dlg = {"prompt": None}
        def on_d(d):
            if d.type != "prompt": alerts.append(d.message)
            d.accept(dlg["prompt"] or "") if d.type == "prompt" else d.accept()
        page.on("dialog", on_d)
        api = ctx.request

        def login(pg, u, p):
            pg.goto(f"{BASE}/login", wait_until="domcontentloaded")
            pg.fill("#username", u); pg.fill("#password", p)
            pg.click("#btnLogin"); pg.wait_for_timeout(1400)
        def open_detail(hid_, wait_zones=True):
            page.goto(f"{BASE}/ie/{hid_}/detail", wait_until="domcontentloaded")
            if wait_zones:
                try: page.wait_for_function("()=>document.querySelectorAll('.zone-card').length>0", timeout=8000)
                except: pass
            page.wait_for_timeout(900)

        try:
            login(page, "jim", "admin123")

            # ═══ A1: 新增鞋型 ═══
            page.goto(f"{BASE}/ie", wait_until="domcontentloaded")
            page.wait_for_selector("#btn-new-model", state="visible", timeout=8000)
            shot(page, "A_ie_list_before")
            page.click("#btn-new-model")
            page.wait_for_selector("#modal-new-model", state="visible", timeout=4000)
            page.fill("#nm-name", MODEL); page.fill("#nm-art", ART1)
            page.select_option("#nm-eolr", "120"); page.fill("#nm-stage", "初版")
            shot(page, "A1_new_modal")
            page.click("#modal-new-model button:has-text('建立')")
            page.wait_for_timeout(2200)
            row = db("SELECT id, eolr FROM ob_header WHERE model_name=?", (MODEL,), one=True)
            ok1 = bool(row) and row["eolr"] == 120
            if row: hid = row["id"]
            arts = [a["art"] for a in db("SELECT art FROM ob_articles WHERE header_id=?", (hid,))] if hid else []
            rec("A1", "admin 新增鞋型 TEST-ACC-001 / 完整驗收 / EOLR=120",
                ok1 and ART1 in arts, f"header_id={hid} eolr={row['eolr'] if row else None} arts={arts}")
            if not hid: raise RuntimeError("A1 建立失敗，中止")

            # ═══ A2: 初版 stage ═══
            stages = api.get(f"{BASE}/api/ie/stages/{hid}").json().get("stages", [])
            init = next((s for s in stages if s["stage_name"] == "初版"), None)
            init_sid = init["id"] if init else None
            open_detail(hid); shot(page, "A2_initial_stage")
            rec("A2", "進新鞋型 → 有『初版』stage", init is not None, f"stages={[s['stage_name'] for s in stages]}")

            # ═══ A3: 加 ART ═══
            api.post(f"{BASE}/api/ie/add_art", data=json.dumps({"header_id": hid, "art": ART2}), headers={"Content-Type": "application/json"})
            arts2 = [a["art"] for a in db("SELECT art FROM ob_articles WHERE header_id=? ORDER BY id", (hid,))]
            open_detail(hid); shot(page, "A3_after_add_art")
            rec("A3", "加 ART TEST-ACC-002 → 成功、ART 出現", ART1 in arts2 and ART2 in arts2, f"arts={arts2}")

            # ═══ A4: 建工序 + 填值 + 存 + 重整 ═══
            add = api.post(f"{BASE}/api/ie/cell/add_row", data=json.dumps({"header_id": hid, "segment": "stitching",
                    "zone": "主流", "process_name": "驗收工序ACC", "standard_time": 120, "stage_id": init_sid, "user": "jim"}),
                    headers={"Content-Type": "application/json"}).json()
            pid = add.get("process_id")
            open_detail(hid); page.evaluate("()=>switchSeg('stitching')"); page.wait_for_timeout(1200)
            page.evaluate("""([pid])=>{const i=[...document.querySelectorAll('input.cut-act-inp')].find(x=>(x.getAttribute('onblur')||'').includes(`,${pid})`));if(i){i.value='6';i.dispatchEvent(new Event('blur'));}}""", [pid])
            page.wait_for_timeout(1200); shot(page, "A4_process_filled")
            open_detail(hid); page.evaluate("()=>switchSeg('stitching')"); page.wait_for_timeout(900)
            pr = db("SELECT standard_time, actual_operators, stage_id FROM ie_process WHERE id=?", (pid,), one=True)
            ok4 = pr and float(pr["standard_time"]) == 120 and str(pr["actual_operators"]) in ("6", "6.0") and pr["stage_id"] == init_sid
            shot(page, "A4_after_reload")
            rec("A4", "建工序、填標時120/實際6 → 存 → 重整值在（綁初版）", ok4, f"DB={pr}")

            # ═══ B5: 送審 → pending ═══
            open_detail(hid)
            sub_vis = page.evaluate("()=>{const b=document.getElementById('btn-submit-review');return b?getComputedStyle(b).display!=='none':false;}")
            el = page.query_selector("#btn-submit-review")
            if el and el.is_visible(): el.click()
            else: page.evaluate("()=>submitForReview()")
            page.wait_for_timeout(1500); shot(page, "B5_submitted")
            q5 = db("SELECT id, status, stage_name, submitted_by FROM ie_review WHERE header_id=? AND status='pending'", (hid,), one=True)
            rec("B5", "編輯員送審當前版本 → 待審 pending", bool(q5), f"送審鈕可見={sub_vis}; DB={q5}")

            # ═══ B6: 經理待審清單只顯示 pending ═══
            page.goto(f"{BASE}/ie/reviews", wait_until="domcontentloaded"); page.wait_for_timeout(1500)
            shot(page, "B6_queue")
            qapi = api.get(f"{BASE}/api/ie/review/queue").json().get("reviews", [])
            in_q = any(r["id"] == q5["id"] for r in qapi) if q5 else False
            allp = all(r["status"] == "pending" for r in qapi)
            rec("B6", "經理待審清單只顯示 pending → 該筆在", in_q and allp, f"佇列筆數={len(qapi)} 全pending={allp} 該筆在={in_q}")

            # ═══ B7: 確認通過 ═══
            appr_before = db("SELECT COALESCE(is_approved,0) a FROM ie_stage WHERE id=?", (init_sid,), one=True)["a"]
            page.evaluate("(id)=>approve(id)", q5["id"]); page.wait_for_timeout(1600); shot(page, "B7_approved")
            a7 = db("SELECT status, reviewed_by FROM ie_review WHERE id=?", (q5["id"],), one=True)
            in_q7 = any(r["id"] == q5["id"] for r in api.get(f"{BASE}/api/ie/review/queue").json().get("reviews", []))
            hist7 = api.get(f"{BASE}/api/ie/review/history").json().get("reviews", [])
            in_hist = any(r["id"] == q5["id"] and r["status"] == "approved" for r in hist7)
            rec("B7", "經理確認通過 → approved、離開待審、歷史有記錄", a7 and a7["status"] == "approved" and not in_q7 and in_hist, f"DB={a7} 仍在佇列={in_q7} 歷史有={in_hist}")

            # ═══ B8: 再送審 → 取消審核(withdraw) ═══
            open_detail(hid)
            el = page.query_selector("#btn-submit-review")
            if el and el.is_visible(): el.click()
            else: page.evaluate("()=>submitForReview()")
            page.wait_for_timeout(1400)
            q8 = db("SELECT id FROM ie_review WHERE header_id=? AND status='pending'", (hid,), one=True)
            open_detail(hid)
            wd = page.query_selector("#btn-withdraw-review")
            if wd and wd.is_visible(): wd.click()
            else: page.evaluate("()=>withdrawReview()")
            page.wait_for_timeout(1400); shot(page, "B8_withdrawn")
            b8 = db("SELECT status FROM ie_review WHERE id=?", (q8["id"],), one=True) if q8 else None
            in_q8 = any(r["id"] == (q8["id"] if q8 else -1) for r in api.get(f"{BASE}/api/ie/review/queue").json().get("reviews", []))
            rec("B8", "再送審 → 取消審核 → withdrawn、離開清單", b8 and b8["status"] == "withdrawn" and not in_q8, f"DB={b8} 仍在佇列={in_q8}")

            # ═══ B9: 再送審 → 駁回+原因 ═══
            open_detail(hid)
            el = page.query_selector("#btn-submit-review")
            if el and el.is_visible(): el.click()
            else: page.evaluate("()=>submitForReview()")
            page.wait_for_timeout(1400)
            q9 = db("SELECT id FROM ie_review WHERE header_id=? AND status='pending'", (hid,), one=True)
            page.goto(f"{BASE}/ie/reviews", wait_until="domcontentloaded"); page.wait_for_timeout(1400)
            REASON = "標時需修正"
            dlg["prompt"] = REASON
            page.evaluate("(id)=>reject(id)", q9["id"]); page.wait_for_timeout(1500); shot(page, "B9_rejected")
            c9 = db("SELECT status, reject_reason FROM ie_review WHERE id=?", (q9["id"],), one=True)
            open_detail(hid)
            badge9 = page.evaluate("()=>{const b=document.getElementById('review-status-badge');return b&&getComputedStyle(b).display!=='none'?b.textContent:'';}")
            shot(page, "B9_editor_sees_reason")
            rec("B9", "再送審 → 駁回+原因 → rejected、原因記錄、編輯員看得到", c9 and c9["status"] == "rejected" and c9["reject_reason"] == REASON and REASON in (badge9 or ""), f"DB={c9} badge={badge9!r}")

            # ═══ B10: 審核歷史三筆齊全 ═══
            page.goto(f"{BASE}/ie/reviews", wait_until="domcontentloaded"); page.wait_for_timeout(1200)
            page.evaluate("()=>showTab('hist')"); page.wait_for_timeout(600); shot(page, "B10_history")
            hist = api.get(f"{BASE}/api/ie/review/history").json().get("reviews", [])
            byid = {r["id"]: r for r in hist}
            got = {byid.get(i, {}).get("status") for i in (q5["id"], q8["id"], q9["id"])}
            full = (byid.get(q5["id"], {}).get("reviewed_by") and byid.get(q9["id"], {}).get("reject_reason")
                    and all(byid.get(i, {}).get("submitted_by") and byid.get(i, {}).get("stage_name") for i in (q5["id"], q8["id"], q9["id"])))
            rec("B10", "審核歷史：approved/withdrawn/rejected 三筆齊全、資訊完整",
                got == {"approved", "withdrawn", "rejected"} and bool(full),
                f"三筆狀態={got} 資訊完整={bool(full)}")

            # ═══ B11: 送審審核 ≠ 鎖定版 ═══
            appr_after = db("SELECT COALESCE(is_approved,0) a FROM ie_stage WHERE id=?", (init_sid,), one=True)["a"]
            rec("B11", "送審通過後該版 is_approved 不變（送審 ≠ 鎖定版，獨立）",
                appr_before == appr_after, f"初版 is_approved：送審審核前={appr_before} 後={appr_after}（應相等）")

            # ═══ C12: 另存第二版 驗收v2 ═══
            open_detail(hid); dlg["prompt"] = "驗收v2"
            page.evaluate("()=>newStage()"); page.wait_for_timeout(2000)
            stg = db("SELECT id, stage_name, COALESCE(is_approved,0) a FROM ie_stage WHERE header_id=? ORDER BY id", (hid,))
            v2 = next((s for s in stg if s["stage_name"] == "驗收v2"), None)
            v2_sid = v2["id"] if v2 else None
            shot(page, "C12_v2")
            rec("C12", "另存第二版 驗收v2 → 初版 + 驗收v2 兩版", v2 is not None and len(stg) == 2, f"stages={[(s['stage_name'],s['a']) for s in stg]}")

            # ═══ C13: 設 v2 鎖定版 ═══
            open_detail(hid); page.select_option("#stageSelect", str(v2_sid)); page.wait_for_timeout(1400)
            b = page.query_selector("#btn-approve-stage")
            if b and b.is_visible(): b.click()
            else: page.evaluate("()=>approveCurrentStage()")
            page.wait_for_timeout(1800); shot(page, "C13_locked")
            v2a = db("SELECT COALESCE(is_approved,0) a FROM ie_stage WHERE id=?", (v2_sid,), one=True)["a"]
            ui13 = page.evaluate("()=>({badge:(()=>{const x=document.getElementById('lock-badge');return x?getComputedStyle(x).display!=='none':false;})(),save:document.getElementById('btnSaveAll')?.disabled})")
            n_lock = db("SELECT COUNT(*) n FROM ie_stage WHERE header_id=? AND is_approved=1", (hid,), one=True)["n"]
            rec("C13", "設 驗收v2 鎖定版 → is_approved=1、徽章、儲存disable", v2a == 1 and n_lock == 1 and ui13["badge"] and ui13["save"], f"is_approved={v2a} 鎖定數={n_lock} badge={ui13['badge']} saveDisabled={ui13['save']}")

            # ═══ C14: 鎖定版試改 → 被擋 ═══
            page.evaluate("()=>switchSeg('stitching')"); page.wait_for_timeout(1100)
            vrow = db("SELECT id, actual_operators FROM ie_process WHERE header_id=? AND stage_id=? AND segment='stitching' AND zone='主流' ORDER BY seq LIMIT 1", (hid, v2_sid), one=True)
            before14 = vrow["actual_operators"] if vrow else None
            alerts.clear()
            if vrow:
                page.evaluate("""([pid])=>{const i=[...document.querySelectorAll('input.cut-act-inp')].find(x=>(x.getAttribute('onblur')||'').includes(`,${pid})`));if(i){i.value='99';i.dispatchEvent(new Event('blur'));}}""", [vrow["id"]])
                page.wait_for_timeout(1200)
            after14 = db("SELECT actual_operators FROM ie_process WHERE id=?", (vrow["id"],), one=True)["actual_operators"] if vrow else None
            shot(page, "C14_locked_blocked")
            rec("C14", "鎖定版試改按儲存 → 被擋、只能另存", str(after14) == str(before14) and any("鎖定版" in a for a in alerts), f"DB {before14}→{after14} alert={alerts[:1]}")

            # ═══ D15: 解鎖 → 可編輯 ═══
            b = page.query_selector("#btn-unlock-stage")
            if b and b.is_visible(): b.click()
            else: page.evaluate("()=>unlockStage()")
            page.wait_for_timeout(1700)
            v2a2 = db("SELECT COALESCE(is_approved,0) a FROM ie_stage WHERE id=?", (v2_sid,), one=True)["a"]
            page.evaluate("()=>switchSeg('stitching')"); page.wait_for_timeout(1000)
            if vrow:
                page.evaluate("""([pid])=>{const i=[...document.querySelectorAll('input.cut-act-inp')].find(x=>(x.getAttribute('onblur')||'').includes(`,${pid})`));if(i){i.value='8';i.dispatchEvent(new Event('blur'));}}""", [vrow["id"]])
                page.wait_for_timeout(1300)
            after15 = db("SELECT actual_operators FROM ie_process WHERE id=?", (vrow["id"],), one=True)["actual_operators"] if vrow else None
            shot(page, "D15_unlocked_edit")
            rec("D15", "解鎖 驗收v2 → is_approved=0 → 改工序存成功", v2a2 == 0 and str(after15) in ("8", "8.0"), f"is_approved={v2a2} 改後DB={after15}")

            # ═══ E16: 設備種類下拉 ═══
            eq = page.evaluate("""([pid])=>{const want=`saveSingleField(this,${pid},'equipment_type')`;const s=[...document.querySelectorAll('select.cell-inp')].find(x=>(x.getAttribute('onchange')||'')===want);if(!s)return null;return {opts:[...s.options].map(o=>o.text)};}""", [vrow["id"]]) if vrow else None
            picked = False
            if eq and "單針針車機" in eq["opts"]:
                picked = page.evaluate("""([pid,v])=>{const want=`saveSingleField(this,${pid},'equipment_type')`;const s=[...document.querySelectorAll('select.cell-inp')].find(x=>(x.getAttribute('onchange')||'')===want);if(!s)return false;s.value=v;s.dispatchEvent(new Event('change'));return true;}""", [vrow["id"], "單針針車機"])
                page.wait_for_timeout(1000)
            shot(page, "E16_equipment")
            open_detail(hid); page.evaluate("()=>switchSeg('stitching')"); page.wait_for_timeout(900)
            eqdb = db("SELECT equipment_type FROM ie_process WHERE id=?", (vrow["id"],), one=True)["equipment_type"] if vrow else None
            ok16 = eq and "單針針車機" in eq["opts"] and "雙針針車機" in eq["opts"] and picked and eqdb == "單針針車機"
            rec("E16", "設備種類下拉有兩選項→選一個存→重整值在", ok16, f"選項={eq['opts'] if eq else None} 重整後DB={eqdb!r}")

            # ═══ E17: 區塊總計 ═══
            tot = page.evaluate("""()=>{const tr=[...document.querySelectorAll('.zone-total-row')].find(r=>r.dataset.totalSeg==='stitching'&&r.dataset.totalZone==='主流');if(!tr)return null;return {std:tr.querySelector('.zt-std')?.textContent,th:tr.querySelector('.zt-theory')?.textContent,ac:tr.querySelector('.zt-actual')?.textContent,inputs:tr.querySelectorAll('input').length};}""")
            # oracle：主流 std/actual 加總（此鞋型只有 1 列 std=120 actual=8）
            prows = db("SELECT standard_time, actual_operators FROM ie_process WHERE header_id=? AND stage_id=? AND segment='stitching' AND zone='主流' AND (flag IS NULL OR flag!='deleted')", (hid, v2_sid))
            exp_std = sum(float(r["standard_time"] or 0) for r in prows)
            exp_ac = sum(float(r["actual_operators"] or 0) for r in prows)
            ok17 = tot and abs(float(tot["std"] or 0) - round(exp_std, 1)) < 0.2 and abs(float(tot["ac"] or 0) - round(exp_ac, 1)) < 0.2 and tot["inputs"] == 0
            shot(page, "E17_zone_total")
            rec("E17", "各區塊最下有『總計』列、加總正確且唯讀", ok17, f"UI總計={tot} oracle std={round(exp_std,1)} ac={round(exp_ac,1)}")

            # ═══ E18: SUM_C2B ═══
            page.evaluate("()=>switchSeg('sum_c2b')")
            try: page.wait_for_function("()=>{const b=document.getElementById('sumC2bBody');return b&&!b.innerText.includes('載入中');}", timeout=8000)
            except: pass
            page.wait_for_timeout(500); shot(page, "E18_sumc2b")
            sc = page.evaluate("""()=>{const rows=[...document.querySelectorAll('#sumC2bBody tr')];const sub=rows.filter(r=>r.className==='sumc2b-sub'||r.className==='sumc2b-grand');const anyNum=sub.some(r=>{const t=r.children[1]?.innerText.trim();return t&&t!=='—'&&t!=='0'&&!isNaN(parseFloat(t));});const epphAllDash=sub.every(r=>r.children[3]?.innerText.trim()==='—');const inputs=document.querySelectorAll('#sumC2bBody input,#sumC2bBody select').length;const nan=rows.some(r=>r.innerText.includes('NaN'));return {subRows:sub.length,anyNum,epphAllDash,inputs,nan};}""")
            ok18 = sc and sc["subRows"] >= 4 and sc["anyNum"] and sc["epphAllDash"] and sc["inputs"] == 0 and not sc["nan"]
            rec("E18", "SUM_C2B：MP/PPH 有數字、E-PPH 顯示—、唯讀、不NaN", ok18, f"{sc}")

            # ═══ F19: 刪 ART ═══
            hcount_b = db("SELECT COUNT(*) n FROM ob_header", one=True)["n"]
            api.post(f"{BASE}/api/ie/remove_art", data=json.dumps({"art": ART2, "header_id": hid}), headers={"Content-Type": "application/json"})
            arts19 = [a["art"] for a in db("SELECT art FROM ob_articles WHERE header_id=?", (hid,))]
            hcount_a = db("SELECT COUNT(*) n FROM ob_header", one=True)["n"]
            open_detail(hid); shot(page, "F19_after_remove_art")
            rec("F19", "刪 TEST-ACC-002 → 消失、別的不受影響", ART2 not in arts19 and ART1 in arts19 and hcount_a == hcount_b, f"arts={arts19} header數 {hcount_b}→{hcount_a}")

            # ═══ H23: 編制表連動（沒鎖定版→紅底）— 刪鞋型前先驗證 ═══
            page.goto(f"{BASE}/bianche", wait_until="domcontentloaded"); page.wait_for_timeout(2500)
            shot(page, "H23_bianche")
            nolock = page.evaluate("()=>{const b=[...document.querySelectorAll('.badge-noie')].filter(e=>e.textContent.includes('未鎖定'));return {redBadges:b.length, sample:b[0]?b[0].closest('tr')?.innerText.slice(0,60):null};}")
            # 佐證：bianzhi API 有 has_locked=false 的 art
            bz = api.get(f"{BASE}/api/bianzhi/detail").json()
            rowsbz = bz.get("rows", []) if isinstance(bz, dict) else []
            has_false = any(r.get("has_locked") is False for r in rowsbz)
            ok23 = nolock["redBadges"] > 0 or has_false
            rec("H23", "編制表：沒鎖定版的鞋型 → MP 空 + 紅底『未鎖定』", ok23, f"紅底未鎖定徽章數={nolock['redBadges']} 例={nolock['sample']!r}; API has_locked=false 存在={has_false}")

            # ═══ F20: 刪整個測試鞋型 + 孤兒檢查 ═══
            dele = api.post(f"{BASE}/api/ie/{hid}/delete").json()
            hgone = db("SELECT id FROM ob_header WHERE id=?", (hid,), one=True) is None
            proc_left = db("SELECT COUNT(*) n FROM ie_process WHERE header_id=?", (hid,), one=True)["n"]
            stage_orphan = db("SELECT COUNT(*) n FROM ie_stage WHERE header_id=?", (hid,), one=True)["n"]
            rev_orphan = db("SELECT COUNT(*) n FROM ie_review WHERE header_id=?", (hid,), one=True)["n"]
            page.goto(f"{BASE}/ie", wait_until="domcontentloaded"); page.wait_for_timeout(1500); shot(page, "F20_after_delete")
            ok20 = hgone and proc_left == 0
            if stage_orphan or rev_orphan:
                findings.append(f"delete_ie_header 未清 ie_stage({stage_orphan})/ie_review({rev_orphan})/ie_process_group/ie_edit_log/lock_history → 刪鞋型留孤兒（真實環境問題，本測試清理時手動補清）")
            rec("F20", "刪整個測試鞋型 → 從清單消失、ie_process 清乾淨", ok20, f"delete={dele} header消失={hgone} ie_process剩={proc_left} 孤兒 stage={stage_orphan} review={rev_orphan}")

            # ═══ G21: data_entry 權限 ═══
            ctx2 = browser.new_context(); p2 = ctx2.new_page(); p2.on("dialog", lambda d: d.accept())
            login(p2, DE_USER, DE_PW)
            p2.goto(f"{BASE}/ie", wait_until="domcontentloaded"); p2.wait_for_timeout(1400)
            de_newbtn = p2.evaluate("()=>{const b=document.getElementById('btn-new-model');return b?getComputedStyle(b).display!=='none':false;}")
            a2 = ctx2.request
            de_create = a2.post(f"{BASE}/api/ie/create_record", data=json.dumps({"art": "TEST-ACC-DENY", "model_name": "DENYX", "eolr": 120}), headers={"Content-Type": "application/json"}).status
            # 用不存在的 id 探測（權限層應先擋 403；即便沒擋也只打到不存在的列，零副作用）
            de_appr = a2.post(f"{BASE}/api/ie/review/999999/approve").status
            de_lock = a2.post(f"{BASE}/api/ie/stages/999999/999999/approve", data="{}", headers={"Content-Type": "application/json"}).status
            de_del = a2.post(f"{BASE}/api/ie/999999/delete").status
            shot(p2, "G21_data_entry")
            ok21 = (not de_newbtn) and de_create == 403 and de_appr == 403 and de_lock == 403 and de_del == 403
            denyx = db("SELECT COUNT(*) n FROM ob_header WHERE model_name='DENYX'", one=True)["n"]
            if denyx: ok21 = False
            rec("G21", "data_entry 不能新增鞋型/確認駁回/設鎖定版/刪除（越權403）", ok21,
                f"新增鈕={de_newbtn} create={de_create} approve={de_appr} setLock={de_lock} delete={de_del}")
            ctx2.close()

            # ═══ G22: read_only 只看鎖定版、全唯讀 ═══
            ctx3 = browser.new_context(); p3 = ctx3.new_page(); p3.on("dialog", lambda d: d.accept())
            login(p3, "tongcai", "x")  # locked read_only 免密碼
            a3 = ctx3.request
            me3 = a3.get(f"{BASE}/api/me").json()
            # 找一個有鎖定版的 header 看（read_only 只看鎖定版）
            locked_hdr = db("SELECT header_id FROM ie_stage WHERE is_approved=1 LIMIT 1", one=True)
            ro_can_create = a3.post(f"{BASE}/api/ie/create_record", data=json.dumps({"art": "X", "model_name": "Y", "eolr": 120}), headers={"Content-Type": "application/json"}).status
            ro_locked_only = None; ro_inputs = None
            if locked_hdr:
                p3.goto(f"{BASE}/ie/{locked_hdr['header_id']}/detail", wait_until="domcontentloaded"); p3.wait_for_timeout(2000)
                st = a3.get(f"{BASE}/api/ie/stages/{locked_hdr['header_id']}").json().get("stages", [])
                ro_locked_only = all(s.get("is_approved") == 1 for s in st) and len(st) >= 1
                ro_inputs = p3.evaluate("()=>document.querySelectorAll('#mainContent input:not([disabled]), #mainContent select:not([disabled])').length")
            shot(p3, "G22_read_only")
            ok22 = (me3.get("user", {}).get("role") == "read_only") and ro_can_create == 403 and (ro_locked_only is not False) and (ro_inputs in (0, None))
            rec("G22", "read_only 只看鎖定版、全唯讀（不能新增）", ok22,
                f"role={me3.get('user',{}).get('role')} create={ro_can_create} 只回鎖定版={ro_locked_only} 可編輯輸入框={ro_inputs}")
            ctx3.close()

        finally:
            # ═══ 清理：purge 所有測試 header + 孤兒 + data_entry 帳號 ═══
            print("\n" + "=" * 70 + "\n清理 TEST-ACC 殘留\n" + "=" * 70)
            test_hids = set()
            if hid: test_hids.add(hid)
            for r in db("SELECT id FROM ob_header WHERE model_name IN (?, 'DENYX', 'Y')", (MODEL,)): test_hids.add(r["id"])
            for r in db("SELECT DISTINCT header_id FROM ob_articles WHERE art LIKE 'TEST-ACC%'"): test_hids.add(r["header_id"])
            print("purge headers:", sorted(test_hids))
            for th in test_hids:
                sids = [r["id"] for r in db("SELECT id FROM ie_stage WHERE header_id=?", (th,))]
                pids = [r["id"] for r in db("SELECT id FROM ie_process WHERE header_id=?", (th,))]
                if sids: dbexec(f"DELETE FROM ie_edit_log WHERE stage_id IN ({','.join('?'*len(sids))})", tuple(sids))
                if pids: dbexec(f"DELETE FROM ie_edit_log WHERE process_id IN ({','.join('?'*len(pids))})", tuple(pids))
                for tbl in ["ie_process", "ie_process_group", "ie_stage", "lock_history", "ie_review", "ie_assignments", "ob_articles", "ob_epph", "ob_rows", "ob_header"]:
                    col = "id" if tbl == "ob_header" else "header_id"
                    try: dbexec(f"DELETE FROM {tbl} WHERE {col}=?", (th,))
                    except Exception as e: print("  clean err", tbl, e)
            # 刪 data_entry 測試帳號
            dbexec("DELETE FROM sys_users WHERE username=?", (DE_USER,))
            left_art = db("SELECT COUNT(*) n FROM ob_articles WHERE art LIKE 'TEST-ACC%'", one=True)["n"]
            left_hdr = db("SELECT COUNT(*) n FROM ob_header WHERE model_name IN (?, 'DENYX', 'Y')", (MODEL,), one=True)["n"]
            left_usr = db("SELECT COUNT(*) n FROM sys_users WHERE username=?", (DE_USER,), one=True)["n"]

            base = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_backend", "test_output", "acc_full_baseline.json")))
            now = {"models": db("SELECT COUNT(DISTINCT model_name) n FROM ob_header", one=True)["n"],
                   "headers": db("SELECT COUNT(*) n FROM ob_header", one=True)["n"],
                   "articles": db("SELECT COUNT(*) n FROM ob_articles", one=True)["n"],
                   "stages": db("SELECT COUNT(*) n FROM ie_stage", one=True)["n"],
                   "ie_process": db("SELECT COUNT(*) n FROM ie_process", one=True)["n"],
                   "users": db("SELECT COUNT(*) n FROM sys_users", one=True)["n"]}
            orphan_stage = db("SELECT COUNT(*) n FROM ie_stage WHERE header_id NOT IN (SELECT id FROM ob_header)", one=True)["n"]
            orphan_proc = db("SELECT COUNT(*) n FROM ie_process WHERE header_id NOT IN (SELECT id FROM ob_header)", one=True)["n"]
            clean_ok = (now["models"] == base["models"] and now["headers"] == base["headers"] and now["articles"] == base["articles"]
                        and now["stages"] == base["stages"] and now["ie_process"] == base["ie_process"] and now["users"] == base["users"]
                        and left_art == 0 and left_hdr == 0 and left_usr == 0 and orphan_proc == 0)
            print("BASELINE:", base); print("NOW     :", now)
            print(f"leftover art={left_art} header={left_hdr} de_user={left_usr}; 孤兒 stage(全庫)={orphan_stage} process={orphan_proc}")
            rec("清理", "清理後正式 DB 乾淨（鞋型數不變、無 TEST-ACC 殘留、無孤兒）", clean_ok,
                f"baseline={base}\nnow={now}\nleftover art={left_art} hdr={left_hdr} user={left_usr} 孤兒proc={orphan_proc}")
            try: page.goto(f"{BASE}/ie", wait_until="domcontentloaded"); page.wait_for_timeout(1000); shot(page, "final_ie_list")
            except: pass
            print("\n" + "=" * 70 + "\n完整驗收總結\n" + "=" * 70)
            npass = sum(1 for _, _, ok in RESULTS if ok); nfail = sum(1 for _, _, ok in RESULTS if not ok)
            for s, t, ok in RESULTS: print(f"  [{s}] {'PASS' if ok else 'FAIL'} — {t}")
            print(f"\n  合計 {npass} PASS / {nfail} FAIL")
            if findings:
                print("\n  ⚠️ 真實環境發現（隔離測試沒抓到）:")
                for f in findings: print("   - " + f)
            print(f"\n  截圖: {SHOT}")
            browser.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
