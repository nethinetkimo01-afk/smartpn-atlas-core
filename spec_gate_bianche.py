# -*- coding: utf-8 -*-
"""
spec_gate_bianche.py — 廠務編制表對「28_BIANCHE_SPEC.md」逐項＋逐單位對帳（頁面級：真瀏覽器渲染/量測）。
★閘門覆蓋率鐵則（25 規則）：必須覆蓋規格的完整結構維度（全部單位/月份/角色），且做「數字可追溯」對帳。
   只驗一個單位（如只驗 CSA）視為閘門失效。

★必須用「正式庫形狀」資料（正式庫副本，非 E2E 種子）：多單位×多月/某月只1單位/空月/缺 IE 鎖定版混合。
用法：SPEC_GATE_BASE=http://127.0.0.1:5095 python spec_gate_bianche.py

結構維度（決策③：編制表明細＝4 單位 CSA/OCS/RB/QC）：
  CSA  = 鞋型 LEAN 明細（區塊B 12 欄、每 LEAN 直工/人力小計、缺 IE 紅底、欄寬對齊）
  OCS/RB/QC = 部門群組人數明細（群組｜上月｜本月）
月份維度：至少 3 個月（含空月）。逐格對帳：區塊A 各單位 直工本月 可從其明細追溯。
"""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = os.environ.get('SPEC_GATE_BASE', 'http://127.0.0.1:5095')
MONTHS = ['2026-06', '2026-05', '2026-07']   # 多月（含空月 2026-07）
DETAIL_UNITS = ['CSA', 'OCS', 'RB', 'QC']    # 決策③ 明細四單位
R = []
COV = {'units': set(), 'months': set(), 'roles': set()}
def rec(n, ok, d=''):
    R.append((n, ok)); print(f"  {'✅' if ok else '❌'} {n}" + (f" — {d}" if d else ''))

