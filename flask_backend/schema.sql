-- DS-03: OB Header (one row per shoe model + EOLR + MP combo)
CREATE TABLE IF NOT EXISTS ob_header (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name  TEXT NOT NULL DEFAULT '',
    season      TEXT,
    material    TEXT,
    category    TEXT,
    eolr        INTEGER NOT NULL,
    run         INTEGER NOT NULL,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- DS-03: OB Articles (many ARTs per header)
CREATE TABLE IF NOT EXISTS ob_articles (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id INTEGER NOT NULL REFERENCES ob_header(id) ON DELETE CASCADE,
    art       TEXT NOT NULL,
    UNIQUE(art, header_id)
);

-- DS-03: OB sub-sheet rows
CREATE TABLE IF NOT EXISTS ob_rows (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id   INTEGER NOT NULL REFERENCES ob_header(id) ON DELETE CASCADE,
    sheet_key   TEXT NOT NULL,
    row_order   INTEGER DEFAULT 0,
    part_viet   TEXT DEFAULT '',
    part_zh     TEXT DEFAULT '',
    mat_cat     TEXT DEFAULT '',
    layers      REAL DEFAULT 0,
    qty_pr      REAL DEFAULT 0,
    knives      REAL DEFAULT 0,
    ct          REAL DEFAULT 0,
    allowance   REAL DEFAULT 10,
    st          REAL DEFAULT 0,
    ops         REAL DEFAULT 0,
    marking     REAL DEFAULT 0,
    skiving     REAL DEFAULT 0,
    attaching   REAL DEFAULT 0,
    edge_paint  REAL DEFAULT 0,
    heat_press  REAL DEFAULT 0
);

-- DS-03: E-PPH per record (from DS-02 LC values)
CREATE TABLE IF NOT EXISTS ob_epph (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id   INTEGER NOT NULL UNIQUE REFERENCES ob_header(id) ON DELETE CASCADE,
    cutting     REAL DEFAULT 0,
    stitching   REAL DEFAULT 0,
    assembly    REAL DEFAULT 0,
    stock       REAL DEFAULT 0,
    source      TEXT DEFAULT 'ie_file'
);

-- Viet-Chinese part name lookup (independent base table)
CREATE TABLE IF NOT EXISTS lookup_viet_zh (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    viet        TEXT NOT NULL UNIQUE,
    zh          TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

-- Change log (tracks all field changes for DS-01, DS-02, DS-03)
CREATE TABLE IF NOT EXISTS change_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name  TEXT NOT NULL,
    record_key  TEXT NOT NULL,
    field_name  TEXT NOT NULL,
    old_value   TEXT,
    new_value   TEXT,
    changed_at  TEXT NOT NULL
);

-- DS-01: Season Plan (placeholder, import pending)
CREATE TABLE IF NOT EXISTS ds01_sp (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id          TEXT NOT NULL,
    product_type_desc   TEXT NOT NULL,
    calendar_month      TEXT NOT NULL,
    quantity            REAL,
    raw_data            TEXT,
    imported_at         TEXT,
    updated_at          TEXT,
    UNIQUE(article_id, product_type_desc, calendar_month)
);

-- DS-02: FOB Price List (placeholder, import pending)
CREATE TABLE IF NOT EXISTS ds02_fob (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    art             TEXT NOT NULL UNIQUE,
    model_no        TEXT,
    model_name      TEXT,
    silhouette_no   TEXT,
    factory         TEXT,
    season          TEXT,
    category        TEXT,
    lc_total        REAL,
    lc_ctb          REAL,
    lc_cutting      REAL,
    lc_stitching    REAL,
    lc_stockfitting REAL,
    lc_assembly     REAL,
    stage           TEXT,
    valid_from      TEXT,
    raw_data        TEXT,
    imported_at     TEXT,
    updated_at      TEXT
);

-- DS-03: IE raw sheet data (full cell dump from source xlsx)
CREATE TABLE IF NOT EXISTS ie_sheet_data (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id   INTEGER NOT NULL REFERENCES ob_header(id) ON DELETE CASCADE,
    sheet_name  TEXT NOT NULL,
    row         INTEGER NOT NULL,
    col         INTEGER NOT NULL,
    value       TEXT,
    formula     TEXT,
    cell_type   TEXT   -- 'formula' | 'manual' | 'empty'
);

-- IE sheet type catalogue
CREATE TABLE IF NOT EXISTS sheet_types (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    type_key     TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    sort_order   INTEGER DEFAULT 99
);

-- IE sheet name → type mapping (raw Excel name → type_key)
CREATE TABLE IF NOT EXISTS sheet_name_map (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_name   TEXT NOT NULL UNIQUE,
    normalized TEXT NOT NULL,
    type_key   TEXT,
    FOREIGN KEY(type_key) REFERENCES sheet_types(type_key)
);

-- ART × sheet-type status matrix
CREATE TABLE IF NOT EXISTS art_sheet_status (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id  INTEGER NOT NULL REFERENCES ob_header(id) ON DELETE CASCADE,
    art        TEXT NOT NULL,
    sheet_type TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'has_data',  -- 'has_data' | 'missing' | 'na'
    UNIQUE(header_id, sheet_type)
);

-- ── 勾選分配系統 (Allocation Phase 1) ──────────────────────────────────────────
-- 勾選明細：一行 = 一個部件 × 一個後製工序（最小勾選單位）
CREATE TABLE IF NOT EXISTS allocation_item (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    header_id     INTEGER,
    art           TEXT,
    lean          TEXT,
    zone          TEXT,
    seq           INTEGER,
    process_name  TEXT,
    part_name     TEXT,
    post_process  TEXT,              -- 後製工序名（ATOM/LASER/打粗…），= zone
    theory_mp     REAL,              -- 理論MP = standard_time ÷ (3600÷eolr)
    target_unit   TEXT,              -- 目標外移單位
    is_checked    INTEGER DEFAULT 0, -- 0=留CSA, 1=外移
    checked_by    TEXT,
    checked_at    TEXT,
    confirmed_by  TEXT,
    confirmed_at  TEXT,
    month         TEXT,              -- 勾選月份快照（YYYY-MM）
    UNIQUE(header_id, art, zone, seq, process_name, part_name, month)
);

-- 勾選彙總（每月，每 LEAN×ART×段×單位 一筆）
CREATE TABLE IF NOT EXISTS allocation_summary (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    lean      TEXT,
    art       TEXT,
    segment   TEXT,
    unit      TEXT,
    total_mp  REAL,
    month     TEXT,
    confirmed INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_alloc_item_lookup ON allocation_item(month, target_unit, lean, art);
CREATE INDEX IF NOT EXISTS idx_alloc_item_header ON allocation_item(header_id);
CREATE INDEX IF NOT EXISTS idx_alloc_summary     ON allocation_summary(month, unit, lean, art);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ie_sheet_data_hdr  ON ie_sheet_data(header_id, sheet_name);
CREATE INDEX IF NOT EXISTS idx_ie_sheet_data_type ON ie_sheet_data(cell_type);
CREATE INDEX IF NOT EXISTS idx_sheet_name_map_raw ON sheet_name_map(raw_name);
CREATE INDEX IF NOT EXISTS idx_art_sheet_status_hdr ON art_sheet_status(header_id);
CREATE INDEX IF NOT EXISTS idx_art_sheet_status_art ON art_sheet_status(art);
CREATE INDEX IF NOT EXISTS idx_ob_articles_art    ON ob_articles(art);
CREATE INDEX IF NOT EXISTS idx_ob_articles_header ON ob_articles(header_id);
CREATE INDEX IF NOT EXISTS idx_ob_epph_header     ON ob_epph(header_id);
CREATE INDEX IF NOT EXISTS idx_ob_rows_header     ON ob_rows(header_id, sheet_key);
CREATE INDEX IF NOT EXISTS idx_change_log_key     ON change_log(table_name, record_key);
CREATE INDEX IF NOT EXISTS idx_ds02_art           ON ds02_fob(art);

-- DS-04: Monthly production schedule orders
CREATE TABLE IF NOT EXISTS ds04_orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    dept                TEXT NOT NULL,
    lean                TEXT NOT NULL,
    model_name          TEXT NOT NULL DEFAULT '',
    art                 TEXT NOT NULL DEFAULT '',
    order_no            TEXT NOT NULL DEFAULT '',
    qty                 INTEGER DEFAULT 0,
    delivery_date            TEXT DEFAULT '',
    is_outsource_upper       INTEGER DEFAULT 0,
    estimated_completion     TEXT DEFAULT '',
    created_at               TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ds04_dept   ON ds04_orders(dept);
CREATE INDEX IF NOT EXISTS idx_ds04_lean   ON ds04_orders(lean);
CREATE INDEX IF NOT EXISTS idx_ds04_art    ON ds04_orders(art);

-- EOLR per LEAN per month (for 廠務編制 calculation)
CREATE TABLE IF NOT EXISTS lean_eolr_settings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    lean        TEXT NOT NULL,
    month       TEXT NOT NULL,
    eolr        INTEGER NOT NULL DEFAULT 120,
    updated_by  TEXT DEFAULT '',
    updated_at  TEXT NOT NULL,
    UNIQUE(lean, month)
);
CREATE INDEX IF NOT EXISTS idx_lean_eolr ON lean_eolr_settings(lean, month);

-- DS-04 manual edit log
CREATE TABLE IF NOT EXISTS ds04_edit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    INTEGER,
    action      TEXT NOT NULL,
    field_name  TEXT DEFAULT '',
    old_value   TEXT DEFAULT '',
    new_value   TEXT DEFAULT '',
    user_name   TEXT DEFAULT '',
    created_at  TEXT NOT NULL
);

