# -*- coding: utf-8 -*-
"""
release_gate.py — 發佈防呆（Jim 要求 2026-07-15，G2）。

★為什麼要這個：
  2026-07-15 Jim 人工發現「更新鈕地雷」——/api/system/update 直接 `git pull origin main` 並重啟。
  只要開發者把半成品 push 上 main，現場（ME129）誤按更新就會拉到半成品：
  程式新、DB 舊 → 白畫面/掛死，且現場沒有回頭路。13 支閘門全綠也擋不住，因為
  **沒有任何閘門攻擊「營運/發佈路徑」**（45 號檔失敗案例表已補此列）。

本模組提供兩道閘：
  一、發佈閘 release gate
      更新目標改為 approved_branch(release)，且遠端該分支的 commit 必須 == RELEASE_GATE.json
      的 approved_commit 才准更新。不符 → 拒絕 + 顯示「等待中樞核可」，**服務照跑不中斷**。
  二、開機 schema 守門 schema guard
      app 啟動先比對「DB 實際 schema」vs「現行程式期望的 schema」。缺表/缺欄 → 拒絕啟動 +
      印出明確訊息 + 一鍵回滾指令，**絕不讓現場拿到白畫面**。
      期望 schema 的唯一真相來源 = schema.sql 的 CREATE TABLE ＋ migrate.py 的 MIGRATIONS。
      只檢查「該有的有沒有」，**不管多出來的**（基準庫獨有欄/表原樣保留，見中樞裁決③）。
"""
import os
import re
import sys
import json
import sqlite3
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, '..'))
GATE_FILE = os.path.join(ROOT, '00_HANDOFF', 'RELEASE_GATE.json')
SCHEMA_SQL = os.path.join(BASE, 'schema.sql')

WAIT_MSG = '等待中樞核可'


# ── 發佈閘 ────────────────────────────────────────────────────────────────────

def load_gate():
    """讀 RELEASE_GATE.json。讀不到/壞掉 → 回 None（呼叫端一律以『不准更新』處理，fail-closed）。"""
    try:
        with open(GATE_FILE, 'r', encoding='utf-8') as f:
            g = json.load(f)
        if not g.get('approved_commit'):
            return None
        return g
    except Exception:
        return None


def _git(args, timeout=20):
    try:
        p = subprocess.run(['git'] + args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or '').strip(), (p.stderr or '').strip()
    except Exception as e:
        return 1, '', str(e)


def _short(sha):
    return (sha or '').strip()[:7]


def check_release(fetch=True):
    """回傳 (ok, info)。ok=True 才准更新。

    fail-closed：任何一步不確定（gate 檔壞、fetch 失敗、分支不存在）一律 ok=False，
    因為「不更新」永遠比「更新到未核可的版本」安全——現場服務本來就還在跑。
    """
    g = load_gate()
    if not g:
        return False, {'reason': 'gate_unreadable',
                       'message': f'{WAIT_MSG}：發佈閘設定檔讀不到或未填 approved_commit',
                       'gate_file': GATE_FILE}
    branch = g.get('approved_branch') or 'release'
    approved = _short(g.get('approved_commit'))

    if fetch:
        rc, _, err = _git(['fetch', 'origin', branch])
        if rc != 0:
            return False, {'reason': 'fetch_failed',
                           'message': f'{WAIT_MSG}：取不到遠端 {branch} 分支（{err[:120]}）',
                           'approved_commit': approved, 'approved_branch': branch}

    rc, remote, err = _git(['rev-parse', '--short', f'origin/{branch}'])
    if rc != 0:
        return False, {'reason': 'branch_missing',
                       'message': f'{WAIT_MSG}：遠端沒有 {branch} 分支（尚未有任何核可版本）',
                       'approved_commit': approved, 'approved_branch': branch}
    remote = _short(remote)
    _, local, _ = _git(['rev-parse', '--short', 'HEAD'])
    local = _short(local)

    info = {'approved_branch': branch, 'approved_commit': approved,
            'remote_commit': remote, 'local_commit': local,
            'approved_by': g.get('approved_by', ''), 'approved_at': g.get('approved_at', ''),
            'last_good_commit': _short(g.get('last_good_commit')),
            'up_to_date': local == approved}

    if remote != approved:
        info['reason'] = 'not_approved'
        info['message'] = (f'{WAIT_MSG}：遠端 {branch}={remote} 與核可版 {approved} 不符。'
                           f'中樞核可前不會更新，現場服務照常運作。')
        return False, info

    if local == approved:
        info['reason'] = 'already_current'
        info['message'] = f'已是核可版 {approved}，無需更新。'
        return False, info

    info['reason'] = 'ok'
    info['message'] = f'可更新至核可版 {approved}。'
    return True, info


# ── 開機 schema 守門 ──────────────────────────────────────────────────────────

_CREATE_RE = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\[]?(\w+)[`"\]]?\s*\((.*?)\)\s*;',
    re.IGNORECASE | re.DOTALL)
_ADDCOL_RE = re.compile(
    r'ALTER\s+TABLE\s+[`"\[]?(\w+)[`"\]]?\s+ADD\s+COLUMN\s+[`"\[]?(\w+)[`"\]]?',
    re.IGNORECASE)


def _strip_comments(sql):
    """去掉 -- 行註解與 /* */ 區塊註解。

    註解裡的逗號/括號會讓欄位切分與括號深度全亂（實測：'-- 1=外移' 會被當成欄名、
    括號深度被註解裡的 '(' 帶偏 → 表級約束 UNIQUE(a, b) 被誤切成欄位）。
    """
    sql = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
    sql = re.sub(r'--[^\n]*', ' ', sql)
    return sql


