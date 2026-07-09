import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.environ.get('ATLAS_DB') or os.path.join(os.path.dirname(__file__), 'data', 'atlas.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

DEFAULT_LOOKUP = {
    'mui giày':'鞋头','đầu mũi':'鞋头','thân giày':'鞋面','lưỡi gà':'舌片',
    'hậu giày':'后跟片','hậu trong':'内跟片','lót mũi':'头内衬','lót hậu':'跟内衬',
    'lót lưỡi':'舌内衬','cổ giày':'鞋领','viền cổ':'领口绑带','đệm cổ':'领口衬垫',
    'lót cổ':'领内衬','dây giày':'鞋带','vải lót':'内衬布','đế trong':'内底',
    'lót trong':'内里','đế ngoài':'外底','đế giữa':'中底','tăng cường':'加强片',
    'miếng đệm':'衬垫','phần gót':'后跟部分','phần mũi':'前端部分',
    'da thật':'真皮','da tổng hợp':'合成皮','vải mesh':'网布','cao su':'橡胶',
    'xốp':'泡棉',
}

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA journal_mode = WAL')
    # waitress 多線程後寫入並發升高，等鎖 15s 再放棄，避免 'database is locked'
    conn.execute('PRAGMA busy_timeout = 15000')
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    with open(SCHEMA_PATH, encoding='utf-8') as f:
        conn.executescript(f.read())
    # Migration: add source column to ob_epph if missing
    cols = [r[1] for r in conn.execute("PRAGMA table_info(ob_epph)").fetchall()]
    if 'source' not in cols:
        conn.execute("ALTER TABLE ob_epph ADD COLUMN source TEXT DEFAULT 'ie_file'")
        conn.commit()
    # Migration: add post_polish_std/ops to ie_process (裁斷機 6th post-process 磨皮)
    iep_cols = [r[1] for r in conn.execute("PRAGMA table_info(ie_process)").fetchall()]
    if iep_cols:  # table exists (created by cutting import); guard fresh DB
        if 'post_polish_std' not in iep_cols:
            conn.execute("ALTER TABLE ie_process ADD COLUMN post_polish_std REAL")
        if 'post_polish_ops' not in iep_cols:
            conn.execute("ALTER TABLE ie_process ADD COLUMN post_polish_ops REAL")
        # Migration: add equipment_type to ie_process (stitching/assembly/STF 設備種類下拉)
        if 'equipment_type' not in iep_cols:
            conn.execute("ALTER TABLE ie_process ADD COLUMN equipment_type TEXT")
        # 版本控制 Step 1: add stage_id (真正綁版本；舊的 stage 欄位是假的固定=1)
        if 'stage_id' not in iep_cols:
            conn.execute("ALTER TABLE ie_process ADD COLUMN stage_id INTEGER")
        conn.commit()
    # 版本控制 Step 1: ie_stage.is_approved（鎖定版旗標，供 effective-stage 排序）
    ist_cols = [r[1] for r in conn.execute("PRAGMA table_info(ie_stage)").fetchall()]
    if ist_cols and 'is_approved' not in ist_cols:
        conn.execute("ALTER TABLE ie_stage ADD COLUMN is_approved INTEGER DEFAULT 0")
        conn.commit()
    # 版本控制 Step 1: self-heal 回填 — 任何有工序但 stage_id=NULL 的 header 綁到初版
    # （讓 ME129 等未跑 versioning_step1.py 的機器在重啟後自動分版；idempotent）
    if iep_cols and 'stage_id' in [r[1] for r in conn.execute("PRAGMA table_info(ie_process)").fetchall()]:
        null_hdrs = [r[0] for r in conn.execute(
            'SELECT DISTINCT header_id FROM ie_process WHERE stage_id IS NULL').fetchall()]
        for hid in null_hdrs:
            srow = conn.execute(
                'SELECT id FROM ie_stage WHERE header_id=? ORDER BY id ASC LIMIT 1', (hid,)).fetchone()
            if srow:
                sid = srow[0]
            else:
                conn.execute("INSERT INTO ie_stage (header_id, stage_name, is_approved) VALUES (?,'初版',0)", (hid,))
                sid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            conn.execute('UPDATE ie_process SET stage_id=? WHERE header_id=? AND stage_id IS NULL', (sid, hid))
            conn.execute('UPDATE ie_process_group SET stage_id=? WHERE header_id=? AND (stage_id IS NULL OR stage_id=0)', (sid, hid))
        if null_hdrs:
            conn.commit()
    # Seed default lookup if empty
    count = conn.execute('SELECT COUNT(*) FROM lookup_viet_zh').fetchone()[0]
    if count == 0:
        ts = now_iso()
        conn.executemany(
            'INSERT OR IGNORE INTO lookup_viet_zh (viet, zh, created_at) VALUES (?,?,?)',
            [(v, z, ts) for v, z in DEFAULT_LOOKUP.items()]
        )
    conn.commit()
    # Migration: sys_users table
    utbls = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if 'sys_users' not in utbls:
        conn.execute('''CREATE TABLE IF NOT EXISTS sys_users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            username     TEXT    NOT NULL UNIQUE,
            display_name TEXT    NOT NULL DEFAULT '',
            role         TEXT    NOT NULL DEFAULT 'read_only',
            password_hash TEXT   NOT NULL DEFAULT '',
            active       INTEGER NOT NULL DEFAULT 1,
            locked       INTEGER NOT NULL DEFAULT 0,
            created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at   TEXT    NOT NULL DEFAULT (datetime('now'))
        )''')
        # Seed fixed external unit accounts (no password = locked, login not needed via UI)
        ts = now_iso()
        conn.executemany(
            '''INSERT OR IGNORE INTO sys_users (username, display_name, role, locked, created_at, updated_at)
               VALUES (?,?,?,1,?,?)''',
            [('tongcai','同材共裁自動化','read_only',ts,ts),
             ('dianno', '電腦針車折邊',  'read_only',ts,ts),
             ('dacu',   '打粗水洗照射',  'read_only',ts,ts)]
        )
        conn.commit()
    # Migration: is_deleted soft-delete for ds04_orders
    cols_ds04 = [r[1] for r in conn.execute("PRAGMA table_info(ds04_orders)").fetchall()]
    if 'is_deleted' not in cols_ds04:
        conn.execute("ALTER TABLE ds04_orders ADD COLUMN is_deleted INTEGER DEFAULT 0")
        conn.commit()
    # Migration: alloc_edit_log and bianche_edit_log tables
    log_tbls = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if 'alloc_edit_log' not in log_tbls:
        conn.execute('''CREATE TABLE alloc_edit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id     INTEGER,
            action      TEXT NOT NULL,
            old_value   TEXT DEFAULT '',
            new_value   TEXT DEFAULT '',
            user_name   TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        )''')
        conn.commit()
    if 'bianche_edit_log' not in log_tbls:
        conn.execute('''CREATE TABLE bianche_edit_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            target_type TEXT NOT NULL,
            target_key  TEXT NOT NULL,
            old_value   TEXT DEFAULT '',
            new_value   TEXT DEFAULT '',
            user_name   TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        )''')
        conn.commit()
    conn.close()

# ── User management ──────────────────────────────────────────────────────────

def _hash_pw(pw: str) -> str:
    import hashlib
    return hashlib.sha256(pw.encode()).hexdigest()

def list_users():
    conn = get_conn()
    rows = conn.execute(
        'SELECT id,username,display_name,role,active,locked,created_at FROM sys_users ORDER BY id'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def create_user(username, display_name, role, password, active=1):
    if not username or not display_name or not password:
        return {'ok': False, 'error': '帳號、名稱、密碼不能空白'}
    if role not in ('admin','manager','data_entry','read_only'):
        return {'ok': False, 'error': '角色無效'}
    conn = get_conn()
    try:
        conn.execute(
            '''INSERT INTO sys_users (username, display_name, role, password_hash, active, updated_at)
               VALUES (?,?,?,?,?,datetime('now'))''',
            (username.strip().lower(), display_name.strip(), role, _hash_pw(password), int(active))
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

def update_user(uid, display_name=None, role=None, password=None, active=None):
    conn = get_conn()
    row = conn.execute('SELECT * FROM sys_users WHERE id=?', (uid,)).fetchone()
    if not row:
        conn.close()
        return {'ok': False, 'error': '帳號不存在'}
    if row['locked']:
        conn.close()
        return {'ok': False, 'error': '系統帳號不可修改'}
    sets, vals = [], []
    if display_name is not None: sets.append('display_name=?'); vals.append(display_name.strip())
    if role is not None:
        if role not in ('admin','manager','data_entry','read_only'):
            conn.close()
            return {'ok': False, 'error': '角色無效'}
        sets.append('role=?'); vals.append(role)
    if password:
        sets.append('password_hash=?'); vals.append(_hash_pw(password))
    if active is not None:
        sets.append('active=?'); vals.append(int(active))
    if not sets:
        conn.close()
        return {'ok': True}
    sets.append("updated_at=datetime('now')")
    vals.append(uid)
    conn.execute(f'UPDATE sys_users SET {", ".join(sets)} WHERE id=?', vals)
    conn.commit()
    conn.close()
    return {'ok': True}

def delete_user(uid):
    conn = get_conn()
    row = conn.execute('SELECT locked FROM sys_users WHERE id=?', (uid,)).fetchone()
    if not row:
        conn.close()
        return {'ok': False, 'error': '帳號不存在'}
    if row['locked']:
        conn.close()
        return {'ok': False, 'error': '系統帳號不可刪除'}
    conn.execute('DELETE FROM sys_users WHERE id=?', (uid,))
    conn.commit()
    conn.close()
    return {'ok': True}

def verify_login(username, password):
    """Returns user dict if credentials valid, else None."""
    uname = username.strip().lower()
    conn = get_conn()
    row = conn.execute(
        'SELECT id,username,display_name,role,active,locked,password_hash FROM sys_users WHERE username=?',
        (uname,)
    ).fetchone()
    conn.close()
    if not row or not row['active']:
        return None
    if row['locked']:
        # locked accounts (tongcai/dianno/dacu) — no password required
        return {k: row[k] for k in ('id','username','display_name','role','active','locked')}
    if _hash_pw(password) != row['password_hash']:
        return None
    return {k: row[k] for k in ('id','username','display_name','role','active','locked')}

def get_user_by_id(uid):
    conn = get_conn()
    row = conn.execute(
        'SELECT id,username,display_name,role,active FROM sys_users WHERE id=? AND active=1', (uid,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None

# ── IE Assignments ───────────────────────────────────────────────────────────

def get_ie_assignments(header_id=None, user_id=None):
    conn = get_conn()
    if header_id is not None:
        rows = conn.execute(
            '''SELECT a.id, a.header_id, a.user_id, u.username, u.display_name
               FROM ie_assignments a JOIN sys_users u ON a.user_id=u.id
               WHERE a.header_id=?''', (header_id,)
        ).fetchall()
    elif user_id is not None:
        rows = conn.execute(
            'SELECT header_id FROM ie_assignments WHERE user_id=?', (user_id,)
        ).fetchall()
    else:
        rows = conn.execute('SELECT header_id, user_id FROM ie_assignments').fetchall()
    conn.close()
    return [dict(r) for r in rows]

def set_ie_assignment(header_id, user_id):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO ie_assignments (header_id, user_id, assigned_at) VALUES (?,?,datetime('now'))",
            (header_id, user_id)
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

def remove_ie_assignment(header_id, user_id):
    conn = get_conn()
    conn.execute('DELETE FROM ie_assignments WHERE header_id=? AND user_id=?', (header_id, user_id))
    conn.commit()
    conn.close()
    return {'ok': True}

def get_assigned_header_ids(user_id):
    conn = get_conn()
    rows = conn.execute('SELECT header_id FROM ie_assignments WHERE user_id=?', (user_id,)).fetchall()
    conn.close()
    return [r['header_id'] for r in rows]

def get_header_id_by_process(process_id):
    conn = get_conn()
    row = conn.execute('SELECT header_id FROM ie_process WHERE id=?', (process_id,)).fetchone()
    conn.close()
    return row['header_id'] if row else None

def get_header_id_by_group(group_id):
    conn = get_conn()
    row = conn.execute('SELECT header_id FROM ie_process_group WHERE id=?', (group_id,)).fetchone()
    conn.close()
    return row['header_id'] if row else None

# ── IE Review Workflow ───────────────────────────────────────────────────────

def submit_ie_review(header_id, stage_id, submitted_by):
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM ie_review WHERE header_id=? AND status='pending'", (header_id,)
        ).fetchone()
        if existing:
            conn.close()
            return {'ok': False, 'error': '已有待審核的送審記錄'}
        rid = conn.execute(
            "INSERT INTO ie_review (header_id, stage_id, submitted_by, submitted_at, status) VALUES (?,?,?,datetime('now'),'pending')",
            (header_id, stage_id, submitted_by)
        ).lastrowid
        conn.commit()
        return {'ok': True, 'review_id': rid}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

def get_reviews(header_id=None, status=None):
    conn = get_conn()
    q = '''SELECT r.id, r.header_id, r.stage_id, r.submitted_by, r.submitted_at,
                  r.status, r.reviewer, r.reviewed_at, r.reject_reason,
                  h.model_name
           FROM ie_review r JOIN ob_header h ON r.header_id=h.id
           WHERE 1=1'''
    params = []
    if header_id: q += ' AND r.header_id=?'; params.append(header_id)
    if status:    q += ' AND r.status=?';    params.append(status)
    q += ' ORDER BY r.submitted_at DESC'
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def approve_review(review_id, reviewer):
    conn = get_conn()
    conn.execute(
        "UPDATE ie_review SET status='approved', reviewer=?, reviewed_at=datetime('now') WHERE id=?",
        (reviewer, review_id)
    )
    conn.commit()
    conn.close()
    return {'ok': True}

def reject_review(review_id, reviewer, reason):
    conn = get_conn()
    conn.execute(
        "UPDATE ie_review SET status='rejected', reviewer=?, reviewed_at=datetime('now'), reject_reason=? WHERE id=?",
        (reviewer, reason, review_id)
    )
    conn.commit()
    conn.close()
    return {'ok': True}

# ── IE Stage Approval ────────────────────────────────────────────────────────

def set_stage_approved(stage_id, header_id):
    conn = get_conn()
    conn.execute('UPDATE ie_stage SET is_approved=0 WHERE header_id=?', (header_id,))
    conn.execute('UPDATE ie_stage SET is_approved=1 WHERE id=? AND header_id=?', (stage_id, header_id))
    conn.commit()
    conn.close()
    return {'ok': True}

# ── IE ART management ────────────────────────────────────────────────────────

def add_art_to_header(art, header_id):
    art = art.strip()
    if not art:
        return {'ok': False, 'error': 'ART不能空白'}
    conn = get_conn()
    try:
        existing = conn.execute('SELECT id FROM ob_header WHERE id=?', (header_id,)).fetchone()
        if not existing:
            conn.close()
            return {'ok': False, 'error': '鞋型不存在'}
        conn.execute('INSERT OR IGNORE INTO ob_articles (header_id, art) VALUES (?,?)', (header_id, art))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

def update_ie_header_season(header_id, season):
    conn = get_conn()
    conn.execute("UPDATE ob_header SET season=?, updated_at=datetime('now') WHERE id=?", (season, header_id))
    conn.commit()
    conn.close()
    return {'ok': True}

def update_ie_header_eolr(header_id, eolr):
    if int(eolr) not in (60, 120):
        return {'ok': False, 'error': 'eolr must be 60 or 120'}
    conn = get_conn()
    conn.execute("UPDATE ob_header SET eolr=?, updated_at=datetime('now') WHERE id=?", (int(eolr), header_id))
    conn.commit()
    conn.close()
    return {'ok': True}

def update_ie_header_material(header_id, material):
    conn = get_conn()
    conn.execute("UPDATE ob_header SET material=?, updated_at=datetime('now') WHERE id=?", (material, header_id))
    conn.commit()
    conn.close()
    return {'ok': True}

def update_ie_header_meta(header_id, season=None, material=None):
    parts, vals = [], []
    if season  is not None: parts.append("season=?");   vals.append(season)
    if material is not None: parts.append("material=?"); vals.append(material)
    if not parts:
        return {'ok': False, 'error': 'nothing to update'}
    conn = get_conn()
    conn.execute(f"UPDATE ob_header SET {','.join(parts)}, updated_at=datetime('now') WHERE id=?",
                 vals + [header_id])
    conn.commit()
    conn.close()
    return {'ok': True}

# ── DS-03 OB ────────────────────────────────────────────────────────────────

def save_ob_record(data):
    conn = get_conn()
    try:
        h   = data.get('header', {})
        art = h.get('art', '').strip()
        eolr = int(h.get('eolr', 60))
        run  = int(h.get('run', 1))
        if not art:
            return {'ok': False, 'error': 'ART is required'}

        ts = now_iso()
        art_row = conn.execute(
            '''SELECT a.header_id FROM ob_articles a
               JOIN ob_header h ON h.id = a.header_id
               WHERE a.art=? AND h.eolr=? AND h.run=?''',
            (art, eolr, run)
        ).fetchone()

        is_new = art_row is None
        if art_row:
            header_id = art_row['header_id']
            conn.execute(
                '''UPDATE ob_header SET model_name=?, season=?, material=?, category=?, updated_at=?
                   WHERE id=?''',
                (h.get('model',''), h.get('season',''), h.get('material',''),
                 h.get('category',''), ts, header_id)
            )
            conn.execute('DELETE FROM ob_rows WHERE header_id=?', (header_id,))
            conn.execute('DELETE FROM ob_epph  WHERE header_id=?', (header_id,))
        else:
            cur = conn.execute(
                '''INSERT INTO ob_header (model_name, season, material, category, eolr, run, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?)''',
                (h.get('model',''), h.get('season',''), h.get('material',''),
                 h.get('category',''), eolr, run, ts, ts)
            )
            header_id = cur.lastrowid
            conn.execute(
                'INSERT OR IGNORE INTO ob_articles (header_id, art) VALUES (?,?)',
                (header_id, art)
            )

        ep = data.get('epph', {})
        conn.execute(
            'INSERT INTO ob_epph (header_id, cutting, stitching, assembly, stock) VALUES (?,?,?,?,?)',
            (header_id,
             float(ep.get('cutting') or 0), float(ep.get('stitching') or 0),
             float(ep.get('assembly') or 0), float(ep.get('stock') or 0))
        )

        sheets = data.get('sheets', {})
        rows_to_insert = []
        for sheet_key, rows in sheets.items():
            for i, r in enumerate(rows):
                rows_to_insert.append((
                    header_id, sheet_key, i,
                    r.get('partViet',''), r.get('partZh',''), r.get('matCat',''),
                    float(r.get('layers') or 0), float(r.get('qtyPr') or 0),
                    float(r.get('knives') or 0), float(r.get('ct') or 0),
                    float(r.get('allowance') or 10), float(r.get('st') or 0),
                    float(r.get('ops') or 0), float(r.get('marking') or 0),
                    float(r.get('skiving') or 0), float(r.get('attaching') or 0),
                    float(r.get('edgePaint') or 0), float(r.get('heatPress') or 0),
                ))
        conn.executemany(
            '''INSERT INTO ob_rows
               (header_id, sheet_key, row_order, part_viet, part_zh, mat_cat,
                layers, qty_pr, knives, ct, allowance, st, ops,
                marking, skiving, attaching, edge_paint, heat_press)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            rows_to_insert
        )

        conn.commit()
        return {'ok': True, 'header_id': header_id, 'new': is_new}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def load_ob_record(art, eolr, run):
    conn = get_conn()
    try:
        row = conn.execute(
            '''SELECT h.* FROM ob_header h
               JOIN ob_articles a ON a.header_id = h.id
               WHERE a.art=? AND h.eolr=? AND h.run=?''',
            (art, int(eolr), int(run))
        ).fetchone()
        if not row:
            return {'ok': False, 'error': 'Record not found'}

        header_id = row['id']
        header = dict(row)
        header['art'] = art
        header['model'] = header.get('model_name', '')
        arts = [r['art'] for r in conn.execute(
            'SELECT art FROM ob_articles WHERE header_id=? ORDER BY id', (header_id,)
        ).fetchall()]
        header['arts'] = arts

        ep_row = conn.execute('SELECT * FROM ob_epph WHERE header_id=?', (header_id,)).fetchone()
        epph = dict(ep_row) if ep_row else {}

        db_rows = conn.execute(
            'SELECT * FROM ob_rows WHERE header_id=? ORDER BY sheet_key, row_order',
            (header_id,)
        ).fetchall()

        sheets = {}
        for r in db_rows:
            k = r['sheet_key']
            if k not in sheets:
                sheets[k] = []
            sheets[k].append({
                'partViet': r['part_viet'], 'partZh': r['part_zh'], 'matCat': r['mat_cat'],
                'layers': r['layers'], 'qtyPr': r['qty_pr'], 'knives': r['knives'],
                'ct': r['ct'], 'allowance': r['allowance'], 'st': r['st'], 'ops': r['ops'],
                'marking': r['marking'], 'skiving': r['skiving'], 'attaching': r['attaching'],
                'edgePaint': r['edge_paint'], 'heatPress': r['heat_press'],
            })

        return {'ok': True, 'header': header, 'epph': epph, 'sheets': sheets}
    finally:
        conn.close()


def list_ob_records():
    conn = get_conn()
    try:
        rows = conn.execute(
            '''SELECT a.art, h.season, h.model_name AS model, h.eolr, h.run, h.updated_at
               FROM ob_articles a
               JOIN ob_header h ON h.id = a.header_id
               ORDER BY h.updated_at DESC, a.id ASC'''
        ).fetchall()
        return {'ok': True, 'records': [dict(r) for r in rows]}
    finally:
        conn.close()


def delete_ob_record(art, eolr, run):
    conn = get_conn()
    try:
        art_row = conn.execute(
            '''SELECT a.id, a.header_id FROM ob_articles a
               JOIN ob_header h ON h.id = a.header_id
               WHERE a.art=? AND h.eolr=? AND h.run=?''',
            (art, int(eolr), int(run))
        ).fetchone()
        if art_row:
            header_id = art_row['header_id']
            conn.execute('DELETE FROM ob_articles WHERE id=?', (art_row['id'],))
            remaining = conn.execute(
                'SELECT COUNT(*) FROM ob_articles WHERE header_id=?', (header_id,)
            ).fetchone()[0]
            if remaining == 0:
                conn.execute('DELETE FROM ob_epph   WHERE header_id=?', (header_id,))
                conn.execute('DELETE FROM ob_rows   WHERE header_id=?', (header_id,))
                conn.execute('DELETE FROM ob_header WHERE id=?',        (header_id,))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def list_ie_records(header_ids=None):
    """Return ob_header rows with ARTs and MP values. header_ids filters to specific ids."""
    conn = get_conn()
    try:
        # One row per (model_name, eolr): keep the header with the latest created_at.
        # ROW_NUMBER over a CTE — avoids the correlated subquery that mis-filtered
        # against ob_epph on the LEFT JOIN. LEFT JOIN kept so headers without an
        # ob_epph row still appear (cutting/stitching just come back NULL).
        base_q = '''
            WITH ranked AS (
                SELECT h.id, h.model_name, h.eolr, h.season, h.material,
                       ROW_NUMBER() OVER (
                           PARTITION BY h.model_name, h.eolr
                           ORDER BY h.created_at DESC, h.id DESC
                       ) AS rn
                FROM ob_header h
            )
            SELECT r.id, r.model_name, r.eolr, r.season, r.material,
                   e.cutting, e.stitching, e.assembly, e.stock, e.source
            FROM ranked r
            LEFT JOIN ob_epph e ON e.header_id = r.id
            WHERE r.rn = 1
        '''
        if header_ids is not None:
            if not header_ids:
                return {'ok': True, 'records': []}
            placeholders = ','.join('?' * len(header_ids))
            base_q += f' AND r.id IN ({placeholders})'
            rows = conn.execute(base_q + ' ORDER BY r.model_name, r.eolr, r.id', header_ids).fetchall()
        else:
            rows = conn.execute(base_q + ' ORDER BY r.model_name, r.eolr, r.id').fetchall()
        result = []
        for r in rows:
            arts = [x['art'] for x in conn.execute(
                'SELECT art FROM ob_articles WHERE header_id=? ORDER BY id', (r['id'],)
            ).fetchall()]
            result.append({
                'id':         r['id'],
                'model_name': r['model_name'],
                'eolr':       r['eolr'],
                'season':     r['season'] or '',
                'material':   r['material'] or '',
                'arts':       arts,
                'cutting':    r['cutting'],
                'stitching':  r['stitching'],
                'assembly':   r['assembly'],
                'stock':      r['stock'],
                'source':     r['source'] or '',
            })
        return {'ok': True, 'records': result}
    finally:
        conn.close()


def get_ie_sheet_names(header_id):
    """Return ordered list of sheet names stored for this header."""
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT DISTINCT sheet_name FROM ie_sheet_data WHERE header_id=? ORDER BY MIN(id)',
            (header_id,)
        ).fetchall()
        return {'ok': True, 'sheets': [r['sheet_name'] for r in rows]}
    finally:
        conn.close()


def get_ie_matrix():
    """Return ART×Sheet matrix data for /ie/matrix page."""
    conn = get_conn()
    try:
        # Sheet types ordered
        type_rows = conn.execute(
            'SELECT type_key, display_name, sort_order FROM sheet_types ORDER BY sort_order'
        ).fetchall()
        if not type_rows:
            return {'ok': True, 'types': [], 'rows': [], 'no_data_arts': [], 'stats': {}}

        # ARTs whose header has NO ie_sheet_data at all
        no_ie_rows = conn.execute(
            '''SELECT a.art, h.model_name, h.eolr, h.id as header_id
               FROM ob_header h
               JOIN ob_articles a ON a.header_id=h.id
               WHERE h.id NOT IN (SELECT DISTINCT header_id FROM ie_sheet_data)
               ORDER BY a.art'''
        ).fetchall()
        no_data_arts = [{'art': r['art'], 'model': (r['model_name'] or '')[:40],
                          'eolr': r['eolr'], 'header_id': r['header_id']} for r in no_ie_rows]

        # Headers with data + their arts
        h_rows = conn.execute(
            '''SELECT DISTINCT a.header_id, a.art, h.model_name, h.eolr
               FROM ie_sheet_data sd
               JOIN ob_articles a ON a.header_id=sd.header_id
               JOIN ob_header h ON h.id=a.header_id
               ORDER BY a.art'''
        ).fetchall()

        # art_sheet_status
        status_rows = conn.execute(
            'SELECT header_id, art, sheet_type, status FROM art_sheet_status'
        ).fetchall()
        status_map = {}
        for sr in status_rows:
            status_map[(sr['header_id'], sr['art'], sr['sheet_type'])] = sr['status']

        types = [{'key': t['type_key'], 'display': t['display_name']} for t in type_rows]

        matrix_rows = []
        for hr in h_rows:
            hid = hr['header_id']
            art = hr['art']
            cells = []
            for t in type_rows:
                tk = t['type_key']
                st = status_map.get((hid, art, tk))
                cells.append({'status': st or 'na'})
            matrix_rows.append({
                'header_id': hid,
                'art': art,
                'model': (hr['model_name'] or '')[:40],
                'eolr': hr['eolr'],
                'cells': cells,
            })

        # Stats
        total_arts = conn.execute('SELECT COUNT(*) FROM ob_articles').fetchone()[0]
        gaps = sum(1 for r in matrix_rows for c in r['cells'] if c['status'] == 'missing')
        has_cnt = sum(1 for r in matrix_rows for c in r['cells'] if c['status'] == 'has_data')
        completion = round(has_cnt / (has_cnt + gaps) * 100, 1) if (has_cnt + gaps) > 0 else 0

        return {
            'ok': True,
            'types': types,
            'rows': matrix_rows,
            'no_data_arts': no_data_arts,
            'stats': {
                'total_arts': total_arts,
                'no_ie_count': len(no_data_arts),
                'gaps': gaps,
                'has_data': has_cnt,
                'completion_pct': completion,
            },
        }
    finally:
        conn.close()


def get_ie_sheet_grid(header_id, sheet_name):
    """Return all cells for one sheet as a 2-D dict {row: {col: {value, formula, cell_type}}}."""
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT row, col, value, formula, cell_type FROM ie_sheet_data WHERE header_id=? AND sheet_name=? ORDER BY row, col',
            (header_id, sheet_name)
        ).fetchall()
        grid = {}
        for r in rows:
            rk = r['row']
            if rk not in grid:
                grid[rk] = {}
            grid[rk][r['col']] = {'v': r['value'], 'f': r['formula'], 't': r['cell_type']}
        max_row = max(grid.keys()) if grid else 0
        max_col = max((max(cols.keys()) for cols in grid.values()), default=0)
        return {'ok': True, 'sheet_name': sheet_name, 'max_row': max_row, 'max_col': max_col, 'grid': grid}
    finally:
        conn.close()


def save_ie_sheet_data(header_id, sheet_rows):
    """Replace all ie_sheet_data for header_id with new rows.
    sheet_rows: list of (sheet_name, row, col, value, formula)
    """
    conn = get_conn()
    try:
        conn.execute('DELETE FROM ie_sheet_data WHERE header_id=?', (header_id,))
        conn.executemany(
            'INSERT INTO ie_sheet_data (header_id, sheet_name, row, col, value, formula) VALUES (?,?,?,?,?,?)',
            [(header_id,) + tuple(r) for r in sheet_rows]
        )
        conn.commit()
        return {'ok': True, 'rows_written': len(sheet_rows)}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def update_ie_mp(header_id, cutting, stitching, assembly, stock):
    """Update ob_epph values for a header (creates row if missing)."""
    conn = get_conn()
    try:
        ts = now_iso()
        existing = conn.execute(
            'SELECT id FROM ob_epph WHERE header_id=?', (header_id,)
        ).fetchone()
        if existing:
            conn.execute(
                '''UPDATE ob_epph SET cutting=?, stitching=?, assembly=?, stock=?,
                   source='manual_ie' WHERE header_id=?''',
                (float(cutting or 0), float(stitching or 0),
                 float(assembly or 0), float(stock or 0), header_id)
            )
        else:
            conn.execute(
                '''INSERT INTO ob_epph (header_id, cutting, stitching, assembly, stock, source)
                   VALUES (?,?,?,?,?,'manual_ie')''',
                (header_id, float(cutting or 0), float(stitching or 0),
                 float(assembly or 0), float(stock or 0))
            )
        conn.execute(
            "UPDATE ob_header SET updated_at=? WHERE id=?", (ts, header_id)
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def add_art_to_header(art, header_id):
    """Add an ART to an existing ob_header. Silently ignores if already present."""
    conn = get_conn()
    try:
        conn.execute(
            'INSERT OR IGNORE INTO ob_articles (header_id, art) VALUES (?,?)',
            (header_id, art.strip())
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

def remove_art_from_header(art, header_id):
    """Remove one ART from a header. Deletes the header if it becomes empty."""
    conn = get_conn()
    try:
        conn.execute('DELETE FROM ob_articles WHERE art=? AND header_id=?', (art, header_id))
        remaining = conn.execute(
            'SELECT COUNT(*) FROM ob_articles WHERE header_id=?', (header_id,)
        ).fetchone()[0]
        deleted_header = False
        if remaining == 0:
            conn.execute('DELETE FROM ob_epph  WHERE header_id=?', (header_id,))
            conn.execute('DELETE FROM ob_rows  WHERE header_id=?', (header_id,))
            conn.execute('DELETE FROM ob_header WHERE id=?',       (header_id,))
            deleted_header = True
        conn.commit()
        return {'ok': True, 'deleted_header': deleted_header}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def delete_ie_header(header_id):
    """Delete a single ob_header record and all its related data."""
    conn = get_conn()
    try:
        conn.execute('DELETE FROM ob_articles WHERE header_id=?', (header_id,))
        conn.execute('DELETE FROM ob_epph     WHERE header_id=?', (header_id,))
        conn.execute('DELETE FROM ob_rows     WHERE header_id=?', (header_id,))
        conn.execute('DELETE FROM ie_process  WHERE header_id=?', (header_id,))
        conn.execute('DELETE FROM ob_header   WHERE id=?',        (header_id,))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def create_ie_record(art, model_name, eolr):
    """Create a new ob_header + ob_articles record."""
    import datetime
    conn = get_conn()
    try:
        ts = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
        header_id = conn.execute(
            'INSERT INTO ob_header (model_name, eolr, run, created_at, updated_at) VALUES (?,?,1,?,?)',
            (model_name, int(eolr), ts, ts)
        ).lastrowid
        conn.execute(
            'INSERT OR IGNORE INTO ob_articles (header_id, art) VALUES (?,?)',
            (header_id, art.strip())
        )
        conn.commit()
        return {'ok': True, 'header_id': header_id}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_ie_model_detail(header_id):
    """Return single header with arts, epph, and ie_sheet_data sheet name list."""
    conn = get_conn()
    try:
        h = conn.execute('SELECT * FROM ob_header WHERE id=?', (header_id,)).fetchone()
        if not h:
            return {'ok': False, 'error': 'Header not found'}
        arts = [r['art'] for r in conn.execute(
            'SELECT art FROM ob_articles WHERE header_id=? ORDER BY id', (header_id,)
        ).fetchall()]
        ep = conn.execute('SELECT * FROM ob_epph WHERE header_id=?', (header_id,)).fetchone()
        sheet_rows = conn.execute(
            'SELECT sheet_name FROM ie_sheet_data WHERE header_id=? GROUP BY sheet_name ORDER BY MIN(id)',
            (header_id,)
        ).fetchall()
        sheets = [r['sheet_name'] for r in sheet_rows]
        return {
            'ok': True,
            'header': {
                'id':         h['id'],
                'model_name': h['model_name'] or '',
                'season':     h['season'] or '',
                'eolr':       h['eolr'],
                'run':        h['run'],
                'material':   h['material'] or '',
                'category':   h['category'] or '',
                'arts':       arts,
                'epph':       dict(ep) if ep else {},
                'sheets':     sheets,
            }
        }
    finally:
        conn.close()


# ── Lookup ───────────────────────────────────────────────────────────────────

def get_all_lookup():
    conn = get_conn()
    try:
        rows = conn.execute('SELECT viet, zh FROM lookup_viet_zh ORDER BY viet').fetchall()
        return {'ok': True, 'lookup': {r['viet']: r['zh'] for r in rows}}
    finally:
        conn.close()


def add_lookup_entry(viet, zh):
    conn = get_conn()
    try:
        viet = viet.lower().strip()
        if not viet or not zh:
            return {'ok': False, 'error': 'viet and zh are required'}
        conn.execute(
            'INSERT INTO lookup_viet_zh (viet, zh, created_at) VALUES (?,?,?) '
            'ON CONFLICT(viet) DO UPDATE SET zh=excluded.zh',
            (viet, zh.strip(), now_iso())
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

# ── DS-02 E-PPH lookup (cross-table join helper) ─────────────────────────────

def get_epph_by_art(art):
    conn = get_conn()
    try:
        row = conn.execute(
            '''SELECT lc_cutting, lc_stitching, lc_stockfitting, lc_assembly
               FROM ds02_fob WHERE art=?''', (art,)
        ).fetchone()
        if not row:
            return {'ok': False, 'error': 'ART not found in DS-02'}
        return {
            'ok': True,
            'cutting':     row['lc_cutting'],
            'stitching':   row['lc_stitching'],
            'assembly':    row['lc_assembly'],
            'stockfitting': row['lc_stockfitting'],
        }
    finally:
        conn.close()


# ── DS-02 / DS-01 Import ─────────────────────────────────────────────────────

def _flt(rec, field):
    v = rec.get(field)
    try:
        return float(v) if v is not None and str(v).strip() != '' else None
    except (TypeError, ValueError):
        return None


def import_ds02_records(records):
    conn = get_conn()
    ts = now_iso()
    stats = {'new': 0, 'updated': 0, 'unchanged': 0, 'errors': 0, 'error_details': []}
    track_fields = ['model_no', 'model_name', 'silhouette_no', 'factory', 'season', 'category',
                    'lc_total', 'lc_ctb', 'lc_cutting', 'lc_stitching', 'lc_stockfitting',
                    'lc_assembly', 'stage', 'valid_from']
    try:
        for rec in records:
            art = str(rec.get('art', '') or '').strip()
            if not art:
                stats['errors'] += 1
                continue
            try:
                existing = conn.execute('SELECT * FROM ds02_fob WHERE art=?', (art,)).fetchone()
                if existing:
                    changes = [(f, existing[f], rec.get(f)) for f in track_fields
                               if str(existing[f] if existing[f] is not None else '')
                               != str(rec.get(f) if rec.get(f) is not None else '')]
                    if changes:
                        for f, ov, nv in changes:
                            conn.execute(
                                'INSERT INTO change_log (table_name,record_key,field_name,old_value,new_value,changed_at) VALUES (?,?,?,?,?,?)',
                                ('ds02_fob', art, f, str(ov), str(nv), ts))
                        conn.execute(
                            '''UPDATE ds02_fob SET model_no=?,model_name=?,silhouette_no=?,
                               factory=?,season=?,category=?,lc_total=?,lc_ctb=?,lc_cutting=?,
                               lc_stitching=?,lc_stockfitting=?,lc_assembly=?,stage=?,
                               valid_from=?,raw_data=?,updated_at=? WHERE art=?''',
                            (rec.get('model_no'), rec.get('model_name'), rec.get('silhouette_no'),
                             rec.get('factory'), rec.get('season'), rec.get('category'),
                             _flt(rec, 'lc_total'), _flt(rec, 'lc_ctb'), _flt(rec, 'lc_cutting'),
                             _flt(rec, 'lc_stitching'), _flt(rec, 'lc_stockfitting'),
                             _flt(rec, 'lc_assembly'), rec.get('stage'), rec.get('valid_from'),
                             rec.get('raw_data'), ts, art))
                        stats['updated'] += 1
                    else:
                        stats['unchanged'] += 1
                else:
                    conn.execute(
                        '''INSERT INTO ds02_fob (art,model_no,model_name,silhouette_no,factory,
                           season,category,lc_total,lc_ctb,lc_cutting,lc_stitching,
                           lc_stockfitting,lc_assembly,stage,valid_from,raw_data,imported_at,updated_at)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (art, rec.get('model_no'), rec.get('model_name'), rec.get('silhouette_no'),
                         rec.get('factory'), rec.get('season'), rec.get('category'),
                         _flt(rec, 'lc_total'), _flt(rec, 'lc_ctb'), _flt(rec, 'lc_cutting'),
                         _flt(rec, 'lc_stitching'), _flt(rec, 'lc_stockfitting'),
                         _flt(rec, 'lc_assembly'), rec.get('stage'), rec.get('valid_from'),
                         rec.get('raw_data'), ts, ts))
                    stats['new'] += 1
            except Exception as e:
                stats['errors'] += 1
                stats['error_details'].append(f'{art}: {e}')
        conn.commit()
        return {'ok': True, 'stats': stats}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e), 'stats': stats}
    finally:
        conn.close()


def import_ds01_records(records):
    conn = get_conn()
    ts = now_iso()
    stats = {'new': 0, 'updated': 0, 'unchanged': 0, 'errors': 0, 'error_details': []}
    try:
        for rec in records:
            art    = str(rec.get('article_id', '') or '').strip()
            ptdesc = str(rec.get('product_type_desc', '') or '').strip()
            month  = str(rec.get('calendar_month', '') or '').strip()
            if not (art and ptdesc and month):
                stats['errors'] += 1
                continue
            try:
                existing = conn.execute(
                    'SELECT * FROM ds01_sp WHERE article_id=? AND product_type_desc=? AND calendar_month=?',
                    (art, ptdesc, month)).fetchone()
                qty = _flt(rec, 'quantity')
                raw = rec.get('raw_data')
                if existing:
                    old_qty = existing['quantity']
                    if str(old_qty or '') != str(qty or ''):
                        conn.execute(
                            'INSERT INTO change_log (table_name,record_key,field_name,old_value,new_value,changed_at) VALUES (?,?,?,?,?,?)',
                            ('ds01_sp', f'{art}|{ptdesc}|{month}', 'quantity', str(old_qty), str(qty), ts))
                        conn.execute(
                            'UPDATE ds01_sp SET quantity=?,raw_data=?,updated_at=? WHERE article_id=? AND product_type_desc=? AND calendar_month=?',
                            (qty, raw, ts, art, ptdesc, month))
                        stats['updated'] += 1
                    else:
                        stats['unchanged'] += 1
                else:
                    conn.execute(
                        'INSERT INTO ds01_sp (article_id,product_type_desc,calendar_month,quantity,raw_data,imported_at,updated_at) VALUES (?,?,?,?,?,?,?)',
                        (art, ptdesc, month, qty, raw, ts, ts))
                    stats['new'] += 1
            except Exception as e:
                stats['errors'] += 1
                stats['error_details'].append(f'{art}|{ptdesc}|{month}: {e}')
        conn.commit()
        return {'ok': True, 'stats': stats}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e), 'stats': stats}
    finally:
        conn.close()


