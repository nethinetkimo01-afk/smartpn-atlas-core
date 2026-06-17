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
