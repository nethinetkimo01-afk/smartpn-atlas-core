#!/usr/bin/env python3
"""
One-time migration: ob_header (art, model) → ob_header (model_name) + ob_articles (art).

Groups records sharing (model, eolr, run, cutting, stitching, assembly, stock)
into a single ob_header row; all ARTs for the group go into ob_articles.

Run: python flask_backend/migrate_ob_articles.py
"""
import sqlite3, sys, os, shutil, datetime
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'atlas.db')

def run():
    # ── Backup ──────────────────────────────────────────────────────────────
    bak = DB_PATH + '.bak_premig_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy2(DB_PATH, bak)
    print(f'[migrate] Backed up → {bak}')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = OFF')

    # ── Before counts ────────────────────────────────────────────────────────
    before_hdr  = conn.execute('SELECT COUNT(*) FROM ob_header').fetchone()[0]
    before_epph = conn.execute('SELECT COUNT(*) FROM ob_epph').fetchone()[0]
    before_rows = conn.execute('SELECT COUNT(*) FROM ob_rows').fetchone()[0]
    print(f'[migrate] BEFORE  ob_header={before_hdr}  ob_epph={before_epph}  ob_rows={before_rows}')

    # ── Abort if ob_articles already exists ─────────────────────────────────
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    if 'ob_articles' in tables:
        print('[migrate] ob_articles already exists — migration already applied. Aborting.')
        conn.close()
        return

    # ── Check ob_header still has art column ────────────────────────────────
    cols = {r[1] for r in conn.execute('PRAGMA table_info(ob_header)').fetchall()}
    if 'art' not in cols:
        print('[migrate] ob_header.art already removed — schema already migrated. Aborting.')
        conn.close()
        return

    # ── Load all records ─────────────────────────────────────────────────────
    rows = conn.execute('''
        SELECT h.id, COALESCE(h.model,'') model, COALESCE(h.art,'') art,
               COALESCE(h.season,'') season, COALESCE(h.material,'') material,
               COALESCE(h.category,'') category, h.eolr, h.run,
               h.created_at, h.updated_at,
               COALESCE(e.cutting,0) cutting, COALESCE(e.stitching,0) stitching,
               COALESCE(e.assembly,0) assembly, COALESCE(e.stock,0) stock,
               COALESCE(e.source,'ie_file') source
        FROM ob_header h LEFT JOIN ob_epph e ON e.header_id = h.id
        ORDER BY h.id
    ''').fetchall()

    # ── Group by (model, eolr, run, MP) ─────────────────────────────────────
    groups = defaultdict(list)
    for r in rows:
        key = (r['model'], r['eolr'], r['run'],
               r['cutting'], r['stitching'], r['assembly'], r['stock'])
        groups[key].append(dict(r))

    print(f'[migrate] Groups: {len(groups)}  (merging {before_hdr - len(groups)} duplicate records)')

    # ── Create new tables ────────────────────────────────────────────────────
    conn.executescript('''
        CREATE TABLE ob_header_new (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name  TEXT NOT NULL,
            season      TEXT,
            material    TEXT,
            category    TEXT,
            eolr        INTEGER NOT NULL,
            run         INTEGER NOT NULL,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );

        CREATE TABLE ob_epph_new (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            header_id INTEGER NOT NULL UNIQUE,
            cutting   REAL DEFAULT 0,
            stitching REAL DEFAULT 0,
            assembly  REAL DEFAULT 0,
            stock     REAL DEFAULT 0,
            source    TEXT DEFAULT 'ie_file'
        );

        CREATE TABLE ob_articles (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            header_id INTEGER NOT NULL,
            art       TEXT NOT NULL,
            UNIQUE(art, header_id)
        );
    ''')

    # ── Migrate data ─────────────────────────────────────────────────────────
    for key, recs in groups.items():
        model_name, eolr, run, cutting, stitching, assembly, stock = key
        first = recs[0]

        cur = conn.execute('''
            INSERT INTO ob_header_new
              (model_name, season, material, category, eolr, run, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
        ''', (model_name, first['season'], first['material'], first['category'],
              eolr, run, first['created_at'], first['updated_at']))
        new_id = cur.lastrowid

        conn.execute('''
            INSERT INTO ob_epph_new (header_id, cutting, stitching, assembly, stock, source)
            VALUES (?,?,?,?,?,?)
        ''', (new_id, cutting, stitching, assembly, stock, first['source']))

        for r in recs:
            conn.execute('INSERT OR IGNORE INTO ob_articles (header_id, art) VALUES (?,?)',
                         (new_id, r['art']))

    # ── Swap tables ──────────────────────────────────────────────────────────
    conn.executescript('''
        DROP TABLE IF EXISTS ob_epph;
        DROP TABLE IF EXISTS ob_rows;
        DROP TABLE IF EXISTS ob_header;
        ALTER TABLE ob_header_new RENAME TO ob_header;
        ALTER TABLE ob_epph_new   RENAME TO ob_epph;

        CREATE TABLE ob_rows (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            header_id   INTEGER NOT NULL,
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

        CREATE INDEX IF NOT EXISTS idx_ob_articles_art    ON ob_articles(art);
        CREATE INDEX IF NOT EXISTS idx_ob_articles_header ON ob_articles(header_id);
        CREATE INDEX IF NOT EXISTS idx_ob_epph_header     ON ob_epph(header_id);
        CREATE INDEX IF NOT EXISTS idx_ob_rows_header     ON ob_rows(header_id, sheet_key);
        CREATE INDEX IF NOT EXISTS idx_change_log_key     ON change_log(table_name, record_key);
        CREATE INDEX IF NOT EXISTS idx_ds02_art           ON ds02_fob(art);
    ''')

    conn.execute('PRAGMA foreign_keys = ON')
    conn.commit()

    # ── After counts ─────────────────────────────────────────────────────────
    after_hdr      = conn.execute('SELECT COUNT(*) FROM ob_header').fetchone()[0]
    after_epph     = conn.execute('SELECT COUNT(*) FROM ob_epph').fetchone()[0]
    after_articles = conn.execute('SELECT COUNT(*) FROM ob_articles').fetchone()[0]
    conn.close()

    print(f'[migrate] AFTER   ob_header={after_hdr}  ob_epph={after_epph}  ob_articles={after_articles}')
    print(f'[migrate] Done. Merged {before_hdr - after_hdr} duplicate records.')

if __name__ == '__main__':
    run()