def list_ds02_records(limit=200, offset=0):
    conn = get_conn()
    try:
        rows = conn.execute(
            '''SELECT art,model_name,factory,season,category,lc_total,
               lc_cutting,lc_stitching,lc_stockfitting,lc_assembly,updated_at
               FROM ds02_fob ORDER BY updated_at DESC LIMIT ? OFFSET ?''',
            (limit, offset)).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM ds02_fob').fetchone()[0]
        return {'ok': True, 'records': [dict(r) for r in rows], 'total': total}
    finally:
        conn.close()


def list_ds01_records(limit=200, offset=0):
    conn = get_conn()
    try:
        rows = conn.execute(
            '''SELECT article_id,product_type_desc,calendar_month,quantity,updated_at
               FROM ds01_sp ORDER BY updated_at DESC LIMIT ? OFFSET ?''',
            (limit, offset)).fetchall()
        total = conn.execute('SELECT COUNT(*) FROM ds01_sp').fetchone()[0]
        return {'ok': True, 'records': [dict(r) for r in rows], 'total': total}
    finally:
        conn.close()


def get_ie_cutting_process(art=None, flag=None, limit=2000):
    conn = get_conn()
    try:
        where_parts = ["segment='cutting'"]
        params = []
        if art:
            where_parts.append("art=?")
            params.append(art)
        if flag:
            where_parts.append("flag=?")
            params.append(flag)
        where_parts.append(_eff_stage_clause('ie_process'))  # 版本控制: 只計有效版本
        where = ' AND '.join(where_parts)
        rows = conn.execute(
            f'''SELECT id, header_id, art, zone, seq, process_name, part_name,
                       tct, value_type, formula, source_sheet, source_row, flag
               FROM ie_process WHERE {where}
               ORDER BY art, source_row LIMIT ?''',
            params + [limit]).fetchall()
        # Stats
        stats_row = conn.execute(
            '''SELECT COUNT(*) as total,
                      COUNT(DISTINCT art) as arts,
                      SUM(CASE WHEN value_type='formula' THEN 1 ELSE 0 END) as formula_cnt,
                      SUM(CASE WHEN value_type='manual' THEN 1 ELSE 0 END) as manual_cnt,
                      SUM(CASE WHEN flag='待分區' THEN 1 ELSE 0 END) as pending_cnt,
                      SUM(CASE WHEN tct IS NOT NULL AND tct > 0 THEN 1 ELSE 0 END) as tct_cnt
               FROM ie_process WHERE segment='cutting' AND ''' + _eff_stage_clause('ie_process')).fetchone()
        stats = dict(stats_row) if stats_row else {}
        return {
            'ok': True,
            'records': [dict(r) for r in rows],
            'stats': stats,
        }
    except Exception as e:
        return {'ok': False, 'error': str(e), 'records': [], 'stats': {}}
    finally:
        conn.close()


