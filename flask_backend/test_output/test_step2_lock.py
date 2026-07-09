"""
版本控制 Step 2「鎖定版語意」Playwright 自動測試

驗證：
  - 設鎖定版(is_approved=1)同 header 只一個、自動解舊
  - 鎖定版「儲存」被擋(前端鈕 disable + 後端拒絕)、值不變
  - 鎖定版「另存新版本」仍有效(複製內容)
  - 解鎖後可再「儲存」
  - 設鎖定版有記 lock_history(時間/版本/設定者/備註)

隔離跑法同 Step 1：複製 DB → 另起 server(5099) → 真開瀏覽器操作 → 每步截圖 → 收尾刪副本。
用法：python flask_backend/test_output/test_step2_lock.py
"""
import os, sys, time, shutil, subprocess, sqlite3, urllib.request, urllib.error

HERE    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
SRC_DB  = os.path.join(BACKEND, 'data', 'atlas.db')
TEST_DB = os.path.join(HERE, '_s2_test.db')
SHOTS   = os.path.join(HERE, 'step2_shots')
PORT    = 5099
BASE    = f'http://127.0.0.1:{PORT}'

os.makedirs(SHOTS, exist_ok=True)
results = []
NOTE = '鎖定備註測試-套用7月編制'


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


def pick_header():
    c = db_conn()
    hid = c.execute(
        "SELECT header_id FROM ie_process WHERE segment='cutting' "
        "AND (flag IS NULL OR flag!='deleted') "
        "GROUP BY header_id ORDER BY COUNT(*) DESC LIMIT 1").fetchone()[0]
    c.close()
    return hid


