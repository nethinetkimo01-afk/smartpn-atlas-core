"""
版本控制「唯讀帳號只看鎖定版」Playwright 自動測試

驗證：
  - 唯讀帳號(read_only)進鞋型細表：版本下拉只有鎖定版、看得到內容、但完全唯讀
    （格子 disabled、無儲存/另存/設鎖定版/解鎖/刪除按鈕）
  - 唯讀帳號呼叫 save/另存/鎖定 API → 後端擋(403)
  - 沒鎖定版的鞋型：唯讀帳號看到「尚無鎖定版」提示，看不到一般版內容
  - admin(jim)同鞋型：能看所有版本、能編輯（不受唯讀限制）

隔離跑法：複製 DB → setup(建 read_only 帳號 viewer1 + 版本狀態) → 另起 server → 兩個瀏覽器
context(唯讀/admin) → 每步截圖 → 收尾刪副本。
用法：python flask_backend/test_output/test_readonly_locked.py
"""
import os, sys, time, shutil, subprocess, sqlite3, urllib.request, urllib.error

HERE    = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
SRC_DB  = os.path.join(BACKEND, 'data', 'atlas.db')
TEST_DB = os.path.join(HERE, '_ro_test.db')
SHOTS   = os.path.join(HERE, 'readonly_shots')
PORT    = 5099
BASE    = f'http://127.0.0.1:{PORT}'
RO_USER, RO_PW = 'viewer1', 'view123'

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

    # setup：建 read_only 帳號 + 版本狀態（在 server 起來前，用 db 函式）
    os.environ['ATLAS_DB'] = TEST_DB
    sys.path.insert(0, BACKEND)
    import database as db
    db.init_db()
    db.create_user(RO_USER, 'Viewer', 'read_only', RO_PW)
    c = sqlite3.connect(TEST_DB)
    hids = [r[0] for r in c.execute(
        "SELECT DISTINCT header_id FROM ie_process WHERE segment='cutting' ORDER BY header_id LIMIT 2")]
    A, B = hids
    sidA = c.execute('SELECT id FROM ie_stage WHERE header_id=? ORDER BY id LIMIT 1', (A,)).fetchone()[0]
    pidA = c.execute("SELECT id FROM ie_process WHERE header_id=? AND stage_id=? LIMIT 1", (A, sidA)).fetchone()[0]
    c.close()
    db.create_ie_stage(A, 'v2一般', None)        # A: 一般版 v2
    db.set_stage_approved(sidA, A, 'jim', '')     # A: 鎖定 v1(初版)
    print(f'header_A={A}(鎖定v1+一般v2)  header_B={B}(只有一般版)  sidA={sidA} pidA={pidA}')

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
        run_ui(A, B, sidA, pidA)
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


def login(page, user, pw):
    page.goto(BASE + '/login')
    page.fill('#username', user); page.fill('#password', pw)
    page.click('#btnLogin')
    page.wait_for_url('**/ie', timeout=10000)


