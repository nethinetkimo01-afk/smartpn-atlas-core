# -*- coding: utf-8 -*-
"""
deploy_gate.py — 營運/發佈路徑閘門（Jim 定案 2026-07-15，規則 R1/R2；hub_ci 常設閘門14）。

★為什麼有這支：
  2026-07-15 Jim 人工發現「更新鈕地雷」：/api/system/update 直接 `git pull origin main` 後重啟。
  開發者一把半成品 push 上 main，現場（ME129）誤按更新就會拉到半成品 → 程式新、DB 舊 → 白畫面。
  當時 13 支閘門**全綠**，卻沒有一支擋得住——因為沒有任何閘門攻擊「營運/發佈路徑」。
  45 號檔失敗案例表已補此列；本閘門即該盲點的永久修正。

攻擊面（每項都在隔離副本上真的做一次，不是搜字串）：
  D1 未核可時按更新（開發中/push 後/核可前）→ 必須被拒 + **服務照跑**
  D2 核可後按更新                         → 必須放行
  D3 半新程式 + 舊 schema                 → 開機守門必須拒絕啟動 + 給明確訊息與回滾路徑
  D4 舊程式 + 新 schema（DB 多欄多表）    → 必須照常啟動（多出來的欄不該擋現場）
  D5 還原備份                             → 還原後 DB 必須可用、資料回到備份時點
  D6 更新中斷電重啟                       → DB 不得損壞、服務要能再起來

判定鐵則：任何一項讓現場掛死或白畫面 = 紅，擋 push。

用法：
  python deploy_gate.py            全部情境
  python deploy_gate.py --keep     不刪隔離環境（除錯用）
"""
import os
import io
import sys
import json
import time
import shutil
import sqlite3
import tempfile
import subprocess
import urllib.request
import urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, 'flask_backend')
PROD_DB = os.path.join(BACKEND, 'data', 'atlas.db')
GATE_FILE = os.path.join(ROOT, '00_HANDOFF', 'RELEASE_GATE.json')
KEEP = '--keep' in sys.argv

sys.path.insert(0, BACKEND)
import release_gate  # noqa: E402

R = []


def rec(name, ok, detail=''):
    R.append((name, ok))
    print(f'  {"✅" if ok else "❌"} {name}' + (f' — {detail}' if detail else ''), flush=True)


def clone_db(dst):
    """唯讀複製正式庫（mode=ro + backup API），與 hub_ci 同一套隔離保證。"""
    uri = 'file:' + PROD_DB.replace('\\', '/') + '?mode=ro'
    src = sqlite3.connect(uri, uri=True)
    src.execute('PRAGMA query_only = ON')
    out = sqlite3.connect(dst)
    with out:
        src.backup(out)
    src.close(); out.close()
    return dst


def boot(db):
    """模擬現場真實開機：app.py 是先 db.init_db() 才跑守門。

    init_db 會 self-heal 一大票欄位/表（equipment_types、recalc_lock、ie_process 各欄…），
    所以「守門直接驗生 DB 檔」是不真實的——會把 app_settings 這種開機才建的表誤判成缺。
    本函式在隔離副本上跑一次 init_db，讓後續判定跟現場一致。
    """
    env = dict(os.environ)
    env['ATLAS_DB'] = db
    p = subprocess.run([sys.executable, '-c',
                        'import database as db; db.init_db()'],
                       cwd=BACKEND, capture_output=True, text=True,
                       encoding='utf-8', errors='replace', env=env)
    return p.returncode == 0


def count_rows(db, table='ie_process'):
    """開→讀→關。**一定要 close**：Windows 上留著連線會佔住 -wal，
    害還原刪不掉 WAL（實測 WinError 32），那是測試自己的 bug，不是 restore 的。"""
    c = sqlite3.connect(db)
    try:
        return c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
    finally:
        c.close()


# ── D1/D2：更新鈕（發佈閘決策邏輯） ─────────────────────────────────────────────

def _fake_gate(tmp, approved_commit):
    """造一份臨時 RELEASE_GATE.json，測「核可/未核可」兩種時點。"""
    p = os.path.join(tmp, 'gate.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump({'approved_branch': 'release', 'approved_commit': approved_commit,
                   'approved_by': 'test', 'approved_at': '2026-07-15',
                   'last_good_commit': 'dbbf2cd'}, f)
    return p


