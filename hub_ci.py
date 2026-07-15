# -*- coding: utf-8 -*-
"""
hub_ci.py — 總閘門（中樞定案 2026-07-15）。一鍵起隔離 server（正式庫形狀副本）→ 依序跑全部閘門
→ 彙總 PASS/FAIL → 對 FAIL 自動輸出退回摘要 → 清理隔離環境。

★鐵則（25 規則）：每次 push 前必跑 `python hub_ci.py`，全綠才可 push；報告附輸出全文 + 閘門檔 hash。

閘門清單（依序）：
  1 spec_gate_bianche   廠務編制表（四單位 CSA/OCS/RB/QC × 三角色 × 多月，數字可追溯）
  2 hub_gate            中樞伺服器缺陷（6 類，83 項）
  3 spec_gate_ie        IE 細表總計完整性（全段×全區塊×全分組：標時/理論人數/實際人數總計）
  4 fresh_click_test    品牌端 SMARTPN_DEMO_V3.html（死按鈕=0）
  5 fresh_click_test    供應商端 SMARTPN_DEMO_SUPPLIER_V3.html（死按鈕=0）
  6 fresh_click_test    工廠端 SMARTPN_DEMO_FACTORY_V3.html（死按鈕=0）
  7 spec_gate_smartpn   三檔 S02–S17 各 16/16
  8 spec_gate_flow      三檔真實點擊路徑逐場景走通（不呼叫任何頁面 API；每步畫面必變＋資料 token 齊）
  9 spec_gate_bfs       三檔真實點擊 BFS 走遍主 UI（補 fresh 判定的覆蓋盲區：深層按鈕逐顆判定）

隔離保證（絕不碰正式庫）：
  - 正式庫 flask_backend/data/atlas.db 以 sqlite3 URI `mode=ro` 唯讀開啟，用 backup API 複製到臨時目錄；
    正式庫全程唯讀，任何閘門/伺服器只看得到副本（ATLAS_DB 指向副本）。
  - 跑完刪除整個臨時目錄 + 關閉 server。

用法：
  python hub_ci.py            全部閘門
  python hub_ci.py --keep     不刪隔離環境（除錯用）
"""
import os, sys, io, time, socket, shutil, sqlite3, hashlib, tempfile, subprocess, urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, 'flask_backend')
PROD_DB = os.path.join(BACKEND, 'data', 'atlas.db')
PREVIEW = os.path.join(ROOT, 'docs', 'preview')
BRAND = os.path.join(PREVIEW, 'SMARTPN_DEMO_V3.html')
SUPPLIER = os.path.join(PREVIEW, 'SMARTPN_DEMO_SUPPLIER_V3.html')
FACTORY = os.path.join(PREVIEW, 'SMARTPN_DEMO_FACTORY_V3.html')

# 判定檔：被驗收方不得修改 → 報告附 hash 自證
GATE_FILES = ['spec_gate_bianche.py', 'hub_gate.py', 'spec_gate_ie.py', 'fresh_click_test.js',
              'spec_gate_smartpn.py', 'spec_gate_flow.py', 'spec_gate_bfs.js', 'hub_ci.py']

KEEP = '--keep' in sys.argv
RESULTS = []   # (name, ok, summary, output)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def clone_prod_db(dst):
    """正式庫唯讀複製（mode=ro + backup API）——正式庫絕不被寫入。"""
    if not os.path.isfile(PROD_DB):
        raise SystemExit(f'❌ 找不到正式庫：{PROD_DB}')
    uri = 'file:' + PROD_DB.replace('\\', '/').replace('?', '%3f').replace('#', '%23') + '?mode=ro'
    src = sqlite3.connect(uri, uri=True)
    out = sqlite3.connect(dst)
    with out:
        src.backup(out)
    src.close(); out.close()
    return dst


def wait_health(base, proc, timeout=90):
    """server 就緒＝/api/health 有回應（任何 HTTP 狀態皆算；未登入時本端點回 401，
    不是掛掉——只有連不上(URLError)才算沒起來）。"""
    t0 = time.time()
    last = ''
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            return False, f'server 提前結束 rc={proc.returncode}'
        try:
            with urllib.request.urlopen(base + '/api/health', timeout=3) as r:
                return True, f'HTTP {r.status}'
        except urllib.error.HTTPError as e:
            return True, f'HTTP {e.code}'          # 有回應＝server 活著
        except Exception as e:
            last = str(e)
            time.sleep(0.6)
    return False, f'{timeout}s 內 /api/health 連不上（{last}）'


def run(name, cmd, env=None, cwd=ROOT, timeout=1800):
    print(f'\n{"─"*64}\n▶ {name}\n{"─"*64}', flush=True)
    e = dict(os.environ); e.update(env or {})
    try:
        p = subprocess.run(cmd, cwd=cwd, env=e, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=timeout)
        out = (p.stdout or '') + (('\n[stderr]\n' + p.stderr) if p.stderr.strip() else '')
        ok = (p.returncode == 0)
    except subprocess.TimeoutExpired:
        out, ok = f'❌ 逾時 {timeout}s', False
    print(out.rstrip(), flush=True)
    RESULTS.append((name, ok, verdict_line(out), out))
    return ok


def verdict_line(out):
    """取「有結論的那一行」當摘要（ALL GREEN / FAIL / n/m），不要抓到分隔線。"""
    lines = [l.strip() for l in out.splitlines() if l.strip() and set(l.strip()) - set('=─█ ')]
    for l in reversed(lines):
        if ('ALL GREEN' in l) or ('FAIL' in l) or ('/' in l and any(c.isdigit() for c in l)):
            return l
    return lines[-1] if lines else '(無輸出)'


