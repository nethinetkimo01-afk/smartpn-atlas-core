"""
版本控制 Step 4c「外移(P/Q/R)改實際人數 + 統一 C2B 基礎」Playwright 自動測試

驗證：
  - 外移人力 = 對應 offline zone 的 actual_operators 加總（不是 theory_mp 理論快照）
  - 改實際人數 → 外移跟著變
  - 不承接(is_checked=0) → 不算進外移（勾選邏輯保留）
  - 承接勾選在改實際人數重讀後不被洗掉
  - C2B = 主線實際 + 外移實際（數字 = 兩者相加）

隔離跑法：複製 DB → 另起 server(5099) → 真開瀏覽器 → 每步截圖 → 收尾刪副本。
（實際人數用直接寫 test DB 模擬「IE 已填」；勾選/prefill 走 API；驗證走 API。）
用法：python flask_backend/test_output/test_step4c_offline_actual.py
"""
import os, sys, time, shutil, subprocess, sqlite3, urllib.request, urllib.error

HERE    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
SRC_DB  = os.path.join(BACKEND, 'data', 'atlas.db')
TEST_DB = os.path.join(HERE, '_s4c_test.db')
SHOTS   = os.path.join(HERE, 'step4c_shots')
PORT    = 5099
BASE    = f'http://127.0.0.1:{PORT}'
MONTH   = '2026-07'
QZONE   = '電腦針車'   # 外移 Q

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


def set_zone_actuals(hid, sid, zone, values):
    """歸零該 zone 所有工序 actual，前 N 列設 values（確保加總 = sum(values)）。"""
    c = db_conn()
    rids = [r[0] for r in c.execute(
        "SELECT id FROM ie_process WHERE header_id=? AND stage_id=? AND zone=? ORDER BY id",
        (hid, sid, zone)).fetchall()]
    for i, rid in enumerate(rids):
        v = values[i] if i < len(values) else 0
        c.execute('UPDATE ie_process SET actual_operators=? WHERE id=?', (v, rid))
    c.commit(); c.close()
    return rids


def zone_item_ids(hid, zone):
    c = db_conn()
    ids = [r[0] for r in c.execute(
        'SELECT id FROM allocation_item WHERE header_id=? AND zone=? AND month=?',
        (hid, zone, MONTH)).fetchall()]
    c.close()
    return ids


def setup_pick():
    c = db_conn()
    row = c.execute('''
        SELECT oa.header_id, o.art, o.model_name, ip2.stage_id
        FROM ds04_orders o
        JOIN ob_articles oa ON oa.art=o.art
        JOIN ie_process ip2 ON ip2.header_id=oa.header_id AND ip2.zone=?
        WHERE COALESCE(o.is_deleted,0)=0 AND COALESCE(o.is_outsource_upper,0)=0
        GROUP BY oa.header_id HAVING COUNT(*)>=2 LIMIT 1''', (QZONE,)).fetchone()
    c.close()
    return row


