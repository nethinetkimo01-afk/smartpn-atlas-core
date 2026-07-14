# -*- coding: utf-8 -*-
"""
Task S 驗收：IE表/編制表 最外層主頁簽整合（/app 統一外框，各載一頁 iframe）。

環境（隔離、不碰正式資料）：
  - 隔離 DB : flask_backend/data/test_isolated/atlas_test.db (atlas.db 一致性副本)
  - 隔離 SERVER: python flask_backend/serve_test_isolated.py → http://127.0.0.1:5099
用法：先啟動隔離 server，再  py test_task_s_shell.py

驗收項（定案 4）：
  1. 兩頁簽互切 10 次，各自功能抽測正常（IE 細表開啟 / 編制表匯入預覽入口 + 表渲染）
  2. IE 細表填值不存 → 切頁簽 → 攔截/flush 保住值，不靜默丟
  3. tongcai 兩頁全灰、editor 權限迴歸、三語切換兩頁皆正常
  4. F5 後停在原頁簽（#ie / #bianche）
"""
import sys, io, os, sqlite3, hashlib, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5099"
HID  = 5                       # 有 stage(未鎖定,可編) + 21 工序列
DBP  = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "flask_backend", "data", "test_isolated", "atlas_test.db")
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "flask_backend", "test_output", "task_s_shots")
os.makedirs(SHOT, exist_ok=True)

ED_USER, ED_PW = "s_editor", "s123"     # 造測用 data_entry（指派 HID）

RESULTS = []
def rec(title, ok, detail=""):
    RESULTS.append((title, ok))
    print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — {title}")
    for ln in detail.splitlines():
        if ln.strip(): print("     " + ln)

def dbexec(sql, p=()):
    c = sqlite3.connect(DBP, timeout=15)
    try: c.execute("PRAGMA busy_timeout=15000"); c.execute(sql, p); c.commit()
    finally: c.close()
def dbq(sql, p=(), one=False):
    c = sqlite3.connect(DBP, timeout=15); c.row_factory = sqlite3.Row
    try:
        rows=[dict(r) for r in c.execute(sql,p).fetchall()]
        return (rows[0] if rows else None) if one else rows
    finally: c.close()

_n={"i":0}
def shot(pg,name):
    _n["i"]+=1
    try: pg.screenshot(path=os.path.join(SHOT,f"{_n['i']:02d}_{name}.png"))
    except Exception as e: print("  (shot",e,")")


def setup_accounts():
    h = hashlib.sha256(ED_PW.encode()).hexdigest()
    dbexec("INSERT OR IGNORE INTO sys_users (username,display_name,role,password_hash,active,locked,created_at,updated_at) "
           "VALUES (?,?,?,?,1,0,datetime('now'),datetime('now'))", (ED_USER,"TaskS編輯員","data_entry",h))
    uid = dbq("SELECT id FROM sys_users WHERE username=?", (ED_USER,), one=True)["id"]
    # 指派 HID 給 editor → 該鞋型可編（驗 editor 權限迴歸：IE 可編、bianche 唯讀）
    dbexec("INSERT OR IGNORE INTO ie_assignments (header_id,user_id) VALUES (?,?)", (HID, uid))

def cleanup_accounts():
    uid = dbq("SELECT id FROM sys_users WHERE username=?", (ED_USER,), one=True)
    if uid:
        dbexec("DELETE FROM ie_assignments WHERE user_id=?", (uid["id"],))
        dbexec("DELETE FROM sys_users WHERE id=?", (uid["id"],))


