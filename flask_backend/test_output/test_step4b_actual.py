"""
版本控制 Step 4b「編制表 MP 改抓實際人數(actual_operators)」Playwright 自動測試

驗證：
  - 針車(stitching) MP = 該鎖定版工序 actual_operators 加總（不是 standard_time 理論換算）
  - 改實際人數 → 編制表跟著變
  - 某工序實際人數留空(NULL) → 當 0 加，不 NaN/不報錯
  - 對比：數字是「實際人數加總」而非「理論換算」

隔離跑法同前：複製 DB → 另起 server(5099) → 真開瀏覽器 → 每步截圖 → 收尾刪副本。
（實際人數的資料狀態用直接寫 test DB 模擬「IE 已填實際人數」；驗證走 API + UI。）
用法：python flask_backend/test_output/test_step4b_actual.py
"""
import os, sys, time, shutil, subprocess, sqlite3, urllib.request, urllib.error

HERE    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
SRC_DB  = os.path.join(BACKEND, 'data', 'atlas.db')
TEST_DB = os.path.join(HERE, '_s4b_test.db')
SHOTS   = os.path.join(HERE, 'step4b_shots')
PORT    = 5099
BASE    = f'http://127.0.0.1:{PORT}'
MONTH   = '2026-07'
STITCH_ZONES = ('電腦針車', '折边')

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


def set_stitch_actuals(hid, sid, values):
    """把該 header 鎖定版所有針車工序 actual_operators 歸零後，前 N 列設成 values。
    （歸零其餘列，確保加總 = sum(values)，避免原始資料干擾）"""
    c = db_conn()
    rids = [r[0] for r in c.execute(
        "SELECT id FROM ie_process WHERE header_id=? AND stage_id=? "
        "AND zone IN (?,?) ORDER BY id", (hid, sid, *STITCH_ZONES)).fetchall()]
    for i, rid in enumerate(rids):
        v = values[i] if i < len(values) else 0
        c.execute('UPDATE ie_process SET actual_operators=? WHERE id=?', (v, rid))
    c.commit(); c.close()
    return rids


def setup_pick():
    """挑一個有針車工序 + 有 ds04 訂單 + 非外包 的 header。"""
    c = db_conn()
    row = c.execute('''
        SELECT oa.header_id, o.art, o.model_name, ip2.stage_id
        FROM ds04_orders o
        JOIN ob_articles oa ON oa.art=o.art
        JOIN ie_process ip2 ON ip2.header_id=oa.header_id AND ip2.zone IN ('電腦針車','折边')
        WHERE COALESCE(o.is_deleted,0)=0 AND COALESCE(o.is_outsource_upper,0)=0
        GROUP BY oa.header_id
        HAVING COUNT(*)>=2
        LIMIT 1''').fetchone()
    c.close()
    return row  # (header_id, art, model, stage_id)


def main():
    if not os.path.exists(SRC_DB):
        print('找不到來源 DB:', SRC_DB); sys.exit(1)
    for ext in ('', '-wal', '-shm'):
        if os.path.exists(TEST_DB + ext):
            os.remove(TEST_DB + ext)
    shutil.copy2(SRC_DB, TEST_DB)

    pick = setup_pick()
    if not pick:
        print('找不到合適 header（有針車工序+訂單+非外包）'); sys.exit(1)
    hid, art, model, sid = pick
    # theory 值（供對比：sum(std)*120/3600）
    c = db_conn()
    theory = c.execute(
        "SELECT COALESCE(SUM(standard_time),0) FROM ie_process "
        "WHERE header_id=? AND stage_id=? AND zone IN (?,?) AND standard_time>0",
        (hid, sid, *STITCH_ZONES)).fetchone()[0]
    c.close()
    theory_mp = round(theory * 120 / 3600.0, 1)
    print(f'測試 header={hid} art={art} model={model} stage={sid}  針車theory~{theory_mp}')

    # 先把針車實際人數設成 3+2=5（模擬 IE 已填實際人數）
    set_stitch_actuals(hid, sid, [3, 2])

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
        run_ui(hid, art, sid, theory_mp)
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


def run_ui(hid, art, sid, theory_mp):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context().new_page()
        page.on('console', lambda m: (m.type == 'error') and print('  [console.error]', m.text))
        page.on('dialog', lambda d: d.accept('') if d.type == 'prompt' else d.accept())

        def model_of(a=art):
            d = page.request.get(f'{BASE}/api/bianzhi/detail?month={MONTH}').json()
            for lg in d.get('leans', []):
                for m in lg.get('models', []):
                    if a in (m.get('arts') or ''):
                        return m
            return None

        # 登入 + 鎖定 header
        page.goto(BASE + '/login')
        page.fill('#username', 'jim'); page.fill('#password', 'admin123')
        page.click('#btnLogin'); page.wait_for_url('**/ie', timeout=10000)
        page.request.post(f'{BASE}/api/ie/stages/{hid}/{sid}/approve', data={'note': 's4b'})
        log('步驟0 登入 + 鎖定 header', True, f'header={hid}')

        # ── 步驟1: 針車 MP = 實際人數加總 5（非理論 {theory}）─────────
        m1 = model_of()
        page.goto(BASE + '/bianche'); page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SHOTS, '01_actual_5.png'), full_page=True)
        ok1 = (m1 and m1['stitching'] == 5.0 and m1['has_locked'] and m1.get('has_actual')
               and m1['stitching'] != theory_mp)
        log('步驟1 針車 MP = 實際人數加總(5)，非理論換算', ok1,
            f'stitching={m1 and m1["stitching"]}(應=5, 理論~{theory_mp}), has_actual={m1 and m1.get("has_actual")}')

        # ── 步驟2: 改實際人數 4+4=8 → 編制表跟著變 ────────────────────
        set_stitch_actuals(hid, sid, [4, 4])
        m2 = model_of()
        page.goto(BASE + '/bianche'); page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SHOTS, '02_actual_8.png'), full_page=True)
        ok2 = m2 and m2['stitching'] == 8.0
        log('步驟2 改實際人數(4+4) → 編制表針車=8', ok2,
            f'stitching={m2 and m2["stitching"]}(應=8)')

        # ── 步驟3: 某工序實際人數留空(NULL) → 當 0，不 NaN ────────────
        set_stitch_actuals(hid, sid, [None, 4])   # 第一列留空、第二列=4
        m3 = model_of()
        page.goto(BASE + '/bianche'); page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(SHOTS, '03_null_zero.png'), full_page=True)
        st = m3 and m3['stitching']
        ok3 = isinstance(st, (int, float)) and st == 4.0
        log('步驟3 實際人數留空(NULL)→當0加，不NaN/報錯', ok3,
            f'stitching={st}(應=4.0, 型別={type(st).__name__})')

        # ── 步驟4: 對比確認是「實際加總」不是「理論換算」 ─────────────
        ok4 = (theory_mp != 4.0) and (theory_mp != 5.0)  # 理論與實際明顯不同
        log('步驟4 數字是實際人數加總，非 standard_time 理論換算', ok4,
            f'理論~{theory_mp} vs 實際 5→8→4，兩者不同')

        browser.close()


if __name__ == '__main__':
    main()
