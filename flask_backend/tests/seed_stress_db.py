"""
Seed an INDEPENDENT stress-test DB: tests/atlas_stress.db

- Schema only — built from schema.sql + the IE tables (ie_process / ie_stage /
  ie_process_group / ie_edit_log) that live outside schema.sql.
- NEVER connects to, copies, or reads data/atlas.db.
- Seeds REAL-scale fake data so the detail-read path (ie_sheet_data) is exercised
  against a genuinely large table — the whole point of redoing this test.

Targets (real system ≈ 152 headers / 20434 ie_process / 522774 ie_sheet_data):
    ob_header      ≥ 150   (we seed 160)
    ie_process     ≥ 8000  (we seed ~11000)
    ie_sheet_data  ≥ 520000 (we seed ~571000, unevenly distributed)

Run:  cd flask_backend && python tests/seed_stress_db.py
"""
import os, sqlite3, sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

TESTS_DIR   = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TESTS_DIR)
SCHEMA_PATH = os.path.join(BACKEND_DIR, 'schema.sql')
STRESS_DB   = os.path.join(TESTS_DIR, 'atlas_stress.db')

N_HEADERS       = 160
N_HEAVY         = 12        # headers carrying a big single Cutting sheet
HEAVY_CELLS     = 18000     # cells per heavy header
NORMAL_CELLS    = 2400      # cells per normal header
SHEET_COLS      = 30        # columns per sheet row (mimics IE sheet width)
PROC_PER_HEADER = 70        # ie_process rows per header  -> 160*70 = 11200

# ── IE tables not present in schema.sql (DDL mirrors production import scripts) ─
IE_PROCESS_DDL = """
CREATE TABLE IF NOT EXISTS ie_process (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id     INTEGER NOT NULL,
    art           TEXT    NOT NULL,
    segment       TEXT    NOT NULL,
    zone          TEXT    NOT NULL,
    stage         INTEGER NOT NULL DEFAULT 1,
    seq           INTEGER,
    process_name  TEXT,
    process_name_vi TEXT,
    process_name_zh TEXT,
    part_name     TEXT,
    mat_cat       TEXT,
    tct           REAL,
    normal_time   REAL,
    allowance_pct REAL,
    standard_time REAL,
    cut_per_hour  REAL,
    qty_per_pair  REAL,
    layers_per_cut REAL,
    actual_operators REAL,
    machine       TEXT,
    post_marking_std REAL, post_marking_ops REAL,
    post_skiving_std REAL, post_skiving_ops REAL,
    post_attach_std  REAL, post_attach_ops  REAL,
    post_edge_std    REAL, post_edge_ops    REAL,
    post_heat_std    REAL, post_heat_ops    REAL,
    post_polish_std  REAL, post_polish_ops  REAL,
    value_type    TEXT,
    is_locked     INTEGER DEFAULT 0,
    formula       TEXT,
    source_sheet  TEXT,
    source_row    INTEGER,
    flag          TEXT
)
"""

IE_OTHER_DDL = [
    """CREATE TABLE IF NOT EXISTS ie_stage (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        header_id   INTEGER NOT NULL,
        stage_name  TEXT NOT NULL DEFAULT '初版',
        created_at  TEXT NOT NULL DEFAULT (datetime('now')),
        is_approved INTEGER DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS ie_process_group (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        header_id   INTEGER NOT NULL,
        segment     TEXT NOT NULL,
        zone        TEXT NOT NULL,
        stage_id    INTEGER,
        process_ids TEXT NOT NULL DEFAULT '[]',
        headcount   REAL,
        note        TEXT DEFAULT ''
    )""",
    """CREATE TABLE IF NOT EXISTS ie_edit_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        process_id  INTEGER,
        stage_id    INTEGER,
        field       TEXT NOT NULL,
        old_value   TEXT,
        new_value   TEXT,
        user        TEXT DEFAULT 'system',
        status      TEXT NOT NULL DEFAULT 'pending',
        created_at  TEXT NOT NULL DEFAULT (datetime('now'))
    )""",
    """CREATE TABLE IF NOT EXISTS ie_assignments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        header_id   INTEGER NOT NULL,
        user_id     INTEGER NOT NULL,
        assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(header_id, user_id)
    )""",
    """CREATE TABLE IF NOT EXISTS ie_review (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        header_id     INTEGER NOT NULL,
        stage_id      INTEGER,
        submitted_by  TEXT NOT NULL,
        submitted_at  TEXT NOT NULL DEFAULT (datetime('now')),
        status        TEXT NOT NULL DEFAULT 'pending',
        reviewer      TEXT,
        reviewed_at   TEXT,
        reject_reason TEXT
    )""",
    # indexes mirroring the production import scripts (so query plans match)
    "CREATE INDEX IF NOT EXISTS idx_iep_hdr ON ie_process(header_id)",
    "CREATE INDEX IF NOT EXISTS idx_iep_art ON ie_process(art)",
    "CREATE INDEX IF NOT EXISTS idx_iep_seg ON ie_process(segment, zone)",
]

