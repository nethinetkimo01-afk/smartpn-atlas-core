# -*- coding: utf-8 -*-
"""
驗證新功能：設備種類下拉改成「可管理選項清單」(equipment_types 表 + /api/equipment_types)，
先塞兩個選項「單針針車機」「雙針針車機」供 Jim 驗收。

環境（隔離、不碰正式資料）：
  - 隔離 DB : flask_backend/data/test_isolated/atlas_test.db (atlas.db 一致性副本)
  - 隔離 SERVER: python flask_backend/serve_test_isolated.py → http://127.0.0.1:5099
    (init_db 於啟動時建 equipment_types 表並塞兩筆)
  - 測試鞋型 : header 5（stitching/assembly/stf 齊全）, stage 5「初版」

用法：先啟動隔離 server，再  py test_equipment_types.py
"""
import sys, io, os, json, sqlite3
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5099"
HID  = 5
STAGE = 5
OPT1 = "單針針車機"
OPT2 = "雙針針車機"
TARGET_PID = 90761   # stitching 主流 第一列
DBPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "flask_backend", "data", "test_isolated", "atlas_test.db")
SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "flask_backend", "test_output", "equip_shots")
os.makedirs(SHOT_DIR, exist_ok=True)

RESULTS = []
def record(title, ok, detail=""):
    RESULTS.append((title, ok))
    print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — {title}")
    for line in detail.splitlines():
        if line.strip(): print("     " + line)