-- 廠務編制 manual fields (per lean per month)
CREATE TABLE IF NOT EXISTS bianche_manual (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    lean        TEXT NOT NULL,
    month       TEXT NOT NULL,
    manager_mp  REAL DEFAULT 0,
    headcount   REAL DEFAULT 0,
    updated_by  TEXT DEFAULT '',
    updated_at  TEXT NOT NULL,
    UNIQUE(lean, month)
);

-- DS-04 月份鎖定
CREATE TABLE IF NOT EXISTS ds04_lock (
    month       TEXT PRIMARY KEY,
    locked_at   TEXT NOT NULL,
    locked_by   TEXT DEFAULT ''
);

-- 廠務編制 per-model manual (CSA tab: 協理給/編制 per 鞋型 per LEAN)
CREATE TABLE IF NOT EXISTS bianche_model_manual (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    lean        TEXT NOT NULL,
    model_name  TEXT NOT NULL,
    month       TEXT NOT NULL,
    manager_mp  REAL DEFAULT 0,
    headcount   REAL DEFAULT 0,
    updated_by  TEXT DEFAULT '',
    updated_at  TEXT NOT NULL,
    UNIQUE(lean, model_name, month)
);

-- 廠務編制 OCS/RB/QC department group headcount
CREATE TABLE IF NOT EXISTS bianche_dept_hc (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    dept        TEXT NOT NULL,
    group_name  TEXT NOT NULL,
    shoe_detail TEXT DEFAULT '',
    month       TEXT NOT NULL,
    headcount   REAL DEFAULT 0,
    updated_by  TEXT DEFAULT '',
    updated_at  TEXT NOT NULL,
    UNIQUE(dept, group_name, month)
);

-- 勾選表月份確認鎖定
CREATE TABLE IF NOT EXISTS alloc_lock (
    month       TEXT PRIMARY KEY,
    locked_at   TEXT NOT NULL,
    locked_by   TEXT DEFAULT ''
);
