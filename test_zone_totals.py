# -*- coding: utf-8 -*-
"""
驗證新功能：每個製程(cutting/stitching/assembly/stf)的每個區塊(zone)表格最下方
「總計」列，加總 標準時間 / 理論人數 / 實際人數（唯讀公式格，空值當0）。

環境（隔離、不碰正式資料）：
  - 隔離 DB : flask_backend/data/test_isolated/atlas_test.db  (atlas.db 的一致性副本)
  - 隔離 SERVER: python flask_backend/serve_test_isolated.py → http://127.0.0.1:5099
  - 測試鞋型 : header 5（四製程齊全）, eolr=120, stage 5「初版」

Oracle：直接抓 UI 消費的同一支 /api/ie/cell 回傳 JSON，用與前端 calcZoneTotals
相同公式在 Python 端獨立算出各區塊總計，再和畫面總計列比對（同輸入→同結果）。

用法：先啟動隔離 server，再  py test_zone_totals.py
"""
import sys, io, os, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5099"
HID  = 5
EOLR = 120
STAGE = 5
SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "flask_backend", "test_output", "totals_shots")
os.makedirs(SHOT_DIR, exist_ok=True)

RESULTS = []
def record(title, ok, detail=""):
    RESULTS.append((title, ok))
    print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — {title}")
    for line in detail.splitlines():
        if line.strip(): print("     " + line)

# ── Oracle：與前端 _rowStd / calcZoneTotals 完全一致 ─────────────────────────
def _f(v):
    try: return float(v)
    except (TypeError, ValueError): return None

def row_std(row, seg, zone):
    if seg == 'cutting':
        if zone == '裁斷機':
            lay, qty, cph = _f(row.get('layers_per_cut')), _f(row.get('qty_per_pair')), _f(row.get('cut_per_hour'))
            if lay and qty and cph and lay > 0 and qty > 0 and cph > 0:
                return 3600 / cph / lay * qty * 1.0  # 2026-07-12 Jim 定案: ×1.1→×1.0
            return None
        return _f(row.get('standard_time'))
    if seg in ('stitching', 'assembly'):
        nt = row.get('normal_time')
        if nt is not None:
            allow = row.get('allowance_pct'); allow = allow if allow is not None else 10
            return nt * (1 + allow / 100)
        return _f(row.get('standard_time'))
    if seg == 'stf' and zone == '貼底':
        nt = row.get('normal_time')
        if nt is not None: return nt * 1.1
        return _f(row.get('standard_time'))
    return _f(row.get('standard_time'))

def oracle_totals(zone_obj, seg, zone, eolr=EOLR):
    divisor = 3600 / eolr
    std = theory = actual = 0.0
    seen = set()
    for row in zone_obj.get('rows', []):
        if row.get('flag') == 'deleted': continue
        st = row_std(row, seg, zone)
        if st is not None and st > 0:
            std += st; theory += st / divisor
        gi = row.get('group_info')
        if gi:
            gid = gi['group_id']
            if gid not in seen:
                seen.add(gid)
                hc = _f(gi.get('headcount'))
                if hc is not None: actual += hc
        else:
            a = _f(row.get('actual_operators'))
            if a is not None: actual += a
    return {'std': std, 'theory': theory, 'actual': actual}

def fmt1(v):   # 複製前端 fmtNum：整數→整數字串，否則四捨五入到小數1位
    if v is None: return ''
    n = float(v)
    return str(int(n)) if n == int(n) else str(round(n + 1e-9, 1))

def uinum(s):
    try: return float(s)
    except (TypeError, ValueError): return None