def run_ui(A, B, sidA, pidA):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ── 唯讀帳號 context ───────────────────────────────────────────
        ro = browser.new_context().new_page()
        ro.on('dialog', lambda d: d.accept())
        login(ro, RO_USER, RO_PW)
        log('步驟0 唯讀帳號 viewer1 登入', True, '')

        # 步驟1: 進有鎖定版的鞋型 A → 下拉只有鎖定版、內容看得到、唯讀
        st = ro.request.get(f'{BASE}/api/ie/stages/{A}').json().get('stages', [])
        ro.goto(BASE + f'/ie/{A}/detail')
        ro.wait_for_selector('#mainContent input.cut-act-inp', timeout=15000)
        ro.wait_for_timeout(800)
        ro.screenshot(path=os.path.join(SHOTS, '01_ro_locked_view.png'), full_page=True)
        opt_cnt = ro.eval_on_selector('#stageSelect', 'el => el.options.length')
        all_locked = all(s['is_approved'] == 1 for s in st)
        inp_disabled = ro.eval_on_selector('#mainContent input.cut-act-inp', 'el => el.disabled')
        save_hidden = ro.eval_on_selector('#saveDropdown', 'el => el.style.display === "none"')
        appr_hidden = ro.eval_on_selector('#btn-approve-stage', 'el => el.style.display === "none"')
        del_hidden  = ro.eval_on_selector('#btn-delete-stage', 'el => el.style.display === "none"')
        ok1 = (len(st) == 1 and all_locked and opt_cnt == 1 and inp_disabled
               and save_hidden and appr_hidden and del_hidden)
        log('步驟1 唯讀進鎖定版鞋型：下拉只鎖定版+內容可見+唯讀', ok1,
            f'stages={len(st)}(locked={all_locked}), 下拉={opt_cnt}, 格disabled={inp_disabled}, '
            f'儲存hidden={save_hidden}, 設鎖定hidden={appr_hidden}, 刪除hidden={del_hidden}')

        # 步驟2: 唯讀呼叫 save/另存/鎖定 API → 後端擋(403)
        r_save = ro.request.post(f'{BASE}/api/ie/cell/save',
                                 data={'cell_id': pidA, 'stage_id': sidA, 'field': 'actual_operators', 'value': 9, 'user': RO_USER})
        r_newstage = ro.request.post(f'{BASE}/api/ie/stages/{A}', data={'stage_name': 'hack', 'source_stage_id': sidA})
        r_approve = ro.request.post(f'{BASE}/api/ie/stages/{A}/{sidA}/approve', data={'note': 'x'})
        ok2 = (r_save.status == 403 and r_newstage.status == 403 and r_approve.status == 403)
        log('步驟2 唯讀寫入 API 全被後端擋(403)', ok2,
            f'save={r_save.status}, 另存={r_newstage.status}, 鎖定={r_approve.status}')

        # 步驟3: 進沒鎖定版的鞋型 B → 「尚無鎖定版」提示、看不到一般版
        st_b = ro.request.get(f'{BASE}/api/ie/stages/{B}').json().get('stages', [])
        ro.goto(BASE + f'/ie/{B}/detail')
        ro.wait_for_timeout(1500)
        ro.screenshot(path=os.path.join(SHOTS, '02_ro_no_locked.png'), full_page=True)
        no_lock_msg = ro.get_by_text('尚無鎖定版').count() > 0
        has_inputs = ro.locator('#mainContent input.cut-act-inp').count()
        ok3 = (len(st_b) == 0 and no_lock_msg and has_inputs == 0)
        log('步驟3 唯讀進無鎖定版鞋型：顯示提示、看不到一般版', ok3,
            f'stages={len(st_b)}, 提示={no_lock_msg}, 工序格數={has_inputs}')

        # ── admin(jim) context 對照 ────────────────────────────────────
        adm = browser.new_context().new_page()
        adm.on('dialog', lambda d: d.accept())
        login(adm, 'jim', 'admin123')
        st_adm = adm.request.get(f'{BASE}/api/ie/stages/{A}').json().get('stages', [])
        adm.goto(BASE + f'/ie/{A}/detail')
        adm.wait_for_selector('#mainContent input.cut-act-inp', timeout=15000)
        adm.wait_for_timeout(800)
        adm.screenshot(path=os.path.join(SHOTS, '03_admin_all_versions.png'), full_page=True)
        adm_opt = adm.eval_on_selector('#stageSelect', 'el => el.options.length')
        adm_inp_enabled = adm.eval_on_selector('#mainContent input.cut-act-inp', 'el => !el.disabled')
        adm_save_visible = adm.eval_on_selector('#saveDropdown', 'el => el.style.display !== "none"')
        ok4 = (len(st_adm) == 2 and adm_opt == 2 and adm_inp_enabled and adm_save_visible)
        log('步驟4 admin 對照：看所有版本(2)+可編輯(不受唯讀限制)', ok4,
            f'stages={len(st_adm)}, 下拉={adm_opt}, 格可編輯={adm_inp_enabled}, 儲存可見={adm_save_visible}')

        browser.close()


if __name__ == '__main__':
    main()
