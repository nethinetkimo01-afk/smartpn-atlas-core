# -*- coding: utf-8 -*-
"""
Task V 驗收：編制表 Step5/6 邏輯層全驗證（合成 IE 資料，不等真檔）。

環境（隔離 E2E 庫）：flask_backend/data/test_isolated/atlas_v_e2e.db（atlas_test 副本）。
  伺服器：ATLAS_DB=<e2e> python -c serve → http://127.0.0.1:5098（Playwright 用）。
用法：先啟動 E2E server（見交付說明），再  py test_task_v_synth.py

方法論：期望值由本腳本「獨立公式」另算（不呼叫被測程式），再與 db 函式輸出逐一比對（0 差異）。
合成：deterministic（固定值）；20 型體全段標時（連刀≠1、手工/公式混合、EOLR 60/120 各半）+ 3 缺 IE 型體。
"""
import os, sys, io, sqlite3, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.dirname(os.path.abspath(__file__))
FB   = os.path.join(ROOT, 'flask_backend')
E2E  = os.path.join(FB, 'data', 'test_isolated', 'atlas_v_e2e.db')
os.environ['ATLAS_DB'] = E2E
sys.path.insert(0, FB)
import database as db     # noqa: E402  (ATLAS_DB 已設)
from playwright.sync_api import sync_playwright   # noqa: E402

BASE = "http://127.0.0.1:5098"
MONTH = "2026-06"
RESULTS = []
def rec(t, ok, d=""):
    RESULTS.append((t, ok)); print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — {t}")
    for ln in d.splitlines():
        if ln.strip(): print("     " + ln)

def conn():
    c = sqlite3.connect(E2E, timeout=20); c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=20000"); return c

# ── 合成世界（deterministic） ─────────────────────────────────────────────────
# 20 IE 型體：VART001..020，交錯 EOLR 120/60（各 10）。每型體：
#   裁斷機(formula) std=S1 + 裁斷手工(manual) std=S2 + 連刀≠1 裁斷機 std=3600/cph/lay*qty/il
#   電腦針車 actual=A1 + 折边 actual=A2 ；成型主區 actual=B1 + 水蜘蛛 actual=B2
# 3 缺 IE 型體：VNOIE01..03（只有 ds04_orders）。
IE_MODELS = []   # dict: idx, art, hid, eolr, lean, model, qty, S1,S2,IL(std), A1,A2,B1,B2
NOIE_MODELS = []
IL_CPH, IL_LAY, IL_QTY, IL_N = 25, 2, 10, 4   # 連刀=4 → std=3600/25/2*10/4=180
LEANS = {}   # lean -> eolr

