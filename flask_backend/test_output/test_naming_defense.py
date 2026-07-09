"""
版本命名防呆 Playwright 自測（補完整測試發現的 2 個 UX 缺口）

驗證後端 create_ie_stage 命名防呆（API 直接呼叫也防）：
  - 空名稱 → 自動變「新版本 MM/DD」有意義的名，不是空白
  - 純空格名稱 → 同樣防呆
  - 同名 → 自動加序號（DUP → DUP (2) → DUP (3)），下拉可區分
  - 正常不重複命名 → 不受影響

隔離跑法：複製 DB → 隔離 server → 登入 jim → API 建版本驗證 + UI 下拉截圖 → 收尾刪副本。
用法：python flask_backend/test_output/test_naming_defense.py
"""
import os, sys, time, shutil, subprocess, sqlite3, urllib.request, urllib.error

HERE    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
SRC_DB  = os.path.join(BACKEND, 'data', 'atlas.db')
TEST_DB = os.path.join(HERE, '_nm_test.db')
SHOTS   = os.path.join(HERE, 'naming_shots')
PORT    = 5099
BASE    = f'http://127.0.0.1:{PORT}'

os.makedirs(SHOTS, exist_ok=True)
results = []


def log(step, ok, detail=''):
    results.append((step, ok, detail))
    print(f'[{"PASS" if ok else "FAIL"}] {step}  {detail}')


def wait_server(timeout=30):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(BASE + '/login', timeout=2) as r:
                if r.status == 200:
                    return True
        except urllib.error.HTTPError:
            return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    if not os.path.exists(SRC_DB):
        print('找不到來源 DB:', SRC_DB); sys.exit(1)
    for ext in ('', '-wal', '-shm'):
        if os.path.exists(TEST_DB + ext):
            os.remove(TEST_DB + ext)
    shutil.copy2(SRC_DB, TEST_DB)
    c = sqlite3.connect(TEST_DB)
    hid = c.execute("SELECT header_id FROM ie_process WHERE segment='cutting' "
                    "GROUP BY header_id ORDER BY COUNT(*) DESC LIMIT 1").fetchone()[0]
    c.close()
    print(f'測試 header={hid}')

    env = dict(os.environ); env['ATLAS_DB'] = TEST_DB; env['ATLAS_SECRET'] = 'x'
    server = subprocess.Popen(
        [sys.executable, '-c',
         "import database as db; db.init_db(); "
         "from app import app; app.run(host='127.0.0.1', port=%d, threaded=True)" % PORT],
        cwd=BACKEND, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_server():
            log('server', False, '逾時'); raise SystemExit(1)
        log('server', True, BASE)
        run(hid)
    finally:
        server.terminate()
        try: server.wait(timeout=5)
        except Exception: server.kill()
        for ext in ('', '-wal', '-shm'):
            if os.path.exists(TEST_DB + ext):
                try: os.remove(TEST_DB + ext)
                except Exception: pass

    print('\n' + '=' * 50)
    p = sum(1 for _, ok, _ in results if ok)
    print(f'結果: {p}/{len(results)} PASS')
    print('=' * 50)
    sys.exit(0 if all(ok for _, ok, _ in results) else 2)


def run(hid):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context().new_page()
        page.on('dialog', lambda d: d.accept())

        page.goto(BASE + '/login'); page.fill('#username', 'jim'); page.fill('#password', 'admin123')
        page.click('#btnLogin'); page.wait_for_url('**/ie', timeout=10000)

        def mk(name):
            return page.request.post(f'{BASE}/api/ie/stages/{hid}', data={'stage_name': name}).json()

        # 步驟1: 空名稱 → 有意義預設名
        r1 = mk('')
        n1 = r1.get('stage_name', '')
        ok1 = r1.get('ok') and n1.strip() != '' and n1.startswith('新版本')
        log('步驟1 空名稱→自動「新版本…」不是空白', ok1, f'建出="{n1}"')

        # 步驟2: 純空格 → 同樣防呆
        r2 = mk('     ')
        n2 = r2.get('stage_name', '')
        ok2 = r2.get('ok') and n2.strip() != '' and n2.startswith('新版本')
        log('步驟2 純空格名稱→同樣防呆', ok2, f'建出="{n2}"')

        # 步驟3+4: 同名三次 → DUP / DUP (2) / DUP (3)
        d1 = mk('DUP').get('stage_name')
        d2 = mk('DUP').get('stage_name')
        d3 = mk('DUP').get('stage_name')
        ok34 = (d1 == 'DUP' and d2 == 'DUP (2)' and d3 == 'DUP (3)')
        log('步驟3+4 同名自動加序號(可區分)', ok34, f'三次建出=[{d1!r}, {d2!r}, {d3!r}]')

        # 步驟5: 正常不重複 → 不受影響
        r5 = mk('正式定案版')
        ok5 = r5.get('stage_name') == '正式定案版'
        log('步驟5 正常命名不受影響', ok5, f'建出="{r5.get("stage_name")}"')

        # 步驟6: UI 下拉截圖(名稱都可區分、無空白項)
        page.goto(BASE + f'/ie/{hid}/detail')
        page.wait_for_selector('#stageSelect', timeout=15000)
        page.wait_for_function("() => document.querySelectorAll('#stageSelect option').length >= 5", timeout=15000)
        page.wait_for_timeout(500)
        opts = page.eval_on_selector_all('#stageSelect option', 'els => els.map(e => e.textContent)')
        page.screenshot(path=os.path.join(SHOTS, '01_dropdown_names.png'), full_page=False)
        blanks = [o for o in opts if not o.replace('🔒', '').replace('—', '').strip()]
        ok6 = len(blanks) == 0
        log('步驟6 下拉每項名稱可區分、無空白項', ok6, f'下拉項={opts}')

        browser.close()


if __name__ == '__main__':
    main()
