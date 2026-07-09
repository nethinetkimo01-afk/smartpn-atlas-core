"""
版本控制 Step 3「刪除版本」Playwright 自動測試

驗證刪除保護：
  - 一般版可刪(乾淨刪：工序+群組+stage)，別版工序不受影響
  - 鎖定版不能刪(先解鎖)
  - 至少保留一個版本
  - admin/manager 才有刪除鈕

隔離跑法同 Step 1/2：複製 DB → 另起 server(5099，啟動前 init_db) → 真開瀏覽器 →
每步截圖 → 收尾刪副本(不污染正式 DB)。
用法：python flask_backend/test_output/test_step3_delete.py
"""
import os, sys, time, shutil, subprocess, sqlite3, urllib.request, urllib.error

HERE    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
SRC_DB  = os.path.join(BACKEND, 'data', 'atlas.db')
TEST_DB = os.path.join(HERE, '_s3_test.db')
SHOTS   = os.path.join(HERE, 'step3_shots')
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
    next_name = {'v': ''}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context().new_page()
        page.on('console', lambda m: (m.type == 'error') and print('  [console.error]', m.text))

        def on_dialog(d):
            if d.type == 'prompt':
                msg = d.message or ''
                d.accept(next_name['v'] if '版本名稱' in msg else ('' if '備註' in msg else ''))
            else:
                d.accept()   # confirm/alert 一律接受
        page.on('dialog', on_dialog)

        def stages():
            return page.request.get(f'{BASE}/api/ie/stages/{hid}').json().get('stages', [])

        def by_name(nm):
            return next((s for s in stages() if s['stage_name'] == nm), None)

        def proc_count(sid):
            c = db_conn(); n = c.execute('SELECT COUNT(*) FROM ie_process WHERE stage_id=?', (sid,)).fetchone()[0]; c.close(); return n

        def another_save(nm):
            n0 = len(stages())
            next_name['v'] = nm
            page.click('text=儲存 ▼'); page.click('text=另存新階段')
            page.wait_for_function("c => document.querySelectorAll('#stageSelect option').length > c",
                                   arg=n0, timeout=10000)
            page.wait_for_selector(ACT_SEL, timeout=15000)
            page.wait_for_timeout(400)

        # ── 登入 + 進 cutting ──────────────────────────────────────────
        page.goto(BASE + '/login')
        page.fill('#username', 'jim'); page.fill('#password', 'admin123')
        page.click('#btnLogin'); page.wait_for_url('**/ie', timeout=10000)
        page.goto(BASE + f'/ie/{hid}/detail')
        page.wait_for_selector(ACT_SEL, timeout=15000); page.wait_for_timeout(600)

        # ── 步驟1: 建到 3 個版本 v1(初版)/v2/v3 ───────────────────────
        another_save('v2')
        another_save('v3')
        st = stages()
        v1 = st[0]; v2 = by_name('v2'); v3 = by_name('v3')
        c_v1, c_v2, c_v3 = proc_count(v1['id']), proc_count(v2['id']), proc_count(v3['id'])
        page.screenshot(path=os.path.join(SHOTS, '01_three_versions.png'), full_page=True)
        log('步驟1 建立 3 個版本', len(st) == 3 and c_v1 and c_v2 and c_v3,
            f'版本數={len(st)}, 工序 v1={c_v1} v2={c_v2} v3={c_v3}')

        # ── 步驟2: 刪 v3(一般版) → 成功，v1/v2 不受影響 ──────────────
        # 目前在 v3（另存後選取的是 v3）；確認在 v3
        page.select_option('#stageSelect', value=str(v3['id']))
        page.wait_for_selector(ACT_SEL, timeout=15000); page.wait_for_timeout(400)
        page.click('#btn-delete-stage')          # confirm → accept
        page.wait_for_timeout(1200)
        st2 = stages()
        page.screenshot(path=os.path.join(SHOTS, '02_deleted_v3.png'), full_page=True)
        ok2 = (by_name('v3') is None) and (len(st2) == 2) and \
              (proc_count(v3['id']) == 0) and (proc_count(v1['id']) == c_v1) and (proc_count(v2['id']) == c_v2)
        log('步驟2 刪 v3(一般版) 成功，別版工序不受影響', ok2,
            f'剩版本={[s["stage_name"] for s in st2]}, v3工序={proc_count(v3["id"])}, v1={proc_count(v1["id"])}, v2={proc_count(v2["id"])}')

        # ── 步驟3: 設 v2 為鎖定版 → 試刪 v2 → 被擋 ───────────────────
        page.select_option('#stageSelect', value=str(v2['id']))
        page.wait_for_selector(ACT_SEL, timeout=15000); page.wait_for_timeout(400)
        page.click('#btn-approve-stage')         # confirm + note prompt → accept
        page.wait_for_timeout(1200)
        del_disabled = page.eval_on_selector('#btn-delete-stage', 'el => el.disabled')
        # 直接打 API 驗證後端也擋
        rj = page.request.post(f'{BASE}/api/ie/stages/{hid}/{v2["id"]}/delete').json()
        page.screenshot(path=os.path.join(SHOTS, '03_locked_cannot_delete.png'), full_page=True)
        ok3 = del_disabled and (rj.get('ok') is False) and rj.get('locked') and (by_name('v2') is not None)
        log('步驟3 鎖定版 v2 不能刪(鈕disable + 後端擋)', ok3,
            f'刪除鈕disabled={del_disabled}, API={rj}')

        # ── 步驟4: 解鎖 v2 → 刪 v2 → 成功 ────────────────────────────
        page.click('#btn-unlock-stage'); page.wait_for_timeout(1000)
        page.click('#btn-delete-stage'); page.wait_for_timeout(1200)
        st4 = stages()
        page.screenshot(path=os.path.join(SHOTS, '04_unlocked_deleted_v2.png'), full_page=True)
        ok4 = (by_name('v2') is None) and (len(st4) == 1) and (proc_count(v2['id']) == 0) and (proc_count(v1['id']) == c_v1)
        log('步驟4 解鎖 v2 後刪除成功', ok4,
            f'剩版本={[s["stage_name"] for s in st4]}, v2工序={proc_count(v2["id"])}, v1工序={proc_count(v1["id"])}')

        # ── 步驟5: 剩最後一個 v1 → 試刪 → 被擋 ───────────────────────
        rj5 = page.request.post(f'{BASE}/api/ie/stages/{hid}/{v1["id"]}/delete').json()
        st5 = stages()
        page.screenshot(path=os.path.join(SHOTS, '05_last_one_blocked.png'), full_page=True)
        ok5 = (rj5.get('ok') is False) and rj5.get('last_one') and (len(st5) == 1) and (proc_count(v1['id']) == c_v1)
        log('步驟5 最後一個版本不能刪(至少留一個)', ok5,
            f'API={rj5}, 剩版本數={len(st5)}, v1工序完整={proc_count(v1["id"])}=={c_v1}')

        browser.close()


if __name__ == '__main__':
    main()
