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
# ATLAS_DB：與 database.py / db_backup.py 一致的覆寫方式。IE-VER 遷移要能在隔離副本上跑，
# 不能只認死 data/atlas.db（正式庫/基準庫都不該被開發流程直接動到）。
DB     = os.environ.get('ATLAS_DB') or os.path.join(BASE, 'data', 'atlas.db')
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
    {
        'id': 'M011',
        'desc': 'IE-VER B2: ob_header.lean —— 基準庫(C槽血脈)沒有這欄，但現行程式的廠務編制'
                '會 SELECT DISTINCT lean FROM ob_header → 不補會直接炸「no such column: lean」。'
                '（此欄原先是被 _migrate_lean.py 這類臨時腳本繞過管理器加的，故 M001-M010 沒有它，'
                '這正是兩條血脈 schema 分歧的成因；補進管理器讓它成為正式遷移。）',
        'sql': [
            "ALTER TABLE ob_header ADD COLUMN lean TEXT",
        ]
    },
    {
        'id': 'M012',
        'desc': 'IE-VER B3：實際人數/合併人數改為「版本×ART×EOLR 分格」存儲。'
                '中樞裁決 2026-07-15：識別單位＝版本×ART（鞋型名僅顯示分組），遷移不合併任何 header；'
                '同一 ART 的 60/120 共用標時/工序 → 標時/工序留在 ie_process（一份），'
                '只有「實際人數/合併人數」拆成 EOLR 兩格存到子表。'
                '★為什麼不是在 ie_process 上加 actual_60/actual_120 兩欄：'
                '那會把「格」寫死成兩欄，將來多一個 EOLR 就要改 schema；子表 (process_id, eolr) '
                '是一格一列，加 EOLR 不動 schema。'
                '★ie_process.actual_operators 保留不動：B3 只加不改（DROP COLUMN 本來就禁），'
                '舊欄留著才能拿來對帳（零丟值斷言＝子表 vs 舊欄逐格比對），也才回得去。',
        'sql': [
            # 實際人數：一格一列。(process_id, eolr) 唯一 → 同一工序同一 EOLR 不可能有兩個值。
            '''CREATE TABLE IF NOT EXISTS ie_process_actual (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                process_id       INTEGER NOT NULL REFERENCES ie_process(id) ON DELETE CASCADE,
                eolr             INTEGER NOT NULL,
                actual_operators REAL,
                updated_at       TEXT,
                UNIQUE(process_id, eolr)
            )''',
            "CREATE INDEX IF NOT EXISTS idx_ie_process_actual_pid  ON ie_process_actual(process_id)",
            "CREATE INDEX IF NOT EXISTS idx_ie_process_actual_eolr ON ie_process_actual(eolr)",
            # 合併人數：群組定義（哪幾列合併）仍在 ie_process_group（＝跟工序走，共用一份），
            # 只有 headcount 分 EOLR 格。基準庫 group 是 0 列、ME129 活庫有 149 列 → 雙源合併時才有值。
            '''CREATE TABLE IF NOT EXISTS ie_group_headcount (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id   INTEGER NOT NULL REFERENCES ie_process_group(id) ON DELETE CASCADE,
                eolr       INTEGER NOT NULL,
                headcount  REAL,
                updated_at TEXT,
                UNIQUE(group_id, eolr)
            )''',
            "CREATE INDEX IF NOT EXISTS idx_ie_group_headcount_gid ON ie_group_headcount(group_id)",
            # 現場確認清單（裁決①）：eolr 欄與標題矛盾、靠裁決落格的 header 要留痕，
            # 不是「落完格就當真」。status=pending 直到現場確認。
            '''CREATE TABLE IF NOT EXISTS ie_eolr_confirm (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                header_id     INTEGER NOT NULL,
                assigned_eolr INTEGER NOT NULL,
                eolr_column   INTEGER,
                eolr_title    INTEGER,
                ruling        TEXT,
                status        TEXT NOT NULL DEFAULT 'pending',
                note          TEXT,
                created_at    TEXT,
                UNIQUE(header_id)
            )''',
            # 裁決②「格子必有、空格留空不繼承」的結構保證：
            # 用 view 生格子，而不是在子表塞 NULL 佔位列。塞佔位列的話，
            # 「漏塞一列」＝格子不見了；view 是算出來的，漏不掉，也不必在每次新增工序時補塞。
            # 60/120 寫死＝裁決②的兩格；若日後新增 EOLR，改這支 view 即可（子表不動）。
            '''CREATE VIEW IF NOT EXISTS v_ie_process_cell AS
                SELECT p.id        AS process_id,
                       p.header_id AS header_id,
                       p.art       AS art,
                       e.eolr      AS eolr,
                       a.actual_operators AS actual_operators
                FROM ie_process p
                CROSS JOIN (SELECT 60 AS eolr UNION ALL SELECT 120 AS eolr) e
                LEFT JOIN ie_process_actual a
                       ON a.process_id = p.id AND a.eolr = e.eolr''',
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

def apply_all(conn, verbose=False):
    """把 MIGRATIONS 套到既有連線上；回傳是否有套用任何一支。

    ★為什麼要有這支（而不是只有 run()）：
      新建 DB 走的是 database.init_db()（schema.sql + 自我修復），**完全沒經過 MIGRATIONS**，
      而開機守門的期望 schema ＝ schema.sql ＋ MIGRATIONS。兩條路不交會 →
      全新安裝的 DB 一開機就被自己的守門擋掉（實測：缺 ob_header.lean、ie_review.reviewer → exit 3）。
      解法不是把每支遷移「順便也抄一份到 schema.sql」——那正是兩條血脈分歧的老毛病，
      下一支遷移又會再犯。解法是讓建庫流程**呼叫同一份 MIGRATIONS**，只留一個真相來源。

    不做備份、不自己開檔：呼叫端（init_db）已經握著這個 conn 和它的交易。
    """
    _ensure_migration_table(conn)
    applied_any = False
    for m in MIGRATIONS:
        mid = m['id']
        if _applied(conn, mid):
            if verbose:
                print(f'[migrate] {mid} already applied — skip')
            continue
        if verbose:
            print(f'[migrate] Applying {mid}: {m["desc"]}')
        deferred = False
        for sql in m['sql']:
            _check_safe(sql)
            try:
                conn.execute(sql)
            except Exception as e:
                msg = str(e).lower()
                if 'duplicate column' in msg or 'already exists' in msg:
                    if verbose:
                        print('[migrate]   (already exists, skipping)')
                elif 'no such table' in msg:
                    # ie_process / ie_stage 這些不是 schema.sql 建的，是匯入時才建 →
                    # 全新 DB 還沒有它們，這支遷移現在無事可做。
                    # ★不可標記成 applied：標了就永遠不會再跑，等匯入把表建出來時
                    #   這支遷移已經「假裝做完了」，欄位永遠缺著。留 pending 讓它下次開機自己補上
                    #   （init_db 每次開機都會呼叫 apply_all，故會自我痊癒）。
                    deferred = True
                    if verbose:
                        print(f'[migrate]   (表還不存在，延後到該表建出來後再跑: {e})')
                else:
                    raise
        if deferred:
            conn.commit()
            if verbose:
                print(f'[migrate] {mid} deferred — 保持 pending，待相依的表存在後自動重跑。')
            continue
        conn.execute(
            'INSERT OR IGNORE INTO schema_migrations (id, applied_at) VALUES (?,?)',
            (mid, datetime.now().isoformat())
        )
        conn.commit()
        applied_any = True
        if verbose:
            print(f'[migrate] {mid} done.')
    return applied_any


def run():
    if not os.path.exists(DB):
        print(f'[migrate] DB not found: {DB}')
        return
    _backup()
    conn = sqlite3.connect(DB)
    try:
        applied_any = apply_all(conn, verbose=True)
    finally:
        conn.close()
    if not applied_any:
        print('[migrate] All migrations already applied. DB is up to date.')

if __name__ == '__main__':
    run()
