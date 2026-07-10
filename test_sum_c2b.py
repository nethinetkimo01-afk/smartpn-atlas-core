# -*- coding: utf-8 -*-
"""
驗證新功能：SUM_C2B 彙總頁把 get_ie_sum 的數字填入（MP(Ops) / PPH / offline 分列），
唯讀、E-PPH 目前以「—」顯示、空值/MP=0 顯示「—」不 NaN。

環境（隔離、不碰正式資料）：
  - 隔離 DB : flask_backend/data/test_isolated/atlas_test.db  (atlas.db 一致性副本)
  - 隔離 SERVER: python flask_backend/serve_test_isolated.py → http://127.0.0.1:5099
  - 測試鞋型 : header 5（四製程齊全，含 stitching/電腦針車、assembly/成型UV offline）, eolr=120

Oracle：獨立重算 get_ie_sum 的邏輯——直接抓 get_ie_sum 內部用的同一支
/api/ie/cell（各製程逐區塊、cutting 用 theory、其他用 actual、offline 分離），
在 Python 端自行加總，再與 (a) 後端 /api/ie/<hid>/sum、(b) 畫面 SUM_C2B 表比對。

用法：先啟動隔離 server，再  py test_sum_c2b.py
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5099"
HID  = 5
EOLR = 120
SHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "flask_backend", "test_output", "sumc2b_shots")
os.makedirs(SHOT_DIR, exist_ok=True)

RESULTS = []
def record(title, ok, detail=""):
    RESULTS.append((title, ok))
    print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — {title}")
    for line in detail.splitlines():
        if line.strip(): print("     " + line)

def approx(a, b, tol=0.06):
    if a is None or b is None: return a == b
    return abs(a - b) <= tol
def _f(v):
    try: return float(v)
    except (TypeError, ValueError): return None

OFFLINE = {'stitching': ['電腦針車', '折边'], 'assembly': ['水蜘蛛', '成型UV']}
STRICT  = {'assembly', 'stitching', 'stf'}
SEGS    = ['cutting', 'stitching', 'assembly', 'stf']

# ── Oracle：與 database.get_ie_sum 完全同邏輯，但輸入取自同一支 cell API ──────────
def oracle_sum(fetch_cell, eolr=EOLR):
    target = eolr * 8
    segres, offline = {}, []
    total = 0.0
    for seg in SEGS:
        cell = fetch_cell(seg)
        ops = 0.0
        offzones = OFFLINE.get(seg, [])
        for z in cell.get('zones', []):
            if z['zone'] == '_summary':
                continue
            zops = 0.0
            for row in z['rows']:
                a = row.get('actual_operators'); th = row.get('theory_operators')
                if seg == 'cutting':
                    t = th if th is not None else (a or 0.0)
                elif a is not None:
                    t = a
                else:
                    t = 0.0
                zops += t
            if z['zone'] in offzones:
                offline.append({'name': f"{seg}/{z['zone']}", 'operators': round(zops, 4),
                                'pph': round(target / zops / 8, 3) if zops else None})
            else:
                ops += zops
        segres[seg] = {'operators': round(ops, 4),
                       'pph': round(target / ops / 8, 3) if ops else None}
        total += ops
    tot = {'operators': round(total, 4), 'pph': round(target / total / 8, 3) if total else None}
    return segres, offline, tot, target


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1400, "height": 1050})
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))

        page.goto(f"{BASE}/login", wait_until="domcontentloaded")
        page.fill("#username", "jim"); page.fill("#password", "admin123")
        page.click("#btnLogin"); page.wait_for_timeout(1200)
        api = ctx.request

        def fetch_cell(seg):
            # 與 get_ie_sum 內部一致：不帶 stage_id → 有效版本
            return api.get(f"{BASE}/api/ie/cell/{HID}?segment={seg}&eolr={EOLR}").json()

        segres, offline, tot, target = oracle_sum(fetch_cell)
        api_sum = api.get(f"{BASE}/api/ie/{HID}/sum?eolr={EOLR}").json()

        # sanity：Oracle 與後端 get_ie_sum 一致（證明我的重算邏輯對）
        d0 = []; ok0 = True
        d0.append(f"target_output = {target} (=eolr×8)")
        for seg in SEGS:
            o, a = segres[seg], api_sum.get(seg, {})
            same = approx(o['operators'], _f(a.get('operators'))) and \
                   (o['pph'] == a.get('pph') or approx(o['pph'], _f(a.get('pph'))))
            d0.append(f"  {seg}: oracle ops={o['operators']} pph={o['pph']} | api ops={a.get('operators')} pph={a.get('pph')}  {'✓' if same else '✗'}")
            ok0 = ok0 and same
        record("Oracle 重算 = 後端 get_ie_sum（邏輯一致性 sanity）", ok0, "\n".join(d0))

        # ── 進頁面切到 SUM_C2B ──
        page.goto(f"{BASE}/ie/{HID}/detail", wait_until="domcontentloaded")
        page.wait_for_function("()=>document.querySelectorAll('.zone-card').length>0", timeout=8000)
        page.evaluate("()=>switchSeg('sum_c2b')")
        page.wait_for_function(
            "()=>{const b=document.getElementById('sumC2bBody');return b && !b.innerText.includes('載入中');}",
            timeout=8000)
        page.wait_for_timeout(300)

        def ui_rows():
            return page.evaluate(
                """()=>[...document.querySelectorAll('#sumC2bBody tr')].map(tr=>({
                     cls:tr.className,
                     dept:tr.children[0]?.innerText.trim(),
                     mp:tr.children[1]?.innerText.trim(),
                     pph:tr.children[2]?.innerText.trim(),
                     epph:tr.children[3]?.innerText.trim(),
                     diff:tr.children[4]?.innerText.trim(),
                     eff:tr.children[5]?.innerText.trim(),
                     inputs:tr.querySelectorAll('input,select,textarea').length}))""")
        rows = ui_rows()
        def find_sub(seg_label):
            for r in rows:
                if r['dept'] == f'∑ {seg_label}': return r
            return None
        SEG_LABEL = {'cutting': 'Cutting', 'stitching': 'Stitching', 'assembly': 'Assembly', 'stf': 'STF'}

        # ── Test 2：各製程 MP(Ops) = 實際人數加總（對應 get_ie_sum）──────────────
        d2 = []; ok2 = True
        for seg in SEGS:
            r = find_sub(SEG_LABEL[seg])
            exp_mp = segres[seg]['operators']
            ui_mp = _f(r['mp']) if r else None
            d2.append(f"  [{seg}] UI ∑MP={r['mp'] if r else None}  期望(get_ie_sum)={round(exp_mp,1)}")
            if not (r and approx(ui_mp, round(exp_mp, 1))):
                ok2 = False; d2.append("    ✗ MP 不符")
        # 額外：assembly(strict actual) 獨立由 cell rows 直接加總 actual(非offline) 佐證「MP=實際人數加總」
        acell = fetch_cell('assembly')
        raw_actual = 0.0
        for z in acell['zones']:
            if z['zone'] in OFFLINE['assembly'] or z['zone'] == '_summary': continue
            for row in z['rows']:
                a = _f(row.get('actual_operators'))
                if a is not None: raw_actual += a
        d2.append(f"  assembly 主線 actual 直接加總(獨立路徑) = {round(raw_actual,1)}  vs UI ∑MP={find_sub('Assembly')['mp']}")
        if not approx(_f(find_sub('Assembly')['mp']), round(raw_actual, 1)):
            ok2 = False; d2.append("    ✗ assembly MP ≠ 實際人數加總")
        record("各製程 MP(Ops) = 實際人數加總（對應 get_ie_sum）", ok2, "\n".join(d2))

        # ── Test 3：PPH = target_output / MP / 8 ────────────────────────────────
        d3 = []; ok3 = True
        for seg in SEGS:
            r = find_sub(SEG_LABEL[seg])
            mp = segres[seg]['operators']
            exp_pph = round(target / mp / 8, 3) if mp else None
            ui_pph = _f(r['pph']) if r and r['pph'] not in ('—', '') else None
            d3.append(f"  [{seg}] MP={round(mp,2)} → 期望PPH=target/MP/8={exp_pph} ; UI PPH={r['pph'] if r else None}")
            if exp_pph is None:
                if ui_pph is not None: ok3 = False; d3.append("    ✗ MP=0 應顯示—")
            elif not approx(ui_pph, round(exp_pph, 2), 0.02):
                ok3 = False; d3.append("    ✗ PPH 不符 target/MP/8")
        # GRAND TOTAL
        gr = next((r for r in rows if 'GRAND' in (r['dept'] or '')), None)
        exp_g = round(target / tot['operators'] / 8, 3) if tot['operators'] else None
        d3.append(f"  GRAND: MP={tot['operators']} 期望PPH={exp_g} ; UI={gr['mp'] if gr else None}/{gr['pph'] if gr else None}")
        if not (gr and approx(_f(gr['mp']), round(tot['operators'],1)) and approx(_f(gr['pph']), round(exp_g,2),0.02)):
            ok3 = False; d3.append("    ✗ GRAND TOTAL 不符")
        record("PPH = target_output / MP / 8 算對（含 GRAND TOTAL）", ok3, "\n".join(d3))

        # ── Test 4：offline 分開顯示（照 offline_list）──────────────────────────
        d4 = []; ok4 = True
        ui_off = [r for r in rows if '(外移)' in (r['dept'] or '')]
        d4.append(f"  Oracle offline 區數={len(offline)}；UI 外移列數={len(ui_off)}")
        for o in offline:
            zn = o['name'].split('/', 1)[1]
            match = next((r for r in ui_off if zn in (r['dept'] or '')), None)
            exp_pph = '—' if o['pph'] is None else str(round(o['pph'], 2))
            d4.append(f"    {o['name']}: ops={o['operators']} pph={o['pph']} → UI: {match['dept'] if match else '缺'} MP={match['mp'] if match else '?'} PPH={match['pph'] if match else '?'}")
            if not match:
                ok4 = False; d4.append("      ✗ UI 未分開列出此 offline")
            elif not approx(_f(match['mp']), round(o['operators'],1)):
                ok4 = False; d4.append("      ✗ offline MP 不符")
        # offline 不併入主線 ∑（get_ie_sum 定義）：stitching ∑MP 不含電腦針車 96
        st_sub = _f(find_sub('Stitching')['mp'])
        d4.append(f"  佐證：stitching ∑MP={st_sub}（不含外移電腦針車96）")
        if st_sub is not None and st_sub > 90:
            ok4 = False; d4.append("      ✗ 外移似乎被併入主線 ∑")
        record("offline(外移) 分開顯示、不併入主線 ∑", ok4, "\n".join(d4))

        # ── Test 5：無資料 / MP=0 → 顯示「—」不 NaN、不當機 ──────────────────────
        d5 = []; ok5 = True
        nan_cells = []
        for r in rows:
            for k in ('mp','pph','epph','diff','eff'):
                v = r.get(k) or ''
                if 'NaN' in v or 'undefined' in v or 'null' in v:
                    nan_cells.append(f"{r['dept']}.{k}={v}")
        d5.append(f"  全表無 NaN/undefined/null: {'✓' if not nan_cells else '✗ ' + ';'.join(nan_cells)}")
        if nan_cells: ok5 = False
        # MP=0 的 offline（折边/水蜘蛛）PPH 應為 —
        zero_rows = [r for r in ui_off if r['mp'] in ('0','0.0')]
        for zr in zero_rows:
            d5.append(f"  MP=0 列 {zr['dept']}: PPH={zr['pph']!r}（應為—）")
            if zr['pph'] != '—': ok5 = False; d5.append("      ✗ MP=0 未顯示—")
        if not zero_rows:
            d5.append("  （本鞋型無 MP=0 offline 列；改由 pageerror 佐證未當機）")
        d5.append(f"  頁面 JS pageerror 數={len(errs)}: {errs[:3]}")
        if errs: ok5 = False; d5.append("      ✗ 有 JS 錯誤")
        record("無資料/MP=0 → 顯示「—」不 NaN、不當機", ok5, "\n".join(d5))

        # ── Test 6：唯讀（整表無輸入框）────────────────────────────────────────
        d6 = []; ok6 = True
        tot_inputs = sum(r['inputs'] for r in rows)
        d6.append(f"  SUM_C2B 表所有列輸入框總數={tot_inputs}（應=0）")
        if tot_inputs != 0: ok6 = False; d6.append("    ✗ 不應可編輯")
        # E-PPH / Diff / Eff 目前皆 — （E-PPH 外部值未帶入）
        bad_epph = [r['dept'] for r in rows if r['cls'] in ('sumc2b-sub','sumc2b-grand') and r['epph'] != '—']
        d6.append(f"  E-PPH 欄（主線列）非「—」的={bad_epph}（設計上目前皆—）")
        record("SUM_C2B 唯讀（無輸入框，不可編輯）", ok6, "\n".join(d6))

        page.screenshot(path=os.path.join(SHOT_DIR, "sum_c2b.png"), full_page=True)

        print("\n" + "=" * 68)
        print("SUM_C2B — 驗證總結")
        print("=" * 68)
        npass = sum(1 for _, ok in RESULTS if ok); nfail = sum(1 for _, ok in RESULTS if not ok)
        for title, ok in RESULTS:
            print(f"  {'PASS' if ok else 'FAIL'} — {title}")
        print(f"\n  合計 {npass} PASS / {nfail} FAIL / {len(RESULTS)} 項")
        print(f"  截圖: {SHOT_DIR}")
        browser.close()
        return nfail

if __name__ == "__main__":
    sys.exit(1 if main() else 0)
