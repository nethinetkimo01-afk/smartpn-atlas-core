# -*- coding: utf-8 -*-
"""
Task S-2 驗收：整合外框生產級返工（iframe 逃逸修復 + 編制表狀態可見 + 升級斷言）。

環境（隔離 + 生產形狀資料）：atlas_s2.db（多單位×多月：2026-06=5單位有資料、2026-05=1單位、2026-07=空月）
  伺服器 http://127.0.0.1:5097。
用法：先起 5097 server，再 py test_task_s2_shell.py

升級斷言（寫入 25 規則）：
  (a) 斷言「當前可見 iframe 的實際內容標題」而非 class；
  (b) 資料集含多單位/多月/缺資料月；
  (c) 頁內跳轉後殼返回列與返回路徑全測；
  (d) 每條斷言留截圖。
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5097"
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_backend", "test_output", "task_s2_shots")
os.makedirs(SHOT, exist_ok=True)
IE_TITLE = "IE 標準化界面"
BZ_TITLE = "廠務組織編制表"

RESULTS = []
_n = {"i": 0}
def rec(page, title, ok, d=""):
    RESULTS.append((title, ok)); print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — {title}")
    for ln in d.splitlines():
        if ln.strip(): print("     " + ln)
    _n["i"] += 1
    try: page.screenshot(path=os.path.join(SHOT, f"{_n['i']:02d}_{'PASS' if ok else 'FAIL'}.png"))
    except Exception: pass

def visible_frame_title(page):
    # 斷言「當前可見 iframe 的實際內容標題」（讀 contentDocument.title，非 class）
    return page.evaluate("""() => {
      for (const t of ['ie','bianche']) {
        const el = document.getElementById('frame-'+t);
        if (el && el.classList.contains('active')) {
          try { return el.contentDocument ? el.contentDocument.title : '(no-doc)'; }
          catch(e){ return '(cross)'; }
        }
      }
      return '(none)';
    }""")

def wait_frame(page, name, sel, to=10000):
    page.wait_for_function(
        "(a)=>{const el=document.getElementById('frame-'+a.n);return el&&el.contentDocument&&!!el.contentDocument.querySelector(a.sel)}",
        arg={"n": name, "sel": sel}, timeout=to)


def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True); ctx = b.new_context(viewport={"width":1520,"height":960}); pg = ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        def login(u,p):
            pg.goto(f"{BASE}/login", wait_until="domcontentloaded")
            pg.fill("#username",u); pg.fill("#password",p or "x"); pg.click("#btnLogin"); pg.wait_for_timeout(1000)

        login("jim","admin123")

        # ══ 1) 預設 IE：可見 iframe 內容標題 == IE 標準化界面 ══
        pg.goto(f"{BASE}/app", wait_until="domcontentloaded"); pg.wait_for_timeout(400)
        wait_frame(pg, "ie", "#ie-tbody")
        t = visible_frame_title(pg)
        rec(pg, "預設進 IE表：可見 iframe 內容標題正確（非 class 斷言）", IE_TITLE in t, f"title={t!r} 應含={IE_TITLE!r}")

        # ══ 2) 切編制表：可見 iframe 內容標題 == 廠務組織編制表 ══
        pg.click("#tab-bianche"); pg.wait_for_timeout(300); wait_frame(pg, "bianche", "#unitTable")
        t2 = visible_frame_title(pg)
        rec(pg, "切編制表：可見 iframe 內容標題正確", t2 == BZ_TITLE, f"title={t2!r} 期望={BZ_TITLE!r}")

        # ══ 3) 編制表狀態可見：2026-06（多單位）N 有資料 / M 未匯入 ══
        wait_frame(pg, "bianche", "#bz-status")
        pg.wait_for_timeout(600)
        st06 = pg.evaluate("document.getElementById('frame-bianche').contentDocument.querySelector('#bz-status').innerText")
        ok06 = ("有資料" in st06) and ("2026-06" in st06) and ("未匯入" in st06)
        rec(pg, "狀態列（2026-06 多單位）顯示 N 有資料/M 未匯入(列名)", ok06, f"bz-status='{st06}'")

        # ══ 4) 多月 + 空月：切 2026-07 空月 → 狀態明確非殘缺（不靜默空白）══
        pg.evaluate("document.getElementById('frame-bianche').contentDocument.querySelector('#selMonth').value='2026-07';"
                    "document.getElementById('frame-bianche').contentWindow.loadAll();")
        pg.wait_for_timeout(1200)
        st07 = pg.evaluate("document.getElementById('frame-bianche').contentDocument.querySelector('#bz-status').innerText")
        ok07 = ("2026-07" in st07) and (("未匯入" in st07) or ("有資料" in st07)) and st07.strip() != ""
        rec(pg, "空月(2026-07) 狀態可見不殘缺（非靜默空白）", ok07, f"bz-status='{st07}'")

        # ══ 5) 錯誤+重試機制存在（errBlock/重試鈕）══
        has_retry = pg.evaluate("typeof document.getElementById('frame-bianche').contentWindow.errBlock === 'function'")
        rec(pg, "API 失敗有明確錯誤+重試機制（errBlock 存在）", bool(has_retry), f"errBlock 函式存在={has_retry}")

        # ══ 6) iframe 逃逸修復：IE 深入頁 → 殼返回列出現 → 路徑正確 ══
        pg.click("#tab-ie"); pg.wait_for_timeout(300); wait_frame(pg, "ie", "#ie-tbody")
        pg.evaluate("document.getElementById('frame-ie').contentWindow.location.href='/admin/users'")
        pg.wait_for_timeout(1200)
        bar_shown = pg.evaluate("getComputedStyle(document.getElementById('shell-return-bar')).display") != "none"
        path_txt = pg.evaluate("document.getElementById('srb-path').innerText")
        deep_title = visible_frame_title(pg)
        ok_escape = bar_shown and ("/admin/users" in path_txt) and (deep_title == "帳號管理 — SmartPN Atlas")
        rec(pg, "iframe 逃逸修復：深入頁顯示殼返回列 + 路徑 + 內容標題", ok_escape,
            f"return_bar_shown={bar_shown} path='{path_txt}' deep_title={deep_title!r}")

        # ══ 7) 一鍵返回頁簽首頁：點返回列 → 回 /ie（內容標題復原、返回列收起）══
        pg.click("#srb-btn"); pg.wait_for_timeout(1000); wait_frame(pg, "ie", "#ie-tbody")
        back_title = visible_frame_title(pg)
        bar_hidden = pg.evaluate("getComputedStyle(document.getElementById('shell-return-bar')).display") == "none"
        rec(pg, "一鍵返回：回 IE 表首頁（內容標題復原 + 返回列收起）",
            (IE_TITLE in back_title) and bar_hidden, f"back_title={back_title!r} bar_hidden={bar_hidden}")

        # ══ 8) 編制表深入(勾選表/allocation)→返回列「← 返回 編制表」→ 一鍵回 ══
        pg.click("#tab-bianche"); pg.wait_for_timeout(300); wait_frame(pg, "bianche", "#unitTable")
        pg.evaluate("document.getElementById('frame-bianche').contentWindow.location.href='/allocation'")
        pg.wait_for_timeout(1200)
        srb_label = pg.evaluate("document.getElementById('srb-btn').innerText")
        pg.click("#srb-btn"); pg.wait_for_timeout(1000); wait_frame(pg, "bianche", "#unitTable")
        back_bz = visible_frame_title(pg)
        rec(pg, "編制表深入(allocation)→返回列標「編制表」→一鍵回", ("編制表" in srb_label) and (back_bz == BZ_TITLE),
            f"srb_label='{srb_label}' back_title={back_bz!r}")

        b.close()

    print("\n" + "="*60)
    npass = sum(1 for _,ok in RESULTS if ok)
    for t,ok in RESULTS: print(f"  {'✅' if ok else '❌'} {t}")
    print(f"\n  {npass}/{len(RESULTS)} PASS"); print("="*60)
    sys.exit(0 if npass == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
