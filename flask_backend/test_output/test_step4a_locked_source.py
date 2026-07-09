"""
版本控制 Step 4a「編制表抓鎖定版 + 沒鎖定空紅底」Playwright 自動測試

驗證：
  - 有鎖定版的 header：編制表 MP 有數字（即時讀鎖定版）
  - 沒鎖定版的 header：編制表 MP 空、has_locked=false（前端紅底）
  - 解鎖 → 變空紅底；重新鎖定 → 又有數字
  - offline 勾選(allocation_item.is_checked)在重跑 prefill 後不被洗掉

隔離跑法同前：複製 DB → 另起 server(5099，啟動前 init_db) → 真開瀏覽器 → 每步截圖 → 收尾刪副本。
用法：python flask_backend/test_output/test_step4a_locked_source.py
"""
import os, sys, time, shutil, subprocess, sqlite3, urllib.request, urllib.error

HERE    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
SRC_DB  = os.path.join(BACKEND, 'data', 'atlas.db')
TEST_DB = os.path.join(HERE, '_s4a_test.db')
SHOTS   = os.path.join(HERE, 'step4a_shots')
PORT    = 5099
BASE    = f'http://127.0.0.1:{PORT}'
MONTH   = '2026-07'

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


def db_conn():
    return sqlite3.connect(TEST_DB)


def pick_two_headers():
    """兩個都有 IE + 有 ds04 訂單、且 model_name 不同的 header。"""
    c = db_conn()
    rows = c.execute('''
        SELECT oa.header_id, o.art, o.lean, o.model_name
        FROM ds04_orders o JOIN ob_articles oa ON oa.art=o.art
        JOIN ie_process ip ON ip.header_id=oa.header_id
        WHERE COALESCE(o.is_deleted,0)=0
        GROUP BY oa.header_id ORDER BY oa.header_id''').fetchall()
    c.close()
    a = rows[0]
    b = next((r for r in rows[1:] if r[3] != a[3]), rows[1])
    return a, b   # each = (header_id, art, lean, model_name)


def stage_id_of(hid):
    c = db_conn()
    sid = c.execute('SELECT id FROM ie_stage WHERE header_id=? ORDER BY id LIMIT 1', (hid,)).fetchone()[0]
    c.close()
    return sid