def scenario_update_button(tmp):
    print('\n▶ D1/D2 更新鈕：各時點按下去會怎樣')
    orig_gate, orig_git = release_gate.GATE_FILE, release_gate._git

    def mk_git(remote_sha, local_sha):
        def _g(args, timeout=20):
            if args[:1] == ['fetch']:
                return 0, '', ''
            if args[:2] == ['rev-parse', '--short']:
                ref = args[2]
                return (0, remote_sha, '') if ref.startswith('origin/') else (0, local_sha, '')
            return 0, '', ''
        return _g

    try:
        # ── D1a 開發中：release 還沒有任何核可版本（遠端無此分支）
        release_gate.GATE_FILE = _fake_gate(tmp, 'dbbf2cd')
        def _g_nobranch(args, timeout=20):
            if args[:1] == ['fetch']:
                return 1, '', "couldn't find remote ref release"
            return 1, '', 'unknown revision'
        release_gate._git = _g_nobranch
        ok, info = release_gate.check_release()
        rec('D1a 開發中按更新（release 分支不存在）→ 被拒',
            (not ok) and release_gate.WAIT_MSG in info.get('message', ''), info.get('reason'))

        # ── D1b push 後、核可前：remote release 已被推到新 sha，但 gate 仍停在舊核可版
        release_gate._git = mk_git('9999abc', 'dbbf2cd')
        ok, info = release_gate.check_release()
        rec('D1b push 後未核可（remote=9999abc ≠ approved=dbbf2cd）→ 被拒',
            (not ok) and info.get('reason') == 'not_approved', info.get('message', '')[:52])

        # ── D1c 有人偷改 gate 檔成空/壞 → fail-closed
        bad = os.path.join(tmp, 'bad_gate.json')
        open(bad, 'w', encoding='utf-8').write('{ this is not json')
        release_gate.GATE_FILE = bad
        ok, info = release_gate.check_release()
        rec('D1c 發佈閘設定檔損壞 → fail-closed 被拒（不是放行）',
            (not ok) and info.get('reason') == 'gate_unreadable')

        # ── D2 核可後：gate 與 remote release 一致，且本機還沒到 → 放行
        release_gate.GATE_FILE = _fake_gate(tmp, '9999abc')
        release_gate._git = mk_git('9999abc', 'dbbf2cd')
        ok, info = release_gate.check_release()
        rec('D2 中樞核可後按更新（remote==approved）→ 放行',
            ok and info.get('reason') == 'ok', info.get('message', '')[:52])

        # ── D2b 已經是核可版 → 不重複更新（也不該報錯）
        release_gate._git = mk_git('9999abc', '9999abc')
        ok, info = release_gate.check_release()
        rec('D2b 已是核可版 → 回「無需更新」（不重啟、不報錯）',
            (not ok) and info.get('reason') == 'already_current')
    finally:
        release_gate.GATE_FILE, release_gate._git = orig_gate, orig_git


# ── D3/D4：程式與 schema 不同步 ────────────────────────────────────────────────

def scenario_schema_mismatch(tmp):
    print('\n▶ D3/D4 程式與 DB schema 不同步')

    # D3 半新程式 + 舊 schema：DB 缺現行程式要的欄 → 必須擋啟動。
    # 用 ob_header.lean 當標的，因為這是**真實案例**：C 槽基準庫就是沒有這欄，
    # 而現行程式的廠務編制會 SELECT DISTINCT lean FROM ob_header → 硬起就是白畫面。
    # 且 init_db 補不了它（只有 migrate.py M011 會補）→ 正好驗到守門的真價值。
    old = os.path.join(tmp, 'old_schema.db')
    clone_db(old)
    c = sqlite3.connect(old)
    c.execute('ALTER TABLE ob_header DROP COLUMN lean')
    c.commit(); c.close()
    boot(old)   # 先 init_db（現場開機順序）——它補不回 lean
    ok, problems, _ = release_gate.check_schema(old)
    rec('D3 舊 schema（缺 ob_header.lean，init_db 補不回）→ 守門判不合格',
        (not ok) and any('lean' in p for p in problems),
        problems[0] if problems else '')

    # D3b 守門擋下時的訊息必須可行動：講原因 + 給回滾路徑，且**不能自己炸掉**。
    # ★一定要真的 subprocess 跑 app.py，不能在行程內抓 stdout：
    #   實測用 io.StringIO 抓會過關，真主控台(cp950)卻 UnicodeEncodeError 炸成 traceback
    #   ——現場只看到堆疊錯誤，正是本閘門要防的事。假環境測不出真環境的編碼問題。
    p = subprocess.run([sys.executable, 'app.py'], cwd=BACKEND,
                       capture_output=True, text=True, encoding='utf-8', errors='replace',
                       env={**os.environ, 'ATLAS_DB': old}, timeout=120)
    msg = (p.stdout or '') + (p.stderr or '')
    rec('D3b 守門擋下 app.py 啟動（真跑 subprocess，exit code 3）',
        p.returncode == 3, f'rc={p.returncode}')
    rec('D3b2 擋下時給出明確訊息＋一鍵回滾指令，且自己不炸（無 Traceback）',
        ('拒絕啟動' in msg) and ('rollback_release.py' in msg) and ('migrate.py' in msg)
        and ('Traceback' not in msg),
        'Traceback!' if 'Traceback' in msg else '')

    # D4 舊程式 + 新 schema：DB 多欄多表 → 不該擋（多出來的欄與現行程式無關）。
    # 這條同時保護中樞裁決③：基準庫獨有欄(group_info/theory_operators)必須原樣保留且不擋啟動。
    new = os.path.join(tmp, 'new_schema.db')
    clone_db(new)
    boot(new)
    c = sqlite3.connect(new)
    c.execute('ALTER TABLE ob_header ADD COLUMN future_col_9527 TEXT')
    c.execute('CREATE TABLE future_table_9527 (id INTEGER PRIMARY KEY, x TEXT)')
    c.commit(); c.close()
    ok, problems, _ = release_gate.check_schema(new)
    rec('D4 新 schema（DB 多一欄一表）→ 守門放行（多出來的不該擋現場）',
        ok, '' if ok else str(problems[:2]))


