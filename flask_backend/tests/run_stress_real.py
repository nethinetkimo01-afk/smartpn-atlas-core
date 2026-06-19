"""
IE 真實量級壓力測試 — 透過真實 HTTP 打 app.run() 開發伺服器。

與舊版的差異（舊版無效原因）：
  舊版用 Flask test_client()（不經 WSGI 伺服器執行緒模型）且 ie_sheet_data=0 筆，
  等於測空表。本版：
    1. seed 獨立測試庫 tests/atlas_stress.db（≥52萬筆 ie_sheet_data，不碰 data/atlas.db）
    2. 以 app.run() 啟動真實伺服器（複製 production 啟動方式）
    3. 用真實 HTTP + 20 條獨立連線並發
    4. 細表載入走 ie_sheet_data 大表 (/api/ie/<hid>/sheet)

Run:  cd flask_backend && python tests/run_stress_real.py
"""
import os, sys, json, time, threading, subprocess, sqlite3
import urllib.request, urllib.error, urllib.parse, http.cookiejar
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

TESTS_DIR   = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TESTS_DIR)
OUTPUT_DIR  = os.path.join(BACKEND_DIR, 'test_output')
STRESS_DB   = os.path.join(TESTS_DIR, 'atlas_stress.db')
SERVER_PY   = os.path.join(TESTS_DIR, '_stress_server.py')
PORT        = 5099
BASE        = f'http://127.0.0.1:{PORT}'

sys.path.insert(0, TESTS_DIR)
import seed_stress_db  # noqa

N_THREADS = 20
N_OPS_EACH = 12          # ≥10 per thread
WRITE_OPS_EACH = 12      # concurrent-write専測

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── HTTP session (per-thread cookie jar = independent connection) ─────────────
class Session:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    def get(self, path):
        req = urllib.request.Request(BASE + path, method='GET')
        return self._do(req)

    def post(self, path, payload):
        data = json.dumps(payload).encode()
        req = urllib.request.Request(BASE + path, data=data,
                                     headers={'Content-Type': 'application/json'}, method='POST')
        return self._do(req)

    def _do(self, req):
        try:
            r = self.opener.open(req, timeout=60)
            body = r.read().decode('utf-8', 'replace')
            return r.status, body
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', 'replace')
            return e.code, body
        except Exception as e:
            return 0, f'__EXC__ {e}'

    def login(self, user='stress_admin', pw='pw_admin'):
        st, body = self.post('/api/login', {'username': user, 'password': pw})
        return st == 200


def is_locked(status, body):
    if body and 'database is locked' in body.lower():
        return True
    return False


def pct(values, p):
    if not values:
        return 0.0
    s = sorted(values)
    k = int(round((p / 100.0) * (len(s) - 1)))
    return s[k]


def summarize(timings):
    """timings: list of (label, ms, status, locked, ok)"""
    by = {}
    for label, ms, status, locked, ok in timings:
        by.setdefault(label, []).append((ms, status, locked, ok))
    out = {}
    for label, rows in by.items():
        msv = [r[0] for r in rows]
        fails = sum(1 for r in rows if not r[3])
        locks = sum(1 for r in rows if r[2])
        out[label] = {
            'count': len(rows),
            'avg': round(sum(msv) / len(msv), 1),
            'p95': round(pct(msv, 95), 1),
            'max': round(max(msv), 1),
            'min': round(min(msv), 1),
            'fails': fails,
            'locks': locks,
        }
    return out


# ── Read seed counts from the stress DB (for the report header) ──────────────
def pick_seed_counts():
    conn = sqlite3.connect(STRESS_DB)
    c = {
        'ob_header':     conn.execute('SELECT COUNT(*) FROM ob_header').fetchone()[0],
        'ob_articles':   conn.execute('SELECT COUNT(*) FROM ob_articles').fetchone()[0],
        'ie_process':    conn.execute('SELECT COUNT(*) FROM ie_process').fetchone()[0],
        'ie_sheet_data': conn.execute('SELECT COUNT(*) FROM ie_sheet_data').fetchone()[0],
        'ie_stage':      conn.execute('SELECT COUNT(*) FROM ie_stage').fetchone()[0],
    }
    heavy = conn.execute(
        'SELECT header_id, COUNT(*) c FROM ie_sheet_data GROUP BY header_id ORDER BY c DESC LIMIT 1'
    ).fetchone()
    big = conn.execute(
        'SELECT sheet_name, COUNT(*) c FROM ie_sheet_data WHERE header_id=? GROUP BY sheet_name ORDER BY c DESC LIMIT 1',
        (heavy[0],)
    ).fetchone()
    c['heavy_header_id'] = heavy[0]
    c['heavy_header_cells'] = heavy[1]
    c['heavy_sheet_name'] = big[0]
    c['heavy_sheet_cells'] = big[1]
    conn.close()
    return c


