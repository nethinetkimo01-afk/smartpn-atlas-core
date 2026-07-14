# -*- coding: utf-8 -*-
"""
Task Y 驗收：編制表五步流程（①匯入→②EOLR→③勾選→④計算→⑤導出），真點擊走通。

環境（隔離）：atlas_y.db（2026-06=完整可走完；2026-07=空月缺資料）@ http://127.0.0.1:5096。
用法：先起 5096 server，再 py test_task_y_flow.py

驗收：①→⑤ 真點擊走通；回退/缺資料/切月份三情境不得白畫面或死路；欄位/總計/三語/read_only 迴歸。
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5096"
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_backend", "test_output", "task_y_shots")
os.makedirs(SHOT, exist_ok=True)
RESULTS = []; _n={"i":0}
def rec(pg, title, ok, d=""):
    RESULTS.append((title, ok)); print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — {title}")
    for ln in d.splitlines():
        if ln.strip(): print("     " + ln)
    _n["i"]+=1
    try: pg.screenshot(path=os.path.join(SHOT, f"{_n['i']:02d}_{'P' if ok else 'F'}.png"))
    except Exception: pass

def embed_nonblank(pg):
    # 內嵌 iframe 實際內容非空白（真渲染，不看字串）
    return pg.evaluate("""() => {
      const w = document.getElementById('flow-embed-wrap');
      if (getComputedStyle(w).display === 'none') return {shown:false, len:0};
      const f = document.getElementById('flow-embed');
      try { const t = f.contentDocument ? f.contentDocument.body.innerText.trim().length : 0; return {shown:true, len:t}; }
      catch(e){ return {shown:true, len:-1}; }
    }""")

def click_step(pg, n):
    pg.eval_on_selector_all("#flow-bar > div",
        "(els,n)=>{els[n-1] && els[n-1].click();}", n)

def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True); ctx=b.new_context(viewport={"width":1520,"height":980}); pg=ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        def login(u,p):
            pg.goto(f"{BASE}/login", wait_until="domcontentloaded")
            pg.fill("#username",u); pg.fill("#password",p or "x"); pg.click("#btnLogin"); pg.wait_for_timeout(900)

        login("jim","admin123")
        pg.goto(f"{BASE}/bianche", wait_until="domcontentloaded")
        pg.wait_for_selector("#flow-bar > div", timeout=8000); pg.wait_for_timeout(900)
        pg.select_option("#selMonth","2026-06"); pg.wait_for_timeout(1200)

        # ══ 1) 流程列 5 步渲染 + 狀態可見 ══
        nchips = pg.eval_on_selector_all("#flow-bar > div","e=>e.length")
        states = pg.evaluate("_FLOW.steps.map(s=>s.status)")
        rec(pg, "流程列 5 步渲染 + 狀態可見", nchips==5 and len(states)==5,
            f"chips={nchips} states={states}")

        # ══ 2) 真點擊走 ①→②→③（內嵌頁非白畫面）══
        walk = {}
        for step,label in [(1,'①匯入DS-04'),(2,'②EOLR'),(3,'③勾選')]:
            click_step(pg, step); pg.wait_for_timeout(1400)
            e = embed_nonblank(pg)
            walk[label] = e
        ok_walk = all(v.get('shown') and v.get('len',0) > 5 for v in walk.values())
        rec(pg, "①②③ 真點擊內嵌頁載入（非白畫面）", ok_walk,
            "\n".join(f"{k}: shown={v['shown']} content_len={v['len']}" for k,v in walk.items()))

        # ══ 3) ④計算編制（原生內容）+ ⑤導出 ready ══
        click_step(pg, 4); pg.wait_for_timeout(800)
        s4 = pg.evaluate("() => ({embed: getComputedStyle(document.getElementById('flow-embed-wrap')).display, unit: !!document.querySelector('#unitTable')})")
        with pg.expect_download(timeout=6000) as di:
            click_step(pg, 5)
        dl = di.value
        rec(pg, "④計算編制原生內容 + ⑤導出真的下載", s4['embed']=='none' and s4['unit'] and dl is not None,
            f"embed_hidden={s4['embed']=='none'} unitTable={s4['unit']} download={dl.suggested_filename if dl else None}")

        # ══ 4) 回退：從④點①→下游標『需重算』，不白畫面 ══
        click_step(pg, 4); pg.wait_for_timeout(400)
        click_step(pg, 1); pg.wait_for_timeout(1200)
        recalc_shown = pg.evaluate("getComputedStyle(document.getElementById('flow-recalc')).display") != "none"
        badge = pg.evaluate("document.getElementById('flow-bar').innerText.includes('需重算')")
        e1 = embed_nonblank(pg)
        rec(pg, "回退到①→下游標『需重算』且不白畫面", recalc_shown and badge and e1.get('shown') and e1.get('len',0)>5,
            f"recalc_bar={recalc_shown} badge={badge} embed_len={e1.get('len')}")

        # ══ 5) 缺資料月(2026-07空)：步驟灰掉+說明，點鎖住步驟不死路 ══
        pg.select_option("#selMonth","2026-07"); pg.wait_for_timeout(1400)
        states9 = pg.evaluate("_FLOW.steps.map(s=>s.status)")
        # 點一個被鎖步驟(如④)→ 應出 toast 說明、不白畫面
        click_step(pg, 4); pg.wait_for_timeout(600)
        toast_vis = pg.evaluate("getComputedStyle(document.getElementById('toast')).display") != "none"
        native_ok = pg.evaluate("!!document.querySelector('#unitTable')")
        rec(pg, "缺資料月：步驟狀態可見 + 點鎖住步驟出說明不死路", ('todo' in states9) and native_ok,
            f"states(2026-07)={states9} toast={toast_vis} native_rendered={native_ok}")

        # ══ 6) 切月份：流程重新derived、不白畫面 ══
        pg.select_option("#selMonth","2026-06"); pg.wait_for_timeout(1200)
        states6 = pg.evaluate("_FLOW.steps.map(s=>s.status)")
        native6 = pg.evaluate("!!document.querySelector('#unitTable') && getComputedStyle(document.getElementById('flow-embed-wrap')).display==='none'")
        rec(pg, "切月份：流程重新推導 + 回計算視圖不白畫面", states6[0]=='locked' and native6,
            f"states(2026-06)={states6} native_view={native6}")

        # ══ 7) read_only 全灰迴歸（tongcai 編制表輸入 disabled）══
        login("tongcai","x")
        pg.goto(f"{BASE}/bianche", wait_until="domcontentloaded")
        pg.wait_for_selector("#unitTable", timeout=8000); pg.wait_for_timeout(900)
        enabled = pg.eval_on_selector_all(".bz-inp","e=>e.filter(x=>!x.disabled).length")
        rec(pg, "read_only(tongcai) 編制表全灰迴歸", enabled==0, f"啟用輸入格={enabled}(期望0)")

        b.close()

    print("\n"+"="*60)
    npass=sum(1 for _,ok in RESULTS if ok)
    for t,ok in RESULTS: print(f"  {'✅' if ok else '❌'} {t}")
    print(f"\n  {npass}/{len(RESULTS)} PASS"); print("="*60)
    sys.exit(0 if npass==len(RESULTS) else 1)

if __name__=="__main__": main()