SEGMENTS = ['cutting', 'stitching', 'assembly', 'stf']
CUT_ZONES = ['裁斷機', 'ATOM', 'Laser', 'EMMA', 'YINGHUI']


def _hash_pw(pw):
    import hashlib
    return hashlib.sha256(pw.encode()).hexdigest()


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def build():
    if os.path.exists(STRESS_DB):
        os.remove(STRESS_DB)
    for ext in ('-wal', '-shm'):
        p = STRESS_DB + ext
        if os.path.exists(p):
            os.remove(p)

    conn = sqlite3.connect(STRESS_DB)
    conn.execute('PRAGMA journal_mode = WAL')
    with open(SCHEMA_PATH, encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.execute(IE_PROCESS_DDL)
    for ddl in IE_OTHER_DDL:
        conn.execute(ddl)
    # sys_users (created inline by database.py in prod) + a test admin
    conn.execute('''CREATE TABLE IF NOT EXISTS sys_users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT NOT NULL UNIQUE,
        display_name  TEXT NOT NULL DEFAULT '',
        role          TEXT NOT NULL DEFAULT 'read_only',
        password_hash TEXT NOT NULL DEFAULT '',
        active        INTEGER NOT NULL DEFAULT 1,
        locked        INTEGER NOT NULL DEFAULT 0,
        created_at    TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
    )''')
    ts = now_iso()
    conn.execute(
        '''INSERT OR IGNORE INTO sys_users
           (username, display_name, role, password_hash, active, locked, created_at, updated_at)
           VALUES ('stress_admin','Stress Admin','admin',?,1,0,?,?)''',
        (_hash_pw('pw_admin'), ts, ts)
    )
    conn.commit()

    # ── ob_header + ob_articles + ob_epph + ie_stage ─────────────────────────
    header_ids = []
    for i in range(N_HEADERS):
        eolr = 120 if i % 2 == 0 else 60
        hid = conn.execute(
            '''INSERT INTO ob_header (model_name, season, material, category, eolr, run, created_at, updated_at)
               VALUES (?,?,?,?,?,1,?,?)''',
            (f'STRESS_MODEL_{i:03d}', '26SS', 'mesh', 'running', eolr, ts, ts)
        ).lastrowid
        header_ids.append(hid)
        conn.execute('INSERT INTO ob_articles (header_id, art) VALUES (?,?)', (hid, f'ST{i:04d}A'))
        conn.execute('INSERT INTO ob_articles (header_id, art) VALUES (?,?)', (hid, f'ST{i:04d}B'))
        conn.execute(
            'INSERT INTO ob_epph (header_id, cutting, stitching, assembly, stock, source) VALUES (?,?,?,?,?,?)',
            (hid, 12.5, 30.2, 18.1, 9.3, 'ie_file')
        )
        conn.execute('INSERT INTO ie_stage (header_id, stage_name) VALUES (?,?)', (hid, '初版'))
    conn.commit()

    # ── ie_process rows (≥8000): spread across headers/segments/zones ────────
    proc_rows = []
    for idx, hid in enumerate(header_ids):
        art = f'ST{idx:04d}A'
        for s in range(PROC_PER_HEADER):
            seg = SEGMENTS[s % len(SEGMENTS)]
            if seg == 'cutting':
                zone = CUT_ZONES[s % len(CUT_ZONES)]
            elif seg == 'stitching':
                zone = ['主流', '支流', '電腦針車', '折边'][s % 4]
            elif seg == 'assembly':
                zone = ['成型', '成型UV'][s % 2]
            else:
                zone = ['打粗', '水洗', '貼底', '照射'][s % 4]
            std = round(2.0 + (s % 40) * 0.37, 3)
            proc_rows.append((
                hid, art, seg, zone, s + 1,
                f'P{seg[:3]}_{s}', f'流程{s}', f'流程{s}',
                'mesh', std, 'manual', 0, None
            ))
    conn.executemany(
        '''INSERT INTO ie_process
           (header_id, art, segment, zone, seq, process_name, process_name_vi,
            process_name_zh, mat_cat, standard_time, value_type, is_locked, flag)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        proc_rows
    )
    conn.commit()

    # ── ie_sheet_data (≥520000): the big table the detail view reads ─────────
    # Heavy headers carry one large 'Cutting' sheet (≈12000 cells) + extras.
    # Normal headers carry several modest sheets. Distribution is intentionally
    # uneven to mimic real data.
    SHEETS_NORMAL = ['Cutting', 'Stitching', 'Assembly', 'SUM_Stock']
    batch = []
    BATCH_SIZE = 50000
    total_cells = 0

    def flush():
        nonlocal batch
        if batch:
            conn.executemany(
                'INSERT INTO ie_sheet_data (header_id, sheet_name, row, col, value, formula, cell_type) VALUES (?,?,?,?,?,?,?)',
                batch
            )
            batch = []

    def emit_sheet(hid, sheet_name, n_cells):
        nonlocal total_cells
        rows = max(1, n_cells // SHEET_COLS)
        for r in range(1, rows + 1):
            for c in range(1, SHEET_COLS + 1):
                # ~30% formula cells, rest manual; some empty for realism
                if c % 7 == 0:
                    val, fml, ctype = '', '', 'empty'
                elif c % 3 == 0:
                    val, fml, ctype = str(round(r * c * 0.13, 3)), f'=3600/{c}/{r}', 'formula'
                else:
                    val, fml, ctype = f'v{r}_{c}', '', 'manual'
                batch.append((hid, sheet_name, r, c, val, fml, ctype))
                total_cells += 1
                if len(batch) >= BATCH_SIZE:
                    flush()

    for idx, hid in enumerate(header_ids):
        if idx < N_HEAVY:
            # one big Cutting sheet + 3 medium sheets
            emit_sheet(hid, 'Cutting', 12000)
            emit_sheet(hid, 'Stitching', 3000)
            emit_sheet(hid, 'Assembly', 1800)
            emit_sheet(hid, 'SUM_Stock', 1200)
        else:
            per = NORMAL_CELLS // len(SHEETS_NORMAL)
            for sname in SHEETS_NORMAL:
                emit_sheet(hid, sname, per)
    flush()
    conn.commit()

    # ── art_sheet_status (matrix view reads this) ────────────────────────────
    st_rows = []
    for hid in header_ids:
        st_rows.append((hid, f'ST{header_ids.index(hid):04d}A', 'cutting', 'has_data'))
    conn.executemany(
        'INSERT OR IGNORE INTO art_sheet_status (header_id, art, sheet_type, status) VALUES (?,?,?,?)',
        st_rows
    )
    conn.commit()

    # ── Counts ───────────────────────────────────────────────────────────────
    counts = {
        'ob_header':     conn.execute('SELECT COUNT(*) FROM ob_header').fetchone()[0],
        'ob_articles':   conn.execute('SELECT COUNT(*) FROM ob_articles').fetchone()[0],
        'ie_process':    conn.execute('SELECT COUNT(*) FROM ie_process').fetchone()[0],
        'ie_sheet_data': conn.execute('SELECT COUNT(*) FROM ie_sheet_data').fetchone()[0],
        'ie_stage':      conn.execute('SELECT COUNT(*) FROM ie_stage').fetchone()[0],
    }
    # Heaviest header + its biggest sheet (for the detail-load test)
    heavy = conn.execute(
        'SELECT header_id, COUNT(*) c FROM ie_sheet_data GROUP BY header_id ORDER BY c DESC LIMIT 1'
    ).fetchone()
    big_sheet = conn.execute(
        'SELECT sheet_name, COUNT(*) c FROM ie_sheet_data WHERE header_id=? GROUP BY sheet_name ORDER BY c DESC LIMIT 1',
        (heavy[0],)
    ).fetchone()
    counts['heavy_header_id'] = heavy[0]
    counts['heavy_header_cells'] = heavy[1]
    counts['heavy_sheet_name'] = big_sheet[0]
    counts['heavy_sheet_cells'] = big_sheet[1]
    conn.close()
    return counts


if __name__ == '__main__':
    c = build()
    print('Stress DB built:', STRESS_DB)
    for k, v in c.items():
        print(f'  {k:22} = {v}')
