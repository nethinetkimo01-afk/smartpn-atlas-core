# -*- coding: utf-8 -*-
"""
驗證：插入功能 + 磨皮欄，在「版本控制（分版/鎖定）」完成後是否仍正常運作。

環境（隔離、絕不碰正式資料）：
  - 隔離 DB : flask_backend/data/test_isolated/atlas_test.db  (atlas.db 的副本)
  - 隔離 SERVER: python flask_backend/serve_test_isolated.py  → http://127.0.0.1:5099
  - 測試鞋型 : header_id=35 (LA TRAINER) — cutting(裁斷機 typeA + ATOM/EMMA typeB) + stitching

用法：先啟動隔離 server，再  py test_insert_polish_verify.py

只測不改。所有寫入都落在隔離 DB。
"""
import sys, io, os, sqlite3, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE   = "http://127.0.0.1:5099"
HID    = 35
EOLR   = 120           # header 35 eolr → divisor = 3600/120 = 30 ; theory = std/30
DIVISOR = 3600 / EOLR
DBPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "flask_backend", "data", "test_isolated", "atlas_test.db")
SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "flask_backend", "test_output", "verify_shots")
os.makedirs(SHOT_DIR, exist_ok=True)
RUN = time.strftime("%H%M%S")   # run tag → unique process names, safe re-runs

RESULTS = []   # (idx, title, status, detail)
def record(idx, title, status, detail=""):
    RESULTS.append((idx, title, status, detail))
    mark = {"PASS":"✅ PASS","FAIL":"❌ FAIL","INFO":"ℹ️  INFO","WARN":"⚠️  WARN"}[status]
    print(f"\n[{idx}] {mark} — {title}")
    if detail:
        for line in detail.splitlines():
            print("     " + line)

def db(sql, params=(), one=False):
    c = sqlite3.connect(DBPATH); c.row_factory = sqlite3.Row
    try:
        cur = c.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        return (rows[0] if rows else None) if one else rows
    finally:
        c.close()

