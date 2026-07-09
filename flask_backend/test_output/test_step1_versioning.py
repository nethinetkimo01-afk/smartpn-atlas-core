"""
版本控制 Step 1 —「資料分版」Playwright 自動測試

驗證：每個版本(stage)有獨立的工序資料；另存新版本=複製一份；
改新版不影響舊版；切版本看到不同內容。

作法（不污染正式 DB）：
  1. 複製 data/atlas.db → test_output/_ver_test.db，整個測試跑在副本上
  2. 用副本另起一個 Flask server(127.0.0.1:5099)
  3. Playwright(chromium) 真的開瀏覽器、登入 jim/admin123、操作 cutting 細表
  4. 每步截圖到 test_output/step1_shots/
  5. 測完關 server、刪副本

測試步驟（對應 Jim 要求 1~7）：
  1 登入 jim/admin123 → 進一個鞋型的 cutting 細表
  2 記下當前版本某工序格的值 V1
  3 「另存新階段」→ 應建立新版本、工序被複製（同一格顯示 V1）
  4 在新版本把該格改成 V2 → 儲存
  5 切回舊版本 → 該格仍是 V1（沒被改）→ 證明分版成功
  6 切到新版本 → 該格是 V2
  7 每步截圖

用法：python flask_backend/test_output/test_step1_versioning.py
成功 exit 0，失敗 exit 非0。
"""
import os, sys, time, shutil, socket, subprocess, sqlite3, urllib.request

HERE      = os.path.dirname(os.path.abspath(__file__))
BACKEND   = os.path.dirname(HERE)
SRC_DB    = os.path.join(BACKEND, 'data', 'atlas.db')
TEST_DB   = os.path.join(HERE, '_ver_test.db')
SHOTS     = os.path.join(HERE, 'step1_shots')
PORT      = 5099
BASE      = f'http://127.0.0.1:{PORT}'

os.makedirs(SHOTS, exist_ok=True)
results = []   # (step, ok, detail)


def log(step, ok, detail=''):
    results.append((step, ok, detail))
    print(f'[{"PASS" if ok else "FAIL"}] {step}  {detail}')


def wait_server(timeout=30):
    # /login 是 open path（未登入也回 200）；能連上即代表 server 起來了
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(BASE + '/login', timeout=2) as r:
                if r.status == 200:
                    return True
        except urllib.error.HTTPError:
            return True   # 有 HTTP 回應 = server 已啟動
        except Exception:
            time.sleep(0.5)
    return False


def pick_header():
    c = sqlite3.connect(TEST_DB)
    hid = c.execute(
        "SELECT header_id FROM ie_process WHERE segment='cutting' "
        "AND (flag IS NULL OR flag!='deleted') "
        "GROUP BY header_id ORDER BY COUNT(*) DESC LIMIT 1").fetchone()[0]
    c.close()
    return hid


