"""
Schema migration manager — ALL schema changes must go through here.

Rules:
  ALLOWED   : ADD COLUMN / CREATE TABLE / CREATE INDEX
  FORBIDDEN : DROP TABLE / DROP COLUMN / ALTER TABLE ... RENAME COLUMN

Usage:
  python flask_backend/migrate.py

Add migrations to the MIGRATIONS list below (append only, never remove).
Each migration is a dict: {'id': 'M001', 'desc': '...', 'sql': ['...']}
"""
import os, re, shutil, sqlite3
from datetime import datetime

BASE   = os.path.dirname(os.path.abspath(__file__))
DB     = os.path.join(BASE, 'data', 'atlas.db')
BACKUP = os.path.join(BASE, 'backup')

# ── Safety: reject forbidden SQL patterns ─────────────────────────────────────
FORBIDDEN = re.compile(
    r'\b(DROP\s+TABLE|DROP\s+COLUMN|ALTER\s+TABLE\s+\S+\s+RENAME\s+COLUMN|TRUNCATE)\b',
    re.IGNORECASE
)

def _check_safe(sql: str):
    m = FORBIDDEN.search(sql)
    if m:
        raise ValueError(f'Forbidden operation: {m.group(0)}')

# ── Migration list (append-only) ──────────────────────────────────────────────
MIGRATIONS = [
    {
        'id': 'M001',
        'desc': 'Add is_deleted to ds04_orders (soft delete)',
        'sql': [
            "ALTER TABLE ds04_orders ADD COLUMN is_deleted INTEGER DEFAULT 0",
        ]
    },
    {
        'id': 'M002',
        'desc': 'Create alloc_edit_log table',
        'sql': [
            '''CREATE TABLE IF NOT EXISTS alloc_edit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id     INTEGER,
                action      TEXT NOT NULL,
                old_value   TEXT DEFAULT '',
                new_value   TEXT DEFAULT '',
                user_name   TEXT DEFAULT '',
                created_at  TEXT NOT NULL
            )'''
        ]
    },
    {
        'id': 'M003',
        'desc': 'Create bianche_edit_log table',
        'sql': [
            '''CREATE TABLE IF NOT EXISTS bianche_edit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                target_type TEXT NOT NULL,
                target_key  TEXT NOT NULL,
                old_value   TEXT DEFAULT '',
                new_value   TEXT DEFAULT '',
                user_name   TEXT DEFAULT '',
                created_at  TEXT NOT NULL
            )'''
        ]
    },
    {
        'id': 'M004',
        'desc': 'Add ie_assignments, ie_review tables + is_approved on ie_stage',
        'sql': [
            '''CREATE TABLE IF NOT EXISTS ie_assignments (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                header_id  INTEGER NOT NULL,
                user_id    INTEGER NOT NULL,
                assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(header_id, user_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS ie_review (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                header_id    INTEGER NOT NULL,
                stage_id     INTEGER,
                submitted_by TEXT NOT NULL,
                submitted_at TEXT NOT NULL DEFAULT (datetime('now')),
                status       TEXT NOT NULL DEFAULT 'pending',
                reviewer     TEXT,
                reviewed_at  TEXT,
                reject_reason TEXT
            )''',
            "ALTER TABLE ie_stage ADD COLUMN is_approved INTEGER DEFAULT 0",
        ]
    },
    {
        'id': 'M005',
        'desc': 'Add post_polish_std/ops to ie_process (裁斷機 6th post-process 磨皮)',
        'sql': [
            "ALTER TABLE ie_process ADD COLUMN post_polish_std REAL",
            "ALTER TABLE ie_process ADD COLUMN post_polish_ops REAL",
        ]
    },
    {
        'id': 'M006',
        'desc': 'Add equipment_type to ie_process (stitching/assembly/STF 設備種類下拉)',
        'sql': [
            "ALTER TABLE ie_process ADD COLUMN equipment_type TEXT",
        ]
    },
    {
        'id': 'M007',
        'desc': '版本控制 Step 1: ie_process.stage_id + ie_stage.is_approved (真正資料分版；'
                '資料回填 v1 由 versioning_step1.py 或 init_db self-heal 執行)',
        'sql': [
            "ALTER TABLE ie_process ADD COLUMN stage_id INTEGER",
            "ALTER TABLE ie_stage ADD COLUMN is_approved INTEGER DEFAULT 0",
        ]
    },
    {
        'id': 'M008',
        'desc': '版本控制 Step 2: lock_history 鎖定版變更歷史表',
        'sql': [
            '''CREATE TABLE IF NOT EXISTS lock_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                header_id    INTEGER NOT NULL,
                stage_id     INTEGER NOT NULL,
                stage_name   TEXT,
                effective_at TEXT NOT NULL,
                set_by       TEXT,
                note         TEXT
            )''',
        ]
    },
    {
        'id': 'M009',
        'desc': '設備種類可管理選項清單 equipment_types + 先塞兩筆(單針/雙針針車機)',
        'sql': [
            '''CREATE TABLE IF NOT EXISTS equipment_types (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL UNIQUE,
                sort_order INTEGER NOT NULL DEFAULT 0,
                active     INTEGER NOT NULL DEFAULT 1,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )''',
            "INSERT OR IGNORE INTO equipment_types (name, sort_order, active) VALUES ('單針針車機', 10, 1)",
            "INSERT OR IGNORE INTO equipment_types (name, sort_order, active) VALUES ('雙針針車機', 20, 1)",
        ]
    },
    {
        'id': 'M010',
        'desc': '送審審核 workflow：ie_review 補 stage_name/reviewed_by 欄 + 狀態索引（M004 已建基本表）',
        'sql': [
            '''CREATE TABLE IF NOT EXISTS ie_review (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                header_id     INTEGER NOT NULL,
                stage_id      INTEGER,
                stage_name    TEXT,
                status        TEXT NOT NULL DEFAULT 'pending',
                submitted_by  TEXT,
                submitted_at  TEXT,
                reviewed_by   TEXT,
                reviewed_at   TEXT,
                reject_reason TEXT
            )''',
            "ALTER TABLE ie_review ADD COLUMN stage_name TEXT",
            "ALTER TABLE ie_review ADD COLUMN reviewed_by TEXT",
            "CREATE INDEX IF NOT EXISTS idx_ie_review_status ON ie_review(status)",
            "CREATE INDEX IF NOT EXISTS idx_ie_review_header ON ie_review(header_id)",
        ]
    },
]