def db(sql, params=(), one=False):
    c = sqlite3.connect(DBPATH); c.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in c.execute(sql, params).fetchall()]
        return (rows[0] if rows else None) if one else rows
    finally:
        c.close()


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = ctx.new_page()
        dlg = {"text": None}
        alerts = []
        def _on_dialog(d):
            if d.type != "prompt":
                alerts.append(d.message)
            d.accept(dlg["text"] or "") if d.type == "prompt" else d.accept()
        page.on("dialog", _on_dialog)

        page.goto(f"{BASE}/login", wait_until="domcontentloaded")
        page.fill("#username", "jim"); page.fill("#password", "admin123")
        page.click("#btnLogin"); page.wait_for_timeout(1200)
        api = ctx.request

        def open_detail():
            page.goto(f"{BASE}/ie/{HID}/detail", wait_until="domcontentloaded")
            page.wait_for_function("()=>document.querySelectorAll('.zone-card').length>0", timeout=8000)
            page.wait_for_timeout(600)

        def switch(seg):
            page.evaluate("(s)=>switchSeg(s)", seg)
            page.wait_for_timeout(900)

        # 讀某 pid 那列的設備種類 <select> 選項與當前值
        def equip_select(pid):
            return page.evaluate(
                """(pid)=>{const sel=[...document.querySelectorAll('select.cell-inp')]
                     .find(s=>{const oc=s.getAttribute('onchange')||'';return oc.includes(`,${pid},'equipment_type'`)||oc.includes('equipment_type') && oc.includes(`(this,${pid},`);});
                   if(!sel)return null;
                   return {options:[...sel.options].map(o=>o.text), value:sel.value};}""", pid)
        # 較穩：直接找 onchange 精準匹配該 pid 的 select
        def equip_select_for(pid):
            return page.evaluate(
                """(pid)=>{const want=`saveSingleField(this,${pid},'equipment_type')`;
                   const sel=[...document.querySelectorAll('select.cell-inp')].find(s=>(s.getAttribute('onchange')||'')===want);
                   if(!sel)return null;
                   return {options:[...sel.options].map(o=>o.text), value:sel.value};}""", pid)

        # ── Test 1：stitching/assembly/STF 設備種類下拉有兩選項(+空白) ──────────
        d1 = []; ok1 = True
        seg_zone_pid = {}
        for seg, zone in [('stitching','主流'), ('assembly','成型主區'), ('stf','貼底')]:
            row = db("SELECT id FROM ie_process WHERE header_id=? AND segment=? AND zone=? "
                     "AND (flag IS NULL OR flag!='deleted') AND stage_id=? ORDER BY seq LIMIT 1",
                     (HID, seg, zone, STAGE), one=True)
            seg_zone_pid[seg] = (zone, row['id'])
            open_detail(); switch(seg) if seg != 'cutting' else None
            sel = equip_select_for(row['id'])
            if not sel:
                ok1 = False; d1.append(f"[{seg}/{zone}] 找不到設備種類下拉"); continue
            opts = sel['options']
            d1.append(f"[{seg}/{zone}] pid={row['id']} 下拉選項={opts}")
            has_blank = opts and opts[0] == '-'
            if not has_blank: ok1 = False; d1.append("  ✗ 第一項非空白「-」")
            if OPT1 not in opts: ok1 = False; d1.append(f"  ✗ 缺「{OPT1}」")
            if OPT2 not in opts: ok1 = False; d1.append(f"  ✗ 缺「{OPT2}」")
        record("stitching/assembly/STF 設備種類下拉有「單針/雙針針車機」兩選項(+空白)", ok1, "\n".join(d1))
        page.screenshot(path=os.path.join(SHOT_DIR, "01_dropdown_options.png"))

        # ── Test 2：選一個 → onchange 即時存 → 重整 值還在 ──────────────────────
        d2 = []; ok2 = True
        open_detail(); switch('stitching')
        picked = page.evaluate(
            """([pid,val])=>{const want=`saveSingleField(this,${pid},'equipment_type')`;
               const sel=[...document.querySelectorAll('select.cell-inp')].find(s=>(s.getAttribute('onchange')||'')===want);
               if(!sel)return false;
               // 確保選項存在
               if(![...sel.options].some(o=>o.value===val))return 'noopt';
               sel.value=val; sel.dispatchEvent(new Event('change')); return true;}""",
            [TARGET_PID, OPT1])
        page.wait_for_timeout(900)  # saveSingleField 即時存
        d2.append(f"UI 選「{OPT1}」(pid={TARGET_PID}) onchange 即時存: {picked}")
        # DB 佐證
        after_db = db("SELECT equipment_type FROM ie_process WHERE id=?", (TARGET_PID,), one=True)
        d2.append(f"DB equipment_type = {after_db['equipment_type']!r}")
        if after_db['equipment_type'] != OPT1: ok2 = False; d2.append("  ✗ 未即時存進 DB")
        # 重整後 UI 仍選著
        open_detail(); switch('stitching')
        sel2 = equip_select_for(TARGET_PID)
        d2.append(f"重整後 UI 下拉當前值 = {sel2['value']!r}" if sel2 else "重整後找不到下拉")
        if not (sel2 and sel2['value'] == OPT1): ok2 = False; d2.append("  ✗ 重整後值不見")
        record("選設備種類 → onchange 即時存 → 重整值還在", ok2, "\n".join(d2))

        # ── Test 3：選了後另存新版本 → 新版該欄值複製過去 ──────────────────────
        d3 = []; ok3 = True
        r = api.post(f"{BASE}/api/ie/stages/{HID}",
                     data=json.dumps({"stage_name": "設備種類測試版", "source_stage_id": STAGE}),
                     headers={"Content-Type": "application/json"})
        j = r.json()
        d3.append(f"另存新版 API: {j}")
        new_stage = j.get('stage_id')
        if not new_stage:
            ok3 = False; d3.append("  ✗ 另存新版失敗")
        else:
            # 新版對應列（同 zone/seq/process_name）應帶 equipment_type
            src = db("SELECT zone, seq, process_name FROM ie_process WHERE id=?", (TARGET_PID,), one=True)
            cp = db("SELECT id, equipment_type FROM ie_process WHERE header_id=? AND stage_id=? "
                    "AND zone=? AND seq=? AND process_name=?",
                    (HID, new_stage, src['zone'], src['seq'], src['process_name']), one=True)
            d3.append(f"新版 stage={new_stage} 對應列: {cp}")
            if not cp or cp['equipment_type'] != OPT1:
                ok3 = False; d3.append("  ✗ 新版未複製到設備種類值")
            if cp and cp['id'] == TARGET_PID:
                ok3 = False; d3.append("  ✗ 複製列與原列同 id（未真正複製）")
        record("選了後另存新版本 → 新版該欄值複製過去", ok3, "\n".join(d3))

        # ── Test 4：WS / cutting 沒有設備種類欄（不受影響）──────────────────────
        d4 = []; ok4 = True
        open_detail()  # cutting tab
        cut_has = page.evaluate(
            """()=>{const sels=[...document.querySelectorAll('select.cell-inp')]
                 .filter(s=>(s.getAttribute('onchange')||'').includes(\"'equipment_type'\"));
               // 裁斷機/ATOM 等 cutting 主表頭是否有「設備種類」欄
               const heads=[...document.querySelectorAll('.proc-table thead')].map(t=>t.innerText);
               return {equipSelects:sels.length, anyHeadHasEquip:heads.some(h=>h.includes('設備種類'))};}""")
        d4.append(f"cutting tab: equipment 下拉數={cut_has['equipSelects']}, 表頭含設備種類={cut_has['anyHeadHasEquip']}")
        if cut_has['equipSelects'] != 0 or cut_has['anyHeadHasEquip']:
            ok4 = False; d4.append("  ✗ cutting 不應有設備種類欄")
        # WS 區塊（stitching 水蜘蛛）欄位只有 工序名稱/實際人數，無設備種類
        switch('stitching')
        ws_info = page.evaluate(
            """()=>{const card=[...document.querySelectorAll('.zone-card')]
                 .find(c=>{const n=c.querySelector('.zone-name');return n && n.innerText.includes('水蜘蛛');});
               if(!card)return {found:false};
               const th=card.querySelector('thead');
               const equipSel=card.querySelectorAll("select.cell-inp").length
                    ? [...card.querySelectorAll('select.cell-inp')].filter(s=>(s.getAttribute('onchange')||'').includes("'equipment_type'")).length : 0;
               return {found:true, head: th?th.innerText:'(no-thead)', equipSelects:equipSel};}""")
        d4.append(f"stitching 水蜘蛛(WS): {ws_info}")
        if ws_info.get('found'):
            if '設備種類' in (ws_info.get('head') or ''):
                ok4 = False; d4.append("  ✗ WS 表頭不應有設備種類欄")
            if ws_info.get('equipSelects'):
                ok4 = False; d4.append("  ✗ WS 不應有設備種類下拉")
        record("WS / cutting 沒有設備種類欄（不受影響）", ok4, "\n".join(d4))

        # ── Test 5：鎖定版 → 設備種類「唯讀」= 不能改（改值被擋、不落地）───────────
        # 說明：本系統對「鎖定版」的唯讀是全欄位一致的做法——欄位仍在，但任何存檔在
        #   前端(saveSingleField 檢查 STAGE.is_approved)＋後端(save_ie_edit locked)都被擋，
        #   跳 alert 且不寫入 DB。equipment_type 沿用同一機制(唯讀=改不動)。
        #   (另有 row.is_locked 逐列鎖→ locked-cell 純文字，屬既有既保留的另一種鎖。)
        d5 = []; ok5 = True
        lr = api.post(f"{BASE}/api/ie/stages/{HID}/{STAGE}/approve",
                      data=json.dumps({"note": "equip test lock"}),
                      headers={"Content-Type": "application/json"}).json()
        d5.append(f"鎖定 stage {STAGE}: {lr}")
        locked = db("SELECT COALESCE(is_approved,0) a FROM ie_stage WHERE id=?", (STAGE,), one=True)
        LOCK_PID = 90762  # stitching 主流 第2列，鎖定前 equipment_type=NULL
        before = db("SELECT equipment_type FROM ie_process WHERE id=?", (LOCK_PID,), one=True)
        if not (locked and locked['a']):
            ok5 = False; d5.append("  ✗ 鎖定失敗")
        else:
            open_detail(); switch('stitching')
            # 確認頁面確實在鎖定版
            on_locked = page.evaluate("()=>!!(STAGE && STAGE.is_approved)")
            d5.append(f"頁面在鎖定版: {on_locked}；改前 DB[{LOCK_PID}].equipment_type={before['equipment_type']!r}")
            alerts.clear()
            tried = page.evaluate(
                """([pid,val])=>{const want=`saveSingleField(this,${pid},'equipment_type')`;
                   const sel=[...document.querySelectorAll('select.cell-inp')].find(s=>(s.getAttribute('onchange')||'')===want);
                   if(!sel)return 'nosel';
                   sel.value=val; sel.dispatchEvent(new Event('change')); return true;}""",
                [LOCK_PID, OPT2])
            page.wait_for_timeout(900)
            after = db("SELECT equipment_type FROM ie_process WHERE id=?", (LOCK_PID,), one=True)
            d5.append(f"嘗試在鎖定版改成「{OPT2}」: tried={tried}；alert={alerts[:1]}；改後 DB={after['equipment_type']!r}")
            if after['equipment_type'] == OPT2:
                ok5 = False; d5.append("  ✗ 鎖定版竟被改動（未擋下）")
            if after['equipment_type'] != before['equipment_type']:
                ok5 = False; d5.append("  ✗ 鎖定版 DB 值被變更")
            if not any('鎖定版' in a for a in alerts):
                ok5 = False; d5.append("  ✗ 未跳「鎖定版不能覆蓋」提示")
            # 佐證 save 按鈕於鎖定版被停用（既有唯讀 UI）
            btns = page.evaluate("()=>({save:document.getElementById('btnSaveAll')?.disabled, cur:document.getElementById('btn-save-current')?.disabled})")
            d5.append(f"鎖定版儲存鈕 disabled: {btns}")
        record("鎖定版 → 設備種類唯讀（改值被前後端擋下、不落地、跳提示）", ok5, "\n".join(d5))
        page.screenshot(path=os.path.join(SHOT_DIR, "05_locked_readonly.png"))

        print("\n" + "=" * 66)
        print("設備種類可管理選項 — 驗證總結")
        print("=" * 66)
        npass = sum(1 for _, ok in RESULTS if ok); nfail = sum(1 for _, ok in RESULTS if not ok)
        for title, ok in RESULTS:
            print(f"  {'PASS' if ok else 'FAIL'} — {title}")
        print(f"\n  合計 {npass} PASS / {nfail} FAIL / {len(RESULTS)} 項")
        print(f"  截圖: {SHOT_DIR}")
        browser.close()
        return nfail

if __name__ == "__main__":
    sys.exit(1 if main() else 0)
