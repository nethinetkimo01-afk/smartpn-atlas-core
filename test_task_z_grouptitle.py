# -*- coding: utf-8 -*-
"""
Task Z 驗收：分組標題規則（裁斷本身分組不渲染標題；非裁斷工序分組保留標題）。

環境（隔離）：atlas_test.db @ http://127.0.0.1:5099。header 32（裁斷機 + post-process 分組）。
用法：先起 5099 server，再 py test_task_z_grouptitle.py

驗收（真 DOM，不看原始碼字串）：
  非裁斷分組(印线/削皮…)標題仍在且對齊；純裁斷分組('裁断')無標題；
  欄位對齊(colspan)/總計列/三語表頭/read_only 全灰 全迴歸。
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:5099"; HID = 32
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "flask_backend", "test_output", "task_z_shots")
os.makedirs(SHOT, exist_ok=True)
RESULTS = []; _n={"i":0}
def rec(pg, t, ok, d=""):
    RESULTS.append((t, ok)); print(f"\n{'✅ PASS' if ok else '❌ FAIL'} — {t}")
    for ln in d.splitlines():
        if ln.strip(): print("     " + ln)
    _n["i"]+=1
    try: pg.screenshot(path=os.path.join(SHOT, f"{_n['i']:02d}_{'P' if ok else 'F'}.png"))
    except Exception: pass

def open_cutting(pg):
    pg.goto(f"{BASE}/ie/{HID}/detail", wait_until="domcontentloaded")
    try: pg.wait_for_function("()=>document.querySelectorAll('.zone-card').length>0", timeout=9000)
    except Exception: pass
    pg.wait_for_timeout(900)

def main():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True); ctx=b.new_context(viewport={"width":1680,"height":980}); pg=ctx.new_page()
        pg.on("dialog", lambda d: d.accept())
        def login(u,p):
            pg.goto(f"{BASE}/login", wait_until="domcontentloaded")
            pg.fill("#username",u); pg.fill("#password",p or "x"); pg.click("#btnLogin"); pg.wait_for_timeout(900)

        login("jim","admin123")
        open_cutting(pg)

        # ══ 1) 裁斷分組('裁断'/'裁断手工')標題不渲染（跨欄群組格 colspan>=2 文字空）══
        # 註：th-cut-group class 也用於欄位標題(流程名稱等,非群組標題)；群組標題＝跨欄(colspan>=2)。
        cutg = pg.eval_on_selector_all(".th-cut-group",
            "els=>els.filter(e=>parseInt(e.getAttribute('colspan')||'1')>=2).map(e=>e.textContent.trim()).filter(t=>t!=='')")
        cutg_count = pg.eval_on_selector_all(".th-cut-group",
            "els=>els.filter(e=>parseInt(e.getAttribute('colspan')||'1')>=2).length")
        rec(pg, "裁斷分組標題不渲染（跨欄群組格皆空、結構/colspan 仍在）",
            len(cutg)==0 and cutg_count>0, f"非空裁斷群組標題={cutg}（期望[]）；跨欄群組格數={cutg_count}")

        # ══ 2) 非裁斷分組(印线/削皮…)標題保留（th-post-group 有文字）══
        postg = pg.eval_on_selector_all(".th-post-group",
            "els=>els.map(e=>e.textContent.trim()).filter(t=>t!=='')")
        keep_ok = len(postg) > 0 and any(('印' in t or '削' in t or '补强' in t or '涂边' in t or '热压' in t or '磨皮' in t) for t in postg)
        rec(pg, "非裁斷工序分組標題保留（印线/削皮/贴补强/涂边/热压…）",
            keep_ok, f"保留的分組標題={postg}")

        # ══ 3) 欄位對齊：th-cut-group 仍帶 colspan（結構/對齊不變）══
        colspans = pg.eval_on_selector_all(".th-cut-group","els=>els.map(e=>e.getAttribute('colspan')).filter(Boolean)")
        rec(pg, "欄位對齊：th-cut-group colspan 保留（對齊不變）",
            len(colspans)>0, f"colspans={colspans}")

        # ══ 4) 總計列位置迴歸（zone-total-row 存在）══
        total_rows = pg.eval_on_selector_all("tr.zone-total-row, tr.sum-row","els=>els.length")
        # 裁斷段用 renderCuttingTotalRow → 檢查每個 cut-table 有合計列
        cut_total = pg.eval_on_selector_all(".cut-table tbody tr, .cut-table tr","els=>els.length")
        has_total = pg.evaluate("!!document.querySelector('.cut-table') && [...document.querySelectorAll('.cut-table tr')].some(r=>r.textContent.includes('合計')||r.className.includes('total'))")
        rec(pg, "總計列位置迴歸（裁斷表含合計列）", has_total, f"cut_total_found={has_total}")

        # ══ 5) 三語表頭迴歸（切 VI → 欄位標題變越文）══
        zh_hdr = pg.eval_on_selector_all(".cut-table thead .th-zh","els=>els.map(e=>e.textContent).join('|').slice(0,40)")
        # 切語言鈕（VI）
        try:
            pg.eval_on_selector("#langVI, [data-lang='vi'], button:has-text('VI')","b=>b.click()")
        except Exception:
            pg.evaluate("if(typeof setLang==='function')setLang('vi')")
        pg.wait_for_timeout(500)
        vi_present = pg.eval_on_selector_all(".cut-table thead .th-vi","els=>els.length>0")
        rec(pg, "三語表頭迴歸（越/英/中三列表頭齊全）", vi_present and len(zh_hdr)>0,
            f"th-vi 存在={vi_present} th-zh樣本='{zh_hdr}'")

        # ══ 6) read_only(tongcai) 裁斷段全灰迴歸（無 input.cell-inp）══
        login("tongcai","x")
        open_cutting(pg)
        inp = pg.eval_on_selector_all("input.cell-inp","els=>els.length")
        cutg2 = pg.eval_on_selector_all(".th-cut-group","els=>els.map(e=>e.textContent.trim()).filter(t=>t!=='')")
        rec(pg, "read_only 裁斷段全灰 + 標題規則仍生效", inp==0 and len(cutg2)==0,
            f"input.cell-inp={inp}(期望0)；裁斷標題非空={cutg2}(期望[])")

        b.close()

    print("\n"+"="*60)
    npass=sum(1 for _,ok in RESULTS if ok)
    for t,ok in RESULTS: print(f"  {'✅' if ok else '❌'} {t}")
    print(f"\n  {npass}/{len(RESULTS)} PASS"); print("="*60)
    sys.exit(0 if npass==len(RESULTS) else 1)

if __name__=="__main__": main()