def _ensure_migration_table(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS schema_migrations (
        id         TEXT PRIMARY KEY,
        applied_at TEXT NOT NULL
    )''')
    conn.commit()

def _applied(conn, mid):
    r = conn.execute('SELECT id FROM schema_migrations WHERE id=?', (mid,)).fetchone()
    return r is not None

def _backup():
    if not os.path.exists(DB):
        return
    os.makedirs(BACKUP, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest  = os.path.join(BACKUP, f'pre_migrate_{stamp}.db')
    shutil.copy2(DB, dest)
    print(f'[migrate] Backup: {dest}')

def run():
    if not os.path.exists(DB):
        print(f'[migrate] DB not found: {DB}')
        return
    _backup()
    conn = sqlite3.connect(DB)
    _ensure_migration_table(conn)
    applied_any = False
    for m in MIGRATIONS:
        mid = m['id']
        if _applied(conn, mid):
            print(f'[migrate] {mid} already applied — skip')
            continue
        print(f'[migrate] Applying {mid}: {m["desc"]}')
        for sql in m['sql']:
            _check_safe(sql)
            try:
                conn.execute(sql)
            except Exception as e:
                if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
                    print(f'[migrate]   (already exists, skipping)')
                else:
                    conn.close()
                    raise
        conn.execute(
            'INSERT OR IGNORE INTO schema_migrations (id, applied_at) VALUES (?,?)',
            (mid, datetime.now().isoformat())
        )
        conn.commit()
        applied_any = True
        print(f'[migrate] {mid} done.')
    conn.close()
    if not applied_any:
        print('[migrate] All migrations already applied. DB is up to date.')

if __name__ == '__main__':
    run()