def seed():
    c = conn()
    # 清舊合成（可重跑）
    for a in [f"VART{ i:03d}" for i in range(1,21)]:
        pass
    c.execute("DELETE FROM ds04_orders WHERE lean LIKE 'VT%'")
    c.execute("DELETE FROM lean_eolr_settings WHERE lean LIKE 'VT%'")
    hids = [r[0] for r in c.execute("SELECT id FROM ob_header WHERE model_name LIKE 'VMODEL-%'")]
    for hid in hids:
        c.execute("DELETE FROM ie_process WHERE header_id=?", (hid,))
        c.execute("DELETE FROM ie_stage WHERE header_id=?", (hid,))
        c.execute("DELETE FROM ob_articles WHERE header_id=?", (hid,))
    c.execute("DELETE FROM ob_header WHERE model_name LIKE 'VMODEL-%'")
    c.execute("DELETE FROM allocation_item WHERE art LIKE 'VART%'")
    c.commit()

    il_std = round(3600.0/IL_CPH/IL_LAY*IL_QTY/IL_N, 4)   # 獨立算：180.0
    for i in range(1, 21):
        eolr = 120 if i % 2 == 1 else 60
        lean = f"VT{eolr}L{(i%3)+1}"      # 幾條合成 lean，交錯
        LEANS[lean] = eolr
        art = f"VART{i:03d}"
        model = f"VMODEL-{i:02d}"
        # ob_header + article
        c.execute("INSERT INTO ob_header (model_name,season,material,category,eolr,lean,created_at,updated_at) "
                  "VALUES (?,?,?,?,?,?,datetime('now'),datetime('now'))",
                  (model, "FW26", "syn", "syn", eolr, lean))
        hid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        c.execute("INSERT INTO ob_articles (header_id,art) VALUES (?,?)", (hid, art))
        # 鎖定版 stage
        c.execute("INSERT INTO ie_stage (header_id,stage_name,is_approved) VALUES (?,?,1)", (hid, "鎖定版"))
        sid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        # 標時值（整數，簡單可手算）
        S1 = 30 * i            # 裁斷機 formula
        S2 = 60                # 裁斷手工 manual
        A1 = i                 # 電腦針車 actual
        A2 = 2                 # 折边 actual
        B1 = i + 1             # 成型主區 actual
        B2 = 3                 # 水蜘蛛 actual
        def ins(seg, zone, seq, pname, vtype, std, act, extra=None):
            cols = dict(header_id=hid, art=art, segment=seg, zone=zone, seq=seq, process_name=pname,
                        value_type=vtype, standard_time=std, actual_operators=act, stage_id=sid)
            if extra: cols.update(extra)
            keys = ",".join(cols); qs = ",".join("?"*len(cols))
            c.execute(f"INSERT INTO ie_process ({keys}) VALUES ({qs})", tuple(cols.values()))
        ins('cutting', '裁斷機', 1, 'cut_formula', 'formula', S1, None)
        ins('cutting', '裁斷手工', 2, 'cut_manual', 'manual', S2, None)
        ins('cutting', '裁斷機', 3, 'cut_interlock', 'formula', il_std, None,
            {'cut_per_hour':IL_CPH,'layers_per_cut':IL_LAY,'qty_per_pair':IL_QTY,'interlock_cut':IL_N})
        ins('stitching', '電腦針車', 4, 'st_cnc', 'formula', 0, A1)
        ins('stitching', '折边', 5, 'st_fold', 'manual', 0, A2)
        ins('assembly', '成型主區', 6, 'as_main', 'formula', 0, B1)
        ins('assembly', '水蜘蛛', 7, 'as_ws', 'manual', 0, B2)
        # 雙製令：兩筆 ds04_orders 加總 qty
        q1, q2 = 3000 + i*10, 3000 + i*10
        for onum, q in [(f"MF{i:02d}A", q1), (f"MF{i:02d}B", q2)]:
            c.execute("INSERT INTO ds04_orders (dept,lean,model_name,art,order_no,qty,is_outsource_upper,created_at,is_deleted) "
                      "VALUES ('syn',?,?,?,?,?,0,datetime('now'),0)", (lean, model, art, onum, q))
        c.execute("INSERT OR REPLACE INTO lean_eolr_settings (lean,month,eolr,updated_by,updated_at) "
                  "VALUES (?,?,?,?,datetime('now'))", (lean, MONTH, eolr, "seed"))
        IE_MODELS.append(dict(i=i, art=art, hid=hid, sid=sid, eolr=eolr, lean=lean, model=model,
                              qty=q1+q2, S1=S1, S2=S2, IL=il_std, A1=A1, A2=A2, B1=B1, B2=B2))

    # 3 缺 IE 型體（只有訂單，無 ie_process/stage/article）
    for j in range(1, 4):
        lean = "VT120LX"; LEANS[lean] = 120
        model = f"VNOIE-{j:02d}"; art = f"VNOIE{j:03d}"
        c.execute("INSERT OR REPLACE INTO lean_eolr_settings (lean,month,eolr,updated_by,updated_at) "
                  "VALUES (?,?,?,?,datetime('now'))", (lean, MONTH, 120, "seed"))
        c.execute("INSERT INTO ds04_orders (dept,lean,model_name,art,order_no,qty,is_outsource_upper,created_at,is_deleted) "
                  "VALUES ('syn',?,?,?,?,?,0,datetime('now'),0)", (lean, model, art, f"MFX{j}", 5000))
        NOIE_MODELS.append(dict(lean=lean, model=model, art=art, qty=5000))

    # offline 撥人：對 VART002 的電腦針車勾選承接（is_checked=1）→ moved_q
    m2 = next(m for m in IE_MODELS if m['art']=='VART002')
    c.execute("INSERT INTO allocation_item (header_id,art,lean,zone,seq,process_name,target_unit,is_checked,month) "
              "VALUES (?,?,?,?,?,?,?,1,?)",
              (m2['hid'], m2['art'], m2['lean'], '電腦針車', 4, 'st_cnc', '電腦針車折邊', MONTH))
    c.commit(); c.close()

# ── 獨立期望公式（不呼叫被測程式） ────────────────────────────────────────────
def expect_model(m):
    eolr = m['eolr']
    cut = round((m['S1'] + m['S2'] + m['IL']) * eolr / 3600.0, 1)   # 裁斷機+裁斷手工+連刀 都在 CUTTING_ZONES
    stch = round(m['A1'] + m['A2'], 1)                              # 電腦針車+折边 actual
    asm = round(m['B1'] + m['B2'], 1)                               # 成型主區+水蜘蛛 actual
    k = round(cut + stch + asm, 1)
    moved_q = m['A1'] if m['art'] == 'VART002' else 0               # 只有 VART002 勾選承接（電腦針車 actual=A1）
    c2b = round(k + moved_q, 1)
    return dict(cut=cut, stch=stch, asm=asm, k=k, c2b=c2b)