def main():
    # ── 1. 準備隔離副本 DB ──────────────────────────────────────────────
    if not os.path.exists(SRC_DB):
        print('找不到來源 DB:', SRC_DB); sys.exit(1)
    for ext in ('', '-wal', '-shm'):
        p = TEST_DB + ext
        if os.path.exists(p):
            os.remove(p)
    shutil.copy2(SRC_DB, TEST_DB)
    hid = pick_header()
    print(f'測試 DB: {TEST_DB}\n測試 header_id: {hid}')

    # ── 2. 啟動隔離 server ─────────────────────────────────────────────
    env = dict(os.environ)
    env['ATLAS_DB'] = TEST_DB
    env['ATLAS_SECRET'] = 'ver-test-secret'
    server = subprocess.Popen(
        [sys.executable, '-c',
         "from app import app; app.run(host='127.0.0.1', port=%d, threaded=True)" % PORT],
        cwd=BACKEND, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_server():
            log('server 啟動', False, '逾時未回應'); raise SystemExit(1)
        log('server 啟動', True, BASE)
        run_ui(hid)
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            server.kill()
        for ext in ('', '-wal', '-shm'):
            p = TEST_DB + ext
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass

    # ── summary ────────────────────────────────────────────────────────
    print('\n' + '=' * 50)
    passed = sum(1 for _, ok, _ in results if ok)
    total  = len(results)
    print(f'結果: {passed}/{total} PASS')
    print('=' * 50)
    ok_all = all(ok for _, ok, _ in results)
    sys.exit(0 if ok_all else 2)


# 目標格：cutting 的「實際人數」輸入格 .cut-act-inp
#   - 每列一個，onblur 即時存進 ie_process（saveSingleActual，依 process_id 存，天生綁版本）
#   - 跨版本用「第一個 .cut-act-inp」定位；v2 是 v1 的完整複本，第一個對應同一邏輯列
ACT_SEL = '#mainContent input.cut-act-inp'


def run_ui(hid):
    from playwright.sync_api import sync_playwright
    V2 = '778899'  # 明顯的測試值

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()

        page.on('console', lambda m: (m.type == 'error') and print('  [console.error]', m.text))
        # prompt(另存版本名) 自動填、alert/confirm 自動接受
        def on_dialog(d):
            d.accept('v2測試') if d.type == 'prompt' else d.accept()
        page.on('dialog', on_dialog)

        def first_act():
            return page.locator(ACT_SEL).first

        def read_act():
            page.wait_for_selector(ACT_SEL, timeout=15000)
            return first_act().input_value()

        # ── 步驟1: 登入 ────────────────────────────────────────────────
        page.goto(BASE + '/login')
        page.fill('#username', 'jim')
        page.fill('#password', 'admin123')
        page.click('#btnLogin')
        page.wait_for_url('**/ie', timeout=10000)
        log('步驟1 登入 jim/admin123', True, '→ /ie')

        # 進 cutting 細表
        page.goto(BASE + f'/ie/{hid}/detail')
        page.wait_for_selector(ACT_SEL, timeout=15000)
        page.wait_for_timeout(800)
        page.screenshot(path=os.path.join(SHOTS, '01_v1_loaded.png'), full_page=True)

        stages_before = page.eval_on_selector(
            '#stageSelect', 'el => [...el.options].map(o=>o.textContent)')
        v1_stage_val = page.eval_on_selector('#stageSelect', 'el => el.value')

        # ── 步驟2: 記下 V1 值（第一列實際人數） ─────────────────────────
        V1 = read_act()
        log('步驟2 記錄當前版本工序值 V1', True,
            f'V1="{V1}", 版本清單={stages_before}, v1_stage={v1_stage_val}')

        # ── 步驟3: 另存新階段（應複製工序） ──────────────────────────
        page.click('text=儲存 ▼')
        page.click('text=另存新階段')          # 觸發 prompt → 自動填 "v2測試"
        page.wait_for_function(
            "cnt => document.querySelectorAll('#stageSelect option').length > cnt",
            arg=len(stages_before), timeout=10000)
        page.wait_for_selector(ACT_SEL, timeout=15000)
        page.wait_for_timeout(800)
        stages_after = page.eval_on_selector(
            '#stageSelect', 'el => [...el.options].map(o=>o.textContent)')
        v2_stage_val = page.eval_on_selector('#stageSelect', 'el => el.value')
        copied_val = read_act()
        page.screenshot(path=os.path.join(SHOTS, '02_v2_created_copied.png'), full_page=True)
        ok3 = (len(stages_after) == len(stages_before) + 1) and (copied_val == V1) and (v2_stage_val != v1_stage_val)
        log('步驟3 另存新版本 + 工序被複製', ok3,
            f'版本清單={stages_after}, v2_stage={v2_stage_val}, 新版第一格="{copied_val}"(應=V1 "{V1}")')

        # ── 步驟4: 新版改值 V2 → onblur 即時存 ────────────────────────
        inp = first_act()
        inp.fill(V2)
        with page.expect_response('**/api/ie/cell/save') as resp_info:
            inp.press('Enter')          # onkeydown Enter → blur → saveSingleActual
        saved_ok = resp_info.value.ok
        page.wait_for_timeout(600)
        set_val = first_act().input_value()
        page.screenshot(path=os.path.join(SHOTS, '03_v2_edited_saved.png'), full_page=True)
        log('步驟4 新版改值 V2 並儲存', (set_val == V2) and saved_ok,
            f'設定值="{set_val}"(應=V2 "{V2}"), save回應ok={saved_ok}')

        # ── 步驟5: 切回舊版 → 值應仍為 V1 ────────────────────────────
        page.select_option('#stageSelect', value=str(v1_stage_val))
        page.wait_for_selector(ACT_SEL, timeout=15000)
        page.wait_for_timeout(800)
        v1_after = read_act()
        page.screenshot(path=os.path.join(SHOTS, '04_back_to_v1.png'), full_page=True)
        ok5 = (v1_after == V1) and (v1_after != V2)
        log('步驟5 切回舊版本，值未被改（分版成功）', ok5,
            f'舊版第一格="{v1_after}"(應=V1 "{V1}", 不應=V2 "{V2}")')

        # ── 步驟6: 切到新版 → 值應為 V2 ──────────────────────────────
        page.select_option('#stageSelect', value=str(v2_stage_val))
        page.wait_for_selector(ACT_SEL, timeout=15000)
        page.wait_for_timeout(800)
        v2_after = read_act()
        page.screenshot(path=os.path.join(SHOTS, '05_back_to_v2.png'), full_page=True)
        ok6 = (v2_after == V2)
        log('步驟6 切到新版本，值為 V2（兩版獨立）', ok6,
            f'新版第一格="{v2_after}"(應=V2 "{V2}")')

        browser.close()


if __name__ == '__main__':
    main()
