# -*- coding: utf-8 -*-
"""
Task W 驗收：SmartPN 品牌端 V3 KPI Dashboard（43 號遺留，中樞代決執行）。

驗收：KPI 全由 MOCK_WORLD 推導、不含毛利率、遵守隱私（不露他方私密）、EN/ZH、
引導腳本+1 步、測試鉤子沿用、功能迴歸 v3 全函式（V1_PARITY 缺一即 FAIL）、0 pageerror。
用法：py test_task_w_dashboard.py（靜態檔，file://，無需 server）。
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

F = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs', 'preview', 'SMARTPN_DEMO_V3.html')
URL = 'file:///' + F.replace('\\', '/')
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_backend', 'test_output', 'task_w_shots')
os.makedirs(SHOT, exist_ok=True)

RESULTS = []
def rec(t, ok, d=""):
    RESULTS.append((t, ok)); print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — {t}")
    for ln in d.splitlines():
        if ln.strip(): print("     " + ln)

def expected_kpis(mw, acc_idx=0):
    acc = mw['accounts'][acc_idx]
    vis = [m for m in mw['materials'] if m['id'] in acc['visibleIds']]
    grants = sum(1 for m in vis if any(f.get('perm') == 'granted' for f in m.get('fields', [])))
    signed = sum(1 for b in mw['mappingBatches'] if b['status'] == 'signed')
    dpp = round(sum(m['dppComplete']/m['dppTotal'] for m in vis)/len(vis)*100) if vis else 0
    return dict(visible=len(vis), grants=grants, mappingSigned=signed,
                mappingTotal=len(mw['mappingBatches']),
                mappingPct=round(signed/len(mw['mappingBatches'])*100),
                evidence=len(mw['evidenceRecords']), dppReadiness=dpp)


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True); ctx = b.new_context(); pg = ctx.new_page()
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(URL, wait_until="domcontentloaded"); pg.wait_for_timeout(500)

        # ══ 1) Dashboard 入口 + 頁面顯示 ══
        try:
            has_btn = pg.query_selector("#nav-dashboard") is not None
            pg.click("#nav-dashboard"); pg.wait_for_timeout(300)
            active = pg.eval_on_selector("#page-dashboard", "e=>e.classList.contains('active')")
            ncards = pg.eval_on_selector_all("#dash-kpis > div", "e=>e.length")
            rec("Dashboard 入口 + 頁面顯示（5 KPI 卡）", has_btn and active and ncards==5,
                f"nav_btn={has_btn} page_active={active} kpi_cards={ncards}")
        except Exception as e:
            rec("Dashboard 入口", False, f"EXC {e}")

        # ══ 2) KPI 全由 MOCK_WORLD 推導（getDashboardKPIs == 獨立期望，Brand-A） ══
        try:
            mw = json.loads(pg.evaluate("JSON.stringify(window.MOCK_WORLD)"))
            got = pg.evaluate("window.getDashboardKPIs()")
            exp = expected_kpis(mw, 0)
            ok = all(got.get(k)==exp[k] for k in exp)
            rec("KPI 全由 MOCK_WORLD 推導（Brand-A == 獨立期望）", ok,
                f"code={got}\nexpect={exp}")
        except Exception as e:
            rec("KPI 推導", False, f"EXC {e}")

        # ══ 3) 帳號切換 A→B：可見材料數改變（選擇性開放） ══
        try:
            mw = json.loads(pg.evaluate("JSON.stringify(window.MOCK_WORLD)"))
            pg.evaluate("window.setAccount('B')"); pg.wait_for_timeout(200)
            gotB = pg.evaluate("window.getDashboardKPIs()")
            expB = expected_kpis(mw, 1)
            # UI 卡片第一張數字應等於 B 可見數
            firstCard = pg.eval_on_selector("#dash-kpis > div:first-child", "e=>e.innerText")
            ok = gotB['visible']==expB['visible'] and str(expB['visible']) in firstCard and expB['visible']!=expected_kpis(mw,0)['visible']
            pg.evaluate("window.setAccount('A')"); pg.wait_for_timeout(150)
            rec("帳號切換 A→B：可見材料數依 MOCK_WORLD 改變", ok,
                f"B visible code={gotB['visible']} expect={expB['visible']}；A={expected_kpis(mw,0)['visible']}")
        except Exception as e:
            rec("帳號切換", False, f"EXC {e}")

        # ══ 4) EN/ZH 切換 ══
        try:
            pg.click("#nav-dashboard"); pg.wait_for_timeout(150)
            en = pg.eval_on_selector("#dash-kpis", "e=>e.innerText")
            pg.evaluate("window.setLang('zh')"); pg.wait_for_timeout(250)
            zh = pg.eval_on_selector("#dash-kpis", "e=>e.innerText")
            ok = ('可見材料數' in zh) and ('Materials visible' in en) and (en!=zh)
            pg.evaluate("window.setLang('en')"); pg.wait_for_timeout(150)
            rec("EN/ZH 雙語（Dashboard 標籤切換）", ok, f"en有'Materials visible'={('Materials visible' in en)} zh有'可見材料數'={('可見材料數' in zh)}")
        except Exception as e:
            rec("EN/ZH", False, f"EXC {e}")

        # ══ 5) 不含毛利率 + 不露他方私密 ══
        try:
            pg.evaluate("window.setAccount('A')"); pg.click("#nav-dashboard"); pg.wait_for_timeout(200)
            txt = pg.eval_on_selector("#page-dashboard", "e=>e.innerText")
            # 不含毛利率＝KPI 卡片(#dash-kpis)無毛利/margin 指標（免疫語揭露 note 不算）
            kpis_txt = pg.eval_on_selector("#dash-kpis", "e=>e.innerText")
            no_margin = ('毛利' not in kpis_txt) and ('margin' not in kpis_txt.lower())
            # 不出現他方私密：evidence 對手方名（Factory Group B / Brand-C）與私密欄位值不得列出
            mw = json.loads(pg.evaluate("JSON.stringify(window.MOCK_WORLD)"))
            leak = any(rec_.get('party','') in txt for rec_ in mw['evidenceRecords'] if 'Brand-A' not in rec_.get('party',''))
            priv_vals = [f['v'] for m in mw['materials'] for f in m.get('fields',[]) if f.get('perm')=='private']
            leak_priv = any(v in txt for v in priv_vals if v)
            rec("不含毛利率 + 不露他方私密（僅彙總數）", no_margin and not leak and not leak_priv,
                f"no_margin={no_margin} 他方名洩露={leak} 私密值洩露={leak_priv}")
        except Exception as e:
            rec("隱私/毛利率", False, f"EXC {e}")

        # ══ 6) 引導腳本 +1 步（6 步，含 Dashboard） ══
        try:
            pg.evaluate("startGuide()"); pg.wait_for_timeout(150)
            total = pg.evaluate("GUIDE.length")
            head = pg.eval_on_selector("#guideOv", "e=>e.innerText")
            pg.evaluate("endGuide()")
            has_dash_step = any(('Dashboard' in s.get('en','')) or ('Dashboard' in s.get('zh','')) for s in pg.evaluate("GUIDE"))
            rec("引導腳本 +1 步（6 步，含 Dashboard）", total==6 and ('1/6' in head) and has_dash_step,
                f"steps={total} 首步標示={'1/6' in head} 含Dashboard步={has_dash_step}")
        except Exception as e:
            rec("引導腳本", False, f"EXC {e}")

        # ══ 7) 功能迴歸 v3 全函式（V1_PARITY 缺一即 FAIL）+ 測試鉤子 ══
        try:
            missing = pg.evaluate("window.V1_PARITY.filter(fn=>typeof window[fn]!=='function' && typeof eval(fn)!=='function')")
            hooks = pg.evaluate("['MOCK_WORLD','setAccount','getVisibleMaterials','setLang','V1_PARITY','getDashboardKPIs'].filter(h=>window[h]===undefined)")
            rec("功能迴歸 v3 全函式（V1_PARITY 0 缺）+ 測試鉤子沿用", not missing and not hooks,
                f"V1_PARITY missing={missing} hooks_missing={hooks}")
        except Exception as e:
            # eval(fn) 在 page context 可能對某些名不可及；改用更保守檢查
            try:
                missing = pg.evaluate("window.V1_PARITY.filter(fn=>{try{return typeof eval(fn)!=='function'}catch(e){return true}})")
                hooks = pg.evaluate("['MOCK_WORLD','setAccount','getVisibleMaterials','setLang','V1_PARITY','getDashboardKPIs'].filter(h=>window[h]===undefined)")
                rec("功能迴歸 v3 全函式（V1_PARITY 0 缺）+ 測試鉤子沿用", not missing and not hooks,
                    f"V1_PARITY missing={missing} hooks_missing={hooks}")
            except Exception as e2:
                rec("功能迴歸 V1_PARITY", False, f"EXC {e2}")

        # ══ 8) 0 pageerror（全程亂點 dashboard/搜尋/帳號切換） ══
        try:
            for act in ["showPage('search')","showPage('dashboard')","setAccount('B')","showPage('dashboard')",
                        "setAccount('A')","showPage('home')","showPage('dashboard')","toggleLang()","toggleLang()"]:
                pg.evaluate(act); pg.wait_for_timeout(80)
            try: pg.screenshot(path=os.path.join(SHOT,'01_dashboard.png'))
            except: pass
            rec("全程操作 0 pageerror", len(errs)==0, f"pageerrors={errs[:3]}")
        except Exception as e:
            rec("0 pageerror", False, f"EXC {e}")

        b.close()

    print("\n"+"="*60)
    npass = sum(1 for _,ok in RESULTS if ok)
    for t,ok in RESULTS: print(f"  {'✅' if ok else '❌'} {t}")
    print(f"\n  {npass}/{len(RESULTS)} PASS"); print("="*60)
    sys.exit(0 if npass==len(RESULTS) else 1)


if __name__ == "__main__":
    main()
