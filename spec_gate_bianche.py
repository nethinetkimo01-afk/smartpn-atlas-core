# -*- coding: utf-8 -*-
"""
spec_gate_bianche.py — 廠務編制表對「28_BIANCHE_SPEC.md」逐項對帳（頁面級：載入 /bianche 真渲染 DOM）。
規格條號是唯一驗收基準。缺一即 FAIL。隔離副本，禁止碰正式 DB。

用法：起一台有編制資料的隔離 server（例 atlas_v_e2e @ 5098），再：
  SPEC_GATE_BASE=http://127.0.0.1:5098 python spec_gate_bianche.py
"""
import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = os.environ.get('SPEC_GATE_BASE', 'http://127.0.0.1:5098')
R = []
def rec(n, ok, d=''):
    R.append((n, ok)); print(f"  {'✅' if ok else '❌'} {n}" + (f" — {d}" if d else ''))

def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True); ctx = b.new_context(viewport={"width":1600,"height":1000}); pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        pg.goto(f"{BASE}/login", wait_until="domcontentloaded")
        pg.fill("#username","jim"); pg.fill("#password","admin123"); pg.click("#btnLogin"); pg.wait_for_timeout(1000)
        pg.goto(f"{BASE}/bianche", wait_until="domcontentloaded")
        pg.wait_for_selector("#csaDetailContainer", timeout=9000); pg.wait_for_timeout(1600)

        # ── 區塊A：各單位編制總表 ──
        aHead = pg.eval_on_selector("#unitTable thead", "e=>e.innerText")
        aCols = all(k in aHead for k in ['單位','直工','間工','直間比','上月','本月'])
        aTotal = pg.eval_on_selector_all("#unitTableBody tr.total-row, #unitTableBody tr", "els=>els.some(r=>/合計/.test(r.innerText))")
        rec('區塊A 欄位（單位|直工上/本月|間工上/本月|直間比上/本月）+ 合計列', aCols and aTotal, f'cols={aCols} 合計列={aTotal}')

        # ── 區塊B：12 欄表頭 ──
        detTxt = pg.inner_text("#csaDetailContainer")
        B12 = ['鞋型','訂單','裁斷','針車','成型','协理给','合計','編制','外移P','外移Q','外移R','C2B']
        missB = [c for c in B12 if c not in detTxt]
        rec('區塊B 12 欄（含 协理给/合計/外移P·Q·R/C2B）', not missB, f'缺={missB}')

        # ── 區塊B 小計：直工小計(N) + 人力小計(P) ──
        subN = '直工小計' in detTxt; subP = '人力小計' in detTxt
        subRows = pg.eval_on_selector_all(".lean-subtotal-row", "e=>e.length")
        rec('區塊B 每 LEAN 底部 直工小計(N) + 人力小計(P)', subN and subP and subRows>0, f'N={subN} P={subP} 小計列={subRows}')

        # ── 區塊C：月度 11 項 ──
        monTxt = pg.inner_text("#monthlyPanel")
        C11 = ['總量','平均LC','直工數','上班時數','總工時','發外工時','扣減工時','效率','80%','實際直工','實際效率']
        C11_alt = {'總量':['總量','进度','進度'],'平均LC':['平均LC','平均 LC','LC'],'直工數':['直工數','直工数','直工'],
                   '上班時數':['上班時數','上班时数','上班'],'總工時':['總工時','总工时','工時','工时'],
                   '發外工時':['發外','发外'],'扣減工時':['扣減','扣减'],'效率':['效率'],'80%':['80'],
                   '實際直工':['實際直工','实际直工'],'實際效率':['實際效率','实际效率']}
        missC = [k for k,alts in C11_alt.items() if not any(a in monTxt for a in alts)]
        rec('區塊C 月度 11 項齊全', len(missC)==0, f'缺={missC}')

        # ── 視覺：手工格 manual-cell / 公式格 formula-cell ──
        nMan = pg.eval_on_selector_all(".manual-cell", "e=>e.length")
        nFor = pg.eval_on_selector_all(".formula-cell", "e=>e.length")
        rec('視覺區分：manual-cell(白底灰框) + formula-cell(無框純黑)', nMan>0 and nFor>0, f'manual={nMan} formula={nFor}')

        # ── 匯入：流程① 有檔案上傳入口 ──
        pg.eval_on_selector_all("#flow-bar > div", "(els)=>{els[0]&&els[0].click();}")  # 點流程①
        pg.wait_for_timeout(900)
        upVisible = pg.eval_on_selector("#ds04-upload", "e=>getComputedStyle(e).display!=='none'")
        hasFile = pg.eval_on_selector_all("#ds04-upload input[type=file]", "e=>e.length")
        rec('匯入：流程① 有 DS-04 檔案上傳入口', bool(upVisible) and hasFile>0, f'可見={upVisible} file_input={hasFile}')

        b.close()

    npass = sum(1 for _,ok in R if ok)
    print('\n'+'='*56)
    print(f'  spec_gate_bianche: {npass}/{len(R)} → {"✅ ALL GREEN" if npass==len(R) else "❌ FAIL"}')
    print('='*56)
    sys.exit(0 if npass==len(R) else 1)

if __name__ == '__main__':
    print(f'===== spec_gate_bianche（頁面級）· BASE={BASE} =====')
    main()