def main():
    if not os.path.exists(SRC_DB):
        print('找不到來源 DB:', SRC_DB); sys.exit(1)
    for ext in ('', '-wal', '-shm'):
        if os.path.exists(TEST_DB + ext):
            os.remove(TEST_DB + ext)
    shutil.copy2(SRC_DB, TEST_DB)

    pick = setup_pick()
    if not pick:
        print('找不到合適 header'); sys.exit(1)
    hid, art, model, sid = pick
    c = db_conn()
    theory = c.execute(
        "SELECT COALESCE(SUM(standard_time),0) FROM ie_process "
        "WHERE header_id=? AND stage_id=? AND zone=? AND standard_time>0",
        (hid, sid, QZONE)).fetchone()[0]
    c.close()
    theory_mp = round(theory * 120 / 3600.0, 1)
    print(f'測試 header={hid} art={art} model={model}  {QZONE} theory~{theory_mp}')

    set_zone_actuals(hid, sid, QZONE, [3, 2])   # 實際人數 3+2=5

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

        def model_of():
            d = page.request.get(f'{BASE}/api/bianzhi/detail?month={MONTH}').json()
            for lg in d.get('leans', []):
                for m in lg.get('models', []):
                    if art in (m.get('arts') or ''):
                        return m
            return None

        def item_checked(iid):
            r = page.request.get(f'{BASE}/api/allocation/items?month={MONTH}&header_id={hid}').json()
            for g in r.get('groups', []):
                for it in g.get('items', []):
                    if it['id'] == iid:
                        return it['is_checked']
            return None

        # 登入 + 鎖定 + allocation 身分 + prefill
        page.goto(BASE + '/login')
        page.fill('#username', 'jim'); page.fill('#password', 'admin123')
        page.click('#btnLogin'); page.wait_for_url('**/ie', timeout=10000)
        page.request.post(f'{BASE}/api/ie/stages/{hid}/{sid}/approve', data={'note': 's4c'})
        page.request.post(f'{BASE}/api/allocation/login', data={'username': 'jim'})
        page.request.post(f'{BASE}/api/allocation/prefill', data={'header_id': hid, 'month': MONTH})
        log('步驟0 登入+鎖定+prefill', True, f'header={hid}')

        qids = zone_item_ids(hid, QZONE)

        # ── 步驟1: 承接(預設勾選)→ 外移Q = 實際人數(5)，非理論 ───────
        m1 = model_of()
        page.goto(BASE + '/bianche'); page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(SHOTS, '01_moved_actual_5.png'), full_page=True)
        ok1 = m1 and m1['q_ext'] == 5.0 and m1['q_ext'] != theory_mp
        log('步驟1 承接→外移Q=實際人數(5)，非理論換算', ok1,
            f'q_ext={m1 and m1["q_ext"]}(應=5, 理論~{theory_mp})')

        # ── 步驟2: 改實際人數 4+4=8 → 外移跟著變 ──────────────────────
        set_zone_actuals(hid, sid, QZONE, [4, 4])
        m2 = model_of()
        page.goto(BASE + '/bianche'); page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(SHOTS, '02_moved_actual_8.png'), full_page=True)
        ok2 = m2 and m2['q_ext'] == 8.0
        log('步驟2 改實際人數(4+4)→外移Q=8(實際基礎)', ok2, f'q_ext={m2 and m2["q_ext"]}(應=8)')

        # ── 步驟3: 不承接(uncheck)→ 不算進外移 ────────────────────────
        for iid in qids:
            page.request.post(f'{BASE}/api/allocation/check', data={'id': iid, 'is_checked': 0})
        m3 = model_of()
        page.goto(BASE + '/bianche'); page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(SHOTS, '03_unchecked_not_counted.png'), full_page=True)
        ok3 = m3 and (m3['q_ext'] or 0) == 0
        log('步驟3 不承接(uncheck)→不算進外移(勾選邏輯保留)', ok3, f'q_ext={m3 and m3["q_ext"]}(應=0)')

        # ── 步驟4: 重新承接 + 改實際人數重讀 → 勾選還在、外移用新實際 ──
        for iid in qids:
            page.request.post(f'{BASE}/api/allocation/check', data={'id': iid, 'is_checked': 1})
        set_zone_actuals(hid, sid, QZONE, [6, 0])   # 實際=6
        still_checked = all(item_checked(iid) == 1 for iid in qids)
        m4 = model_of()
        page.goto(BASE + '/bianche'); page.wait_for_timeout(1200)
        page.screenshot(path=os.path.join(SHOTS, '04_recheck_preserved.png'), full_page=True)
        ok4 = still_checked and m4 and m4['q_ext'] == 6.0
        log('步驟4 承接勾選改實際人數重讀後保留', ok4,
            f'仍勾選={still_checked}, q_ext={m4 and m4["q_ext"]}(應=6)')

        # ── 步驟5: C2B = 主線(k) + 外移(p+q+r)，基礎一致 ─────────────
        m5 = model_of()
        k = m5['total_k'] or 0
        pqr = (m5['p_ext'] or 0) + (m5['q_ext'] or 0) + (m5['r_ext'] or 0)
        expect = round(k + pqr, 1)
        page.screenshot(path=os.path.join(SHOTS, '05_c2b_consistent.png'), full_page=True)
        ok5 = m5['c2b'] == expect
        log('步驟5 C2B = 主線實際 + 外移實際(兩者相加)', ok5,
            f'c2b={m5["c2b"]} == k({k})+外移({round(pqr,1)})={expect}')

        browser.close()


if __name__ == '__main__':
    main()