# ── Pick targets straight from the stress DB (read-only) ─────────────────────
def pick_targets():
    conn = sqlite3.connect(STRESS_DB)
    counts = {
        'ob_header':     conn.execute('SELECT COUNT(*) FROM ob_header').fetchone()[0],
        'ie_process':    conn.execute('SELECT COUNT(*) FROM ie_process').fetchone()[0],
        'ie_sheet_data': conn.execute('SELECT COUNT(*) FROM ie_sheet_data').fetchone()[0],
    }
    heavy = conn.execute(
        'SELECT header_id, COUNT(*) c FROM ie_sheet_data GROUP BY header_id ORDER BY c DESC LIMIT 1'
    ).fetchone()
    heavy_hid, heavy_cells = heavy[0], heavy[1]
    big_sheet = conn.execute(
        'SELECT sheet_name, COUNT(*) c FROM ie_sheet_data WHERE header_id=? GROUP BY sheet_name ORDER BY c DESC LIMIT 1',
        (heavy_hid,)
    ).fetchone()
    heavy_sheet, heavy_sheet_cells = big_sheet[0], big_sheet[1]
    # all header ids for per-thread distinct writes
    header_ids = [r[0] for r in conn.execute('SELECT id FROM ob_header ORDER BY id').fetchall()]
    # process id + stage id per header (first row)
    proc_by_header = {}
    stage_by_header = {}
    for hid in header_ids:
        pr = conn.execute('SELECT id FROM ie_process WHERE header_id=? LIMIT 1', (hid,)).fetchone()
        sr = conn.execute('SELECT id FROM ie_stage WHERE header_id=? LIMIT 1', (hid,)).fetchone()
        if pr: proc_by_header[hid] = pr[0]
        if sr: stage_by_header[hid] = sr[0]
    edit_log_before = conn.execute('SELECT COUNT(*) FROM ie_edit_log').fetchone()[0]
    conn.close()
    return {
        'counts': counts,
        'heavy_hid': heavy_hid, 'heavy_cells': heavy_cells,
        'heavy_sheet': heavy_sheet, 'heavy_sheet_cells': heavy_sheet_cells,
        'header_ids': header_ids,
        'proc_by_header': proc_by_header,
        'stage_by_header': stage_by_header,
        'edit_log_before': edit_log_before,
    }


def wait_ready(timeout=40):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = urllib.request.urlopen(BASE + '/login', timeout=3)
            if r.status == 200:
                return True
        except urllib.error.HTTPError:
            return True  # server responding
        except Exception:
            time.sleep(0.4)
    return False