def main():
    if not os.path.exists(SRC_DB):
        print('找不到來源 DB:', SRC_DB); sys.exit(1)
    for ext in ('', '-wal', '-shm'):
        if os.path.exists(TEST_DB + ext):
            os.remove(TEST_DB + ext)
    shutil.copy2(SRC_DB, TEST_DB)
    A, B = pick_two_headers()
    print(f'測試 DB: {TEST_DB}')
    print(f'header_A(要鎖) = {A}')
    print(f'header_B(不鎖) = {B}')

    env = dict(os.environ)
    env['ATLAS_DB'] = TEST_DB
    env['ATLAS_SECRET'] = 'ver-test-secret'
    server = subprocess.Popen(
        [sys.executable, '-c',
         "import database as db; db.init_db(); "
         "from app import app; app.run(host='127.0.0.1', port=%d, threaded=True)" % PORT],
        cwd=BACKEND, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_server():
            log('server 啟動', False, '逾時'); raise SystemExit(1)
        log('server 啟動', True, BASE)
        run_ui(A, B)
    finally:
        server.terminate()
        try: server.wait(timeout=5)
        except Exception: server.kill()
        for ext in ('', '-wal', '-shm'):
            if os.path.exists(TEST_DB + ext):
                try: os.remove(TEST_DB + ext)
                except Exception: pass

    print('\n' + '=' * 50)
    passed = sum(1 for _, ok, _ in results if ok)
    print(f'結果: {passed}/{len(results)} PASS')
    print('=' * 50)
    sys.exit(0 if all(ok for _, ok, _ in results) else 2)


def run_ui(A, B):
    from playwright.sync_api import sync_playwright
    hidA, artA, leanA, modelA = A
    hidB, artB, leanB, modelB = B
    sidA = stage_id_of(hidA)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context().new_page()
        page.on('console', lambda m: (m.type == 'error') and print('  [console.error]', m.text))
        page.on('dialog', lambda d: d.accept('') if d.type == 'prompt' else d.accept())

        def find_model(art, month=MONTH):
            d = page.request.get(f'{BASE}/api/bianzhi/detail?month={month}').json()
            for lg in d.get('leans', []):
                for m in lg.get('models', []):
                    if art in (m.get('arts') or ''):
                        return m
            return None

        # ── 登入 ───────────────────────────────────────────────────────
        page.goto(BASE + '/login')
        page.fill('#username', 'jim'); page.fill('#password', 'admin123')
        page.click('#btnLogin'); page.wait_for_url('**/ie', timeout=10000)
        log('步驟0 登入 jim/admin123', True, '')

        # 基線：都沒鎖定 → 編制表全紅
        page.goto(BASE + '/bianche')
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SHOTS, '01_baseline_all_red.png'), full_page=True)
        mA0 = find_model(artA)
        base_ok = (mA0 is not None) and (mA0['has_locked'] is False) and (mA0['cutting'] is None)
        log('步驟0b 基線(無鎖定)→ 該 header MP 空', base_ok,
            f'A has_locked={mA0 and mA0["has_locked"]}, cutting={mA0 and mA0["cutting"]}')

        # ── 步驟1: 鎖 header_A → A 有數字、B 空 ───────────────────────
        rj = page.request.post(f'{BASE}/api/ie/stages/{hidA}/{sidA}/approve',
                               data={'note': 'step4a'}).json()
        mA = find_model(artA); mB = find_model(artB)
        page.goto(BASE + '/bianche'); page.wait_for_timeout(1500)
        red_badges = page.get_by_text('未鎖定').count()
        page.screenshot(path=os.path.join(SHOTS, '02_A_locked.png'), full_page=True)
        ok1 = (rj.get('ok') and mA and mA['has_locked'] is True and mA['cutting'] is not None
               and mB and mB['has_locked'] is False and mB['cutting'] is None and red_badges > 0)
        log('步驟1 鎖 header_A → A 有數字、B 空紅底', ok1,
            f'A(has_locked={mA and mA["has_locked"]},cutting={mA and mA["cutting"]}) '
            f'B(has_locked={mB and mB["has_locked"]},cutting={mB and mB["cutting"]}) 未鎖定badge={red_badges}')

        # ── 步驟2: 解鎖 A → A 變空紅底 ─────────────────────────────────
        page.request.post(f'{BASE}/api/ie/stages/{hidA}/unlock')
        mA2 = find_model(artA)
        page.goto(BASE + '/bianche'); page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SHOTS, '03_A_unlocked_red.png'), full_page=True)
        ok2 = mA2 and mA2['has_locked'] is False and mA2['cutting'] is None
        log('步驟2 解鎖 A → A 變空紅底', ok2,
            f'A has_locked={mA2 and mA2["has_locked"]}, cutting={mA2 and mA2["cutting"]}')

        # ── 步驟3: 重新鎖 A → A 又有數字 ──────────────────────────────
        page.request.post(f'{BASE}/api/ie/stages/{hidA}/{sidA}/approve', data={'note': 'relock'})
        mA3 = find_model(artA)
        page.goto(BASE + '/bianche'); page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SHOTS, '04_A_relocked.png'), full_page=True)
        ok3 = mA3 and mA3['has_locked'] is True and mA3['cutting'] is not None
        log('步驟3 重新鎖 A → A 又有數字', ok3,
            f'A has_locked={mA3 and mA3["has_locked"]}, cutting={mA3 and mA3["cutting"]}')

        # ── 步驟4: offline 勾選在重跑 prefill 後不被洗掉 ──────────────
        page.request.post(f'{BASE}/api/allocation/login', data={'username': 'jim'})
        page.request.post(f'{BASE}/api/allocation/prefill', data={'header_id': hidA, 'month': MONTH})
        items = page.request.get(f'{BASE}/api/allocation/items?month={MONTH}&header_id={hidA}').json()
        item_id = None
        for g in items.get('groups', []):
            if g.get('items'):
                item_id = g['items'][0]['id']; break
        checked_ok = False; preserved_ok = False
        if item_id:
            page.request.post(f'{BASE}/api/allocation/check', data={'id': item_id, 'is_checked': 1})
            c = db_conn(); v1 = c.execute('SELECT is_checked FROM allocation_item WHERE id=?', (item_id,)).fetchone()[0]; c.close()
            checked_ok = (v1 == 1)
            # 重跑 prefill（即時重讀 IE）→ 勾選應保留
            page.request.post(f'{BASE}/api/allocation/prefill', data={'header_id': hidA, 'month': MONTH})
            c = db_conn(); v2 = c.execute('SELECT is_checked FROM allocation_item WHERE id=?', (item_id,)).fetchone()[0]; c.close()
            preserved_ok = (v2 == 1)
        page.screenshot(path=os.path.join(SHOTS, '05_offline_check_preserved.png'), full_page=True)
        log('步驟4 offline 勾選重跑 prefill 後保留', checked_ok and preserved_ok,
            f'item={item_id}, 勾選後={checked_ok}, 重跑prefill後仍勾={preserved_ok}')

        browser.close()


if __name__ == '__main__':
    main()