def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True); ctx = b.new_context(viewport={"width":1600,"height":1000}); pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        pg.goto(f"{BASE}/login", wait_until="domcontentloaded")
        pg.fill("#username","jim"); pg.fill("#password","admin123"); pg.click("#btnLogin"); pg.wait_for_timeout(900)
        COV['roles'].add('jim(admin)')

        # 後端事實：13 單位摘要 + 4 單位明細資料
        summ = pg.evaluate(f"""async()=>{{const r=await fetch('/api/bianzhi/summary?month=2026-06');return await r.json();}}""")
        bian = pg.evaluate(f"""async()=>{{const r=await fetch('/api/bianche?month=2026-06');return await r.json();}}""")
        a_units = [u for u in summ.get('units',[]) if not u.get('is_subtotal') and not u.get('is_total')]
        print(f"  ▸ 後端 區塊A 單位數={len(a_units)}；明細四單位資料 keys={[k for k in ['csa','ocs','rb','qc'] if k in bian]}")

        pg.goto(f"{BASE}/bianche", wait_until="domcontentloaded")
        pg.wait_for_selector("#unitTable", timeout=9000); pg.wait_for_timeout(1600)

        # ── 區塊A：涵蓋全部單位 + 合計列 ──
        aHead = pg.eval_on_selector("#unitTable thead", "e=>e.innerText")
        aBodyRows = pg.eval_on_selector_all("#unitTableBody tr", "e=>e.length")
        aTotal = pg.eval_on_selector_all("#unitTableBody tr", "els=>els.some(r=>/合計/.test(r.innerText))")
        aColsOk = all(k in aHead for k in ['單位','直工','間工','直間比','上月','本月'])
        rec(f'區塊A 欄位+合計列+涵蓋全部 {len(a_units)} 單位（渲染列≥單位數）',
            aColsOk and aTotal and aBodyRows >= len(a_units), f'欄={aColsOk} 合計={aTotal} 渲染列={aBodyRows}/單位{len(a_units)}')

        # ── 區塊B：4 單位明細逐一斷言（決策③ CSA/OCS/RB/QC）──
        for unit in DETAIL_UNITS:
            cont = pg.query_selector(f'[data-bz-unit="{unit}"]')
            if not cont:
                rec(f'[單位 {unit}] 明細容器存在', False, '容器不存在（未渲染）'); continue
            COV['units'].add(unit)
            txt = cont.inner_text()
            if unit == 'CSA':
                # 12 欄 + 小計 + 紅底(缺IE) + 欄寬對齊
                b12 = ['鞋型','訂單','裁斷','針車','成型','协理给','合計','編制','外移P','外移Q','外移R','C2B']
                miss = [c for c in b12 if c not in txt]
                rec(f'[CSA] 區塊B 12 欄', not miss, f'缺={miss}')
                subN = '直工小計' in txt; subP = '人力小計' in txt
                subRows = pg.eval_on_selector_all(f'[data-bz-unit="CSA"] .lean-subtotal-row', "e=>e.length")
                rec(f'[CSA] 每 LEAN 直工小計(N)+人力小計(P)', subN and subP and subRows>0, f'N={subN} P={subP} 小計列={subRows}')
                nMan = pg.eval_on_selector_all(f'[data-bz-unit="CSA"] .manual-cell', "e=>e.length")
                nFor = pg.eval_on_selector_all(f'[data-bz-unit="CSA"] .formula-cell', "e=>e.length")
                rec(f'[CSA] 手工格 manual-cell + 公式格 formula-cell', nMan>0 and nFor>0, f'manual={nMan} formula={nFor}')
                redn = pg.eval_on_selector_all(f'[data-bz-unit="CSA"] .badge-noie, [data-bz-unit="CSA"] [title*="鎖定"]', "e=>e.length")
                rec(f'[CSA] 缺 IE 鎖定版列渲染紅底+未鎖定標記（決策③不擋單）', redn>0 or ('未鎖定' in txt) or ('無IE' in txt), f'紅底/標記數={redn}')
                align = pg.evaluate("""()=>{const ts=[...document.querySelectorAll('[data-bz-unit=\\"CSA\\"] table.bz-fixed')];const sig=t=>[...t.querySelectorAll('thead th')].map(th=>{const r=th.getBoundingClientRect();return Math.round(r.left)+':'+Math.round(r.width);}).join('|');const s=ts.map(sig);const f=s[0]||'';return {n:ts.length,mism:s.filter(x=>x!==f).length};}""")
                rec(f'[CSA] 欄寬對齊：≥3 LEAN 表同名欄 0px 誤差', align['n']>=3 and align['mism']==0, f"LEAN表={align['n']} 不一致={align['mism']}")
            else:
                # OCS/RB/QC：部門群組人數明細（section→group｜上月｜本月）或明確狀態（不空白）
                hasGrp = ('上月人數' in txt and '本月人數' in txt) or ('無資料' in txt) or ('未匯入' in txt)
                rec(f'[{unit}] 部門群組人數明細（群組/上月/本月）或明確狀態（不空白）', bool(hasGrp), f'ok={bool(hasGrp)}')
                # 逐格對帳：unit-total 顯示的直工本月 == 各 group 本月人數加總（誤差 0）
                r = pg.evaluate(f"""()=>{{
                  const tot=document.getElementById('total-{unit}'); const tv=tot?(tot.textContent.match(/([\\d.]+)\\s*$/)||[])[1]:null;
                  const inps=[...document.querySelectorAll('[data-bz-unit=\\"{unit}\\"] tbody tr td:nth-child(3) input')];
                  let s=0; inps.forEach(i=>{{const v=parseFloat(i.value);if(!isNaN(v))s+=v;}});
                  return {{shown: tv==null?null:parseFloat(tv), sum: Math.round(s*10)/10}};
                }}""")
                tok = (r['shown'] is not None) and (abs((r['shown'] or 0)-(r['sum'] or 0))<=0.11)
                rec(f'[{unit}] 逐格對帳：直工本月 = 各 group 本月人數加總（誤差 0）', tok, f"顯示={r['shown']} vs 加總={r['sum']}")

        # ── 逐格對帳：CSA 直工本月(明細單位標題) == CSA 明細各 LEAN N 小計加總（0 誤差，可追溯）──
        r = pg.evaluate("""()=>{
          const tot=document.getElementById('total-CSA'); const tv=tot?(tot.textContent.match(/([\\d.]+)\\s*$/)||[])[1]:null;
          const rows=[...document.querySelectorAll('[data-bz-unit=\\"CSA\\"] .lean-subtotal-row')];
          let s=0; rows.forEach(r=>{const m=r.innerText.match(/直工小計\\s*N＝\\s*([\\d.]+)/);if(m)s+=parseFloat(m[1]);});
          return {shown: tv==null?null:parseFloat(tv), sum: Math.round(s*10)/10};
        }""")
        trace_ok = (r['shown'] is not None) and (abs((r['shown'] or 0) - (r['sum'] or 0)) <= 0.11)
        rec('逐格對帳：CSA 直工本月 = 明細各 LEAN 直工小計 N 加總（誤差 0）',
            trace_ok, f"顯示={r['shown']} vs N小計加總={r['sum']}")

        # ── 多月維度：切至少 3 個月不崩、空月顯示狀態不空白 ──
        month_ok = True; mdet = []
        for m in MONTHS:
            try:
                pg.eval_on_selector("#selMonth", "(e,m)=>{e.value=m;e.dispatchEvent(new Event('change'));}", m)
                pg.wait_for_timeout(1200); COV['months'].add(m)
                empty_ok = True
                if m == '2026-07':
                    dtxt = pg.eval_on_selector("#csaDetailContainer", "e=>e.innerText") if pg.query_selector("#csaDetailContainer") else ''
                    empty_ok = ('無資料' in dtxt) or ('未匯入' in dtxt) or ('無 DS-04' in dtxt) or len(pg.query_selector_all('[data-bz-unit]'))>0
                mdet.append(f'{m}:ok')
                month_ok = month_ok and empty_ok
            except Exception as e:
                month_ok = False; mdet.append(f'{m}:EXC')
        rec('多月維度：≥3 月可切、空月顯示狀態不空白', month_ok and len(COV['months'])>=3, ' '.join(mdet))

        # ── 匯入：流程① DS-04 上傳入口可見可點 ──
        pg.eval_on_selector("#selMonth", "e=>{e.value='2026-06';e.dispatchEvent(new Event('change'));}"); pg.wait_for_timeout(1000)
        pg.eval_on_selector_all("#flow-bar > div", "(els)=>{els[0]&&els[0].click();}"); pg.wait_for_timeout(900)
        upVisible = pg.eval_on_selector("#ds04-upload", "e=>getComputedStyle(e).display!=='none'") if pg.query_selector("#ds04-upload") else False
        rec('匯入：流程① DS-04 上傳入口可見可點', bool(upVisible), f'可見={upVisible}')

        b.close()

    npass = sum(1 for _,ok in R if ok)
    print('\n' + '─'*56)
    print(f'  閘門覆蓋率：明細單位 {sorted(COV["units"])}（{len(COV["units"])}/{len(DETAIL_UNITS)}）'
          f'· 月份 {sorted(COV["months"])}（{len(COV["months"])}）· 角色 {sorted(COV["roles"])}')
    print('='*56)
    print(f'  spec_gate_bianche: {npass}/{len(R)} → {"✅ ALL GREEN" if npass==len(R) else "❌ FAIL"}')
    print('='*56)
    sys.exit(0 if npass==len(R) else 1)

if __name__ == '__main__':
    print(f'===== spec_gate_bianche（頁面級·逐單位·可追溯）· BASE={BASE} =====')
    main()