def get_ie_cutting_arts():
    conn = get_conn()
    try:
        rows = conn.execute(
            '''SELECT art, COUNT(*) as row_cnt,
                      SUM(CASE WHEN value_type='formula' THEN 1 ELSE 0 END) as formula_cnt,
                      SUM(CASE WHEN flag='待分區' THEN 1 ELSE 0 END) as pending_cnt,
                      SUM(CASE WHEN tct IS NOT NULL AND tct > 0 THEN 1 ELSE 0 END) as tct_cnt
               FROM ie_process WHERE segment='cutting' AND ''' + _eff_stage_clause('ie_process') + '''
               GROUP BY art ORDER BY art''').fetchall()
        return {'ok': True, 'arts': [dict(r) for r in rows]}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'arts': []}
    finally:
        conn.close()


def get_ie_process_by_header(header_id, segment='cutting'):
    conn = get_conn()
    try:
        rows = conn.execute(
            '''SELECT zone, seq, process_name, part_name, tct, value_type, formula, flag, source_sheet
               FROM ie_process
               WHERE header_id=? AND segment=? AND ''' + _eff_stage_clause('ie_process') + '''
               ORDER BY zone, seq, source_sheet, id''',
            (header_id, segment)).fetchall()
        zones = {}
        for r in rows:
            z = r['zone'] if not r['flag'] else '待分區'
            if z not in zones:
                zones[z] = []
            zones[z].append(dict(r))
        stats_row = conn.execute(
            '''SELECT COUNT(*) as total,
                      SUM(CASE WHEN value_type='formula' THEN 1 ELSE 0 END) as formula_cnt,
                      SUM(CASE WHEN value_type='manual'  THEN 1 ELSE 0 END) as manual_cnt,
                      SUM(CASE WHEN flag='待分區'        THEN 1 ELSE 0 END) as pending_cnt
               FROM ie_process WHERE header_id=? AND segment=? AND ''' + _eff_stage_clause('ie_process'),
            (header_id, segment)).fetchone()
        stats = dict(stats_row) if stats_row else {}
        return {'ok': True, 'segment': segment, 'zones': zones, 'stats': stats}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'zones': {}, 'stats': {}}
    finally:
        conn.close()


ZONE_ORDER = {
    'cutting':  ['裁斷機', 'ATOM', 'Laser', 'EMMA', 'YINGHUI', '移印', '轉印', '水蜘蛛', '_summary', '待分區'],
    'stitching':['主流', '支流', '電腦針車', '折边', '水蜘蛛', '待分區'],
    'assembly': ['成型主區', '成型UV', '水蜘蛛', '待分區'],
    'stf':      ['打粗', '照射', '水洗', '貼底', '水蜘蛛', '待分區'],
}
# Offline zones excluded from SUM C2B per-segment totals
OFFLINE_ZONES = {
    'cutting':   ['水蜘蛛'],
    'stitching': ['電腦針車', '折边', '水蜘蛛'],
    'assembly':  ['水蜘蛛', '成型UV'],
    'stf':       ['水蜘蛛'],
}


def get_ie_stages(header_id):
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT id, stage_name, created_at, COALESCE(is_approved,0) AS is_approved '
            'FROM ie_stage WHERE header_id=? ORDER BY id',
            (header_id,)
        ).fetchall()
        return {'ok': True, 'stages': [dict(r) for r in rows]}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


# ── 版本控制 Step 1: effective-stage 解析 ─────────────────────────────────────
# 「當前有效版本」規則：指定 stage_id → 用它；否則該 header 的鎖定版(is_approved=1)；
# 沒鎖定版 → 最新版(id 最大)。單一版本資料下等同回傳唯一的 v1（本步驟為 no-op）。
def _effective_stage_id(conn, header_id, stage_id=None):
    if stage_id:
        return int(stage_id)
    r = conn.execute(
        'SELECT id FROM ie_stage WHERE header_id=? '
        'ORDER BY COALESCE(is_approved,0) DESC, id DESC LIMIT 1',
        (header_id,)
    ).fetchone()
    return r[0] if r else None

# 相關子查詢：把某 header 的 ie_process 限制在其 effective stage。
# 對「每 header 恰一版本」的現況是 no-op；一旦出現多版本可防止聚合重複計算。
# {a} = ie_process 的別名（例如 'ip' / 'ip2' / 'ie_process'）。
def _eff_stage_clause(a='ie_process'):
    return (f"{a}.stage_id = (SELECT s.id FROM ie_stage s "
            f"WHERE s.header_id = {a}.header_id "
            f"ORDER BY COALESCE(s.is_approved,0) DESC, s.id DESC LIMIT 1)")


def _calc_theory(standard_time, eolr):
    if standard_time is None:
        return None
    divisor = 3600.0 / eolr
    return round(standard_time / divisor, 4) if divisor else None