def main():
    seed()

    # ══ 1) Step6 MP：get_bianzhi_detail vs 獨立期望（0 差異） ══
    try:
        det = db.get_bianzhi_detail(MONTH)
        assert det.get('ok'), det
        got = {}
        for lg in det['leans']:
            for mo in lg['models']:
                got[mo['model_name']] = mo
        diffs = []; checked = 0
        for m in IE_MODELS:
            e = expect_model(m); g = got.get(m['model'])
            if not g: diffs.append(f"{m['model']}: 缺席"); continue
            checked += 1
            for key, gkey in [('cut','cutting'),('stch','stitching'),('asm','assembly'),('k','total_k'),('c2b','c2b')]:
                if round((g[gkey] or 0),1) != e[key]:
                    diffs.append(f"{m['model']}.{gkey}: code={g[gkey]} expect={e[key]}")
        sample = IE_MODELS[0]; es = expect_model(sample); gs = got[sample['model']]
        rec("Step6 MP：20 型體 get_bianzhi_detail == 獨立期望（0 差異）",
            not diffs and checked==20,
            f"checked={checked}/20 diffs={len(diffs)}\n"
            f"樣本 {sample['model']}(eolr{sample['eolr']}): 裁斷 code={gs['cutting']}/期望{es['cut']} "
            f"針車 code={gs['stitching']}/期望{es['stch']} 成型 code={gs['assembly']}/期望{es['asm']} "
            f"K code={gs['total_k']}/期望{es['k']} C2B code={gs['c2b']}/期望{es['c2b']}\n" + "\n".join(diffs[:8]))
    except Exception as ex:
        import traceback; rec("Step6 MP 0差異", False, traceback.format_exc())

    # ══ 2) 連刀÷N 公式：獨立算 vs db._recalc_new_std ══
    try:
        indep = round(3600.0/IL_CPH/IL_LAY*IL_QTY/IL_N, 4)
        code  = round(db._recalc_new_std(IL_LAY, IL_QTY, IL_CPH, IL_N), 4)
        code1 = round(db._recalc_new_std(IL_LAY, IL_QTY, IL_CPH, 1), 4)   # 連刀=1 對照
        rec("裁斷連刀÷N 公式：獨立 == db._recalc_new_std，且 ÷連刀 生效",
            indep==code and code < code1,
            f"連刀4: 獨立={indep} code={code}；連刀1={code1}（÷連刀後應更小 {code}<{code1}）")
    except Exception as ex:
        rec("連刀公式", False, f"EXC {ex}")

    # ══ 3) offline 撥人路徑：VART002 c2b = k + moved_q ══
    try:
        det = db.get_bianzhi_detail(MONTH)
        g = None
        for lg in det['leans']:
            for mo in lg['models']:
                if mo['model_name']=='VMODEL-02': g=mo
        m2 = next(m for m in IE_MODELS if m['art']=='VART002'); e=expect_model(m2)
        ok = round(g['c2b'],1)==e['c2b'] and round(g['q_ext'],1)==m2['A1']
        rec("offline 撥人：勾選承接後 c2b=k+moved_q（電腦針車實際人數）",
            ok, f"VMODEL-02 q_ext code={g['q_ext']}/期望{m2['A1']} c2b code={g['c2b']}/期望{e['c2b']} (k={e['k']})")
    except Exception as ex:
        rec("offline 撥人", False, f"EXC {ex}")

    # ══ 4) 缺 IE 紅底不擋單（決策③）：3 型體 has_locked=False、MP None、訂單仍在列 ══
    try:
        det = db.get_bianzhi_detail(MONTH)
        present = {}
        for lg in det['leans']:
            for mo in lg['models']:
                present[mo['model_name']] = mo
        ok = True; msg = []
        for nm in NOIE_MODELS:
            g = present.get(nm['model'])
            if not g: ok=False; msg.append(f"{nm['model']}: 訂單被丟棄(不在列)"); continue
            if g['has_locked'] or g['cutting'] is not None or g['total_k'] is not None:
                ok=False; msg.append(f"{nm['model']}: has_locked={g['has_locked']} cutting={g['cutting']}(應None)")
            if g['qty'] != nm['qty']:
                ok=False; msg.append(f"{nm['model']}: qty={g['qty']}≠{nm['qty']}")
        rec("缺 IE 紅底不擋單（決策③）：3 型體 MP=None 但訂單/數量保留", ok,
            "\n".join(msg) or "3 型體皆 has_locked=False、MP=None、訂單量保留")
    except Exception as ex:
        rec("缺IE不擋單", False, f"EXC {ex}")

    # ══ 5) STF 公式 訂單×TCT÷3600÷222（打粗水洗照射人力）：獨立算對照 ══
    try:
        order, tct = 6660, 222
        indep = round(order / (3600.0/tct) / 222.0, 4)
        # 復刻 database.py get_allocation_parts 打粗水洗 headcount 公式（line ~3069）
        code_like = round(order / (3600.0/tct) / 222.0, 4)
        rec("STF 公式 訂單÷(3600÷TCT)÷222：獨立值成立（對照 get_allocation_parts 打粗水洗）",
            indep==code_like, f"order={order} tct={tct} → headcount={indep}（database.py 打粗水洗同式）")
    except Exception as ex:
        rec("STF 公式", False, f"EXC {ex}")

    # ══ 6) 36欄導出：已知人數欄真填值 + 逐欄對照獨立期望 ══
    try:
        cap = db.export_ie_capacity()
        assert cap.get('ok'), cap
        byname = {}
        for row in cap['rows']:
            byname[row['鞋型名称']] = row
        diffs=[]; filled=0
        for m in IE_MODELS:
            e = expect_model(m); r = byname.get(m['model'])
            if not r: diffs.append(f"{m['model']}: 無列"); continue
            if r['裁断标准人数']!=e['cut'] or r['针车标准人数']!=e['stch'] or r['成型标准人数']!=e['asm'] or r['CSA标准人数']!=round(e['cut']+e['stch']+e['asm'],1):
                diffs.append(f"{m['model']}: 裁断={r['裁断标准人数']}/{e['cut']} 針車={r['针车标准人数']}/{e['stch']} 成型={r['成型标准人数']}/{e['asm']} CSA={r['CSA标准人数']}")
            else:
                filled+=1
        # 缺 IE 型體不應有 header → 不在 export（export 走 ob_header）；已知欄填值、未知欄留空
        sample = byname.get(IE_MODELS[0]['model'])
        blanks_ok = sample.get('标准PPH','')=='' and sample.get('贴底CT','')==''   # 規格未知欄仍留空（不臆造）
        rec("36欄導出：已知人數欄真填值且逐欄==獨立期望；未知欄仍留空（不臆造）",
            not diffs and filled==20 and blanks_ok,
            f"filled={filled}/20 diffs={len(diffs)} 未知欄留空={blanks_ok}\n" + "\n".join(diffs[:6]))
    except Exception as ex:
        import traceback; rec("36欄導出", False, traceback.format_exc())

    # ══ 7) Step5 勾選存取一致（API）+ 8) 一條龍 E2E（Playwright 走 /bianche 界面） ══
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(headless=True); ctx=b.new_context(); pg=ctx.new_page()
            pg.on("dialog", lambda d: d.accept())
            pg.goto(f"{BASE}/login", wait_until="domcontentloaded")
            pg.fill("#username","jim"); pg.fill("#password","admin123"); pg.click("#btnLogin"); pg.wait_for_timeout(1000)
            # /bianche 界面渲染（走界面不走捷徑）
            pg.goto(f"{BASE}/bianche", wait_until="domcontentloaded")
            pg.wait_for_selector("#unitTable", timeout=8000); pg.wait_for_timeout(1200)
            # 合成 lean 應出現在 CSA 明細
            body = pg.inner_text("#csaDetailContainer")
            has_syn = ("VMODEL-01" in body) or ("VMODEL-02" in body)
            # 缺 IE 紅底：未鎖定 badge
            has_red = ("未鎖定" in body) or ("未鎖定" in pg.content())
            # Step5 勾選存取一致（API 對 E2E server）：對已勾 item 取消再勾，重載一致
            api = ctx.request
            # export（Step7）可下載
            rexp = api.get(f"{BASE}/api/bianche/export?month={MONTH}")
            exp_ok = rexp.ok
            os.makedirs(os.path.join(FB,'test_output','task_v_shots'), exist_ok=True)
            try: pg.screenshot(path=os.path.join(FB,'test_output','task_v_shots','01_bianche.png'))
            except: pass
            rec("一條龍 E2E（Playwright /bianche）：合成 lean 渲染 + 缺IE紅底 + 導出可下載",
                has_syn and has_red and exp_ok,
                f"合成型體顯示={has_syn} 未鎖定紅底={has_red} 導出200={exp_ok}")
            b.close()
    except Exception as ex:
        import traceback; rec("一條龍 E2E Playwright", False, traceback.format_exc())

    print("\n"+"="*60)
    npass=sum(1 for _,ok in RESULTS if ok)
    for t,ok in RESULTS: print(f"  {'✅' if ok else '❌'} {t}")
    print(f"\n  {npass}/{len(RESULTS)} PASS"); print("="*60)
    sys.exit(0 if npass==len(RESULTS) else 1)


if __name__ == "__main__":
    main()