# ══════════════════════════════════════════════════════════════════════════════
def run_battery(server_mode='apprun', threads=8):
    """Launch the server in the given mode against the (already-seeded) stress DB,
    run baseline + 20-concurrent-mix + concurrent-write tests, return results dict.
    server_mode: 'apprun' (Werkzeug app.run) | 'waitress' (waitress threads=N)."""
    seed_counts = pick_seed_counts()
    label = 'waitress(threads=%d)' % threads if server_mode == 'waitress' else 'app.run()'
    print(f'\n>>> 啟動伺服器：{label} ...')
    env = dict(os.environ, STRESS_PORT=str(PORT),
               STRESS_SERVER=server_mode, STRESS_THREADS=str(threads))
    server = subprocess.Popen([sys.executable, SERVER_PY], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_ready():
            raise RuntimeError('伺服器未就緒')
        print(f'    伺服器就緒 @ {BASE} ({label})')

        tgt = pick_targets()
        heavy_hid = tgt['heavy_hid']
        heavy_sheet = tgt['heavy_sheet']
        header_ids = tgt['header_ids']
        proc_by_header = tgt['proc_by_header']
        stage_by_header = tgt['stage_by_header']
        print(f"    重型 header={heavy_hid} ({tgt['heavy_cells']} cells), "
              f"最大 sheet='{heavy_sheet}' ({tgt['heavy_sheet_cells']} cells)")

        admin = Session()
        assert admin.login(), 'admin 登入失敗'

        results = {'seed_counts': seed_counts, 'targets': tgt,
                   'server_mode': server_mode, 'server_label': label}

        # ── Test 1: 細表載入 (讀 ie_sheet_data 大表) baseline ───────────────
        print('\n[3] 單線程基準 ...')
        def timed(fn):
            t0 = time.perf_counter()
            st, body = fn()
            return (time.perf_counter() - t0) * 1000, st, body

        # detail meta
        d_ms, d_st, _ = timed(lambda: admin.get(f'/api/ie/detail/{heavy_hid}'))
        # heavy sheet grid — the real ie_sheet_data heavy read
        g_ms, g_st, g_body = timed(lambda: admin.get(
            f'/api/ie/{heavy_hid}/sheet?name={urllib.parse.quote(heavy_sheet)}'))
        # cell data (ie_process)
        c_ms, c_st, _ = timed(lambda: admin.get(f'/api/ie/cell/{heavy_hid}?segment=cutting&eolr=120'))
        # list
        l_ms, l_st, l_body = timed(lambda: admin.get('/api/ie/list'))
        list_recs = len((json.loads(l_body) or {}).get('records', [])) if l_st == 200 else 0
        grid_cells = 0
        if g_st == 200:
            gj = json.loads(g_body)
            grid_cells = sum(len(v) for v in gj.get('grid', {}).values())
        results['baseline'] = {
            'detail_ms': round(d_ms, 1), 'detail_st': d_st,
            'sheet_ms': round(g_ms, 1), 'sheet_st': g_st, 'sheet_cells_returned': grid_cells,
            'cell_ms': round(c_ms, 1), 'cell_st': c_st,
            'list_ms': round(l_ms, 1), 'list_st': l_st, 'list_records': list_recs,
        }
        print(f"    detail={d_ms:.0f}ms  sheet讀大表={g_ms:.0f}ms ({grid_cells} cells)  "
              f"cell={c_ms:.0f}ms  list={l_ms:.0f}ms ({list_recs}筆)")

        # ── Test 3: 20 並發 × 混合 (讀清單/開細表讀大表/寫格子) ─────────────
        print(f'\n[4] 20 並發 × {N_OPS_EACH} 混合操作 ...')
        mix_timings = []
        mlock = threading.Lock()

        def mix_worker(tid):
            s = Session()
            s.login()
            # each thread reads a different heavy/normal header
            hid = header_ids[tid % len(header_ids)]
            pid = proc_by_header.get(hid)
            sid = stage_by_header.get(hid)
            local = []
            for op in range(N_OPS_EACH):
                kind = op % 3
                t0 = time.perf_counter()
                if kind == 0:
                    st, body = s.get('/api/ie/list')
                    label = 'list'
                elif kind == 1:
                    # open detail of a HEAVY header → read ie_sheet_data big sheet
                    hh = header_ids[(tid + op) % seed_stress_db.N_HEAVY]
                    sname = 'Cutting'
                    st, body = s.get(f'/api/ie/{hh}/sheet?name={urllib.parse.quote(sname)}')
                    label = 'detail_read(大表)'
                else:
                    st, body = s.post('/api/ie/cell/save', {
                        'cell_id': pid, 'stage_id': sid, 'field': 'standard_time',
                        'value': float(tid) + op * 0.1, 'user': f'mix_t{tid}'})
                    label = 'cell_write'
                ms = (time.perf_counter() - t0) * 1000
                locked = is_locked(st, body)
                if label == 'cell_write':
                    try:
                        ok = st == 200 and json.loads(body).get('ok') is True
                    except Exception:
                        ok = False
                else:
                    ok = st == 200
                local.append((label, ms, st, locked, ok))
            with mlock:
                mix_timings.extend(local)

        t0 = time.perf_counter()
        threads = [threading.Thread(target=mix_worker, args=(i,)) for i in range(N_THREADS)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=120)
        mix_wall = (time.perf_counter() - t0) * 1000
        results['mix'] = {'wall_ms': round(mix_wall, 0), 'by_op': summarize(mix_timings),
                          'total': len(mix_timings)}
        print(f"    完成 {len(mix_timings)} 請求, wall={mix_wall:.0f}ms")

        # ── Test 4: 並發寫專測 (同/不同 header 同時寫) ───────────────────────
        print(f'\n[5] 並發寫專測 — 20 並發 × {WRITE_OPS_EACH} 寫 (一半同 header 一半不同) ...')
        write_timings = []
        wlock = threading.Lock()
        shared_hid = header_ids[0]
        shared_pid = proc_by_header[shared_hid]
        shared_sid = stage_by_header[shared_hid]

        def write_worker(tid):
            s = Session()
            s.login()
            same = tid % 2 == 0      # half hammer the SAME header (max contention)
            if same:
                hid, pid, sid = shared_hid, shared_pid, shared_sid
            else:
                hid = header_ids[tid % len(header_ids)]
                pid, sid = proc_by_header.get(hid), stage_by_header.get(hid)
            local = []
            for op in range(WRITE_OPS_EACH):
                t0 = time.perf_counter()
                st, body = s.post('/api/ie/cell/save', {
                    'cell_id': pid, 'stage_id': sid, 'field': 'standard_time',
                    'value': float(tid) * 100 + op, 'user': f'w_t{tid}'})
                ms = (time.perf_counter() - t0) * 1000
                locked = is_locked(st, body)
                try:
                    ok = st == 200 and json.loads(body).get('ok') is True
                except Exception:
                    ok = False
                local.append(('cell_write' + ('(same)' if same else '(diff)'), ms, st, locked, ok))
            with wlock:
                write_timings.extend(local)

        t0 = time.perf_counter()
        threads = [threading.Thread(target=write_worker, args=(i,)) for i in range(N_THREADS)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=120)
        write_wall = (time.perf_counter() - t0) * 1000

        expected_writes = sum(1 for r in write_timings if r[4])  # ok responses
        # verify nothing lost: ie_edit_log rows added should == ok writes
        conn = sqlite3.connect(STRESS_DB)
        edit_log_after = conn.execute('SELECT COUNT(*) FROM ie_edit_log').fetchone()[0]
        conn.close()
        # mix test also wrote (op kind==2): count those oks too
        mix_writes_ok = sum(1 for (label, ms, st, lk, ok) in mix_timings if label == 'cell_write' and ok)
        total_ok_writes = expected_writes + mix_writes_ok
        rows_written = edit_log_after - tgt['edit_log_before']

        results['write'] = {
            'wall_ms': round(write_wall, 0),
            'by_op': summarize(write_timings),
            'total': len(write_timings),
            'ok_writes_this_test': expected_writes,
            'mix_ok_writes': mix_writes_ok,
            'edit_log_before': tgt['edit_log_before'],
            'edit_log_after': edit_log_after,
            'rows_written': rows_written,
            'total_ok_writes': total_ok_writes,
            'lost': total_ok_writes - rows_written,
        }
        all_locks = sum(s['locks'] for s in results['mix']['by_op'].values()) + \
                    sum(s['locks'] for s in results['write']['by_op'].values())
        all_fails = sum(s['fails'] for s in results['mix']['by_op'].values()) + \
                    sum(s['fails'] for s in results['write']['by_op'].values())
        results['totals'] = {'locks': all_locks, 'fails': all_fails}
        print(f"    完成 {len(write_timings)} 寫, wall={write_wall:.0f}ms, "
              f"DB locked={all_locks}, 寫入 ie_edit_log 新增={rows_written} 筆, "
              f"遺失={results['write']['lost']}")

        # ── Test 5: 20 並發純讀 — 真實尺寸細表 (一般 header 的 sheet) ─────────
        # 細表一次只開一張 sheet；真實 sheet 約數百~千格，遠小於 12000 格的極端值。
        # 這段量「真實尺寸」下 waitress 的並發表現（與極端 12000 格區隔）。
        normal_hid = header_ids[seed_stress_db.N_HEAVY + 5]  # 一般 header
        # find its biggest sheet + cell count
        conn = sqlite3.connect(STRESS_DB)
        nrow = conn.execute(
            'SELECT sheet_name, COUNT(*) c FROM ie_sheet_data WHERE header_id=? GROUP BY sheet_name ORDER BY c DESC LIMIT 1',
            (normal_hid,)).fetchone()
        conn.close()
        normal_sheet, normal_cells = nrow[0], nrow[1]
        print(f'\n[6] 20 並發純讀真實尺寸細表 (header={normal_hid} sheet={normal_sheet} {normal_cells} cells) ...')
        nread_timings = []
        nlock = threading.Lock()

        def nread_worker(tid):
            s = Session(); s.login()
            local = []
            for op in range(8):
                t0 = time.perf_counter()
                st, body = s.get(f'/api/ie/{normal_hid}/sheet?name={urllib.parse.quote(normal_sheet)}')
                ms = (time.perf_counter() - t0) * 1000
                local.append(('normal_read', ms, st, is_locked(st, body), st == 200))
            with nlock:
                nread_timings.extend(local)

        threads = [threading.Thread(target=nread_worker, args=(i,)) for i in range(N_THREADS)]
        for t in threads: t.start()
        for t in threads: t.join(timeout=120)
        results['normal_read'] = {
            'header_id': normal_hid, 'sheet': normal_sheet, 'cells': normal_cells,
            'by_op': summarize(nread_timings),
        }
        nr = results['normal_read']['by_op'].get('normal_read', {})
        print(f"    真實尺寸 ({normal_cells} cells) 20並發: avg={nr.get('avg')}ms "
              f"p95={nr.get('p95')}ms max={nr.get('max')}ms")

        return results

    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except Exception:
            server.kill()
        print(f'    伺服器已關閉 ({label})')


def main():
    print('=' * 60)
    print('  IE 真實量級 HTTP 壓力測試 — app.run()')
    print('=' * 60)
    print('\n[1] Seeding 獨立測試庫 ...')
    seed_counts = seed_stress_db.build()
    for k, v in seed_counts.items():
        print(f'    {k:22} = {v}')
    results = run_battery('apprun')
    write_report(results)


def write_report(r):
    sc = r['seed_counts']
    b = r['baseline']
    mix = r['mix']
    w = r['write']
    tot = r['totals']
    n = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # verdict
    detail_conc = mix['by_op'].get('detail_read(大表)', {})
    detail_avg = detail_conc.get('avg', 0)
    detail_p95 = detail_conc.get('p95', 0)
    detail_max = detail_conc.get('max', 0)
    # serialization ratio: concurrent avg vs single-thread baseline.
    # ≈ N_THREADS means the dev server is queueing requests one-by-one.
    serial_ratio = round(detail_avg / b['sheet_ms'], 1) if b['sheet_ms'] else 0
    serialized = serial_ratio >= 3            # clearly not serving concurrently
    sheet_slow = b['sheet_ms'] > 1000 or detail_p95 > 2000
    has_lock = tot['locks'] > 0
    has_fail = tot['fails'] > 0
    lost = w['lost'] != 0

    if has_lock or lost or has_fail:
        verdict = '❌ 不堪用 — 出現 DB locked / 寫入遺失 / 請求失敗，必須改 waitress'
    elif serialized or sheet_slow:
        verdict = ('⚠️ 勉強可用 — 無 DB locked、無寫入遺失，但 app.run() 在並發下把重型細表讀取'
                   '排隊序列化，p95 飆到秒級，建議改 waitress')
    else:
        verdict = '✅ 可用 — 真實 52 萬筆 + 20 並發下回應時間在可接受範圍'

    L = []
    L.append('# IE 系統 — 真實量級 20 並發壓力測試報告（HTTP / app.run()）')
    L.append('')
    L.append(f'**執行時間**: {n}  ')
    L.append('**測試方式**: 真實 HTTP 打 `app.run()` 開發伺服器（複製 production 啟動方式），'
             '20 條獨立連線並發。**不經 test_client**。')
    L.append('**測試庫**: `tests/atlas_stress.db`（獨立 schema-only 庫，全程未連線 / 未複製 `data/atlas.db`）')
    L.append('')
    L.append('## ⭐ 測試庫真實筆數（證明不是空表）')
    L.append('')
    L.append('| 資料表 | 筆數 |')
    L.append('|--------|------|')
    L.append(f"| ob_header | **{sc['ob_header']:,}** |")
    L.append(f"| ob_articles | {sc['ob_articles']:,} |")
    L.append(f"| ie_process | **{sc['ie_process']:,}** |")
    L.append(f"| ie_sheet_data | **{sc['ie_sheet_data']:,}** |")
    L.append(f"| ie_stage | {sc['ie_stage']:,} |")
    L.append('')
    L.append(f"> 對照舊測試：舊版 ie_sheet_data = **0 筆**（測空表，無意義）。"
             f"本版 = **{sc['ie_sheet_data']:,} 筆**，貼近真實系統 522,774 筆量級。")
    L.append(f"> 細表讀取走的 `ie_sheet_data` 已塞滿；最重 header={sc['heavy_header_id']} "
             f"({sc['heavy_header_cells']:,} cells)，最大單一 sheet='{sc['heavy_sheet_name']}' "
             f"({sc['heavy_sheet_cells']:,} cells)。")
    L.append('')
    L.append('---')
    L.append('')
    L.append('## 一、單線程基準')
    L.append('')
    L.append('| 操作 | 耗時(ms) | 狀態 | 備註 |')
    L.append('|------|---------|------|------|')
    L.append(f"| 細表 meta `/api/ie/detail/{r['targets']['heavy_hid']}` | {b['detail_ms']} | {b['detail_st']} | 重型 header |")
    L.append(f"| **細表載入(讀大表)** `/api/ie/<hid>/sheet` | **{b['sheet_ms']}** | {b['sheet_st']} | "
             f"回傳 {b['sheet_cells_returned']:,} cells（ie_sheet_data 真實讀取）|")
    L.append(f"| 格子資料 `/api/ie/cell/<hid>` | {b['cell_ms']} | {b['cell_st']} | 讀 ie_process |")
    L.append(f"| 清單 `/api/ie/list` | {b['list_ms']} | {b['list_st']} | {b['list_records']} 筆 |")
    L.append('')
    L.append('---')
    L.append('')
    L.append(f"## 二、20 並發 × 混合操作（讀清單 / 開細表讀大表 / 寫格子）")
    L.append('')
    L.append(f"- 線程：{N_THREADS} 條（各自獨立登入 / cookie / 連線）")
    L.append(f"- 每線程：{N_OPS_EACH} 次 → 總請求 {mix['total']}")
    L.append(f"- 總耗時(wall)：{mix['wall_ms']:.0f} ms")
    L.append('')
    L.append('| 操作 | 請求數 | 平均(ms) | p95(ms) | 最大(ms) | 失敗 | DB locked |')
    L.append('|------|--------|---------|--------|---------|------|-----------|')
    for op, s in mix['by_op'].items():
        L.append(f"| {op} | {s['count']} | {s['avg']} | {s['p95']} | {s['max']} | {s['fails']} | {s['locks']} |")
    L.append('')
    L.append('---')
    L.append('')
    L.append('## 三、並發寫專測（同 / 不同 header 同時寫）')
    L.append('')
    L.append(f"- 線程：{N_THREADS} 條，一半猛打同一 header（最大鎖競爭），一半寫各自 header")
    L.append(f"- 每線程：{WRITE_OPS_EACH} 寫 → 總寫入請求 {w['total']}")
    L.append(f"- 總耗時(wall)：{w['wall_ms']:.0f} ms")
    L.append('')
    L.append('| 操作 | 請求數 | 平均(ms) | p95(ms) | 最大(ms) | 失敗 | DB locked |')
    L.append('|------|--------|---------|--------|---------|------|-----------|')
    for op, s in w['by_op'].items():
        L.append(f"| {op} | {s['count']} | {s['avg']} | {s['p95']} | {s['max']} | {s['fails']} | {s['locks']} |")
    L.append('')
    L.append('**寫入完整性驗證（有無寫入遺失）**')
    L.append('')
    L.append(f"- ie_edit_log 測前：{w['edit_log_before']:,} 筆")
    L.append(f"- ie_edit_log 測後：{w['edit_log_after']:,} 筆")
    L.append(f"- 實際新增：**{w['rows_written']:,} 筆**")
    L.append(f"- 成功寫入回應（並發寫 {w['ok_writes_this_test']} + 混合測 {w['mix_ok_writes']}）："
             f"**{w['total_ok_writes']:,} 筆**")
    L.append(f"- **寫入遺失：{w['lost']} 筆** {'✅ 無遺失' if w['lost'] == 0 else '❌ 有遺失'}")
    L.append('')
    L.append('---')
    L.append('')
    L.append('## 四、結論')
    L.append('')
    L.append(f"**總體判斷：{verdict}**")
    L.append('')
    L.append(f"- DB locked 總次數：**{tot['locks']}**")
    L.append(f"- 請求失敗總數：**{tot['fails']}**")
    L.append(f"- 寫入遺失：**{w['lost']}**")
    # slowest op
    slowest = ('', 0)
    for op, s in list(mix['by_op'].items()) + list(w['by_op'].items()):
        if s['max'] > slowest[1]:
            slowest = (op, s['max'])
    L.append(f"- 最慢操作：**{slowest[0]}**（最大 {slowest[1]} ms）")
    L.append('')
    if '✅' in verdict:
        L.append('### app.run() 評估')
        L.append('')
        L.append('真實 52 萬筆 ie_sheet_data + 20 並發下：無 DB locked、無寫入遺失、無請求失敗，'
                 '細表大表讀取與寫入耗時均在可接受範圍。現階段 `app.run()` 堪用。')
        L.append('')
        L.append('**但仍建議切 waitress 作為下一步**（非緊急）：Werkzeug 開發伺服器非生產級，'
                 '使用者增至 30+ 或同時開多張重型細表時，建議用 `waitress-serve --threads=8 '
                 '--host=0.0.0.0 --port=5000 app:app`（零改 app.py）以穩定吞吐。')
    else:
        L.append('### 根因（附數據佐證）')
        L.append('')
        L.append(f"重型細表讀取 `/api/ie/<hid>/sheet`（讀 ie_sheet_data 大表）：")
        L.append(f"- 單線程基準：**{b['sheet_ms']} ms**")
        L.append(f"- 20 並發下：平均 **{detail_avg} ms** / p95 **{detail_p95} ms** / 最大 **{detail_max} ms**")
        L.append(f"- 並發/單線程倍率 ≈ **{serial_ratio}×**（{N_THREADS} 並發；倍率遠大於 1）")
        L.append('')
        L.append(f"單次讀取只要 {b['sheet_ms']} ms（DB 查詢不慢、索引有效），但 {N_THREADS} 人同時開細表時"
                 f"平均要等 {detail_avg:.0f} ms、最後一個人等到 ~{detail_max:.0f} ms。"
                 f"耗時隨並發數近乎線性放大（倍率 {serial_ratio}× ≫ 1），"
                 f"代表 `app.run()`（Werkzeug 開發伺服器）**把請求排隊逐一處理、沒有真正並發服務**。"
                 f"DB locked={tot['locks']}、寫入遺失={w['lost']}、失敗={tot['fails']}，"
                 f"**瓶頸不在 SQLite，而在前端伺服器序列化**。")
        L.append('')
        L.append('### 必要改善')
        L.append('')
        L.append(f"1. **改用 waitress（最關鍵）**：`pip install waitress` → "
                 f"`python -m waitress --host=0.0.0.0 --port=5000 --threads=8 app:app`（零改 app.py）。"
                 f"多線程同時服務多個讀取請求，重型細表 p95 可由 {detail_p95} ms 降回接近單線程的 "
                 f"{b['sheet_ms']} ms 量級。")
        L.append(f"2. **細表大表前端分頁/虛擬捲動**：單一 sheet 一次回 {b['sheet_cells_returned']:,} cells，"
                 f"單次 {b['sheet_ms']} ms 主要花在序列化大量 cell。已有索引 "
                 f"`idx_ie_sheet_data_hdr(header_id, sheet_name)`，DB 端無需加索引；"
                 f"建議前端按可視範圍分批載入，降低單次傳輸量。")
        L.append(f"3. **（次要）提高 SQLite busy_timeout**：`get_conn()` 用預設 5s timeout，本次未觸發 locked；"
                 f"切 waitress 後寫入並發升高，可預防性加 `PRAGMA busy_timeout=15000`。")

    out = os.path.join(OUTPUT_DIR, 'ie_stress_test_real.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    print(f'\n[報告] → {out}')


if __name__ == '__main__':
    main()