def reject_summary():
    """對 FAIL 自動輸出退回摘要（誰失敗/失敗在哪/怎麼重現）。"""
    bad = [r for r in RESULTS if not r[1]]
    if not bad:
        return
    print('\n' + '█' * 64)
    print('█ 退回摘要（RETURN / 未通過項目）')
    print('█' * 64)
    for name, _ok, summary, out in bad:
        print(f'\n▼ {name}')
        print(f'  結論：{summary}')
        fails = [l for l in out.splitlines() if '❌' in l]
        if fails:
            print('  失敗明細：')
            for l in fails[:20]:
                print('   ' + l.strip())
            if len(fails) > 20:
                print(f'   …（另有 {len(fails)-20} 條）')
        print(f'  重現：python hub_ci.py（本檔會重建隔離環境並重跑此閘門）')


def main():
    print('=' * 64)
    print('  hub_ci — 總閘門（隔離副本·正式庫形狀·絕不碰正式庫）')
    print('=' * 64)

    print('\n▸ 判定檔 hash（證明閘門判定未被修改）：')
    for f in GATE_FILES:
        fp = os.path.join(ROOT, f)
        print(f'   {sha256(fp)[:16]}  {f}' if os.path.isfile(fp) else f'   (缺檔)          {f}')

    tmp = tempfile.mkdtemp(prefix='hub_ci_')
    db = os.path.join(tmp, 'atlas_ci.db')
    proc = None
    try:
        print(f'\n▸ 複製正式庫（唯讀 mode=ro）→ 隔離副本')
        clone_prod_db(db)
        print(f'   正式庫：{PROD_DB}  ({os.path.getsize(PROD_DB)/1048576:.1f} MB, 唯讀)')
        print(f'   副本  ：{db}  ({os.path.getsize(db)/1048576:.1f} MB)')

        port = free_port()
        base = f'http://127.0.0.1:{port}'
        env = dict(os.environ, ATLAS_DB=db, ATLAS_PORT=str(port), PYTHONIOENCODING='utf-8')
        boot = ('import database as db; db.init_db();'
                'from app import app; from waitress import serve;'
                f'serve(app, host="127.0.0.1", port={port}, threads=8)')
        print(f'\n▸ 起隔離 server：{base}（ATLAS_DB=副本）')
        proc = subprocess.Popen([sys.executable, '-c', boot], cwd=BACKEND, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                encoding='utf-8', errors='replace')
        ok, why = wait_health(base, proc)
        if not ok:
            tail = ''
            try:
                proc.kill(); tail = (proc.stdout.read() or '')[-1500:]
            except Exception:
                pass
            print(f'❌ 隔離 server 起不來：{why}\n{tail}')
            RESULTS.append(('隔離 server 啟動', False, why, tail))
        else:
            print(f"   ✅ /api/health 就緒（{why}）")
            run('閘門1 spec_gate_bianche（四單位×三角色×多月·可追溯）',
                [sys.executable, 'spec_gate_bianche.py'], env={'SPEC_GATE_BASE': base, **env})
            run('閘門2 hub_gate（伺服器缺陷 6 類）',
                [sys.executable, 'hub_gate.py'], env={'HUB_GATE_BASE': base, **env})
            run('閘門3 spec_gate_ie（IE 細表總計完整性·逐段逐區塊逐分組）',
                [sys.executable, 'spec_gate_ie.py'], env={'SPEC_GATE_IE_BASE': base, **env})

        run('閘門4 fresh_click_test（品牌端 SMARTPN_DEMO_V3）', ['node', 'fresh_click_test.js', BRAND])
        run('閘門5 fresh_click_test（供應商端 SMARTPN_DEMO_SUPPLIER_V3）', ['node', 'fresh_click_test.js', SUPPLIER])
        run('閘門6 fresh_click_test（工廠端 SMARTPN_DEMO_FACTORY_V3）', ['node', 'fresh_click_test.js', FACTORY])
        run('閘門7 spec_gate_smartpn（三檔 S02–S17 各 16/16）', [sys.executable, 'spec_gate_smartpn.py'])
        run('閘門8 spec_gate_flow（三檔真實點擊路徑逐場景走通）', [sys.executable, 'spec_gate_flow.py'])
        for _n, _f in (('品牌', BRAND), ('供應商', SUPPLIER), ('工廠', FACTORY)):
            run(f'閘門9 spec_gate_bfs（{_n}端 真實點擊 BFS 走遍主 UI）', ['node', 'spec_gate_bfs.js', _f], timeout=3600)
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()
        if KEEP:
            print(f'\n▸ --keep：保留隔離環境 {tmp}')
        else:
            shutil.rmtree(tmp, ignore_errors=True)
            print(f'\n▸ 清理隔離環境：{tmp} → 已刪除（正式庫全程未被寫入）')

    print('\n' + '=' * 64)
    print('  hub_ci 彙總')
    print('=' * 64)
    for name, ok, summary, _ in RESULTS:
        print(f'  {"✅ PASS" if ok else "❌ FAIL"}  {name}')
        print(f'          └ {summary}')
    npass = sum(1 for r in RESULTS if r[1])
    allgreen = npass == len(RESULTS) and len(RESULTS) >= 11
    reject_summary()
    print('\n' + '=' * 64)
    print(f'  hub_ci: {npass}/{len(RESULTS)} → {"✅ ALL GREEN（可以 push）" if allgreen else "❌ FAIL（不准 push）"}')
    print('=' * 64)
    sys.exit(0 if allgreen else 1)


if __name__ == '__main__':
    main()