def _parse_cols(body):
    """從 CREATE TABLE 的括號內容抓欄名。跳過 表級約束(PRIMARY KEY(..)/UNIQUE(..)/FOREIGN KEY..)。"""
    cols, depth, cur = [], 0, ''
    for ch in body:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ',' and depth == 0:
            cols.append(cur); cur = ''
        else:
            cur += ch
    cols.append(cur)
    out = []
    for c in cols:
        c = c.strip()
        if not c:
            continue
        first = c.split()[0].strip('`"[]')
        if first.upper() in ('PRIMARY', 'UNIQUE', 'FOREIGN', 'CHECK', 'CONSTRAINT'):
            continue
        out.append(first)
    return out


def expected_schema():
    """現行程式期望的 schema：schema.sql 的 CREATE TABLE ＋ migrate.py MIGRATIONS 的增修。

    回傳 {table: set(columns)}。這是**唯一真相來源**——改 schema 一律走 schema.sql / migrate.py，
    守門才不會和實作脫節。

    ★做法：把 schema.sql + MIGRATIONS 真的**建進一個 :memory: DB**，再用 PRAGMA 讀回來。
      （不用 regex 剖 SQL：實測 regex 會把 -- 註解、表級約束 UNIQUE(a, b)、
        DEFAULT (datetime('now')) 的括號通通剖歪 → ie_process 只剖出 4 欄。
        讓 SQLite 自己剖是唯一不會歪的解。）
    """
    mem = sqlite3.connect(':memory:')
    try:
        with open(SCHEMA_SQL, 'r', encoding='utf-8') as f:
            mem.executescript(f.read())
    except Exception:
        pass

    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('_mig', os.path.join(BASE, 'migrate.py'))
        mig = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mig)
        for m in getattr(mig, 'MIGRATIONS', []):
            for stmt in m.get('sql', []):
                try:
                    mem.execute(stmt)
                except Exception:
                    # duplicate column / already exists → 該欄本來就在 schema.sql 裡，不是問題
                    pass
    except Exception:
        pass

    exp = {}
    for (t,) in mem.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        if t.startswith('sqlite_'):
            continue
        exp[t] = {r[1] for r in mem.execute(f'PRAGMA table_info({t})')}
    mem.close()
    return exp


def actual_schema(db_path):
    uri = 'file:' + db_path.replace('\\', '/') + '?mode=ro'
    c = sqlite3.connect(uri, uri=True)
    c.execute('PRAGMA query_only = ON')
    out = {}
    for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
        out[t] = {r[1] for r in c.execute(f'PRAGMA table_info({t})')}
    c.close()
    return out


def check_schema(db_path):
    """回傳 (ok, problems, detail)。只驗『該有的有沒有』，多出來的一律放行。"""
    if not os.path.exists(db_path):
        return False, [f'DB 不存在：{db_path}'], {}
    exp, act = expected_schema(), actual_schema(db_path)
    missing_tables, missing_cols = [], []
    for t, cols in exp.items():
        if t not in act:
            missing_tables.append(t)
            continue
        miss = sorted(cols - act[t])
        if miss:
            missing_cols.append((t, miss))
    problems = []
    for t in sorted(missing_tables):
        problems.append(f'缺表：{t}')
    for t, miss in sorted(missing_cols):
        problems.append(f'缺欄：{t}.{", ".join(miss)}')
    return (not problems), problems, {'expected_tables': len(exp), 'actual_tables': len(act)}


def _emit(msg=''):
    """安全輸出。

    ★別把這行改回 print()：ME129 的主控台是 cp950，print('❌…中文…') 會直接
      UnicodeEncodeError 炸掉——守門本身變成 traceback，現場只看到堆疊錯誤，
      正是本模組要防的「看不懂 + 沒有回頭路」。實測炸在 guard_or_die 第一行。
    """
    try:
        print(msg)
    except UnicodeEncodeError:
        enc = (getattr(sys.stdout, 'encoding', None) or 'ascii')
        sys.stdout.write(msg.encode(enc, 'replace').decode(enc, 'replace') + '\n')


def guard_or_die(db_path):
    """app 啟動時呼叫。schema 不符 → 印明確訊息 + 一鍵回滾指令 → 拒絕啟動（絕不白畫面）。"""
    ok, problems, detail = check_schema(db_path)
    if ok:
        return True
    # 能升級成 UTF-8 就升（訊息才看得懂）；不行也不能炸 → 下面 _emit 還有一層保險。
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    g = load_gate() or {}
    last_good = g.get('last_good_commit') or 'dbbf2cd'
    line = '=' * 72
    _emit(line)
    _emit('[X] 拒絕啟動：DB schema 與現行程式不符（開機守門 schema guard）')
    _emit(line)
    _emit(f'  DB：{db_path}')
    _emit(f'  期望 {detail.get("expected_tables", "?")} 表 / 實際 {detail.get("actual_tables", "?")} 表')
    _emit('  不符項目：')
    for p in problems:
        _emit(f'    - {p}')
    _emit('')
    _emit('  這代表「程式比 DB 新」——若硬啟動，現場會拿到白畫面或掛死，所以這裡直接擋下。')
    _emit('')
    _emit('  修法二選一：')
    _emit('    (1) 升級 DB：python flask_backend\\migrate.py')
    _emit('    (2) 一鍵回滾上一版程式（現場優先，先讓系統跑起來）：')
    _emit('        python flask_backend\\rollback_release.py')
    _emit(f'        → 回滾到 last_good_commit = {last_good}')
    _emit(line)
    return False