def get_ie_cell_data(header_id, segment='cutting', eolr=120, stage_id=None):
    conn = get_conn()
    try:
        eolr = int(eolr)
        # 版本控制 Step 1: 解析當前有效版本，只讀該版工序
        eff_stage = _effective_stage_id(conn, header_id, stage_id)
        stage_row = conn.execute(
            'SELECT id, stage_name, COALESCE(is_approved,0) AS is_approved '
            'FROM ie_stage WHERE id=?', (eff_stage,)
        ).fetchone() if eff_stage else None
        stage = dict(stage_row) if stage_row else {'id': None, 'stage_name': '無', 'is_approved': 0}

        stage_filter = ' AND stage_id=?' if eff_stage else ''
        stage_param  = [eff_stage] if eff_stage else []

        rows = conn.execute('''
            SELECT id, zone, seq, process_name, part_name, flag,
                   normal_time, allowance_pct, standard_time, tct,
                   actual_operators, machine, cut_per_hour, qty_per_pair,
                   layers_per_cut, process_name_vi, process_name_zh, mat_cat,
                   equipment_type,
                   post_marking_std, post_marking_ops,
                   post_skiving_std, post_skiving_ops,
                   post_attach_std, post_attach_ops,
                   post_edge_std, post_edge_ops,
                   post_heat_std, post_heat_ops,
                   post_polish_std, post_polish_ops,
                   value_type, is_locked, source_sheet, formula, stage
            FROM ie_process
            WHERE header_id=? AND segment=? AND (flag IS NULL OR flag != 'deleted')''' + stage_filter + '''
            ORDER BY zone, seq ASC, id
        ''', [header_id, segment] + stage_param).fetchall()

        # Also load process groups for this segment (同版過濾)
        group_rows = conn.execute('''
            SELECT id, zone, process_ids, headcount, note
            FROM ie_process_group
            WHERE header_id=? AND segment=?''' + stage_filter + '''
            ORDER BY id
        ''', [header_id, segment] + stage_param).fetchall()
        # Build map: process_id -> (group_id, headcount)
        group_map = {}
        for gr in group_rows:
            import json as _json
            pids = _json.loads(gr['process_ids'])
            for pid in pids:
                group_map[pid] = {'group_id': gr['id'], 'headcount': gr['headcount'], 'note': gr['note']}

        zone_map = {}
        hand_total = 0.0

        for r in rows:
            z = r['zone']
            if not z:
                z = '待分區'

            rec = dict(r)
            # Recalculate theory from standard_time if not locked
            if r['is_locked']:
                rec['theory_operators'] = r['tct']  # fixed value
            else:
                rec['theory_operators'] = _calc_theory(r['standard_time'], eolr)

            # Attach group info if this process is grouped
            if r['id'] in group_map:
                rec['group_info'] = group_map[r['id']]
            else:
                rec['group_info'] = None

            if z not in zone_map:
                zone_map[z] = []
            zone_map[z].append(rec)

            # Accumulate hand total (non-裁斷機 + non-offline zones, non-summary)
            offline = OFFLINE_ZONES.get(segment, [])
            if segment == 'cutting' and z not in ('裁斷機', '_summary') and z not in offline and rec['theory_operators']:
                hand_total += rec['theory_operators']

        # Build ordered list of zones — always include 水蜘蛛 even if empty
        order = list(ZONE_ORDER.get(segment, []))
        seen = set(order)
        for z in zone_map:
            if z not in seen:
                order.append(z)

        zones = []
        for z in order:
            if z in ('_summary', '待分區'):
                # _summary / 待分區：只有真的有資料(孤兒工序)才顯示
                if z in zone_map:
                    zones.append({'zone': z, 'rows': zone_map[z], 'always_show': False})
            elif z in seen:
                # ZONE_ORDER 內的標準區(主流/支流/電腦針車/折边/水蜘蛛/成型主區/成型UV/
                # 打粗/照射/水洗/貼底/裁斷機…)：空的也固定顯示框架(表頭 + ＋號)，
                # 讓所有鞋型結構一致，差異只在有無資料
                zones.append({'zone': z, 'rows': zone_map.get(z, []), 'always_show': True})
            elif z in zone_map:
                # ZONE_ORDER 之外、僅存在於資料的額外 zone：有資料才顯示
                zones.append({'zone': z, 'rows': zone_map[z], 'always_show': False})

        # Update _summary row theory_operators with computed hand_total
        for z_entry in zones:
            if z_entry['zone'] == '_summary':
                for row in z_entry['rows']:
                    row['theory_operators'] = round(hand_total, 4)

        return {
            'ok': True, 'header_id': header_id, 'segment': segment,
            'eolr': eolr, 'stage': stage, 'zones': zones,
            'hand_total': round(hand_total, 4),
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def save_ie_edit(process_id, stage_id, field, value, user):
    conn = get_conn()
    try:
        old_row = conn.execute(
            f'SELECT {field} FROM ie_process WHERE id=?', (process_id,)
        ).fetchone()
        old_value = str(old_row[0]) if old_row and old_row[0] is not None else None
        # Apply immediately to ie_process so values survive reload/merge
        conn.execute(f'UPDATE ie_process SET {field}=? WHERE id=?', (value, process_id))
        # Record with status='applied' for audit trail
        conn.execute('''
            INSERT INTO ie_edit_log (process_id, stage_id, field, old_value, new_value, user, status)
            VALUES (?,?,?,?,?,?, 'applied')
        ''', (process_id, stage_id, field, old_value, str(value), user))
        conn.commit()
        log_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        return {'ok': True, 'log_id': log_id}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def approve_ie_edit(log_id, approver):
    conn = get_conn()
    try:
        log_row = conn.execute(
            'SELECT process_id, field, new_value FROM ie_edit_log WHERE id=? AND status=?',
            (log_id, 'pending')
        ).fetchone()
        if not log_row:
            return {'ok': False, 'error': 'log not found or already processed'}
        conn.execute(
            f'UPDATE ie_process SET {log_row["field"]}=? WHERE id=?',
            (log_row['new_value'], log_row['process_id'])
        )
        conn.execute(
            'UPDATE ie_edit_log SET status=?, user=? WHERE id=?',
            ('approved', approver, log_id)
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def add_ie_process_row(header_id, segment, zone, process_name, standard_time, stage_id, user='demo', part_name=None, tct=None,
                       mat_cat=None, process_name_zh=None, cut_per_hour=None, qty_per_pair=None, layers_per_cut=None, actual_operators=None,
                       normal_time=None, allowance_pct=None):
    """Add a new process row and log the action."""
    # Auto-compute standard_time for stitching/assembly/STF rows (normal_time × allowance)
    # Cutting type A (裁斷機) intentionally stores NULL — frontend computes live from three fields
    if standard_time is None and normal_time is not None:
        try:
            ap = float(allowance_pct) if allowance_pct is not None else 10.0
            standard_time = round(float(normal_time) * (1 + ap / 100), 4)
        except (TypeError, ValueError):
            pass
    conn = get_conn()
    try:
        # 版本控制: 新工序綁到當前有效版本（stage_id 省略時自動解析）
        eff_stage = _effective_stage_id(conn, header_id, stage_id)
        # Look up art from existing rows for this header
        art_row = conn.execute(
            'SELECT art FROM ie_process WHERE header_id=? LIMIT 1', (header_id,)
        ).fetchone()
        art = art_row['art'] if art_row else str(header_id)
        # Find max seq in this zone (同版)
        max_seq = conn.execute(
            'SELECT MAX(seq) FROM ie_process WHERE header_id=? AND segment=? AND zone=? '
            'AND (stage_id=? OR ? IS NULL)',
            (header_id, segment, zone, eff_stage, eff_stage)
        ).fetchone()[0] or 0
        conn.execute('''
            INSERT INTO ie_process (header_id, art, segment, zone, seq, process_name, part_name, tct, standard_time, flag,
                                    mat_cat, process_name_zh, cut_per_hour, qty_per_pair, layers_per_cut, actual_operators,
                                    normal_time, allowance_pct, stage_id)
            VALUES (?,?,?,?,?,?,?,?,?, 'new',?,?,?,?,?,?,?,?,?)
        ''', (header_id, art, segment, zone, max_seq + 1, process_name, part_name, tct, standard_time,
              mat_cat, process_name_zh, cut_per_hour, qty_per_pair, layers_per_cut, actual_operators,
              normal_time, allowance_pct, eff_stage))
        conn.commit()
        new_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        # Log as edit
        conn.execute('''
            INSERT INTO ie_edit_log (process_id, stage_id, field, old_value, new_value, user, status)
            VALUES (?,?,'_add',NULL,?,?,'pending')
        ''', (new_id, stage_id, process_name, user))
        conn.commit()
        return {'ok': True, 'process_id': new_id}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def insert_ie_process_row_after(after_process_id, process_name, stage_id, user='demo', part_name=None, tct=None,
                                mat_cat=None, process_name_zh=None, cut_per_hour=None, qty_per_pair=None,
                                layers_per_cut=None, actual_operators=None, normal_time=None, allowance_pct=None,
                                standard_time=None):
    """Insert a new process row directly BELOW an existing row (same segment/zone),
    pushing all later rows in that zone down by one seq. Mirrors add_ie_process_row."""
    if standard_time is None and normal_time is not None:
        try:
            ap = float(allowance_pct) if allowance_pct is not None else 10.0
            standard_time = round(float(normal_time) * (1 + ap / 100), 4)
        except (TypeError, ValueError):
            pass
    conn = get_conn()
    try:
        anchor = conn.execute(
            'SELECT header_id, art, segment, zone, seq, stage_id FROM ie_process WHERE id=?', (after_process_id,)
        ).fetchone()
        if not anchor:
            return {'ok': False, 'error': 'anchor row not found'}
        header_id = anchor['header_id']
        art       = anchor['art']
        segment   = anchor['segment']
        zone      = anchor['zone']
        after_seq = anchor['seq'] if anchor['seq'] is not None else 0
        # 版本控制: 新列繼承 anchor 的版本（同版插入）
        eff_stage = anchor['stage_id'] if anchor['stage_id'] is not None else _effective_stage_id(conn, header_id, stage_id)
        # Push later rows in the same zone down by one, so the new row slots in right after anchor (同版)
        conn.execute(
            'UPDATE ie_process SET seq = seq + 1 WHERE header_id=? AND segment=? AND zone=? AND seq > ? '
            'AND (stage_id=? OR ? IS NULL)',
            (header_id, segment, zone, after_seq, eff_stage, eff_stage)
        )
        conn.execute('''
            INSERT INTO ie_process (header_id, art, segment, zone, seq, process_name, part_name, tct, standard_time, flag,
                                    mat_cat, process_name_zh, cut_per_hour, qty_per_pair, layers_per_cut, actual_operators,
                                    normal_time, allowance_pct, stage_id)
            VALUES (?,?,?,?,?,?,?,?,?, 'new',?,?,?,?,?,?,?,?,?)
        ''', (header_id, art, segment, zone, after_seq + 1, process_name, part_name, tct, standard_time,
              mat_cat, process_name_zh, cut_per_hour, qty_per_pair, layers_per_cut, actual_operators,
              normal_time, allowance_pct, eff_stage))
        conn.commit()
        new_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.execute('''
            INSERT INTO ie_edit_log (process_id, stage_id, field, old_value, new_value, user, status)
            VALUES (?,?,'_add',NULL,?,?,'pending')
        ''', (new_id, stage_id, process_name, user))
        conn.commit()
        return {'ok': True, 'process_id': new_id, 'segment': segment, 'zone': zone}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def delete_ie_process_row(process_id, stage_id, user='demo'):
    """Soft-delete: mark flag='deleted' and log."""
    ALLOWED = {'actual_operators', 'standard_time', 'normal_time', 'cut_per_hour',
               'qty_per_pair', 'layers_per_cut', 'process_name', 'process_name_vi',
               'allowance_pct', 'flag', '_add', '_delete'}
    conn = get_conn()
    try:
        old_row = conn.execute(
            'SELECT process_name, flag FROM ie_process WHERE id=?', (process_id,)
        ).fetchone()
        if not old_row:
            return {'ok': False, 'error': 'row not found'}
        conn.execute("UPDATE ie_process SET flag='deleted' WHERE id=?", (process_id,))
        conn.execute('''
            INSERT INTO ie_edit_log (process_id, stage_id, field, old_value, new_value, user, status)
            VALUES (?,?,'_delete',?,'deleted',?,'pending')
        ''', (process_id, stage_id, old_row['process_name'], user))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def save_ie_process_group(header_id, segment, zone, stage_id, process_ids, headcount, note=''):
    """Save or update a process grouping, then reorder seq so merged rows are adjacent."""
    import json as _json
    conn = get_conn()
    try:
        # 版本控制: 合併綁到當前有效版本
        eff_stage = _effective_stage_id(conn, header_id, stage_id)
        # Remove existing groups that overlap these process_ids (同版)
        existing = conn.execute(
            'SELECT id, process_ids FROM ie_process_group '
            'WHERE header_id=? AND segment=? AND zone=? AND (stage_id=? OR ? IS NULL)',
            (header_id, segment, zone, eff_stage, eff_stage)
        ).fetchall()
        pid_set = set(int(p) for p in process_ids)
        for eg in existing:
            old_pids = set(_json.loads(eg['process_ids']))
            if old_pids & pid_set:
                conn.execute('DELETE FROM ie_process_group WHERE id=?', (eg['id'],))
        conn.execute('''
            INSERT INTO ie_process_group (header_id, segment, zone, stage_id, process_ids, headcount, note)
            VALUES (?,?,?,?,?,?,?)
        ''', (header_id, segment, zone, eff_stage, _json.dumps([int(p) for p in process_ids]), headcount, note))

        # Reorder seq so merged processes sit adjacent (at the position of the earliest merged process).
        # actual_operators on each ie_process row is NOT touched — values survive merge/unmerge. (同版)
        all_rows = conn.execute(
            'SELECT id FROM ie_process '
            'WHERE header_id=? AND segment=? AND zone=? AND (flag IS NULL OR flag != \'deleted\') '
            'AND (stage_id=? OR ? IS NULL) '
            'ORDER BY seq ASC, id ASC',
            (header_id, segment, zone, eff_stage, eff_stage)
        ).fetchall()
        all_ids = [r['id'] for r in all_rows]
        if all_ids:
            merged_in_order = [rid for rid in all_ids if rid in pid_set]
            non_merged      = [rid for rid in all_ids if rid not in pid_set]
            # anchor = how many non-merged rows come before the first merged row
            first_merged_pos = all_ids.index(merged_in_order[0])
            anchor = sum(1 for rid in all_ids[:first_merged_pos] if rid not in pid_set)
            new_order = non_merged[:anchor] + merged_in_order + non_merged[anchor:]
            for new_seq, rid in enumerate(new_order, start=1):
                conn.execute('UPDATE ie_process SET seq=? WHERE id=?', (new_seq, rid))

        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def update_ie_process_group(group_id, headcount):
    """Update headcount for an existing group."""
    conn = get_conn()
    try:
        conn.execute('UPDATE ie_process_group SET headcount=? WHERE id=?', (headcount, group_id))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def delete_ie_process_group(group_id):
    """Delete a group. Each process retains its own actual_operators (not cleared)."""
    conn = get_conn()
    try:
        conn.execute('DELETE FROM ie_process_group WHERE id=?', (group_id,))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_ie_process_groups(header_id, segment):
    """Return all groupings for a header/segment."""
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT id, zone, process_ids, headcount, note FROM ie_process_group WHERE header_id=? AND segment=?',
            (header_id, segment)
        ).fetchall()
        return {'ok': True, 'groups': [dict(r) for r in rows]}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def create_ie_stage(header_id, stage_name, source_stage_id=None):
    """另存新版本 = 建新 stage + 複製「來源版本」的所有工序與合併到新 stage。
    source_stage_id 省略 → 複製當前有效版本。新版本是來源版的完整獨立副本，
    之後改新版不影響來源版。"""
    conn = get_conn()
    try:
        src_stage = _effective_stage_id(conn, header_id, source_stage_id)

        conn.execute('INSERT INTO ie_stage (header_id, stage_name, is_approved) VALUES (?,?,0)',
                     (header_id, stage_name))
        new_stage = conn.execute('SELECT last_insert_rowid()').fetchone()[0]

        copied_rows = 0
        id_map = {}  # old process id -> new process id（供 group 重新對應）
        if src_stage:
            # 動態欄位清單：複製除 id 外全部欄位，stage_id 換成新版
            cols = [r[1] for r in conn.execute('PRAGMA table_info(ie_process)')]
            copy_cols = [c for c in cols if c != 'id']
            select_list = ', '.join(copy_cols)
            insert_list = ', '.join(copy_cols)
            placeholders = ', '.join('?' * len(copy_cols))
            stage_idx = copy_cols.index('stage_id')

            src_rows = conn.execute(
                f'SELECT id, {select_list} FROM ie_process WHERE header_id=? AND stage_id=?',
                (header_id, src_stage)
            ).fetchall()
            for r in src_rows:
                old_id = r['id']
                vals = [r[c] for c in copy_cols]
                vals[stage_idx] = new_stage  # 綁新版
                conn.execute(
                    f'INSERT INTO ie_process ({insert_list}) VALUES ({placeholders})', vals)
                id_map[old_id] = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
                copied_rows += 1

            # 複製合併群組，process_ids 重新對應到新 rows
            import json as _json
            gcols = [r[1] for r in conn.execute('PRAGMA table_info(ie_process_group)')]
            gcopy = [c for c in gcols if c != 'id']
            g_sel = ', '.join(gcopy)
            g_ph  = ', '.join('?' * len(gcopy))
            src_groups = conn.execute(
                f'SELECT {g_sel} FROM ie_process_group WHERE header_id=? AND stage_id=?',
                (header_id, src_stage)
            ).fetchall()
            for g in src_groups:
                gvals = {c: g[c] for c in gcopy}
                gvals['stage_id'] = new_stage
                try:
                    old_pids = _json.loads(g['process_ids'])
                    gvals['process_ids'] = _json.dumps(
                        [id_map[p] for p in old_pids if p in id_map])
                except Exception:
                    pass
                conn.execute(
                    f'INSERT INTO ie_process_group ({g_sel}) VALUES ({g_ph})',
                    [gvals[c] for c in gcopy])

        conn.commit()
        return {'ok': True, 'stage_id': new_stage, 'copied_rows': copied_rows,
                'source_stage_id': src_stage}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_ie_header_meta(header_id):
    conn = get_conn()
    try:
        r = conn.execute(
            'SELECT id, model_name, eolr, season, material FROM ob_header WHERE id=?',
            (header_id,)
        ).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()


def search_ie_headers(q, exclude_header_id=None):
    """Search ob_header by model_name or ob_articles by art (LIKE %q%).
    Returns [{header_id, model_name, art}] deduplicated by header_id."""
    conn = get_conn()
    try:
        like = f'%{q}%'
        rows = conn.execute('''
            SELECT DISTINCT h.id AS header_id, h.model_name,
                   (SELECT art FROM ob_articles WHERE header_id=h.id ORDER BY id LIMIT 1) AS art
            FROM ob_header h
            LEFT JOIN ob_articles a ON a.header_id = h.id
            WHERE (h.model_name LIKE ? OR a.art LIKE ?)
              AND (? IS NULL OR h.id != ?)
            ORDER BY h.model_name
            LIMIT 50
        ''', (like, like, exclude_header_id, exclude_header_id)).fetchall()
        return [{'header_id': r['header_id'], 'model_name': r['model_name'] or '', 'art': r['art'] or ''} for r in rows]
    finally:
        conn.close()


def get_ie_import_zones(source_header_id, segment):
    """Return distinct non-deleted zones for a source header+segment."""
    conn = get_conn()
    try:
        rows = conn.execute('''
            SELECT DISTINCT zone FROM ie_process
            WHERE header_id=? AND segment=? AND (flag IS NULL OR flag != 'deleted')
            ORDER BY zone
        ''', (source_header_id, segment)).fetchall()
        _exclude = {'_summary', '待分區', '水蜘蛛'}
        return [r['zone'] for r in rows if r['zone'] and r['zone'] not in _exclude]
    finally:
        conn.close()


def import_ie_zone(target_header_id, source_header_id, segment, zone, overwrite=False):
    """Copy all non-deleted ie_process rows from source zone to target zone.
    If overwrite=False and target zone has existing rows, return need_confirm.
    If overwrite=True (or target is empty), soft-delete target zone rows then insert copies."""
    conn = get_conn()
    try:
        # Check target has existing non-deleted rows
        existing = conn.execute('''
            SELECT COUNT(*) FROM ie_process
            WHERE header_id=? AND segment=? AND zone=? AND (flag IS NULL OR flag != 'deleted')
        ''', (target_header_id, segment, zone)).fetchone()[0]

        if existing > 0 and not overwrite:
            return {'ok': False, 'need_confirm': True}

        # Fetch source rows ordered by seq
        src_rows = conn.execute('''
            SELECT seq, process_name, part_name, tct,
                   normal_time, allowance_pct, standard_time,
                   actual_operators, machine,
                   cut_per_hour, qty_per_pair, layers_per_cut,
                   process_name_vi, process_name_zh, mat_cat,
                   equipment_type,
                   post_marking_std, post_marking_ops,
                   post_skiving_std, post_skiving_ops,
                   post_attach_std, post_attach_ops,
                   post_edge_std, post_edge_ops,
                   post_heat_std, post_heat_ops,
                   post_polish_std, post_polish_ops,
                   value_type, is_locked, source_sheet, formula, stage
            FROM ie_process
            WHERE header_id=? AND segment=? AND zone=? AND (flag IS NULL OR flag != 'deleted')
            ORDER BY seq ASC, id ASC
        ''', (source_header_id, segment, zone)).fetchall()

        if not src_rows:
            return {'ok': False, 'error': '來源區塊無工序資料'}

        # Get target art
        art_row = conn.execute(
            'SELECT art FROM ie_process WHERE header_id=? LIMIT 1', (target_header_id,)
        ).fetchone()
        if not art_row:
            art_row = conn.execute(
                'SELECT art FROM ob_articles WHERE header_id=? ORDER BY id LIMIT 1', (target_header_id,)
            ).fetchone()
        target_art = art_row['art'] if art_row else str(target_header_id)

        # Soft-delete existing target zone rows
        conn.execute('''
            UPDATE ie_process SET flag='deleted'
            WHERE header_id=? AND segment=? AND zone=? AND (flag IS NULL OR flag != 'deleted')
        ''', (target_header_id, segment, zone))

        # 裁斷機 zone in cutting segment: standard_time stored NULL (frontend computes live)
        is_cutting_machine = (segment == 'cutting' and zone == '裁斷機')

        count = 0
        for i, r in enumerate(src_rows):
            std = None if is_cutting_machine else r['standard_time']
            conn.execute('''
                INSERT INTO ie_process
                  (header_id, art, segment, zone, seq,
                   process_name, part_name, tct, standard_time, flag,
                   mat_cat, process_name_zh, process_name_vi, equipment_type,
                   cut_per_hour, qty_per_pair, layers_per_cut,
                   actual_operators, normal_time, allowance_pct, machine,
                   post_marking_std, post_marking_ops,
                   post_skiving_std, post_skiving_ops,
                   post_attach_std, post_attach_ops,
                   post_edge_std, post_edge_ops,
                   post_heat_std, post_heat_ops,
                   post_polish_std, post_polish_ops,
                   value_type, is_locked, source_sheet, formula, stage)
                VALUES (?,?,?,?,?,?,?,?,?,NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                target_header_id, target_art, segment, zone, i + 1,
                r['process_name'], r['part_name'], r['tct'], std,
                r['mat_cat'], r['process_name_zh'], r['process_name_vi'], r['equipment_type'],
                r['cut_per_hour'], r['qty_per_pair'], r['layers_per_cut'],
                r['actual_operators'], r['normal_time'], r['allowance_pct'], r['machine'],
                r['post_marking_std'], r['post_marking_ops'],
                r['post_skiving_std'], r['post_skiving_ops'],
                r['post_attach_std'], r['post_attach_ops'],
                r['post_edge_std'], r['post_edge_ops'],
                r['post_heat_std'], r['post_heat_ops'],
                r['post_polish_std'], r['post_polish_ops'],
                r['value_type'], r['is_locked'], r['source_sheet'], r['formula'], r['stage'],
            ))
            count += 1

        conn.commit()
        return {'ok': True, 'imported_count': count}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_ie_sum(header_id, eolr=120):
    """SUM C2B: aggregate actual_operators (fallback to theory) per segment.
    Offline zones: 電腦針車 (stitching), 水蜘蛛 + 成型UV (assembly).
    All water spiders are stored in assembly/水蜘蛛 and excluded from totals.
    """
    eolr = int(eolr)
    target_output = eolr * 8  # pairs / 8-hour shift

    meta = get_ie_header_meta(header_id)
    if not meta:
        return {'ok': False, 'error': f'header {header_id} not found'}

    SEGMENTS = ['cutting', 'stitching', 'assembly', 'stf']
    OFFLINE_ZONES = {
        'stitching': ['電腦針車', '折边'],
        'assembly':  ['水蜘蛛', '成型UV'],  # WS = overhead; 成型UV = UV machine op
    }
    # Segments with comprehensive actual_operators data: use strict actual (NULL=0)
    # cutting uses theory fallback because formula rows rarely have actual filled
    STRICT_ACTUAL_SEGS = {'assembly', 'stitching', 'stf'}

    result = {'ok': True, 'header_id': header_id, 'eolr': eolr,
               'target_output': target_output, 'meta': meta}
    total_ops = 0.0
    offline_list = []
    seg_results = {}

    for seg in SEGMENTS:
        cell = get_ie_cell_data(header_id, seg, eolr)
        ops_sum = 0.0
        tct_sum = 0.0
        offline_zones = OFFLINE_ZONES.get(seg, [])
        strict = seg in STRICT_ACTUAL_SEGS

        for zone_entry in cell.get('zones', []):
            zname = zone_entry['zone']
            if zname == '_summary':
                continue
            zone_ops = 0.0
            zone_tct = 0.0
            for row in zone_entry['rows']:
                actual = row.get('actual_operators')
                theory = row.get('theory_operators')
                if seg == 'cutting':
                    # cutting：theory 優先（公式基準），水蜘蛛(theory=None) fallback actual
                    t = theory if theory is not None else (actual or 0.0)
                elif actual is not None:
                    t = actual           # assembly/stitching/stf：有 actual 就用
                else:
                    t = 0.0              # 嚴格模式：actual=NULL → 不計入
                zone_ops += t
                zone_tct += row.get('standard_time') or 0.0

            if zname in offline_zones:
                pph_z = round(target_output / zone_ops / 8, 3) if zone_ops else None
                offline_list.append({
                    'name': f'{seg}/{zname}', 'eolr': eolr,
                    'operators': round(zone_ops, 4),
                    'tct': round(zone_tct, 2),
                    'pph': pph_z,
                })
            else:
                ops_sum += zone_ops
                tct_sum += zone_tct

        pph = round(target_output / ops_sum / 8, 3) if ops_sum else None
        seg_results[seg] = {
            'operators': round(ops_sum, 4),
            'pph': pph,
            'tct_sum': round(tct_sum, 2),
        }
        total_ops += ops_sum

    result['cutting']   = seg_results['cutting']
    result['stitching'] = seg_results['stitching']
    result['assembly']  = seg_results['assembly']
    result['stf']       = seg_results['stf']
    result['total']     = {
        'operators': round(total_ops, 4),
        'pph': round(target_output / total_ops / 8, 3) if total_ops else None,
    }
    result['offline'] = offline_list
    return result


def get_db_stats():
    conn = get_conn()
    try:
        return {
            'ok': True,
            'ds01_count':       conn.execute('SELECT COUNT(*) FROM ds01_sp').fetchone()[0],
            'ds02_count':       conn.execute('SELECT COUNT(*) FROM ds02_fob').fetchone()[0],
            'ds03_count':       conn.execute('SELECT COUNT(*) FROM ob_header').fetchone()[0],
            'lookup_count':     conn.execute('SELECT COUNT(*) FROM lookup_viet_zh').fetchone()[0],
            'change_log_count': conn.execute('SELECT COUNT(*) FROM change_log').fetchone()[0],
        }
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# 勾選分配系統 (Allocation Phase 1)
# ══════════════════════════════════════════════════════════════════════════════

# 後製工序 zone → 外移單位
ZONE_TO_UNIT = {
    'ATOM': '同材共裁自動化', 'LASER': '同材共裁自動化', 'EMMA': '同材共裁自動化',
    '裁斷機': '同材共裁自動化', 'YINGHUI': '同材共裁自動化',
    '電腦針車': '電腦針車折邊', '折边': '電腦針車折邊',
    '打粗': '打粗水洗照射', '照射': '打粗水洗照射',
}
# 後製工序 zone → IE 段（用於 CSA MP 扣除歸段）
ZONE_TO_SEGMENT = {
    'ATOM': 'cutting', 'LASER': 'cutting', 'EMMA': 'cutting',
    '裁斷機': 'cutting', 'YINGHUI': 'cutting',
    '電腦針車': 'stitching', '折边': 'stitching',
    '打粗': 'stf', '照射': 'stf',
}
ALLOCATION_UNITS = ['同材共裁自動化', '電腦針車折邊', '打粗水洗照射']
TARGET_ZONES = ['ATOM', 'Laser', 'EMMA', '裁斷機', 'YINGHUI', '電腦針車', '折边', '打粗', '照射']

# 各外移單位顯示的 zone（同材共裁含裁斷機但不可切換外移）
UNIT_DISPLAY_ZONES = {
    '同材共裁自動化': ['ATOM', 'Laser', 'EMMA', 'YINGHUI', '裁斷機'],
    '電腦針車折邊':   ['電腦針車', '折边'],
    '打粗水洗照射':   ['打粗', '照射'],
}
ALL_DISPLAY_ZONES = [z for zones in UNIT_DISPLAY_ZONES.values() for z in zones]
NON_TOGGLEABLE_ZONES = frozenset(['裁斷機'])  # 主裁斷：永遠留CSA，前端不顯示勾選框


def _zone_unit(zone):
    return ZONE_TO_UNIT.get((zone or '').upper(), ZONE_TO_UNIT.get(zone or ''))

def _zone_segment(zone):
    return ZONE_TO_SEGMENT.get((zone or '').upper(), ZONE_TO_SEGMENT.get(zone or ''))


def _ensure_alloc_tables(conn):
    """Create allocation tables on any DB (works even when init_db never ran here)."""
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS allocation_item (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        header_id INTEGER, art TEXT, lean TEXT, zone TEXT, seq INTEGER,
        process_name TEXT, part_name TEXT, post_process TEXT,
        theory_mp REAL, target_unit TEXT,
        is_checked INTEGER DEFAULT 0,
        checked_by TEXT, checked_at TEXT, confirmed_by TEXT, confirmed_at TEXT,
        month TEXT,
        UNIQUE(header_id, art, zone, seq, process_name, part_name, month)
    );
    CREATE TABLE IF NOT EXISTS allocation_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lean TEXT, art TEXT, segment TEXT, unit TEXT, total_mp REAL, month TEXT, confirmed INTEGER DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_alloc_item_lookup ON allocation_item(month, target_unit, lean, art);
    CREATE INDEX IF NOT EXISTS idx_alloc_item_header ON allocation_item(header_id);
    ''')
    conn.commit()


def _art_order_qty(conn, art):
    """Defensive order-qty lookup (DS-04 ob_articles.ob_qty if present, else DS-01 quantity, else 0)."""
    try:
        cols = [r[1] for r in conn.execute('PRAGMA table_info(ob_articles)').fetchall()]
        if 'ob_qty' in cols:
            r = conn.execute('SELECT SUM(ob_qty) FROM ob_articles WHERE art=?', (art,)).fetchone()
            if r and r[0]:
                return float(r[0])
    except Exception:
        pass
    try:
        r = conn.execute('SELECT SUM(quantity) FROM ds01_sp WHERE article_id=?', (art,)).fetchone()
        if r and r[0]:
            return float(r[0])
    except Exception:
        pass
    return 0.0


def prefill_allocation(header_id=None, month=None):
    """Step 2: scan ie_process target zones → seed allocation_item rows.
    header_id=None → prefill every ob_header. Idempotent (INSERT OR IGNORE on unique key).
    """
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        month = month or now_iso()[:7]
        if header_id:
            hdr_ids = [header_id]
        else:
            hdr_ids = [r[0] for r in conn.execute('SELECT id FROM ob_header').fetchall()]

        inserted = 0
        for hid in hdr_ids:
            meta = conn.execute('SELECT eolr FROM ob_header WHERE id=?', (hid,)).fetchone()
            if not meta:
                continue
            eolr = int(meta['eolr'] or 120)
            divisor = 3600.0 / eolr
            arts = [r['art'] for r in conn.execute(
                'SELECT art FROM ob_articles WHERE header_id=? ORDER BY id', (hid,)).fetchall()]
            if not arts:
                arts = [None]
            try:
                rows = conn.execute('''
                    SELECT zone, seq, process_name, part_name, standard_time
                    FROM ie_process
                    WHERE header_id=? AND (flag IS NULL OR flag != 'deleted')
                      AND {eff}
                      AND zone IN ({ph})
                    ORDER BY zone, seq, id
                '''.format(eff=_eff_stage_clause('ie_process'), ph=','.join('?' * len(TARGET_ZONES))),
                    [hid] + TARGET_ZONES).fetchall()
            except Exception:
                rows = []
            for art in arts:
                # look up lean from ds04_orders for this art
                lean_row = conn.execute(
                    'SELECT lean FROM ds04_orders WHERE art=? AND COALESCE(is_deleted,0)=0 LIMIT 1', (art,)).fetchone() if art else None
                lean_val = lean_row['lean'] if lean_row else ''
                for r in rows:
                    zone = r['zone']
                    st = r['standard_time']
                    theory_mp = round(st / divisor, 4) if st else None
                    # 裁斷機 stays in CSA (0); all other zones default to moved-out (1)
                    default_checked = 0 if zone in NON_TOGGLEABLE_ZONES else 1
                    cur = conn.execute('''
                        INSERT OR IGNORE INTO allocation_item
                        (header_id, art, lean, zone, seq, process_name, part_name,
                         post_process, theory_mp, target_unit, is_checked, month)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                    ''', (hid, art, lean_val, zone, r['seq'], r['process_name'], r['part_name'],
                          zone, theory_mp, _zone_unit(zone), default_checked, month))
                    inserted += cur.rowcount
        conn.commit()
        return {'ok': True, 'inserted': inserted, 'month': month, 'headers': len(hdr_ids)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_allocation_items(month=None, unit=None, lean=None, art=None, header_id=None):
    """Step 3: return allocation items grouped by ART for the 勾選 grid."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        month = month or now_iso()[:7]
        where = ['month=?']
        params = [month]
        if unit:      where.append('target_unit=?'); params.append(unit)
        if lean:      where.append('lean=?');         params.append(lean)
        if art:       where.append('art=?');          params.append(art)
        if header_id: where.append('header_id=?');    params.append(header_id)
        rows = conn.execute(
            'SELECT * FROM allocation_item WHERE ' + ' AND '.join(where) +
            ' ORDER BY art, zone, seq, id', params).fetchall()

        groups = {}
        for r in rows:
            d = dict(r)
            a = d['art'] or '(無ART)'
            g = groups.setdefault(a, {'art': a, 'lean': d['lean'], 'items': [],
                                      'allocated_mp': 0.0, 'csa_mp': 0.0, 'total_mp': 0.0})
            g['items'].append(d)
            mp = d['theory_mp'] or 0.0
            g['total_mp'] += mp
            if d['is_checked']:
                g['allocated_mp'] += mp
            else:
                g['csa_mp'] += mp
        out = []
        for g in groups.values():
            g['allocated_mp'] = round(g['allocated_mp'], 4)
            g['csa_mp'] = round(g['csa_mp'], 4)
            g['total_mp'] = round(g['total_mp'], 4)
            out.append(g)
        out.sort(key=lambda x: x['art'])
        return {'ok': True, 'month': month, 'unit': unit, 'groups': out,
                'item_count': len(rows)}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'groups': []}
    finally:
        conn.close()


def get_allocation_item(item_id):
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        r = conn.execute('SELECT * FROM allocation_item WHERE id=?', (item_id,)).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()


def set_allocation_check(item_id, is_checked, user='demo'):
    """Toggle 外移/留CSA for one allocation item."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        old = conn.execute('SELECT is_checked FROM allocation_item WHERE id=?', (item_id,)).fetchone()
        new_val = 1 if is_checked else 0
        conn.execute(
            'UPDATE allocation_item SET is_checked=?, checked_by=?, checked_at=? WHERE id=?',
            (new_val, user, now_iso(), item_id))
        conn.execute(
            'INSERT INTO alloc_edit_log (item_id,action,old_value,new_value,user_name,created_at) VALUES (?,?,?,?,?,?)',
            (item_id, 'check', str(old['is_checked'] if old else ''), str(new_val), user, now_iso()))
        conn.commit()
        return {'ok': True, 'id': item_id, 'is_checked': new_val}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_allocation_leans(month=None):
    """Return all assigned LEANs from ob_header (month-independent)."""
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT DISTINCT lean FROM ob_header WHERE lean IS NOT NULL ORDER BY lean'
        ).fetchall()
        return {'ok': True, 'leans': [r[0] for r in rows]}
    finally:
        conn.close()


def _seg_ie_mp(conn, header_id, segment, divisor):
    try:
        r = conn.execute(
            "SELECT SUM(standard_time) FROM ie_process WHERE header_id=? AND segment=? "
            "AND (flag IS NULL OR flag != 'deleted') AND " + _eff_stage_clause('ie_process'),
            (header_id, segment)).fetchone()
        s = r[0] if r else None
        return round((s or 0.0) / divisor, 4) if s else 0.0
    except Exception:
        return 0.0


def get_csa_mp(lean=None, art=None, eolr=120, month=None):
    """Step 4: per-segment IE / allocated / CSA MP for one ART."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        eolr = int(eolr)
        divisor = 3600.0 / eolr
        month = month or now_iso()[:7]
        hdr = conn.execute(
            'SELECT header_id FROM ob_articles WHERE art=? ORDER BY header_id DESC LIMIT 1',
            (art,)).fetchone()
        header_id = hdr['header_id'] if hdr else None

        SEGS = ['cutting', 'stitching', 'assembly', 'stf']
        out = {'ok': True, 'art': art, 'lean': lean, 'eolr': eolr, 'header_id': header_id}
        for seg in SEGS:
            ie_mp = _seg_ie_mp(conn, header_id, seg, divisor) if header_id else 0.0
            seg_zones = [z for z in TARGET_ZONES if _zone_segment(z) == seg]
            allocated = 0.0
            if seg_zones:
                ar = conn.execute(
                    'SELECT SUM(theory_mp) FROM allocation_item '
                    'WHERE art=? AND is_checked=1 AND month=? AND zone IN ({})'.format(
                        ','.join('?' * len(seg_zones))),
                    [art, month] + seg_zones).fetchone()
                allocated = round((ar[0] or 0.0), 4) if ar and ar[0] else 0.0
            out[f'{seg}_ie_mp'] = ie_mp
            out[f'{seg}_allocated_mp'] = allocated
            out[f'{seg}_csa_mp'] = round(ie_mp - allocated, 4)
        return out
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_allocation_parts(month=None, unit=None, lean=None):
    """LEAN → model×ART → parts, filtered by unit display zones (excluding 裁斷機 from toggle)."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        month = month or now_iso()[:7]

        # Zone whitelist: filter by unit's display zones, not target_unit
        display_zones = UNIT_DISPLAY_ZONES.get(unit, ALL_DISPLAY_ZONES) if unit else ALL_DISPLAY_ZONES
        zone_ph = ','.join('?' * len(display_zones))

        where_clauses = ['ai.month=?', f'ai.zone IN ({zone_ph})']
        params_after = [month] + list(display_zones)
        if lean:
            where_clauses.append('ai.lean=?')
            params_after.append(lean)

        # CTE dedup: same art×zone×seq×process_name can appear in multiple
        # ob_header rows (different EOLRs).  Pick MIN(id) to get one row each.
        cte_where = f'ai.month=? AND ai.zone IN ({zone_ph})'
        if lean:
            cte_where += ' AND ai.lean=?'

        eff_ip2 = _eff_stage_clause('ip2')  # 版本控制: 有效版本過濾

        rows = conn.execute(f'''
            WITH ai_dedup AS (
                SELECT MIN(ai.id) AS id
                FROM allocation_item ai
                WHERE {cte_where}
                GROUP BY ai.lean, ai.art, ai.zone, ai.seq, ai.process_name, ai.month
            )
            SELECT
                ai.id, ai.art, ai.lean, ai.zone, ai.seq,
                ai.process_name, ai.part_name,
                ai.theory_mp, ai.is_checked, ai.target_unit,
                ip.cut_per_hour, ip.layers_per_cut, ip.qty_per_pair, ip.standard_time,
                h.model_name, h.eolr,
                COALESCE(s.qty, 0) AS order_qty
            FROM ai_dedup d
            JOIN allocation_item ai ON ai.id = d.id
            LEFT JOIN (
                SELECT oa.art, ip2.zone, ip2.seq,
                       MAX(ip2.cut_per_hour)   AS cut_per_hour,
                       MAX(ip2.layers_per_cut) AS layers_per_cut,
                       MAX(ip2.qty_per_pair)   AS qty_per_pair,
                       MAX(ip2.standard_time)  AS standard_time
                FROM ie_process ip2
                JOIN ob_articles oa ON oa.header_id = ip2.header_id
                WHERE (ip2.flag IS NULL OR ip2.flag != 'deleted') AND {eff_ip2}
                GROUP BY oa.art, ip2.zone, ip2.seq
            ) ip ON ip.art=ai.art AND ip.zone=ai.zone AND ip.seq=ai.seq
            LEFT JOIN ob_header h ON h.id=ai.header_id
            LEFT JOIN (
                SELECT art, SUM(qty) AS qty
                FROM ds04_orders WHERE COALESCE(is_deleted,0)=0 GROUP BY art
            ) s ON s.art=ai.art
            ORDER BY
                CASE WHEN ai.lean IS NULL THEN 1 ELSE 0 END,
                ai.lean, h.model_name, ai.art,
                CASE ai.zone WHEN '裁斷機' THEN 1 ELSE 0 END,
                ai.zone, ai.seq, ai.id
        ''', params_after).fetchall()

        lean_groups = {}
        lean_order = []

        for r in rows:
            d = dict(r)
            lk = d.get('lean') or None
            label = lk if lk else '—'
            if label not in lean_groups:
                lean_groups[label] = {
                    'lean': lk,
                    'allocated_mp': 0.0, 'csa_mp': 0.0, 'ie_mp': 0.0,
                    '_models': {}
                }
                lean_order.append(label)

            lg = lean_groups[label]
            model_raw = d.get('model_name') or ''
            model = model_raw.split('Target Output')[0].strip()
            art = d.get('art') or '(無ART)'
            mk = f'{art}||{model}'

            if mk not in lg['_models']:
                lg['_models'][mk] = {
                    'model_name': model,
                    'art': art,
                    'eolr': d.get('eolr') or 120,
                    'order_qty': float(d.get('order_qty') or 0),
                    'allocated_mp': 0.0, 'csa_mp': 0.0, 'ie_mp': 0.0,
                    'items': []
                }

            mg = lg['_models'][mk]
            raw_mp = d.get('theory_mp')          # None when CT is NULL
            mp = float(raw_mp or 0.0)            # 0.0 for totals arithmetic
            zone = d.get('zone') or ''
            is_csa_locked = zone in NON_TOGGLEABLE_ZONES
            is_checked = 0 if is_csa_locked else (1 if d.get('is_checked') else 0)
            ct = d.get('standard_time')
            qty_pp = d.get('qty_per_pair')
            order_qty = float(d.get('order_qty') or 0)

            mg['ie_mp'] += mp
            lg['ie_mp'] += mp
            if is_checked and not is_csa_locked:
                mg['allocated_mp'] += mp
                lg['allocated_mp'] += mp
            else:
                mg['csa_mp'] += mp
                lg['csa_mp'] += mp

            mg['items'].append({
                'id': d['id'],
                'seq': d['seq'],
                'zone': zone,
                'part_name': d.get('process_name') or d.get('part_name') or '',
                'cut_per_hour': d.get('cut_per_hour'),
                'layers': d.get('layers_per_cut'),
                'qty_per_pair': qty_pp,
                'total_pieces': round(order_qty * float(qty_pp)) if qty_pp and order_qty else None,
                'ct_sec': round(float(ct), 3) if ct else None,
                'output': round(3600.0 / float(ct), 1) if ct else None,
                'theory_mp': round(raw_mp, 4) if raw_mp is not None else None,
                'is_checked': is_checked,
                'is_csa_locked': is_csa_locked,
                'target_unit': d.get('target_unit'),
            })

        out = []
        for lk in lean_order:
            lg = lean_groups[lk]
            models_list = []
            for mg in lg.pop('_models').values():
                mg['allocated_mp'] = round(mg['allocated_mp'], 4)
                mg['csa_mp'] = round(mg['csa_mp'], 4)
                mg['ie_mp'] = round(mg['ie_mp'], 4)
                models_list.append(mg)
            lg['models'] = models_list
            lg['allocated_mp'] = round(lg['allocated_mp'], 4)
            lg['csa_mp'] = round(lg['csa_mp'], 4)
            lg['ie_mp'] = round(lg['ie_mp'], 4)
            out.append(lg)

        return {'ok': True, 'month': month, 'unit': unit, 'leans': out}
    except Exception as e:
        import traceback
        return {'ok': False, 'error': str(e), 'trace': traceback.format_exc(), 'leans': []}
    finally:
        conn.close()


def get_allocation_export_rows(unit, month=None):
    """Step 5: rows for a unit's reference xlsx (checked items only)."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        month = month or now_iso()[:7]
        rows = conn.execute('''
            SELECT ai.lean, ai.art, ai.part_name, ai.zone AS process, ai.theory_mp,
                   ip.standard_time AS tct
            FROM allocation_item ai
            LEFT JOIN ie_process ip
              ON ip.header_id=ai.header_id AND ip.zone=ai.zone AND ip.seq=ai.seq
             AND ip.process_name=ai.process_name AND ''' + _eff_stage_clause('ip') + '''
            WHERE ai.target_unit=? AND ai.month=? AND ai.is_checked=1
            ORDER BY ai.lean, ai.art, ai.zone, ai.seq
        ''', (unit, month)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d['order_qty'] = _art_order_qty(conn, d['art']) if d['art'] else 0.0
            tct = d.get('tct') or 0.0
            # 打粗水洗：需求人力 = 訂單 ÷ (3600 ÷ TCT) ÷ 222
            d['headcount'] = round(d['order_qty'] / (3600.0 / tct) / 222.0, 4) if tct else None
            out.append(d)
        return {'ok': True, 'unit': unit, 'month': month, 'rows': out}
    finally:
        conn.close()


# ── DS-04 Production Schedule Orders ────────────────────────────────────────

DS04_DEPT_ORDER = ['1部','2部','3部','5部','6部','7部','8部','9部','10部','11部','11部 (2)','12部']
DS04_LEAN_ORDER = [
    '1A','1B','1C','2A','2B','2C','3A','3B','3C','4A','4B','4C',
    '5A','5B','5C','6A','6B','6C','7A','7B','7C','8A','8B','8C',
    '9A','9B','9C','10A','10B','10C','11A1','11A2','11B1','11B2','11C',
]

def _ds04_dept_key(d): return DS04_DEPT_ORDER.index(d) if d in DS04_DEPT_ORDER else 999
def _ds04_lean_key(l): return DS04_LEAN_ORDER.index(l) if l in DS04_LEAN_ORDER else 999

def _ensure_ds04_ext(conn):
    """Add estimated_completion column if it doesn't exist yet."""
    existing = {r[1] for r in conn.execute('PRAGMA table_info(ds04_orders)').fetchall()}
    if 'estimated_completion' not in existing:
        conn.execute("ALTER TABLE ds04_orders ADD COLUMN estimated_completion TEXT DEFAULT ''")
        conn.commit()

def ds04_import(records):
    """Bulk-replace all ds04_orders rows."""
    conn = get_conn()
    try:
        conn.execute('DELETE FROM ds04_orders')
        ts = now_iso()
        conn.executemany(
            '''INSERT INTO ds04_orders
               (dept, lean, model_name, art, order_no, qty, delivery_date, is_outsource_upper, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)''',
            [(r['部門'], r['LEAN'], r['鞋型名稱'], r['ART'], r['訂單號'],
              int(r['數量'] or 0), r['交期'], 1 if r['外包鞋面'] == 'Y' else 0, ts)
             for r in records]
        )
        conn.commit()
        return {'ok': True, 'count': len(records)}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

def ds04_get_orders(dept=None, lean=None, outsource=None):
    """Query ds04_orders with optional filters, sorted by spec order."""
    conn = get_conn()
    try:
        _ensure_ds04_ext(conn)
        where, params = [], []
        if dept:
            where.append('dept=?'); params.append(dept)
        if lean:
            where.append('lean=?'); params.append(lean)
        if outsource == 'Y':
            where.append('is_outsource_upper=1')
        elif outsource == 'N':
            where.append('is_outsource_upper=0')
        where.append('COALESCE(is_deleted,0)=0')
        sql = 'SELECT * FROM ds04_orders'
        if where:
            sql += ' WHERE ' + ' AND '.join(where)
        sql += ' ORDER BY dept, lean, model_name, id'
        rows = conn.execute(sql, params).fetchall()
        result = [dict(r) for r in rows]
        result.sort(key=lambda r: (_ds04_dept_key(r.get('dept','')),
                                   _ds04_lean_key(r.get('lean','')),
                                   r.get('model_name',''), r.get('id',0)))
        return {'ok': True, 'rows': result}
    finally:
        conn.close()

def ds04_get_filters():
    """Return distinct dept and lean values sorted by spec order."""
    conn = get_conn()
    try:
        raw_depts = [r[0] for r in conn.execute(
            'SELECT DISTINCT dept FROM ds04_orders WHERE COALESCE(is_deleted,0)=0'
        ).fetchall()]
        raw_leans = [r[0] for r in conn.execute(
            'SELECT DISTINCT lean FROM ds04_orders WHERE COALESCE(is_deleted,0)=0'
        ).fetchall()]
        depts = sorted(raw_depts, key=_ds04_dept_key)
        leans = sorted(raw_leans, key=_ds04_lean_key)
        return {'ok': True, 'depts': depts, 'leans': leans}
    finally:
        conn.close()

def ds04_get_lock_status(month):
    conn = get_conn()
    try:
        r = conn.execute('SELECT month, locked_at, locked_by FROM ds04_lock WHERE month=?', (month,)).fetchone()
        if r:
            return {'ok': True, 'locked': True, 'month': r['month'],
                    'locked_at': r['locked_at'], 'locked_by': r['locked_by']}
        return {'ok': True, 'locked': False, 'month': month}
    finally:
        conn.close()

def ds04_lock_month(month, locked_by=''):
    conn = get_conn()
    try:
        ts = now_iso()
        conn.execute(
            '''INSERT INTO ds04_lock (month, locked_at, locked_by)
               VALUES (?,?,?)
               ON CONFLICT(month) DO UPDATE SET locked_at=excluded.locked_at, locked_by=excluded.locked_by''',
            (month, ts, locked_by)
        )
        conn.commit()
        return {'ok': True, 'month': month, 'locked_at': ts}
    except Exception as e:
        conn.rollback(); return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

def ds04_unlock_month(month):
    conn = get_conn()
    try:
        conn.execute('DELETE FROM ds04_lock WHERE month=?', (month,))
        conn.commit()
        return {'ok': True, 'month': month}
    except Exception as e:
        conn.rollback(); return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

def _check_ds04_lock(month):
    """Return error dict if month is locked, else None."""
    if not month:
        return None
    status = ds04_get_lock_status(month)
    if status.get('locked'):
        return {'ok': False, 'error': f'本月 {month} 已確認鎖定，無法修改。如需解鎖請聯繫管理員。'}
    return None

def ds04_add_order(data):
    lock_err = _check_ds04_lock(data.get('month', ''))
    if lock_err:
        return lock_err
    conn = get_conn()
    try:
        _ensure_ds04_ext(conn)
        ts = now_iso()
        cur = conn.execute(
            '''INSERT INTO ds04_orders
               (dept, lean, model_name, art, order_no, qty, delivery_date,
                is_outsource_upper, estimated_completion, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (data.get('dept',''), data.get('lean',''), data.get('model_name',''),
             data.get('art',''), data.get('order_no',''), int(data.get('qty',0)),
             data.get('delivery_date',''), 1 if data.get('is_outsource_upper') else 0,
             data.get('estimated_completion',''), ts)
        )
        conn.execute(
            'INSERT INTO ds04_edit_log (order_id,action,user_name,new_value,created_at) VALUES (?,?,?,?,?)',
            (cur.lastrowid, 'add', data.get('user',''), str(data), ts)
        )
        conn.commit()
        return {'ok': True, 'id': cur.lastrowid}
    except Exception as e:
        conn.rollback(); return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

def ds04_update_order(order_id, data):
    lock_err = _check_ds04_lock(data.get('month', ''))
    if lock_err:
        return lock_err
    conn = get_conn()
    try:
        ts = now_iso()
        old = conn.execute('SELECT * FROM ds04_orders WHERE id=?', (order_id,)).fetchone()
        if not old:
            return {'ok': False, 'error': 'not found'}
        old_ec = old['estimated_completion'] if 'estimated_completion' in old.keys() else ''
        conn.execute(
            '''UPDATE ds04_orders SET dept=?,lean=?,model_name=?,art=?,order_no=?,
               qty=?,delivery_date=?,is_outsource_upper=?,estimated_completion=? WHERE id=?''',
            (data.get('dept', old['dept']), data.get('lean', old['lean']),
             data.get('model_name', old['model_name']), data.get('art', old['art']),
             data.get('order_no', old['order_no']), int(data.get('qty', old['qty'])),
             data.get('delivery_date', old['delivery_date']),
             1 if data.get('is_outsource_upper') else 0,
             data.get('estimated_completion', old_ec), order_id)
        )
        conn.execute(
            'INSERT INTO ds04_edit_log (order_id,action,old_value,new_value,user_name,created_at) VALUES (?,?,?,?,?,?)',
            (order_id, 'update', str(dict(old)), str(data), data.get('user',''), ts)
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        conn.rollback(); return {'ok': False, 'error': str(e)}
    finally:
        conn.close()

def ds04_delete_order(order_id, month=''):
    lock_err = _check_ds04_lock(month)
    if lock_err:
        return lock_err
    conn = get_conn()
    try:
        ts = now_iso()
        old = conn.execute('SELECT * FROM ds04_orders WHERE id=?', (order_id,)).fetchone()
        if not old:
            return {'ok': False, 'error': 'not found'}
        conn.execute('UPDATE ds04_orders SET is_deleted=1 WHERE id=?', (order_id,))
        conn.execute(
            'INSERT INTO ds04_edit_log (order_id,action,old_value,user_name,created_at) VALUES (?,?,?,?,?)',
            (order_id, 'soft_delete', str(dict(old)), '', ts)
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        conn.rollback(); return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


# ── EOLR Settings ─────────────────────────────────────────────────────────────

def get_eolr_settings(month):
    """Return all LEAN eolr settings for given month. Missing leans inherit 120."""
    conn = get_conn()
    try:
        # All leans from ds04_orders
        all_leans = [r[0] for r in conn.execute(
            'SELECT DISTINCT lean FROM ds04_orders WHERE COALESCE(is_deleted,0)=0 ORDER BY lean'
        ).fetchall()]
        # Existing settings for this month
        rows = conn.execute(
            'SELECT lean, eolr, updated_by, updated_at FROM lean_eolr_settings WHERE month=?', (month,)
        ).fetchall()
        setting_map = {r['lean']: dict(r) for r in rows}
        result = []
        for lean in all_leans:
            s = setting_map.get(lean)
            result.append({
                'lean': lean,
                'eolr': s['eolr'] if s else 120,
                'updated_by': s['updated_by'] if s else '',
                'updated_at': s['updated_at'] if s else '',
                'is_default': s is None,
            })
        return {'ok': True, 'month': month, 'settings': result}
    finally:
        conn.close()

def set_eolr_setting(lean, month, eolr, updated_by=''):
    conn = get_conn()
    try:
        ts = now_iso()
        conn.execute(
            '''INSERT INTO lean_eolr_settings (lean, month, eolr, updated_by, updated_at)
               VALUES (?,?,?,?,?)
               ON CONFLICT(lean, month) DO UPDATE SET eolr=excluded.eolr,
               updated_by=excluded.updated_by, updated_at=excluded.updated_at''',
            (lean, month, int(eolr), updated_by, ts)
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        conn.rollback(); return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


# ── 廠務編制表 計算 ────────────────────────────────────────────────────────────

CUTTING_ZONES   = {'裁斷機', 'ATOM', 'Laser', 'EMMA', 'YINGHUI'}
AUTO_ZONES      = {'ATOM', 'Laser', 'EMMA', 'YINGHUI'}   # can be checked out
STITCH_ZONES    = {'電腦針車', '折边'}
ASSEMBLY_ZONES  = {'成型主區', '成型UV', '水蜘蛛'}
STF_ZONES       = {'打粗', '照射'}

def get_bianche_data(month='2026-06'):
    conn = get_conn()
    try:
        # 1. EOLR map per LEAN for this month (default 120)
        eolr_rows = conn.execute(
            'SELECT lean, eolr FROM lean_eolr_settings WHERE month=?', (month,)
        ).fetchall()
        eolr_map = {r['lean']: r['eolr'] for r in eolr_rows}

        # 2. DS-04 orders grouped by lean + model + art
        order_rows = conn.execute(
            '''SELECT lean, model_name, art, SUM(qty) AS qty, MAX(is_outsource_upper) AS is_outsource
               FROM ds04_orders WHERE COALESCE(is_deleted,0)=0
               GROUP BY lean, model_name, art
               ORDER BY lean, model_name, art'''
        ).fetchall()

        # 3. IE process data: art → zone → [std_time]
        ie_rows = conn.execute(
            '''SELECT oa.art, ip.zone, ip.standard_time
               FROM ie_process ip
               JOIN ob_articles oa ON oa.header_id = ip.header_id
               WHERE (ip.flag IS NULL OR ip.flag != 'deleted') AND ip.standard_time > 0
                 AND ''' + _eff_stage_clause('ip') + '''
               ORDER BY oa.art, ip.zone''',
        ).fetchall()
        ie_data = {}   # art → zone → [std_time]
        for r in ie_rows:
            a = r['art']
            z = r['zone']
            if a not in ie_data:
                ie_data[a] = {}
            if z not in ie_data[a]:
                ie_data[a][z] = []
            ie_data[a][z].append(r['standard_time'] or 0)

        # 4. Checked (moved-out) allocation_item: art → zone → moved_mp
        chk_rows = conn.execute(
            '''SELECT art, zone, SUM(theory_mp) AS moved
               FROM allocation_item
               WHERE is_checked=1 AND month=?
               GROUP BY art, zone''',
            (month,)
        ).fetchall()
        moved_data = {}   # art → zone → moved_mp
        for r in chk_rows:
            a = r['art']
            if a not in moved_data:
                moved_data[a] = {}
            moved_data[a][r['zone']] = r['moved'] or 0

        # 5. Manual bianche fields (manager_mp, headcount)
        manual_rows = conn.execute(
            'SELECT lean, manager_mp, headcount FROM bianche_manual WHERE month=?', (month,)
        ).fetchall()
        manual_map = {r['lean']: {'manager_mp': r['manager_mp'], 'headcount': r['headcount']} for r in manual_rows}

        # 6. Compute per order
        def zone_mp(art, zones, eolr):
            d = ie_data.get(art, {})
            return round(sum(sum(d.get(z, [])) for z in zones) * eolr / 3600.0, 4)

        def zone_moved(art, zones):
            d = moved_data.get(art, {})
            return round(sum(d.get(z, 0) for z in zones), 4)

        def zone_tct(art, zones):
            d = ie_data.get(art, {})
            return sum(sum(d.get(z, [])) for z in zones)

        results = []
        for ord_row in order_rows:
            lean   = ord_row['lean']
            art    = ord_row['art']
            qty    = ord_row['qty'] or 0
            eolr   = eolr_map.get(lean, 120)
            is_out = ord_row['is_outsource'] or 0
            has_ie = art in ie_data

            if has_ie:
                cut_ie   = zone_mp(art, CUTTING_ZONES, eolr)
                cut_mv   = zone_moved(art, AUTO_ZONES)
                stch_ie  = zone_mp(art, STITCH_ZONES, eolr)
                stch_mv  = zone_moved(art, STITCH_ZONES)
                asm_ie   = zone_mp(art, ASSEMBLY_ZONES, eolr)
                asm_mv   = zone_moved(art, ASSEMBLY_ZONES)
                tct      = zone_tct(art, STF_ZONES)
                stf_mp   = round(qty * tct / 3600.0 / 222.0, 4) if tct else 0

                if is_out:
                    cut_act  = 0.0
                    stch_act = 0.0
                else:
                    cut_act  = round(cut_ie - cut_mv, 4)
                    stch_act = round(stch_ie - stch_mv, 4)
                asm_act = round(asm_ie - asm_mv, 4)
            else:
                cut_ie = stch_ie = asm_ie = 0.0
                cut_mv = stch_mv = asm_mv = 0.0
                cut_act = stch_act = asm_act = stf_mp = None

            results.append({
                'lean': lean,
                'model_name': ord_row['model_name'],
                'art': art,
                'qty': qty,
                'is_outsource': is_out,
                'has_ie': has_ie,
                'eolr': eolr,
                # IE (before allocation)
                'cutting_ie_mp':   cut_ie,
                'stitching_ie_mp': stch_ie,
                'assembly_ie_mp':  asm_ie,
                # Moved out
                'cutting_moved':   cut_mv,
                'stitching_moved': stch_mv,
                'assembly_moved':  asm_mv,
                # Actual (None = no IE data)
                'cutting_mp':   cut_act,
                'stitching_mp': stch_act,
                'assembly_mp':  asm_act,
                'stf_mp':       stf_mp,
                'total_mp':     round((cut_act or 0) + (stch_act or 0) + (asm_act or 0) + (stf_mp or 0), 4),
                # Manual
                'manager_mp':  manual_map.get(lean, {}).get('manager_mp', 0),
                'headcount':   manual_map.get(lean, {}).get('headcount', 0),
            })

        def _s(r, k): return r[k] if r[k] is not None else 0
        totals = {
            'cutting':   round(sum(_s(r,'cutting_mp')   for r in results), 2),
            'stitching': round(sum(_s(r,'stitching_mp') for r in results), 2),
            'assembly':  round(sum(_s(r,'assembly_mp')  for r in results), 2),
            'stf':       round(sum(_s(r,'stf_mp')       for r in results), 2),
        }
        totals['grand'] = round(sum(totals.values()), 2)

        return {'ok': True, 'month': month, 'rows': results, 'totals': totals}
    finally:
        conn.close()

def set_bianche_manual(lean, month, manager_mp, headcount, updated_by=''):
    conn = get_conn()
    try:
        ts = now_iso()
        old = conn.execute('SELECT manager_mp, headcount FROM bianche_manual WHERE lean=? AND month=?', (lean, month)).fetchone()
        conn.execute(
            '''INSERT INTO bianche_manual (lean, month, manager_mp, headcount, updated_by, updated_at)
               VALUES (?,?,?,?,?,?)
               ON CONFLICT(lean, month) DO UPDATE SET manager_mp=excluded.manager_mp,
               headcount=excluded.headcount, updated_by=excluded.updated_by, updated_at=excluded.updated_at''',
            (lean, month, float(manager_mp or 0), float(headcount or 0), updated_by, ts)
        )
        conn.execute(
            'INSERT INTO bianche_edit_log (target_type,target_key,old_value,new_value,user_name,created_at) VALUES (?,?,?,?,?,?)',
            ('manual', f'{lean}:{month}', str(dict(old)) if old else '', f'manager_mp={manager_mp},hc={headcount}', updated_by, ts))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        conn.rollback(); return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# 廠務編制 CSA (model-level) + OCS/RB/QC dept headcount + Allocation lock
# ══════════════════════════════════════════════════════════════════════════════

OCS_DAODI_GROUPS = ['贴1','贴2','贴3','贴5','贴6','贴7','贴8','贴9',
                    '贴10','贴11','贴12','贴20','贴21','贴22','贴23']

RB_GROUPS = [
    '預備組','生管','倉庫生管','出半成品','模具',
    '密練A','密練B','混A','混B','混C',
    '熱A','熱B','熱C','整理A','整理B','整理C','技術組','硫化組',
]

QC_GROUPS_MAIN = [
    'OCPT','實驗室','課部助理','協理助理','QA','樣品室QC','開發QA',
    '檢驗真皮組','檢驗副料組','收料組','底料檢驗組','EVC檢驗',
    'T2中底廠商','T3外包底料','印刷高周波QC','外包QC部件','QCRB','外包RBQC',
    '自動化中心','電腦針車QC','QC貼底課','外包QC貼底',
    'QC1','QC2','QC3','QC5','QC6','QC7','QC8','QC9','QC10','QC11','QC12','QC YH',
    'QC YH（針車鞋面）','美城QC','驗貨員','包裝員','驗貨員（專員）',
    '美興QC','JIATAI','美君','品包1組','品包2組','品包3組','掃描組','貼外箱標組','QC入庫和領料樣品室',
]

DEPT_GROUPS = {
    'OCS': [
        ('大底課', OCS_DAODI_GROUPS),
        ('組底配套', ['組底倉庫','整理組','外包組','打粗組','UV水洗組','配套組']),
        ('自動化', ['同材共裁1,2組','自動裁斷1,2組','鞋墊手工組','保全技術組','倉庫']),
        ('電腦針車', ['折邊','電腦針車','倉庫','保全技術組']),
        ('印刷', ['高周波','印刷組','配套組','網板組','印刷房','印刷開發','加工組']),
        ('設備工程', ['保全','西工']),
        ('副總室', ['副總室']),
        ('現場技轉/KTHT', ['現場技轉/KTHT']),
    ],
    'RB': [('RB', RB_GROUPS)],
    'QC': [
        ('QC', QC_GROUPS_MAIN),
        ('設備工程', ['保全','西工','副總室','現場技轉']),
    ],
}


def _ensure_bianche_ext(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS bianche_model_manual (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lean TEXT NOT NULL, model_name TEXT NOT NULL, month TEXT NOT NULL,
        manager_mp REAL DEFAULT 0, headcount REAL DEFAULT 0,
        updated_by TEXT DEFAULT '', updated_at TEXT NOT NULL,
        UNIQUE(lean, model_name, month)
    );
    CREATE TABLE IF NOT EXISTS bianche_dept_hc (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept TEXT NOT NULL, group_name TEXT NOT NULL,
        shoe_detail TEXT DEFAULT '', month TEXT NOT NULL,
        headcount REAL DEFAULT 0, updated_by TEXT DEFAULT '', updated_at TEXT NOT NULL,
        UNIQUE(dept, group_name, month)
    );
    CREATE TABLE IF NOT EXISTS bianche_lean_hc (
        lean TEXT NOT NULL, month TEXT NOT NULL,
        headcount REAL DEFAULT 0, updated_at TEXT NOT NULL,
        PRIMARY KEY(lean, month)
    );
    CREATE TABLE IF NOT EXISTS alloc_lock (
        month TEXT PRIMARY KEY, locked_at TEXT NOT NULL, locked_by TEXT DEFAULT ''
    );
    ''')
    conn.commit()


def get_bianche_lean_hcs(month):
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        rows = conn.execute('SELECT lean, headcount FROM bianche_lean_hc WHERE month=?', (month,)).fetchall()
        return {'ok': True, 'lean_hc': {r['lean']: r['headcount'] for r in rows}}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def set_bianche_lean_hc(lean, month, headcount):
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        old = conn.execute('SELECT headcount FROM bianche_lean_hc WHERE lean=? AND month=?', (lean, month)).fetchone()
        ts_now = now_iso()
        conn.execute(
            'INSERT INTO bianche_lean_hc (lean,month,headcount,updated_at) VALUES(?,?,?,?) '
            'ON CONFLICT(lean,month) DO UPDATE SET headcount=excluded.headcount, updated_at=excluded.updated_at',
            (lean, month, float(headcount or 0), ts_now)
        )
        conn.execute(
            'INSERT INTO bianche_edit_log (target_type,target_key,old_value,new_value,user_name,created_at) VALUES (?,?,?,?,?,?)',
            ('lean_hc', f'{lean}:{month}', str(old['headcount'] if old else ''), str(headcount), '', ts_now))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        conn.rollback(); return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_bianche_csa_data(month='2026-06'):
    """CSA tab: per LEAN per model_name, multiple ARTs merged."""
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        eolr_map = {r['lean']: r['eolr'] for r in conn.execute(
            'SELECT lean, eolr FROM lean_eolr_settings WHERE month=?', (month,)).fetchall()}

        # DS-04 orders grouped by lean+model
        order_rows = conn.execute(
            '''SELECT lean, model_name,
                      GROUP_CONCAT(DISTINCT art) AS arts,
                      SUM(qty) AS qty,
                      MAX(is_outsource_upper) AS is_outsource
               FROM ds04_orders WHERE COALESCE(is_deleted,0)=0
               GROUP BY lean, model_name ORDER BY lean, model_name'''
        ).fetchall()

        # IE data per art
        ie_data = {}
        for r in conn.execute(
            '''SELECT oa.art, ip.zone, ip.standard_time FROM ie_process ip
               JOIN ob_articles oa ON oa.header_id=ip.header_id
               WHERE (ip.flag IS NULL OR ip.flag!='deleted') AND ip.standard_time>0
                 AND ''' + _eff_stage_clause('ip') + '''  '''):
            a, z = r['art'], r['zone']
            ie_data.setdefault(a, {}).setdefault(z, []).append(r['standard_time'] or 0)

        # Moved out per art+zone
        moved_data = {}
        for r in conn.execute(
            '''SELECT art, zone, SUM(theory_mp) AS moved FROM allocation_item
               WHERE is_checked=1 AND month=? GROUP BY art, zone''', (month,)):
            moved_data.setdefault(r['art'], {})[r['zone']] = r['moved'] or 0

        # Manual per-model
        manual_map = {}
        for r in conn.execute(
            'SELECT lean, model_name, manager_mp, headcount FROM bianche_model_manual WHERE month=?', (month,)):
            manual_map[(r['lean'], r['model_name'])] = {'manager_mp': r['manager_mp'] or 0, 'headcount': r['headcount'] or 0}

        results = []
        for row in order_rows:
            lean = row['lean']
            model = row['model_name']
            arts = [a.strip() for a in (row['arts'] or '').split(',') if a.strip()]
            qty = row['qty'] or 0
            is_out = row['is_outsource'] or 0
            eolr = eolr_map.get(lean, 120)
            first_art = next((a for a in arts if a in ie_data), None)
            has_ie = first_art is not None

            if has_ie:
                d = ie_data[first_art]
                def _ie(zones): return round(sum(sum(d.get(z, [])) for z in zones) * eolr / 3600.0, 4)
                def _mv(zones): return round(sum(moved_data.get(a, {}).get(z, 0) for a in arts for z in zones), 4)
                cut_ie  = _ie(CUTTING_ZONES);  cut_mv  = _mv(AUTO_ZONES)
                stch_ie = _ie(STITCH_ZONES);   stch_mv = _mv(STITCH_ZONES)
                asm_ie  = _ie(ASSEMBLY_ZONES); asm_mv  = _mv(ASSEMBLY_ZONES)
                cut_act  = 0.0 if is_out else round(cut_ie  - cut_mv,  4)
                stch_act = 0.0 if is_out else round(stch_ie - stch_mv, 4)
                asm_act  = round(asm_ie - asm_mv, 4)
            else:
                cut_ie = stch_ie = asm_ie = None
                cut_mv = stch_mv = asm_mv = None
                cut_act = stch_act = asm_act = None

            m = manual_map.get((lean, model), {})
            results.append({
                'lean': lean, 'model_name': model, 'arts': row['arts'] or '',
                'qty': qty, 'is_outsource': is_out, 'has_ie': has_ie, 'eolr': eolr,
                'cutting_ie_mp': cut_ie, 'cutting_moved': cut_mv, 'cutting_mp': cut_act,
                'stitching_ie_mp': stch_ie, 'stitching_moved': stch_mv, 'stitching_mp': stch_act,
                'assembly_ie_mp': asm_ie, 'assembly_moved': asm_mv, 'assembly_mp': asm_act,
                'manager_mp': m.get('manager_mp', 0),
            })
        lean_hc = {r['lean']: r['headcount'] for r in conn.execute(
            'SELECT lean, headcount FROM bianche_lean_hc WHERE month=?', (month,)).fetchall()}
        return {'ok': True, 'month': month, 'rows': results, 'lean_hc': lean_hc}
    except Exception as e:
        import traceback; return {'ok': False, 'error': str(e), 'trace': traceback.format_exc()}
    finally:
        conn.close()


def set_bianche_model_manual(lean, model_name, month, manager_mp=None, headcount=None, updated_by=''):
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        ex = conn.execute(
            'SELECT manager_mp, headcount FROM bianche_model_manual WHERE lean=? AND model_name=? AND month=?',
            (lean, model_name, month)).fetchone()
        mgr = float(manager_mp) if manager_mp is not None else (float(ex['manager_mp']) if ex else 0)
        hc  = float(headcount)  if headcount  is not None else (float(ex['headcount'])  if ex else 0)
        ts_now = now_iso()
        conn.execute(
            '''INSERT INTO bianche_model_manual (lean,model_name,month,manager_mp,headcount,updated_by,updated_at)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(lean,model_name,month) DO UPDATE SET
               manager_mp=excluded.manager_mp,headcount=excluded.headcount,
               updated_by=excluded.updated_by,updated_at=excluded.updated_at''',
            (lean, model_name, month, mgr, hc, updated_by, ts_now))
        conn.execute(
            'INSERT INTO bianche_edit_log (target_type,target_key,old_value,new_value,user_name,created_at) VALUES (?,?,?,?,?,?)',
            ('model_manual', f'{lean}:{model_name}:{month}', str(dict(ex)) if ex else '', f'mgr={mgr},hc={hc}', updated_by, ts_now))
        conn.commit(); return {'ok': True}
    except Exception as e:
        conn.rollback(); return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_bianche_dept(dept, month):
    """OCS/RB/QC: groups with last_month and this_month headcounts."""
    if dept not in DEPT_GROUPS:
        return {'ok': False, 'error': f'unknown dept: {dept}'}
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        y, m = int(month[:4]), int(month[5:7])
        m -= 1
        if m == 0: m = 12; y -= 1
        prev = f'{y:04d}-{m:02d}'

        curr_map = {r['group_name']: {'hc': r['headcount'], 'shoe': r['shoe_detail'] or ''} for r in conn.execute(
            'SELECT group_name, shoe_detail, headcount FROM bianche_dept_hc WHERE dept=? AND month=?', (dept, month))}
        prev_map = {r['group_name']: r['headcount'] for r in conn.execute(
            'SELECT group_name, headcount FROM bianche_dept_hc WHERE dept=? AND month=?', (dept, prev))}

        sections = []
        for section_name, groups in DEPT_GROUPS[dept]:
            gl = []
            for g in groups:
                prev_hc = prev_map.get(g)
                curr_hc = curr_map.get(g, {}).get('hc')
                this_hc = curr_hc if curr_hc is not None else (prev_hc if prev_hc is not None else 0)
                gl.append({'group': g, 'shoe_detail': curr_map.get(g, {}).get('shoe', ''),
                           'last_month_hc': prev_hc, 'this_month_hc': this_hc})
            sections.append({'section': section_name, 'groups': gl})
        return {'ok': True, 'dept': dept, 'month': month, 'sections': sections}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def set_bianche_dept_hc(dept, group_name, month, headcount, shoe_detail='', updated_by=''):
    if dept not in DEPT_GROUPS:
        return {'ok': False, 'error': f'unknown dept: {dept}'}
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        old_hc = conn.execute('SELECT headcount FROM bianche_dept_hc WHERE dept=? AND group_name=? AND month=?', (dept, group_name, month)).fetchone()
        ts_now = now_iso()
        conn.execute(
            '''INSERT INTO bianche_dept_hc (dept,group_name,shoe_detail,month,headcount,updated_by,updated_at)
               VALUES(?,?,?,?,?,?,?)
               ON CONFLICT(dept,group_name,month) DO UPDATE SET
               shoe_detail=excluded.shoe_detail,headcount=excluded.headcount,
               updated_by=excluded.updated_by,updated_at=excluded.updated_at''',
            (dept, group_name, shoe_detail or '', month, float(headcount or 0), updated_by, ts_now))
        conn.execute(
            'INSERT INTO bianche_edit_log (target_type,target_key,old_value,new_value,user_name,created_at) VALUES (?,?,?,?,?,?)',
            ('dept_hc', f'{dept}:{group_name}:{month}', str(old_hc['headcount'] if old_hc else ''), str(headcount), updated_by, ts_now))
        conn.commit(); return {'ok': True}
    except Exception as e:
        conn.rollback(); return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def alloc_fix_default_checked(month):
    """One-time: set all non-裁斷機 items for month to is_checked=1 (moved out by default)."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        n = conn.execute(
            "UPDATE allocation_item SET is_checked=1 WHERE month=? AND zone != '裁斷機'",
            (month,)
        ).rowcount
        conn.commit()
        return {'ok': True, 'updated': n}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def alloc_get_lock(month):
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        r = conn.execute('SELECT locked_at, locked_by FROM alloc_lock WHERE month=?', (month,)).fetchone()
        return {'ok': True, 'locked': bool(r), 'locked_at': r['locked_at'] if r else None, 'locked_by': r['locked_by'] if r else None}
    finally:
        conn.close()


def alloc_lock_month(month, locked_by=''):
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        ts = now_iso()
        conn.execute('INSERT OR REPLACE INTO alloc_lock (month,locked_at,locked_by) VALUES(?,?,?)', (month, ts, locked_by))
        conn.commit(); return {'ok': True, 'locked_at': ts}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def alloc_unlock_month(month):
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        conn.execute('DELETE FROM alloc_lock WHERE month=?', (month,))
        conn.commit(); return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_bianche_export_data(month):
    """Collect all 4 tabs for xlsx export."""
    csa = get_bianche_csa_data(month)
    ocs = get_bianche_dept('OCS', month)
    rb  = get_bianche_dept('RB',  month)
    qc  = get_bianche_dept('QC',  month)
    return {'ok': True, 'month': month, 'csa': csa, 'ocs': ocs, 'rb': rb, 'qc': qc}


# ── 廠務組織編制表 (bianzhi) — 上半總表 + 下半CSA明細 ─────────────────────────────

BIANZHI_UNITS = ['CSA','大底課','自動化','電腦針車','品包','C2B合計','品管','RB','印刷高周波','設備工程部','副總室','現場技轉/KTHT']

BIANZHI_MONTHLY_KEYS = [
    'total_qty',       # 本月進度表總量 (calculated)
    'avg_lc',          # 本月平均LC (manual)
    'direct_planned',  # 本月預計直工數 (= C2B合計直工本月)
    'working_hours',   # 本月平均上班時數 (manual)
    'total_manhours',  # 預計總工時 (= direct_planned * working_hours)
    'external_hours',  # 本月預計發外工時 (manual)
    'deduct_hours',    # 本月預計扣減工時 (manual)
    'planned_eff',     # 本月預計效率 (calculated)
    'target80_direct', # 達80%效率需直工數 (calculated)
    'actual_direct',   # 本月實際直工數 (manual)
    'actual_eff',      # 本月實際效率 (calculated)
]

def _ensure_bianzhi_ext(conn):
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS bianzhi_unit_manual (
        month   TEXT NOT NULL,
        unit    TEXT NOT NULL,
        field   TEXT NOT NULL,
        value   REAL DEFAULT 0,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (month, unit, field)
    );
    CREATE TABLE IF NOT EXISTS bianzhi_monthly_manual (
        month   TEXT NOT NULL,
        key     TEXT NOT NULL,
        value   REAL DEFAULT 0,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (month, key)
    );
    ''')
    conn.commit()


def _lean_major(lean):
    """Extract major LEAN number from lean name ('1A'→'1', '3A1'→'3', '11B2'→'11')."""
    import re
    m = re.match(r'^(\d+)', str(lean or ''))
    return m.group(1) if m else ''


def get_bianzhi_detail(month):
    """CSA LEAN detail: per lean, per model_name row with calculated + manual values."""
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        _ensure_bianzhi_ext(conn)

        eolr_map = {r['lean']: r['eolr'] for r in conn.execute(
            'SELECT lean, eolr FROM lean_eolr_settings WHERE month=?', (month,)).fetchall()}

        # DS-04 orders
        order_rows = conn.execute(
            '''SELECT lean, model_name,
                      GROUP_CONCAT(DISTINCT art) AS arts,
                      SUM(qty) AS qty,
                      MAX(is_outsource_upper) AS is_outsource
               FROM ds04_orders WHERE COALESCE(is_deleted,0)=0
               GROUP BY lean, model_name ORDER BY lean, model_name'''
        ).fetchall()

        # IE standard times per art+zone
        ie_data = {}
        for r in conn.execute(
            '''SELECT oa.art, ip.zone, ip.standard_time FROM ie_process ip
               JOIN ob_articles oa ON oa.header_id=ip.header_id
               WHERE (ip.flag IS NULL OR ip.flag!='deleted') AND ip.standard_time>0
                 AND ''' + _eff_stage_clause('ip') + '''  '''):
            ie_data.setdefault(r['art'], {}).setdefault(r['zone'], []).append(r['standard_time'] or 0)

        # Allocation moved per art+zone type
        moved_p = {}  # P: same-cut / auto / fold — stays in CSA as ext
        moved_q = {}  # Q: computer stitching
        moved_r = {}  # R: sole attachment / 大底課
        for r in conn.execute(
            'SELECT art, zone, SUM(theory_mp) AS mp FROM allocation_item '
            'WHERE is_checked=1 AND month=? GROUP BY art, zone', (month,)):
            z = r['zone'] or ''
            a = r['art']
            mp = r['mp'] or 0
            # P: cutting moved (auto zones in allocation)
            if z in AUTO_ZONES or z in {'同材共裁', '折邊', '自動化'}:
                moved_p[a] = moved_p.get(a, 0) + mp
            # Q: computer stitching
            elif z in {'電腦針車', 'CNC', '电脑针车', '折边'}:
                moved_q[a] = moved_q.get(a, 0) + mp
            # R: sole / 大底
            elif z in {'成型', '貼底', '大底課'}:
                moved_r[a] = moved_r.get(a, 0) + mp

        # Manual bianzhi per model
        manual_map = {}
        for r in conn.execute(
            'SELECT lean, model_name, headcount FROM bianche_model_manual WHERE month=?', (month,)):
            manual_map[(r['lean'], r['model_name'])] = r['headcount'] or 0

        # Build lean → model rows
        lean_map = {}
        for row in order_rows:
            lean = row['lean']
            model = row['model_name']
            arts = [a.strip() for a in (row['arts'] or '').split(',') if a.strip()]
            qty = row['qty'] or 0
            is_out = row['is_outsource'] or 0
            eolr = eolr_map.get(lean, 120)
            first_art = next((a for a in arts if a in ie_data), None)
            has_ie = first_art is not None

            if has_ie:
                d = ie_data[first_art]
                def _ie(zones): return round(sum(sum(d.get(z, [])) for z in zones) * eolr / 3600.0, 1)
                cut = 0.0 if is_out else _ie(CUTTING_ZONES)
                stch = 0.0 if is_out else _ie(STITCH_ZONES)
                asm  = _ie(ASSEMBLY_ZONES)
            else:
                cut = stch = asm = None

            k = round((cut or 0) + (stch or 0) + (asm or 0), 1) if has_ie else None
            bz = manual_map.get((lean, model))
            if bz is None and k is not None:
                bz = k  # default bianzhi = calculated

            p_ext = round(sum(moved_p.get(a, 0) for a in arts), 1)
            q_ext = round(sum(moved_q.get(a, 0) for a in arts), 1)
            r_ext = round(sum(moved_r.get(a, 0) for a in arts), 1)
            c2b   = round((k or 0) + p_ext + q_ext + r_ext, 1) if k is not None else None

            if lean not in lean_map:
                lean_map[lean] = {
                    'lean': lean, 'lean_major': _lean_major(lean),
                    'eolr': eolr, 'models': []
                }
            lean_map[lean]['models'].append({
                'model_name': model, 'arts': row['arts'] or '',
                'qty': qty, 'is_outsource': bool(is_out), 'has_ie': has_ie,
                'cutting': cut, 'stitching': stch, 'assembly': asm,
                'total_k': k, 'bianzhi': bz,
                'p_ext': p_ext, 'q_ext': q_ext, 'r_ext': r_ext, 'c2b': c2b,
            })

        # Sort leans, compute totals
        def _lean_sort(l):
            import re
            m = re.match(r'^(\d+)([A-Za-z]+)(\d*)', l)
            if m:
                return (int(m.group(1)), m.group(2), int(m.group(3) or 0))
            return (999, l, 0)

        leans_sorted = sorted(lean_map.values(), key=lambda x: _lean_sort(x['lean']))
        for lg in leans_sorted:
            lg['total_bianzhi'] = round(sum(
                (m['bianzhi'] or 0) for m in lg['models'] if m['bianzhi'] is not None), 1)

        return {'ok': True, 'leans': leans_sorted}
    except Exception as e:
        import traceback; return {'ok': False, 'error': str(e), 'trace': traceback.format_exc()}
    finally:
        conn.close()


def get_bianzhi_summary(month):
    """Upper summary: unit table + monthly metrics."""
    conn = get_conn()
    try:
        _ensure_bianche_ext(conn)
        _ensure_bianzhi_ext(conn)

        # Unit manual values
        unit_manual = {}
        for r in conn.execute('SELECT unit, field, value FROM bianzhi_unit_manual WHERE month=?', (month,)):
            unit_manual.setdefault(r['unit'], {})[r['field']] = r['value']

        # Monthly manual values
        monthly_manual = {r['key']: r['value'] for r in conn.execute(
            'SELECT key, value FROM bianzhi_monthly_manual WHERE month=?', (month,))}

        # CSA direct this month = sum of all lean bianzhi
        csa_lean_hc = conn.execute(
            'SELECT SUM(headcount) FROM bianche_lean_hc WHERE month=?', (month,)).fetchone()[0] or 0

        # Total qty from DS04
        total_qty = conn.execute(
            'SELECT SUM(qty) FROM ds04_orders WHERE COALESCE(is_deleted,0)=0').fetchone()[0] or 0

        def _um(unit, field, default=None):
            return unit_manual.get(unit, {}).get(field, default)

        def _mm(key, default=None):
            return monthly_manual.get(key, default)

        # Build unit rows
        def _unit(name, direct_last=None, direct_this=None, ind_last=None, ind_this=None, formula_direct=False):
            dl = _um(name, 'direct_last', direct_last)
            dt = csa_lean_hc if formula_direct else _um(name, 'direct_this', direct_this)
            il = _um(name, 'indirect_last', ind_last)
            it = _um(name, 'indirect_this', ind_this)
            rl = round(dl / il, 3) if (dl and il and isinstance(dl,(int,float)) and isinstance(il,(int,float)) and il != 0) else None
            rt = round(dt / it, 3) if (dt and it and isinstance(dt,(int,float)) and isinstance(it,(int,float)) and it != 0) else None
            return {'unit': name, 'direct_last': dl, 'direct_this': dt,
                    'indirect_last': il, 'indirect_this': it,
                    'ratio_last': rl, 'ratio_this': rt,
                    'formula_direct': formula_direct}

        units = [
            _unit('CSA', formula_direct=True),
            _unit('大底課'),
            _unit('自動化'),
            _unit('電腦針車'),
            _unit('品包'),
        ]
        # C2B 合計 = SUM of above 5
        c2b_dl = sum((u['direct_last'] or 0) for u in units if isinstance(u['direct_last'], (int, float)))
        c2b_dt = sum((u['direct_this'] or 0) for u in units if isinstance(u['direct_this'], (int, float)))
        c2b_il = sum((u['indirect_last'] or 0) for u in units if isinstance(u['indirect_last'], (int, float)))
        c2b_it = sum((u['indirect_this'] or 0) for u in units if isinstance(u['indirect_this'], (int, float)))
        c2b_rl = round(c2b_dl / c2b_il, 3) if c2b_il else None
        c2b_rt = round(c2b_dt / c2b_it, 3) if c2b_it else None
        units.append({'unit': 'C2B合計', 'direct_last': c2b_dl or None, 'direct_this': c2b_dt or None,
                      'indirect_last': c2b_il or None, 'indirect_this': c2b_it or None,
                      'ratio_last': c2b_rl, 'ratio_this': c2b_rt, 'is_subtotal': True})

        for u_name in ['品管', 'RB', '印刷高周波', '設備工程部', '副總室', '現場技轉/KTHT']:
            units.append(_unit(u_name))

        # Grand total
        all_units = [u for u in units if u['unit'] != 'C2B合計']
        t_dl = sum((u['direct_last'] or 0) for u in all_units if isinstance(u['direct_last'], (int, float)))
        t_dt = sum((u['direct_this'] or 0) for u in all_units if isinstance(u['direct_this'], (int, float)))
        t_il = sum((u['indirect_last'] or 0) for u in all_units if isinstance(u['indirect_last'], (int, float)))
        t_it = sum((u['indirect_this'] or 0) for u in all_units if isinstance(u['indirect_this'], (int, float)))
        units.append({'unit': '合計', 'direct_last': t_dl or None, 'direct_this': t_dt or None,
                      'indirect_last': t_il or None, 'indirect_this': t_it or None,
                      'ratio_last': None, 'ratio_this': None, 'is_total': True})

        # Monthly metrics
        direct_planned = c2b_dt or 0
        working_hrs    = _mm('working_hours', 239.5)
        total_mh       = round(direct_planned * (working_hrs or 239.5), 1)
        ext_hrs        = _mm('external_hours', 0)
        ded_hrs        = _mm('deduct_hours', 0)
        avg_lc         = _mm('avg_lc', 0)
        tq             = total_qty

        # 預計效率 = ((avg_lc/233 * tq) / (total_mh + ext_hrs - ded_hrs - 60*240))
        # 達80%直工 = (((avg_lc/233*tq)/0.8) - ext_hrs + ded_hrs) / working_hrs
        eff_denom = (total_mh + (ext_hrs or 0) - (ded_hrs or 0) - 60 * 240)
        plan_eff = round(((avg_lc / 233 * tq) / eff_denom), 4) if (avg_lc and tq and eff_denom) else None
        target80 = round((((avg_lc / 233 * tq) / 0.8) - (ext_hrs or 0) + (ded_hrs or 0)) / (working_hrs or 1), 1) if (avg_lc and tq) else None
        actual_direct = _mm('actual_direct', 0)
        act_eff_denom = ((actual_direct or 0) * (working_hrs or 1) + (ext_hrs or 0) - (ded_hrs or 0))
        actual_eff = round((avg_lc / 233 * tq) / act_eff_denom, 4) if (avg_lc and tq and act_eff_denom) else None

        monthly = {
            'total_qty': tq, 'avg_lc': avg_lc,
            'direct_planned': direct_planned, 'working_hours': working_hrs,
            'total_manhours': total_mh, 'external_hours': ext_hrs,
            'deduct_hours': ded_hrs, 'planned_eff': plan_eff,
            'target80_direct': target80, 'actual_direct': actual_direct,
            'actual_eff': actual_eff,
        }
        return {'ok': True, 'units': units, 'monthly': monthly, 'month': month}
    except Exception as e:
        import traceback; return {'ok': False, 'error': str(e), 'trace': traceback.format_exc()}
    finally:
        conn.close()


def set_bianzhi_unit_manual(month, unit, field, value):
    conn = get_conn()
    try:
        _ensure_bianzhi_ext(conn)
        conn.execute(
            'INSERT INTO bianzhi_unit_manual (month,unit,field,value,updated_at) VALUES(?,?,?,?,?) '
            'ON CONFLICT(month,unit,field) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at',
            (month, unit, field, float(value or 0), now_iso()))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def set_bianzhi_monthly_manual(month, key, value):
    conn = get_conn()
    try:
        _ensure_bianzhi_ext(conn)
        conn.execute(
            'INSERT INTO bianzhi_monthly_manual (month,key,value,updated_at) VALUES(?,?,?,?) '
            'ON CONFLICT(month,key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at',
            (month, key, float(value or 0), now_iso()))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_bianzhi_months():
    """Available months in ds04_orders (YYYYMM → YYYY-MM)."""
    conn = get_conn()
    try:
        return {'ok': True, 'months': ['2026-05', '2026-06', '2026-07']}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()
