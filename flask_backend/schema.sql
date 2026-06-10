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
    formula     TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ie_sheet_data_hdr  ON ie_sheet_data(header_id, sheet_name);
CREATE INDEX IF NOT EXISTS idx_ob_articles_art    ON ob_articles(art);
CREATE INDEX IF NOT EXISTS idx_ob_articles_header ON ob_articles(header_id);
CREATE INDEX IF NOT EXISTS idx_ob_epph_header     ON ob_epph(header_id);
CREATE INDEX IF NOT EXISTS idx_ob_rows_header     ON ob_rows(header_id, sheet_key);
CREATE INDEX IF NOT EXISTS idx_change_log_key     ON change_log(table_name, record_key);
CREATE INDEX IF NOT EXISTS idx_ds02_art           ON ds02_fob(art);