def main():
    if not os.path.exists(SRC_DB):
        print('找不到來源 DB:', SRC_DB); sys.exit(1)
    for ext in ('', '-wal', '-shm'):
        if os.path.exists(TEST_DB + ext):
            os.remove(TEST_DB + ext)
    shutil.copy2(SRC_DB, TEST_DB)
    hid = pick_header()
    print(f'測試 DB: {TEST_DB}\n測試 header_id: {hid}')

    env = dict(os.environ)
    env['ATLAS_DB'] = TEST_DB
    env['ATLAS_SECRET'] = 'ver-test-secret'
    server = subprocess.Popen(
        [sys.executable, '-c',
         # 與 serve.py / app.py __main__ 一致：啟動前先 init_db（建 lock_history 等）
         "import database as db; db.init_db(); "
         "from app import app; app.run(host='127.0.0.1', port=%d, threaded=True)" % PORT],
        cwd=BACKEND, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_server():
            log('server 啟動', False, '逾時'); raise SystemExit(1)
        log('server 啟動', True, BASE)
        run_ui(hid)
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


def run_ui(hid):
    from playwright.sync_api import sync_playwright
    ACT_SEL = '#mainContent input.cut-act-inp'
    next_stage_name = {'v': 'v2鎖'}   # 可變：another-save 時用

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context()
        page = ctx.new_page()
        page.on('console', lambda m: (m.type == 'error') and print('  [console.error]', m.text))

        def on_dialog(d):
            if d.type == 'prompt':
                msg = d.message or ''
                if '版本名稱' in msg:
                    d.accept(next_stage_name['v'])
                elif '備註' in msg:
                    d.accept(NOTE)
                else:
                    d.accept('')
            else:
                d.accept()   # confirm/alert
        page.on('dialog', on_dialog)

        def api_stages():
            r = page.request.get(f'{BASE}/api/ie/stages/{hid}')
            return r.json().get('stages', [])

        def stage_by_name(nm):
            for s in api_stages():
                if s['stage_name'] == nm:
                    return s
            return None

        # ── 登入 + 進 cutting ──────────────────────────────────────────
        page.goto(BASE + '/login')
        page.fill('#username', 'jim'); page.fill('#password', 'admin123')
        page.click('#btnLogin')
        page.wait_for_url('**/ie', timeout=10000)
        page.goto(BASE + f'/ie/{hid}/detail')
        page.wait_for_selector(ACT_SEL, timeout=15000)
        page.wait_for_timeout(800)
        log('步驟0 登入 jim/admin123 進 cutting', True, f'header={hid}')

        # ── 步驟1: 另存 v2 → 設 v2 為鎖定版 ───────────────────────────
        n0 = len(api_stages())
        next_stage_name['v'] = 'v2鎖'
        page.click('text=儲存 ▼'); page.click('text=另存新階段')
        page.wait_for_function("c => document.querySelectorAll('#stageSelect option').length > c",
                               arg=n0, timeout=10000)
        page.wait_for_selector(ACT_SEL, timeout=15000)
        page.wait_for_timeout(500)
        v2 = stage_by_name('v2鎖')
        # 點「設為鎖定版」→ confirm→note prompt
        page.click('#btn-approve-stage')
        page.wait_for_timeout(1200)   # 等 approve + reloadStages
        stages = api_stages()
        v2 = stage_by_name('v2鎖')
        approved = [s for s in stages if s['is_approved']]
        page.screenshot(path=os.path.join(SHOTS, '01_v2_locked.png'), full_page=True)
        ok1 = v2 and v2['is_approved'] == 1 and len(approved) == 1 and approved[0]['id'] == v2['id']
        log('步驟1 設 v2 為鎖定版(互斥, 只一個)', ok1,
            f'v2.is_approved={v2 and v2["is_approved"]}, approved數={len(approved)}')

        # 前端：鎖定徽章顯示、儲存鈕 disable、解鎖鈕出現
        badge_vis = page.eval_on_selector('#lock-badge', 'el => el.style.display !== "none"')
        save_dis  = page.eval_on_selector('#btn-save-current', 'el => el.disabled')
        unlock_vis= page.eval_on_selector('#btn-unlock-stage', 'el => el.style.display !== "none"')
        log('步驟2 前端鎖定 UI(徽章顯示/儲存disable/解鎖鈕出現)',
            badge_vis and save_dis and unlock_vis,
            f'徽章={badge_vis}, 儲存disabled={save_dis}, 解鎖鈕={unlock_vis}')

        # ── 步驟3: 鎖定版試「儲存」→ 後端拒絕、值不變 ─────────────────
        c = db_conn()
        prow = c.execute('SELECT id, actual_operators FROM ie_process WHERE stage_id=? LIMIT 1',
                         (v2['id'],)).fetchone()
        c.close()
        pid, before_val = prow[0], prow[1]
        resp = page.request.post(f'{BASE}/api/ie/cell/save',
                                 data={'cell_id': pid, 'stage_id': v2['id'],
                                       'field': 'actual_operators', 'value': 987654, 'user': 'jim'})
        j = resp.json()
        c = db_conn()
        after_val = c.execute('SELECT actual_operators FROM ie_process WHERE id=?', (pid,)).fetchone()[0]
        c.close()
        page.screenshot(path=os.path.join(SHOTS, '02_save_blocked.png'), full_page=True)
        ok3 = (j.get('ok') is False) and j.get('locked') and (after_val == before_val)
        log('步驟3 鎖定版儲存被後端擋 + 值不變', ok3,
            f'save回應={j}, 值 前={before_val} 後={after_val}')

        # ── 步驟4: 鎖定版「另存新版本」v3 → 成功複製 ──────────────────
        n1 = len(api_stages())
        next_stage_name['v'] = 'v3'
        page.click('text=儲存 ▼'); page.click('text=另存新階段')
        page.wait_for_function("c => document.querySelectorAll('#stageSelect option').length > c",
                               arg=n1, timeout=10000)
        page.wait_for_selector(ACT_SEL, timeout=15000)
        page.wait_for_timeout(500)
        v3 = stage_by_name('v3')
        c = db_conn()
        cnt_v2 = c.execute('SELECT COUNT(*) FROM ie_process WHERE stage_id=?', (v2['id'],)).fetchone()[0]
        cnt_v3 = c.execute('SELECT COUNT(*) FROM ie_process WHERE stage_id=?', (v3['id'],)).fetchone()[0]
        c.close()
        page.screenshot(path=os.path.join(SHOTS, '03_v3_saved_as.png'), full_page=True)
        ok4 = v3 and v3['is_approved'] == 0 and cnt_v3 == cnt_v2 and cnt_v3 > 0
        log('步驟4 鎖定版「另存新版本」v3 成功(複製內容, 未鎖定)', ok4,
            f'v3.is_approved={v3 and v3["is_approved"]}, v2工序={cnt_v2}, v3工序={cnt_v3}')

        # ── 步驟5: 解鎖 v2 → 再儲存成功 ───────────────────────────────
        page.select_option('#stageSelect', value=str(v2['id']))
        page.wait_for_selector(ACT_SEL, timeout=15000)
        page.wait_for_timeout(500)
        page.click('#btn-unlock-stage')          # confirm → accept
        page.wait_for_timeout(1000)
        v2b = stage_by_name('v2鎖')
        # 解鎖後 save 應成功
        resp2 = page.request.post(f'{BASE}/api/ie/cell/save',
                                  data={'cell_id': pid, 'stage_id': v2['id'],
                                        'field': 'actual_operators', 'value': 321, 'user': 'jim'})
        j2 = resp2.json()
        c = db_conn()
        val_after = c.execute('SELECT actual_operators FROM ie_process WHERE id=?', (pid,)).fetchone()[0]
        c.close()
        page.screenshot(path=os.path.join(SHOTS, '04_unlocked_saved.png'), full_page=True)
        ok5 = v2b and v2b['is_approved'] == 0 and j2.get('ok') and str(val_after) == '321.0'
        log('步驟5 解鎖 v2 後可再儲存', ok5,
            f'v2.is_approved={v2b and v2b["is_approved"]}, save={j2.get("ok")}, 新值={val_after}')

        # ── 步驟6: lock_history 有記錄(含備註) ────────────────────────
        hist = page.request.get(f'{BASE}/api/ie/stages/{hid}/lock_history').json().get('history', [])
        rec = next((h for h in hist if h.get('note') == NOTE), None)
        # 開 UI 歷史彈窗截圖
        page.click('#btn-lock-hist')
        page.wait_for_selector('#lockHistModal', state='visible', timeout=5000)
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(SHOTS, '05_lock_history.png'), full_page=True)
        ok6 = bool(rec) and rec.get('set_by') == 'jim' and rec.get('stage_name') == 'v2鎖' and rec.get('effective_at')
        log('步驟6 lock_history 有記錄(版本/設定者/時間/備註)', ok6,
            f'記錄={rec}')

        browser.close()


if __name__ == '__main__':
    main()