# ── D5：還原備份 ───────────────────────────────────────────────────────────────

def scenario_restore(tmp):
    print('\n▶ D5 還原備份')
    work = os.path.join(tmp, 'restore_work')
    os.makedirs(work, exist_ok=True)
    db = os.path.join(work, 'atlas.db')
    clone_db(db)
    boot(db)

    n0 = count_rows(db)
    env = dict(os.environ)
    env['ATLAS_DB'] = db
    env['ATLAS_BACKUP_DIR'] = os.path.join(work, 'auto_backup')

    p = subprocess.run([sys.executable, os.path.join(BACKEND, 'db_backup.py'), 'backup'],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    backups = []
    bdir = env['ATLAS_BACKUP_DIR']
    if os.path.isdir(bdir):
        backups = [os.path.join(bdir, f) for f in os.listdir(bdir) if f.endswith('.db')]
    rec('D5a 建立備份成功', p.returncode == 0 and len(backups) == 1,
        os.path.basename(backups[0]) if backups else (p.stdout or p.stderr)[-90:])
    if not backups:
        rec('D5b 還原備份（前置失敗，跳過）', False)
        return

    # 破壞 live DB（模擬現場砍錯資料），再還原
    c = sqlite3.connect(db)
    c.execute('DELETE FROM ie_process')
    c.commit(); c.close()
    n_broken = count_rows(db)

    p = subprocess.run([sys.executable, os.path.join(BACKEND, 'db_backup.py'), 'restore', backups[0]],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
    n1 = count_rows(db)
    rec(f'D5b 還原備份：{n0} → 砍成 {n_broken} → 還原回 {n1}',
        p.returncode == 0 and n1 == n0 and n0 > 0)
    ok, _, _ = release_gate.check_schema(db)
    rec('D5c 還原後的 DB 通過 schema 守門（還原不會讓現場起不來）', ok)


# ── D6：更新中斷電重啟 ─────────────────────────────────────────────────────────

def scenario_power_cut(tmp):
    print('\n▶ D6 更新中斷電重啟')
    work = os.path.join(tmp, 'powercut')
    os.makedirs(work, exist_ok=True)
    db = os.path.join(work, 'atlas.db')
    clone_db(db)
    boot(db)

    # 模擬：寫入交易進行中（WAL 有未 checkpoint 的內容）時整台斷電——
    # 不 commit、不 close，直接讓連線物件消失，留下 -wal/-shm。
    c = sqlite3.connect(db)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute("UPDATE ie_process SET actual_operators = actual_operators WHERE id = (SELECT MIN(id) FROM ie_process)")
    os.close(os.open(db, os.O_RDONLY))   # 觸碰檔案，確保 wal 已落地
    del c                                 # 不 commit / 不 close ＝ 斷電

    # 重啟：DB 必須還能開、資料完整、schema 守門過得了
    try:
        c2 = sqlite3.connect(db)
        ig = c2.execute('PRAGMA integrity_check').fetchone()[0]
        n = c2.execute('SELECT COUNT(*) FROM ie_process').fetchone()[0]
        c2.close()
        opened = True
    except Exception as e:
        ig, n, opened = str(e), -1, False
    rec('D6a 斷電後 DB 仍可開啟且 integrity_check=ok', opened and ig == 'ok', f'ie_process={n}')
    ok, problems, _ = release_gate.check_schema(db)
    rec('D6b 斷電後通過 schema 守門（服務能再起來）', ok, '' if ok else str(problems[:2]))


def main():
    print('=' * 68)
    print('deploy_gate — 營運/發佈路徑閘門（hub_ci 閘門14）')
    print('=' * 68)
    print(f'正式庫（唯讀來源）：{PROD_DB}')
    if not os.path.isfile(PROD_DB):
        print('❌ 找不到正式庫 → 中止')
        return 2

    tmp = tempfile.mkdtemp(prefix='deploy_gate_')
    try:
        scenario_update_button(tmp)
        scenario_schema_mismatch(tmp)
        scenario_restore(tmp)
        scenario_power_cut(tmp)
    finally:
        if KEEP:
            print(f'\n[--keep] 隔離環境保留：{tmp}')
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    npass = sum(1 for _, ok in R if ok)
    print('\n' + '=' * 68)
    for n, ok in R:
        if not ok:
            print(f'  ❌ {n}')
    allgreen = npass == len(R) and len(R) >= 13
    print(f'  deploy_gate: {npass}/{len(R)} → '
          f'{"✅ ALL GREEN" if allgreen else "❌ FAIL（發佈路徑有地雷，擋 push）"}')
    print('=' * 68)
    return 0 if allgreen else 1


if __name__ == '__main__':
    sys.exit(main())