def shot(page, name):
    p = os.path.join(SHOT_DIR, f"{name}.png")
    try: page.screenshot(path=p, full_page=False)
    except Exception as e: print("  (screenshot fail:", e, ")")
    return p


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width":1600,"height":1000})
        page = ctx.new_page()
        # 攔 dialog（newStage 用 prompt / 各種 alert）——依情境動態設定
        dialog_state = {"accept_text": None, "last": None}
        def on_dialog(d):
            dialog_state["last"] = d.message
            if d.type == "prompt":
                d.accept(dialog_state["accept_text"] or "")
            else:
                d.accept()
        page.on("dialog", on_dialog)

        # ---- 登入 jim/admin123 (admin) ----
        page.goto(f"{BASE}/login", wait_until="domcontentloaded")
        page.fill("#username", "jim")
        page.fill("#password", "admin123")
        page.click("#btnLogin")
        page.wait_for_timeout(1500)  # doLogin fetch → redirect /ie

        # 當前(唯一)版本 = 一般版
        gen_stage = db("SELECT id, stage_name, is_approved FROM ie_stage WHERE header_id=? "
                       "ORDER BY id LIMIT 1", (HID,), one=True)
        print(f"起始一般版 stage: {gen_stage}")

        def open_detail():
            page.goto(f"{BASE}/ie/{HID}/detail", wait_until="domcontentloaded")
            page.wait_for_function("()=>document.querySelectorAll('.zone-card').length>0", timeout=8000)
            page.wait_for_timeout(800)  # init() + loadSegment('cutting') settle

        # =====================================================================
        # 【插入功能】
        # =====================================================================
        open_detail()
        shot(page, "00_cutting_loaded")

        # 選一個 裁斷機 anchor 列（一般版、當前 seq 排序第一筆非刪除）
        anchor = db("SELECT id, seq, process_name FROM ie_process "
                    "WHERE header_id=? AND segment='cutting' AND zone='裁斷機' "
                    "AND (flag IS NULL OR flag!='deleted') AND stage_id=? "
                    "ORDER BY seq LIMIT 1", (HID, gen_stage["id"]), one=True)
        after_seq = anchor["seq"]
        # 記錄 anchor 之後「原本」的下一列（用來確認被往下推）
        next_before = db("SELECT id, seq, process_name FROM ie_process "
                         "WHERE header_id=? AND segment='cutting' AND zone='裁斷機' "
                         "AND (flag IS NULL OR flag!='deleted') AND stage_id=? AND seq>? "
                         "ORDER BY seq LIMIT 1", (HID, gen_stage["id"], after_seq), one=True)

        # ---- Check 1: 一般版 裁斷機 插入 ----
        ins_name = f"插入測試A_{RUN}"
        # 點該 anchor 列的「插」鈕：用 evaluate 直接呼叫 insertRowAfter(pid) 確保命中正確列
        page.evaluate("(pid)=>insertRowAfter(pid)", anchor["id"])
        page.wait_for_selector("#addRowModal", state="visible", timeout=4000)
        page.fill("#addProcessName", ins_name)
        page.fill("#addTCT", "40")
        shot(page, "01_insert_modal")
        # 直接攔插入 API 回應，確認真的送出且成功（避免時序誤判）
        insert_api = {"status": None, "body": None}
        with page.expect_response("**/api/ie/cell/insert_row", timeout=8000) as rinfo:
            page.click("button.btn-mok:has-text('新增')")
        try:
            resp = rinfo.value
            insert_api["status"] = resp.status
            insert_api["body"] = resp.json()
        except Exception as e:
            insert_api["body"] = f"(response capture err: {e})"
        page.wait_for_timeout(1500)  # submitAddRow → loadSegment reload
        page.wait_for_function("()=>document.querySelectorAll('.zone-card').length>0", timeout=8000)
        print(f"  insert_row API: HTTP {insert_api['status']} → {insert_api['body']}")

        new_row = db("SELECT id, seq, zone, segment, stage_id, flag, process_name, tct "
                     "FROM ie_process WHERE header_id=? AND process_name=?",
                     (HID, ins_name), one=True)
        next_after = db("SELECT id, seq FROM ie_process WHERE id=?",
                        (next_before["id"],), one=True) if next_before else None
        d1 = []
        ok1 = True
        d1.append(f"insert_row API: HTTP {insert_api['status']} → {insert_api['body']}")
        if not new_row:
            ok1 = False; d1.append("新工序未寫入 DB")
        else:
            d1.append(f"新工序 id={new_row['id']} seq={new_row['seq']} zone={new_row['zone']} "
                      f"segment={new_row['segment']} stage_id={new_row['stage_id']} flag={new_row['flag']}")
            d1.append(f"anchor seq={after_seq} → 期望新列 seq={after_seq+1} ; 實際={new_row['seq']}")
            if new_row["seq"] != after_seq + 1: ok1 = False; d1.append("  ✗ seq 不等於 anchor+1")
            if new_row["zone"] != "裁斷機":      ok1 = False; d1.append("  ✗ zone 不正確")
            if new_row["segment"] != "cutting":  ok1 = False; d1.append("  ✗ segment 不正確")
            if new_row["stage_id"] != gen_stage["id"]: ok1 = False; d1.append("  ✗ 未綁到當前一般版")
            if next_before:
                d1.append(f"anchor 後原本列 id={next_before['id']} seq {next_before['seq']} → {next_after['seq']}"
                          + (" (已下推)" if next_after and next_after['seq']==next_before['seq']+1 else " (未正確下推)"))
                if not (next_after and next_after['seq']==next_before['seq']+1):
                    ok1 = False; d1.append("  ✗ 後列未被往下推")
            # UI 確認：新列出現在 anchor 下方（DOM 相鄰順序）
            order = page.evaluate(
                """(nm)=>{const t=document.getElementById('tbody-cut-裁斷機');
                    if(!t)return null;const names=[...t.querySelectorAll('tr td.name')].map(td=>td.innerText.trim());
                    return names;}""", ins_name)
            in_dom = order is not None and any(ins_name in (n or "") for n in order)
            d1.append(f"UI DOM 裁斷機列中含新工序: {in_dom}")
            if not in_dom: ok1 = False; d1.append("  ✗ 新列未出現在畫面")
        shot(page, "01_after_insert")
        record(1, "一般版 裁斷機『插』→下方插入、seq/順序/zone 正確", "PASS" if ok1 else "FAIL", "\n".join(d1))

        # ---- Check 2: 插入列填值→存→重整→值還在 ----
        d2 = []; ok2 = True
        if new_row:
            val_act = "3"
            # 填「裁機要求人數」(actual_operators) —— 此欄 onblur 走 saveSingleActual 即時存
            filled = page.evaluate(
                """([pid,v])=>{const inp=document.querySelector(`input.cut-act-inp[data-pid="${pid}"]`);
                     if(!inp)return false; inp.value=v; inp.dispatchEvent(new Event('blur')); return true;}""",
                [new_row["id"], val_act])
            page.wait_for_timeout(800)
            d2.append(f"填 actual_operators={val_act} via UI input(blur, 即時存): dom命中={filled}")
            # 也用 儲存流程存一個非即時欄位 (tct 已在插入時帶入; 這裡改 layers_per_cut 經 EDITS+儲存)
            page.evaluate(
                """([pid])=>{const inp=document.querySelector(`input.cell-inp[data-cfield="layers_per_cut"]`);}""",
                [new_row["id"]])
            # 直接針對此列的 layers_per_cut 欄位填值並觸發 commitEditStatic，再按儲存
            filled2 = page.evaluate(
                """([pid])=>{const rows=document.querySelectorAll('#tbody-cut-裁斷機 tr');
                    for(const tr of rows){const del=tr.querySelector('button.btn-ins');
                      if(del && del.getAttribute('onclick')===`insertRowAfter(${pid})`){
                        const inp=tr.querySelector('input.cell-inp[data-cfield="layers_per_cut"]');
                        if(inp){inp.value='2'; inp.dispatchEvent(new Event('input'));
                                inp.dispatchEvent(new Event('blur')); return true;}}}
                    return false;}""", [new_row["id"]])
            page.wait_for_timeout(300)
            # 按「儲存」(saveSilent) 落地 EDITS
            page.evaluate("()=>saveSilent()")
            page.wait_for_timeout(900)
            d2.append(f"填 layers_per_cut=2 via EDITS+儲存: dom命中={filled2}")
            # 重整
            open_detail()
            page.wait_for_timeout(400)
            persisted = db("SELECT actual_operators, layers_per_cut, tct FROM ie_process WHERE id=?",
                           (new_row["id"],), one=True)
            d2.append(f"重整後 DB: actual_operators={persisted['actual_operators']} "
                      f"layers_per_cut={persisted['layers_per_cut']} tct={persisted['tct']}")
            if str(persisted["actual_operators"]) not in (val_act, "3.0"): ok2 = False; d2.append("  ✗ actual_operators 未持久化")
            if str(persisted["layers_per_cut"]) not in ("2","2.0"): ok2 = False; d2.append("  ✗ layers_per_cut 未持久化")
            # UI 也要看得到
            ui_act = page.evaluate(
                """([pid])=>{const inp=document.querySelector(`input.cut-act-inp[data-pid="${pid}"]`);
                     return inp?inp.value:null;}""", [new_row["id"]])
            d2.append(f"重整後 UI actual_operators 顯示={ui_act}")
            if not ui_act: ok2 = False; d2.append("  ✗ UI 未顯示已存值")
        else:
            ok2 = False; d2.append("(略) 因 Check1 未建立列")
        shot(page, "02_after_reload_persist")
        record(2, "插入列填值→存→重整 值不消失（即時存）", "PASS" if ok2 else "FAIL", "\n".join(d2))

        # =====================================================================
        # 【磨皮欄】 (先在一般版做，之後另存/鎖定會用到)
        # =====================================================================
        # ---- Check 5: 裁斷機(typeA) 有磨皮欄 ----
        d5 = []; ok5 = True
        head_txt = page.evaluate(
            """()=>{const card=[...document.querySelectorAll('.zone-card')]
                 .find(c=>c.querySelector('.zone-name') && c.querySelector('.zone-name').innerText.includes('裁斷機'));
                 return card? card.querySelector('table thead').innerText : null;}""")
        if head_txt and "磨皮" in head_txt:
            d5.append("裁斷機表頭含後製欄「磨皮」✓")
        else:
            ok5 = False; d5.append(f"裁斷機表頭未見「磨皮」: {repr(head_txt)[:200]}")
        # 磨皮 = 第6個後製 (印线/画线,削皮,贴补强,涂边/烘毛边,热压,磨皮)
        post_groups = page.evaluate(
            """()=>{const card=[...document.querySelectorAll('.zone-card')]
                 .find(c=>c.querySelector('.zone-name') && c.querySelector('.zone-name').innerText.includes('裁斷機'));
                 if(!card)return null; return [...card.querySelectorAll('thead th.th-post-group')].map(t=>t.innerText.trim());}""")
        d5.append(f"裁斷機 後製群組: {post_groups}")
        if not (post_groups and len(post_groups)==6 and post_groups[-1]=="磨皮"):
            ok5 = False; d5.append("  ✗ 後製群組不是 6 個且末位為磨皮")
        shot(page, "05_typeA_polish_column")
        record(5, "裁斷機(typeA) 有「磨皮」欄（標時+理論人數，第6後製）", "PASS" if ok5 else "FAIL", "\n".join(d5))

        # ---- Check 6: 磨皮填標時 → 理論人數自動算 (std/(3600/eolr)) ----
        d6 = []; ok6 = True
        # 選 anchor 那列(原有裁斷機列)填磨皮標時
        polish_pid = anchor["id"]
        polish_std = 90.0
        expect_theory = round(polish_std / DIVISOR, 4)   # 90/30 = 3.0
        setp = page.evaluate(
            """([pid,v])=>{const rows=document.querySelectorAll('#tbody-cut-裁斷機 tr');
                for(const tr of rows){const b=tr.querySelector('button.btn-ins');
                  if(b && b.getAttribute('onclick')===`insertRowAfter(${pid})`){
                    const inp=tr.querySelector('input[onblur*="post_polish_std"]');
                    if(inp){inp.value=String(v); inp.dispatchEvent(new Event('input'));
                            inp.dispatchEvent(new Event('blur')); return true;}}}
                return false;}""", [polish_pid, polish_std])
        d6.append(f"填 post_polish_std={polish_std} via UI(onblur→EDITS): dom命中={setp}")
        page.evaluate("()=>saveSilent()")
        page.wait_for_timeout(900)
        open_detail(); page.wait_for_timeout(400)
        # DB 值
        pdb = db("SELECT post_polish_std FROM ie_process WHERE id=?", (polish_pid,), one=True)
        d6.append(f"重整後 DB post_polish_std={pdb['post_polish_std']}")
        if str(pdb["post_polish_std"]) not in (str(polish_std), "90", "90.0"):
            ok6 = False; d6.append("  ✗ 磨皮標時未持久化")
        # UI 理論人數 cell (磨皮 ops) — 該列磨皮欄後的 th-post-ops-cell
        theory_ui = page.evaluate(
            """([pid])=>{const rows=document.querySelectorAll('#tbody-cut-裁斷機 tr');
                for(const tr of rows){const b=tr.querySelector('button.btn-ins');
                  if(b && b.getAttribute('onclick')===`insertRowAfter(${pid})`){
                    const inp=tr.querySelector('input[onblur*="post_polish_std"]');
                    if(inp){const cell=inp.closest('td').nextElementSibling;
                            return cell?cell.innerText.trim():null;}}}
                return null;}""", [polish_pid])
        d6.append(f"UI 磨皮理論人數 cell={theory_ui} ; 期望={expect_theory}")
        try:
            if abs(float(theory_ui) - expect_theory) > 0.01:
                ok6 = False; d6.append("  ✗ 理論人數計算不符")
        except (TypeError, ValueError):
            ok6 = False; d6.append("  ✗ 理論人數 cell 無數值")
        shot(page, "06_polish_theory")
        record(6, "磨皮填標時 → 理論人數自動算 = 標時÷(3600/eolr)", "PASS" if ok6 else "FAIL", "\n".join(d6))

        # ---- Check 7: ATOM/EMMA(typeB) 沒有磨皮欄、對齊沒跑掉 ----
        d7 = []; ok7 = True
        for zoneB in ("ATOM","EMMA"):
            info = page.evaluate(
                """(zn)=>{const card=[...document.querySelectorAll('.zone-card')]
                     .find(c=>c.querySelector('.zone-name') && c.querySelector('.zone-name').innerText.trim().includes(zn));
                     if(!card)return {found:false};
                     const thead=card.querySelector('table thead');
                     const groups=[...card.querySelectorAll('thead th.th-post-group')].map(t=>t.innerText.trim());
                     const bodyCells=(()=>{const tr=card.querySelector('tbody tr');return tr?tr.querySelectorAll('td').length:0;})();
                     // 表格欄數 = 各表頭列 colspan 總和的最大值（考慮 rowspan 欄如刪除欄跨到末列）
                     const headCols=(()=>{let mx=0;for(const tr of thead.querySelectorAll('tr')){
                          const s=[...tr.children].reduce((n,th)=>n+(parseInt(th.getAttribute('colspan'))||1),0); if(s>mx)mx=s;}
                          return mx;})();
                     return {found:true, hasPolish: thead.innerText.includes('磨皮'), groups, bodyCells, headCols};}""",
                zoneB)
            if not info.get("found"):
                d7.append(f"[{zoneB}] 此鞋型無此區塊（跳過對齊比對）")
                continue
            d7.append(f"[{zoneB}] hasPolish={info['hasPolish']} 後製群組={info['groups']} "
                      f"(共{len(info['groups'])}) body首列td數={info['bodyCells']} 表頭末列欄數={info['headCols']}")
            if info["hasPolish"]:
                ok7 = False; d7.append(f"  ✗ {zoneB} 竟出現磨皮欄")
            if len(info["groups"]) != 5:
                ok7 = False; d7.append(f"  ✗ {zoneB} 後製群組非 5（typeB 應維持 5 後製）")
            # 對齊：body 首列 td 數應等於表頭末列欄數
            if info["bodyCells"] and info["headCols"] and info["bodyCells"] != info["headCols"]:
                ok7 = False; d7.append(f"  ✗ {zoneB} 對齊跑掉：body td={info['bodyCells']} vs head欄={info['headCols']}")
        shot(page, "07_typeB_no_polish")
        record(7, "ATOM/EMMA(typeB) 沒有磨皮欄、維持5後製、對齊不跑", "PASS" if ok7 else "FAIL", "\n".join(d7))

        # =====================================================================
        # 【另存新版本 — 插入列 + 磨皮值 是否正確複製】
        # =====================================================================
        # ---- Check 4 + 8: 另存新版 → 含插入的工序 & 磨皮值 ----
        d48 = []; ok4 = True; ok8 = True
        new_stage_name = f"新版本_{RUN}"
        dialog_state["accept_text"] = new_stage_name
        page.evaluate("()=>newStage()")   # prompt → accept with name
        page.wait_for_timeout(1800)
        copy_stage = db("SELECT id, stage_name, is_approved FROM ie_stage "
                        "WHERE header_id=? AND stage_name=?", (HID, new_stage_name), one=True)
        if not copy_stage:
            ok4 = ok8 = False; d48.append("另存新版失敗：找不到新 stage")
        else:
            d48.append(f"新版本 stage id={copy_stage['id']} name={copy_stage['stage_name']} approved={copy_stage['is_approved']}")
            # (4) 新版是否含插入的工序（同名、同 zone、綁新 stage）
            cp_ins = db("SELECT id, seq, zone, stage_id, tct FROM ie_process "
                        "WHERE header_id=? AND stage_id=? AND process_name=?",
                        (HID, copy_stage["id"], ins_name), one=True)
            if cp_ins:
                d48.append(f"[4] 新版含插入工序『{ins_name}』 id={cp_ins['id']} seq={cp_ins['seq']} "
                           f"zone={cp_ins['zone']} tct={cp_ins['tct']} (獨立於原版列)")
                if cp_ins["zone"] != "裁斷機": ok4 = False; d48.append("  ✗ 複製列 zone 錯")
                if cp_ins["id"] == (new_row["id"] if new_row else None):
                    ok4 = False; d48.append("  ✗ 複製列與原列同一 id（未真正複製）")
            else:
                ok4 = False; d48.append(f"[4] ✗ 新版缺少插入工序『{ins_name}』")
            # (8) 新版是否含磨皮值（複製自原版 anchor 對應列）
            cp_polish = db("SELECT id, post_polish_std FROM ie_process "
                           "WHERE header_id=? AND stage_id=? AND zone='裁斷機' "
                           "AND post_polish_std IS NOT NULL AND post_polish_std=? ",
                           (HID, copy_stage["id"], polish_std))
            if cp_polish:
                d48.append(f"[8] 新版含磨皮值 post_polish_std={polish_std} 的列數={len(cp_polish)} "
                           f"(例 id={cp_polish[0]['id']})")
            else:
                ok8 = False; d48.append(f"[8] ✗ 新版未複製到磨皮值 {polish_std}")
        shot(page, "04_08_saveas_newversion")
        record(4, "另存新版 → 新版包含插入的工序（複製正確、獨立列）", "PASS" if ok4 else "FAIL", "\n".join(d48))
        record(8, "磨皮值存進版本 → 另存新版有複製到磨皮值", "PASS" if ok8 else "FAIL",
               "(同上 Check4 之新版檢查)")

        # =====================================================================
        # 【與版本控制互動：鎖定版】
        # =====================================================================
        # 鎖定「新版本」(含插入列+磨皮值)，之後測：插入被擋 + 編制表抓鎖定版
        lock_target = copy_stage["id"] if copy_stage else gen_stage["id"]
        api = ctx.request
        lock_resp = api.post(f"{BASE}/api/ie/stages/{HID}/{lock_target}/approve",
                             data=json.dumps({"note":"verify test lock"}),
                             headers={"Content-Type":"application/json"})
        lock_json = lock_resp.json()
        print(f"\n鎖定 stage {lock_target}: HTTP {lock_resp.status} {lock_json}")
        is_locked_now = db("SELECT COALESCE(is_approved,0) a FROM ie_stage WHERE id=?", (lock_target,), one=True)

        # ---- Check 3: 鎖定版試插入 → 被擋 ----
        d3 = []; ok3 = True
        if not (is_locked_now and is_locked_now["a"]):
            ok3 = False; d3.append(f"前置失敗：stage {lock_target} 未成功鎖定 ({lock_json})")
        else:
            d3.append(f"stage {lock_target} 已鎖定（is_approved=1）")
            # 取鎖定版裡的一列當 anchor
            locked_anchor = db("SELECT id, seq FROM ie_process WHERE header_id=? AND stage_id=? "
                               "AND segment='cutting' AND zone='裁斷機' AND (flag IS NULL OR flag!='deleted') "
                               "ORDER BY seq LIMIT 1", (HID, lock_target), one=True)
            cnt_before = db("SELECT COUNT(*) n FROM ie_process WHERE header_id=? AND stage_id=? "
                            "AND segment='cutting' AND zone='裁斷機'", (HID, lock_target), one=True)["n"]
            # 後端直呼 insert_row（與前端 submitAddRow 同一 API）
            blk_name = f"鎖定版禁止插入_{RUN}"
            r = api.post(f"{BASE}/api/ie/cell/insert_row",
                         data=json.dumps({"after_process_id": locked_anchor["id"],
                                          "stage_id": lock_target, "user":"demo",
                                          "process_name": blk_name}),
                         headers={"Content-Type":"application/json"})
            rj = r.json()
            d3.append(f"插入鎖定版 API 回應: HTTP {r.status} → {rj}")
            cnt_after = db("SELECT COUNT(*) n FROM ie_process WHERE header_id=? AND stage_id=? "
                           "AND segment='cutting' AND zone='裁斷機'", (HID, lock_target), one=True)["n"]
            blocked = (rj.get("ok") is False) and (rj.get("locked") is True)
            not_written = db("SELECT id FROM ie_process WHERE header_id=? AND process_name=?",
                             (HID, blk_name), one=True) is None
            d3.append(f"被擋(ok:false, locked:true)={blocked} ; 未寫入DB={not_written} ; "
                      f"列數 {cnt_before}→{cnt_after}")
            if not blocked:  ok3 = False; d3.append("  ✗ 後端未回 locked 拒絕")
            if not not_written or cnt_after != cnt_before:
                ok3 = False; d3.append("  ✗ 鎖定版竟被寫入新列")
            d3.append("備註：admin/manager 帳號→後端擋在 DB 層回 {ok:false,locked:true}(HTTP 200)；"
                      "非編輯者/read_only 才會在權限層回 HTTP 403。兩者皆有效阻擋。")
            # UI 層佐證：鎖定版時 saveSilent/儲存鈕會提示「鎖定版不能覆蓋」
        shot(page, "03_locked_insert_blocked")
        record(3, "鎖定版試插入 → 被擋（不可改）", "PASS" if ok3 else "FAIL", "\n".join(d3))

        # ---- Check 9: 編制表抓鎖定版時，插入/磨皮工序是否正確計入 ----
        d9 = []; ok9 = True
        # 編制表/allocation 讀 IE 用 _locked_stage_clause：ie_process.stage_id = (該 header 的 is_approved=1 stage)
        # 直接以同一 clause 查 header 35 art 的鎖定版工序，確認插入列 + 磨皮列 都在其中且只計一次
        art_row = db("SELECT art FROM ie_process WHERE header_id=? AND stage_id=? LIMIT 1",
                     (HID, lock_target), one=True)
        d9.append(f"鎖定版 art={art_row['art'] if art_row else None} (stage {lock_target})")
        locked_clause_rows = db(
            "SELECT id, zone, seq, process_name, standard_time, actual_operators, post_polish_std "
            "FROM ie_process ip "
            "WHERE ip.header_id=? AND (ip.flag IS NULL OR ip.flag!='deleted') "
            "AND ip.stage_id = (SELECT s.id FROM ie_stage s WHERE s.header_id=ip.header_id "
            "                   AND COALESCE(s.is_approved,0)=1 LIMIT 1)", (HID,))
        # 這批 rows 就是編制表/allocation 會取用的鎖定版工序
        ins_in_locked = [r for r in locked_clause_rows if r["process_name"] == ins_name]
        polish_in_locked = [r for r in locked_clause_rows if r["post_polish_std"] == polish_std]
        # 全部 rows 必須屬於 lock_target
        stray = db("SELECT DISTINCT ip.stage_id FROM ie_process ip "
                   "WHERE ip.header_id=? AND (ip.flag IS NULL OR ip.flag!='deleted') "
                   "AND ip.stage_id = (SELECT s.id FROM ie_stage s WHERE s.header_id=ip.header_id "
                   "                   AND COALESCE(s.is_approved,0)=1 LIMIT 1)", (HID,))
        d9.append(f"編制表 locked-clause 取到工序 {len(locked_clause_rows)} 列，皆屬 stage_id={[s['stage_id'] for s in stray]}")
        d9.append(f"其中『插入工序』出現 {len(ins_in_locked)} 次 "
                  + (f"(id={ins_in_locked[0]['id']} seq={ins_in_locked[0]['seq']} act={ins_in_locked[0]['actual_operators']})" if ins_in_locked else ""))
        d9.append(f"其中『磨皮值={polish_std}』出現 {len(polish_in_locked)} 次 "
                  + (f"(id={polish_in_locked[0]['id']})" if polish_in_locked else ""))
        if len(ins_in_locked) != 1:  ok9 = False; d9.append("  ✗ 插入工序未被鎖定版取到 / 或重複計")
        if len(polish_in_locked) < 1: ok9 = False; d9.append("  ✗ 磨皮工序未被鎖定版取到")
        if [s["stage_id"] for s in stray] not in ([lock_target],):
            ok9 = False; d9.append(f"  ✗ locked-clause 取到非鎖定版列（應只 {lock_target}）")
        # 額外佐證：呼叫真正的編制表 API（best-effort，看是否有回鎖定資料）
        try:
            b = api.get(f"{BASE}/api/bianzhi/detail")
            d9.append(f"/api/bianzhi/detail HTTP {b.status}（編制表前端資料來源，讀鎖定版）")
        except Exception as e:
            d9.append(f"/api/bianzhi/detail 呼叫略過: {e}")
        record(9, "插入/磨皮工序：編制表抓鎖定版時正確計入（只計一次、僅取鎖定版）",
               "PASS" if ok9 else "FAIL", "\n".join(d9))

        # =====================================================================
        print("\n" + "="*70)
        print("驗證總結")
        print("="*70)
        npass = sum(1 for r in RESULTS if r[2]=="PASS")
        nfail = sum(1 for r in RESULTS if r[2]=="FAIL")
        for idx,title,status,_ in sorted(RESULTS):
            print(f"  [{idx}] {status:4} — {title}")
        print(f"\n  合計 {npass} PASS / {nfail} FAIL / {len(RESULTS)} 項")
        print(f"  截圖目錄: {SHOT_DIR}")
        browser.close()
        return nfail

if __name__ == "__main__":
    sys.exit(1 if main() else 0)