def main():
    setup_accounts()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width":1600,"height":1000})
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())

        def login(u, p):
            page.goto(f"{BASE}/login", wait_until="domcontentloaded")
            page.fill("#username", u); page.fill("#password", p or "x")
            page.click("#btnLogin"); page.wait_for_timeout(1200)

        def frame(name):
            return page.frame(name=name)

        def wait_frame(name, sel, to=9000):
            page.wait_for_function(
                "(a)=>{const el=document.getElementById('frame-'+a.n);return el&&el.contentDocument&&!!el.contentDocument.querySelector(a.sel)}",
                arg={"n":name,"sel":sel}, timeout=to)

        # ══ 1) 登入預設進 IE表 ══
        try:
            login("jim","admin123")
            page.goto(f"{BASE}/app", wait_until="domcontentloaded")
            page.wait_for_selector("#tab-ie", timeout=6000)
            wait_frame("ie", "#ie-tbody")
            ie_active = "active" in (page.get_attribute("#frame-ie","class") or "")
            tab_active = "active" in (page.get_attribute("#tab-ie","class") or "")
            hash_ok = page.evaluate("location.hash") in ("#ie","")
            shot(page,"login_default_ie")
            rec("登入後預設進 IE表（IE frame active + 頁簽亮 + #ie）",
                ie_active and tab_active, f"ie_frame_active={ie_active} tab_active={tab_active} hash={page.evaluate('location.hash')}")
        except Exception as e:
            rec("登入後預設進 IE表", False, f"EXC {e}")

        # ══ 2) 兩頁簽互切 10 次，各自功能抽測 ══
        try:
            ok_switch = True; detail=[]
            for i in range(10):
                page.click("#tab-bianche"); page.wait_for_timeout(120)
                wait_frame("bianche", "#unitTable")
                bz_ok = ("active" in (page.get_attribute("#frame-bianche","class") or "")) and \
                        frame("frame-bianche").query_selector("#unitTable") is not None
                page.click("#tab-ie"); page.wait_for_timeout(120)
                wait_frame("ie", "#ie-tbody")
                ie_ok = ("active" in (page.get_attribute("#frame-ie","class") or "")) and \
                        frame("frame-ie").query_selector("#ie-tbody") is not None
                if not (bz_ok and ie_ok):
                    ok_switch=False; detail.append(f"round {i+1}: bz={bz_ok} ie={ie_ok}")
            shot(page,"after_10_switch")
            rec("兩頁簽互切 10 次，各自表格皆渲染", ok_switch, "\n".join(detail) or "10 輪皆 OK")
        except Exception as e:
            rec("兩頁簽互切 10 次", False, f"EXC {e}")

        # ══ 3) IE 細表開啟（抽測 IE 功能） ══
        try:
            page.click("#tab-ie"); page.wait_for_timeout(150); wait_frame("ie","#ie-tbody")
            frame("frame-ie").evaluate("location.href='/ie/%d/detail'" % HID)
            page.wait_for_timeout(400)
            wait_frame("ie", ".cell-inp, .zone-card, #mainContent", to=12000)
            has_cells = frame("frame-ie").query_selector(".cell-inp") is not None
            shot(page,"ie_cell_detail")
            rec("IE 細表開啟（jim 可見編輯格 .cell-inp）", has_cells, f"cell_inp_present={has_cells}")
        except Exception as e:
            rec("IE 細表開啟", False, f"EXC {e}")

        # ══ 4) 編制表匯入預覽入口 + 表渲染（抽測 bianche 功能） ══
        try:
            page.click("#tab-bianche"); page.wait_for_timeout(200); wait_frame("bianche","#unitTable")
            bz = frame("frame-bianche")
            imp = bz.query_selector("input[type=file]") is not None          # ⬆ 匯入 入口
            exp = bz.query_selector("button:has-text('匯出')") is not None
            rows = bz.eval_on_selector_all("#unitTableBody tr","els=>els.length")
            shot(page,"bianche_tools")
            rec("編制表功能抽測（匯入入口+匯出鈕+單位表渲染）",
                imp and exp and rows>0, f"import_input={imp} export_btn={exp} unit_rows={rows}")
        except Exception as e:
            rec("編制表功能抽測", False, f"EXC {e}")

        # ══ 5) IE 細表填值不存 → 切頁簽 → 保住值，不靜默丟 ══
        try:
            page.click("#tab-ie"); page.wait_for_timeout(150)
            frame("frame-ie").evaluate("location.href='/ie/%d/detail'" % HID)
            page.wait_for_timeout(500)
            wait_frame("ie",".cell-inp",to=12000)
            ie = frame("frame-ie")
            testval = "77.7"
            # 對第一個 input.cell-inp（手工文字格，非連刀 select）輸值 + 觸發 onblur(commitEditStatic → EDITS)
            first = ie.query_selector("input.cell-inp")
            first.fill(testval)
            ie.evaluate("()=>{const el=document.querySelector('input.cell-inp'); el.blur();}")
            page.wait_for_timeout(150)
            pending_before = ie.evaluate("()=>Object.values(EDITS).reduce((n,f)=>n+Object.keys(f).length,0)")
            # 切到編制表 → shell.flushActive() 應對 IE frame 呼叫 flushPendingEdits
            page.click("#tab-bianche"); page.wait_for_timeout(400); wait_frame("bianche","#unitTable")
            # 切回 IE → frame 保活，input 仍在
            page.click("#tab-ie"); page.wait_for_timeout(300)
            ie = frame("frame-ie")
            val_after = ie.evaluate("()=>{const el=document.querySelector('input.cell-inp'); return el?el.value:null;}")
            pending_after = ie.evaluate("()=>Object.values(EDITS).reduce((n,f)=>n+Object.keys(f).length,0)")
            kept = (str(val_after) == testval)
            flushed = (pending_before >= 1 and pending_after == 0)
            shot(page,"flush_roundtrip")
            rec("IE 細表未存值：切頁簽 flush 且值保住（不靜默丟）",
                kept and flushed,
                f"pending_before={pending_before} pending_after={pending_after} val_after={val_after} (期望切前有未存、切後已flush、值={testval}保留)")
        except Exception as e:
            rec("IE 細表未存值切頁簽保住", False, f"EXC {e}")

        # ══ 6) 三語切換：IE 頁三語正常；bianche 頁不破（無語言鈕，照渲染） ══
        try:
            page.click("#tab-ie"); page.wait_for_timeout(150)
            frame("frame-ie").evaluate("location.href='/ie'")
            page.wait_for_timeout(400); wait_frame("ie","#th-model")
            ie = frame("frame-ie")
            zh = ie.query_selector("#th-model").inner_text()
            ie.eval_on_selector("button[data-lang='en']","b=>b.click()"); page.wait_for_timeout(200)
            en = ie.query_selector("#th-model").inner_text()
            ie.eval_on_selector("button[data-lang='vi']","b=>b.click()"); page.wait_for_timeout(200)
            vi = ie.query_selector("#th-model").inner_text()
            ie.eval_on_selector("button[data-lang='zh']","b=>b.click()"); page.wait_for_timeout(150)
            ie_trilingual = (zh!=en) or (zh!=vi) or (en!=vi)
            # bianche 照渲染（無語言鈕 by design）
            page.click("#tab-bianche"); page.wait_for_timeout(200); wait_frame("bianche","#unitTable")
            bz_ok = frame("frame-bianche").eval_on_selector_all("#unitTableBody tr","e=>e.length")>0
            shot(page,"trilingual")
            rec("三語切換：IE 三語切換有效 + 編制表照常渲染",
                ie_trilingual and bz_ok, f"zh={zh!r} en={en!r} vi={vi!r} bianche_rows_ok={bz_ok}")
        except Exception as e:
            rec("三語切換兩頁皆正常", False, f"EXC {e}")

        # ══ 7) F5 停在原頁簽 ══
        try:
            page.goto(f"{BASE}/app#bianche", wait_until="domcontentloaded")
            wait_frame("bianche","#unitTable")
            page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(400)
            wait_frame("bianche","#unitTable")
            stay_bz = "active" in (page.get_attribute("#frame-bianche","class") or "") and page.evaluate("location.hash")=="#bianche"
            page.goto(f"{BASE}/app#ie", wait_until="domcontentloaded")
            wait_frame("ie","#ie-tbody")
            page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(400)
            wait_frame("ie","#ie-tbody")
            stay_ie = "active" in (page.get_attribute("#frame-ie","class") or "") and page.evaluate("location.hash")=="#ie"
            shot(page,"f5_stay")
            rec("F5 後停在原頁簽（#bianche→bianche、#ie→ie）", stay_bz and stay_ie, f"stay_bianche={stay_bz} stay_ie={stay_ie}")
        except Exception as e:
            rec("F5 後停在原頁簽", False, f"EXC {e}")

        # ══ 8) tongcai 兩頁全灰（read_only） ══
        try:
            login("tongcai","x")
            page.goto(f"{BASE}/app#ie", wait_until="domcontentloaded")
            wait_frame("ie","#ie-tbody")
            frame("frame-ie").evaluate("location.href='/ie/%d/detail'" % HID)
            page.wait_for_timeout(500); wait_frame("ie","#mainContent, .zone-card", to=12000)
            page.wait_for_timeout(400)
            ie_inp = frame("frame-ie").eval_on_selector_all(".cell-inp","e=>e.length")  # 全灰→input 被替換成 span → 0
            page.click("#tab-bianche"); page.wait_for_timeout(300); wait_frame("bianche","#unitTable")
            bz = frame("frame-bianche")
            bz_total = bz.eval_on_selector_all(".bz-inp","e=>e.length")
            bz_enabled = bz.eval_on_selector_all(".bz-inp","e=>e.filter(x=>!x.disabled).length")
            shot(page,"tongcai_grey")
            rec("tongcai 兩頁全灰（IE 無可編格 + 編制表輸入全 disabled）",
                ie_inp==0 and (bz_total==0 or bz_enabled==0),
                f"ie_cell_inp={ie_inp}(期望0) bianche_inp_total={bz_total} enabled={bz_enabled}(期望0)")
        except Exception as e:
            rec("tongcai 兩頁全灰", False, f"EXC {e}")

        # ══ 9) editor 權限迴歸（IE 指派可編 + 編制表唯讀） ══
        try:
            login(ED_USER, ED_PW)
            page.goto(f"{BASE}/app#ie", wait_until="domcontentloaded")
            wait_frame("ie","#ie-tbody")
            frame("frame-ie").evaluate("location.href='/ie/%d/detail'" % HID)
            page.wait_for_timeout(500); wait_frame("ie",".cell-inp, #mainContent", to=12000)
            page.wait_for_timeout(300)
            ed_ie_edit = frame("frame-ie").eval_on_selector_all(".cell-inp","e=>e.length")  # 指派 → 可編 → >0
            page.click("#tab-bianche"); page.wait_for_timeout(300); wait_frame("bianche","#unitTable")
            bz = frame("frame-bianche")
            bz_enabled = bz.eval_on_selector_all(".bz-inp","e=>e.filter(x=>!x.disabled).length")  # 28 規格：非manager→唯讀
            # 硬打 IE 寫入 API（未指派其他 header 應 403；指派的可寫）— 打一個未指派 header 的 can_edit
            api = ctx.request
            other = dbq("SELECT id FROM ob_header WHERE id<>? ORDER BY id LIMIT 1",(HID,),one=True)["id"]
            r_other = api.get(f"{BASE}/api/ie/{other}/can_edit")
            can_other = r_other.json().get("can_edit", None)
            shot(page,"editor_regression")
            rec("editor 權限迴歸（指派 header 可編 + 未指派唯讀 + 編制表唯讀）",
                ed_ie_edit>0 and bz_enabled==0 and can_other in (False,0),
                f"assigned_ie_editable={ed_ie_edit}(期望>0) bianche_enabled={bz_enabled}(期望0) other_header_can_edit={can_other}(期望False)")
        except Exception as e:
            rec("editor 權限迴歸", False, f"EXC {e}")

        # ══ 10) 舊入口零迴歸：/ie 與 /bianche 仍可獨立開 ══
        try:
            login("jim","admin123")
            page.goto(f"{BASE}/ie", wait_until="domcontentloaded")
            page.wait_for_selector("#ie-tbody", timeout=6000)
            ie_standalone = page.query_selector("#ie-tbody") is not None
            page.goto(f"{BASE}/bianche", wait_until="domcontentloaded")
            page.wait_for_selector("#unitTable", timeout=6000)
            bz_standalone = page.query_selector("#unitTable") is not None
            rec("舊入口零迴歸（/ie、/bianche 仍可獨立開）", ie_standalone and bz_standalone,
                f"/ie={ie_standalone} /bianche={bz_standalone}")
        except Exception as e:
            rec("舊入口零迴歸", False, f"EXC {e}")

        browser.close()

    cleanup_accounts()
    print("\n" + "="*60)
    npass = sum(1 for _,ok in RESULTS if ok)
    for t,ok in RESULTS: print(f"  {'✅' if ok else '❌'} {t}")
    print(f"\n  {npass}/{len(RESULTS)} PASS")
    print("="*60)
    sys.exit(0 if npass==len(RESULTS) else 1)


if __name__ == "__main__":
    main()