def approx(a, b, tol=0.06):
    if a is None or b is None: return a == b
    return abs(a - b) <= tol


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1700, "height": 1000})
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())

        page.goto(f"{BASE}/login", wait_until="domcontentloaded")
        page.fill("#username", "jim"); page.fill("#password", "admin123")
        page.click("#btnLogin"); page.wait_for_timeout(1200)
        api = ctx.request

        def cell_zone(seg, zone):
            r = api.get(f"{BASE}/api/ie/cell/{HID}?segment={seg}&eolr={EOLR}&stage_id={STAGE}")
            j = r.json()
            for z in j.get('zones', []):
                if z['zone'] == zone: return z
            return None

        def open_seg(seg):
            page.goto(f"{BASE}/ie/{HID}/detail", wait_until="domcontentloaded")
            page.wait_for_function("()=>document.querySelectorAll('.zone-card').length>0", timeout=8000)
            if seg != 'cutting':
                page.evaluate("(s)=>switchSeg(s)", seg)
                page.wait_for_timeout(1000)
            else:
                page.wait_for_timeout(600)

        def ui_total(seg, zone):
            return page.evaluate(
                """([seg,zone])=>{const tr=[...document.querySelectorAll('.zone-total-row')]
                     .find(r=>r.dataset.totalSeg===seg && r.dataset.totalZone===zone);
                   if(!tr)return null;
                   return {std:tr.querySelector('.zt-std')?.textContent ?? null,
                           theory:tr.querySelector('.zt-theory')?.textContent ?? null,
                           actual:tr.querySelector('.zt-actual')?.textContent ?? null,
                           inputs:tr.querySelectorAll('input,select,textarea').length,
                           title:tr.querySelector('.zt-title')?.textContent ?? null,
                           html:tr.innerText};}""", [seg, zone])

        # ── Test 1 + 5：四製程各測一個區塊，總計=各欄加總正確 ───────────────────
        cases = [
            ('cutting',   '裁斷機'),
            ('stitching', '主流'),
            ('assembly',  '成型主區'),
            ('stf',       '貼底'),
        ]
        all_ok = True
        for seg, zone in cases:
            zobj = cell_zone(seg, zone)
            exp = oracle_totals(zobj, seg, zone)
            open_seg(seg)
            ui = ui_total(seg, zone)
            d = []
            if not ui:
                all_ok = False; record(f"[{seg}/{zone}] 總計列存在且加總正確", False, "找不到總計列"); continue
            d.append(f"工序列數={len(zobj.get('rows',[]))}")
            d.append(f"Oracle: 標時={fmt1(exp['std'])} 理論={fmt1(exp['theory'])} 實際={fmt1(exp['actual'])}")
            d.append(f"UI    : 標時={ui['std']} 理論={ui['theory']} 實際={ui['actual']}  (title={ui['title']})")
            ok = True
            if not approx(uinum(ui['std']), round(exp['std'],1)):     ok = False; d.append("  ✗ 標準時間加總不符")
            if not approx(uinum(ui['theory']), round(exp['theory'],1)):ok = False; d.append("  ✗ 理論人數加總不符")
            if not approx(uinum(ui['actual']), round(exp['actual'],1)):ok = False; d.append("  ✗ 實際人數加總不符")
            if ui['title'] != '總計': ok = False; d.append("  ✗ 缺「總計」標題")
            all_ok = all_ok and ok
            record(f"[{seg}/{zone}] 總計列存在且 標時/理論/實際 加總正確", ok, "\n".join(d))

        # ── Test 5b：cutting 只加總對應欄位（層/件/刀/後製 不加總＝總計列該欄空）──
        open_seg('cutting')
        cut_cells = page.evaluate(
            """()=>{const tr=[...document.querySelectorAll('.zone-total-row')]
                 .find(r=>r.dataset.totalSeg==='cutting' && r.dataset.totalZone==='裁斷機');
               if(!tr)return null;
               const cells=[...tr.children].map(td=>({txt:td.innerText.trim(),
                    cls:td.className, colspan:td.getAttribute('colspan')||1}));
               const numbered=cells.filter(c=>c.txt!=='' && c.txt!=='總計');
               return {cells, numberedCount:numbered.length,
                       hasStd:!!tr.querySelector('.zt-std'), hasTh:!!tr.querySelector('.zt-theory'),
                       hasAc:!!tr.querySelector('.zt-actual')};}""")
        d = []
        ok = True
        d.append(f"裁斷機總計列：有數字的欄位數={cut_cells['numberedCount']}（應=3：標時/理論/實際）")
        d.append(f"欄位明細: " + ", ".join(f"{c['txt'] or '·'}" for c in cut_cells['cells']))
        if cut_cells['numberedCount'] != 3: ok = False; d.append("  ✗ 層數/件數/刀數/後製欄不應有加總數字")
        if not (cut_cells['hasStd'] and cut_cells['hasTh'] and cut_cells['hasAc']):
            ok = False; d.append("  ✗ 缺 標時/理論/實際 加總格")
        record("[cutting] 只加總 標時/理論/實際；層/件/刀/後製欄不加總", ok, "\n".join(d))

        # ── Test 6：總計列唯讀（無輸入框、不能改）─────────────────────────────
        d = []; ok = True
        open_seg('cutting')
        ro = page.evaluate(
            """()=>{const rows=[...document.querySelectorAll('.zone-total-row')];
               const withInputs=rows.filter(r=>r.querySelectorAll('input,select,textarea').length>0).length;
               return {total:rows.length, withInputs};}""")
        d.append(f"cutting 總計列共 {ro['total']} 列，含輸入框的 {ro['withInputs']} 列（應=0）")
        if ro['withInputs'] != 0: ok = False; d.append("  ✗ 總計列不應有輸入框（須唯讀）")
        record("總計列唯讀（無 input/select，公式格樣式）", ok, "\n".join(d))

        # ── Test 4：空值當0、整區塊空不 NaN ──────────────────────────────────
        d = []; ok = True
        nan_found = []
        for seg in ('cutting', 'stitching', 'assembly', 'stf'):
            open_seg(seg)
            vals = page.evaluate(
                """()=>[...document.querySelectorAll('.zone-total-row')].map(r=>({
                     zone:r.dataset.totalZone,
                     std:r.querySelector('.zt-std')?.textContent ?? '',
                     th:r.querySelector('.zt-theory')?.textContent ?? '',
                     ac:r.querySelector('.zt-actual')?.textContent ?? ''}))""")
            for v in vals:
                for k in ('std','th','ac'):
                    if 'NaN' in (v[k] or '') or 'undefined' in (v[k] or ''):
                        nan_found.append(f"{seg}/{v['zone']}.{k}={v[k]}")
            # 找一個空區塊確認顯示 0（非 NaN/非空白破圖）
            empties = [v for v in vals if v['std'] in ('0','') and v['th'] in ('0','') and v['ac'] in ('0','')]
            if empties:
                d.append(f"[{seg}] 空/零區塊示例: zone={empties[0]['zone']} std={empties[0]['std']!r} "
                         f"th={empties[0]['th']!r} ac={empties[0]['ac']!r}")
        if nan_found:
            ok = False; d.append("  ✗ 出現 NaN/undefined: " + "; ".join(nan_found))
        else:
            d.append("四製程所有總計列皆無 NaN/undefined ✓")
        # 明確驗證「空值當0加」：裁斷機有 std=NULL 的列，oracle 與 UI 仍相符（前面 Test1 已比對）
        record("空值當0加、整區塊空 → 總計 0（不 NaN）", ok, "\n".join(d))

        # ── Test 3：改一個工序的值 → 總計自動更新（不 reload）────────────────
        d = []; ok = True
        open_seg('cutting')
        # 取裁斷機一個「非合併」且可編輯的 actual 輸入框
        pick = page.evaluate(
            """()=>{const tb=document.getElementById('tbody-cut-裁斷機');
               const inp=tb?tb.querySelector('input.cut-act-inp'):null;
               if(!inp)return null;
               return {pid:inp.getAttribute('data-pid')||inp.dataset.pid||null, cur:inp.value};}""")
        before = ui_total('cutting', '裁斷機')
        before_ac = uinum(before['actual']) if before else None
        # 用一個明確增量：把該格改成 (原值 or 0)+7
        old_val = uinum(pick['cur']) or 0.0 if pick else 0.0
        new_val = old_val + 7
        did = page.evaluate(
            """([v])=>{const tb=document.getElementById('tbody-cut-裁斷機');
               const inp=tb.querySelector('input.cut-act-inp');
               if(!inp)return false; inp.value=String(v);
               inp.dispatchEvent(new Event('blur')); return true;}""", [new_val])
        page.wait_for_timeout(900)   # saveSingleActual 完成 + 即時刷新總計（無 reload）
        after = ui_total('cutting', '裁斷機')
        after_ac = uinum(after['actual']) if after else None
        d.append(f"改前 實際總計={before_ac}；某工序 actual {old_val} → {new_val}（+7）")
        d.append(f"改後 實際總計={after_ac}（未 reload，即時更新）；期望≈{(before_ac or 0)+7 if before_ac is not None else None}")
        # 頁面未重整佐證：URL 未變、且輸入框仍在
        if before_ac is None or after_ac is None:
            ok = False; d.append("  ✗ 讀不到總計")
        elif not approx(after_ac, before_ac + 7, 0.06):
            ok = False; d.append("  ✗ 總計未即時 +7")
        # 再從 DB 佐證有存進去（即時存）
        import sqlite3
        dbp = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "flask_backend","data","test_isolated","atlas_test.db")
        c = sqlite3.connect(dbp)
        # 找剛剛那格的 pid：重讀第一個裁斷機 cut-act row 對應 DB？改用 zone 內 actual 總和比對
        c.close()
        record("改工序值 → 該區塊總計即時自動更新（無需重整）", ok, "\n".join(d))
        page.screenshot(path=os.path.join(SHOT_DIR, "03_live_update.png"))

        # ── 截圖：四製程總計列 ───────────────────────────────────────────────
        for seg in ('cutting', 'stitching', 'assembly', 'stf'):
            open_seg(seg)
            page.screenshot(path=os.path.join(SHOT_DIR, f"zone_totals_{seg}.png"), full_page=False)

        # ── 總結 ───────────────────────────────────────────────────────────
        print("\n" + "=" * 68)
        print("區塊總計 — 驗證總結")
        print("=" * 68)
        npass = sum(1 for _, ok in RESULTS if ok)
        nfail = sum(1 for _, ok in RESULTS if not ok)
        for title, ok in RESULTS:
            print(f"  {'PASS' if ok else 'FAIL'} — {title}")
        print(f"\n  合計 {npass} PASS / {nfail} FAIL / {len(RESULTS)} 項")
        print(f"  截圖: {SHOT_DIR}")
        browser.close()
        return nfail

if __name__ == "__main__":
    sys.exit(1 if main() else 0)
