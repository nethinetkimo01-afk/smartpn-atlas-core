#!/usr/bin/env python3
"""
Re-apply the ob_header / ob_articles grouping rule to the CURRENT database.

Merge rule (same as migrate_ob_articles.py but without 'run'):
    (model_name, eolr, cutting, stitching, assembly, stock) identical
    → one ob_header row; all ARTs go into ob_articles.

Safe to run multiple times; each run starts from the live tables.

Run: python flask_backend/regroup_ob_articles.py
"""
import sqlite3, shutil, datetime, os
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'atlas.db')


def run():
    # ── Backup ──────────────────────────────────────────────────────────────
    ts  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = DB_PATH + f'.bak_regroup_{ts}'
    shutil.copy2(DB_PATH, bak)
    print(f'[regroup] Backed up → {bak}')

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = OFF')
    conn.execute('PRAGMA journal_mode = WAL')

    # ── Verify schema is already migrated ───────────────────────────────────
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    required = {'ob_header', 'ob_articles', 'ob_epph'}
    if not required.issubset(tables):
        print(f'[regroup] Missing tables: {required - tables}. Run migrate_ob_articles.py first.')
        conn.close()
        return

    cols = {r[1] for r in conn.execute('PRAGMA table_info(ob_header)').fetchall()}
    if 'art' in cols:
        print('[regroup] ob_header still has art column — run migrate_ob_articles.py first.')
        conn.close()
        return

    # ── Load current state ───────────────────────────────────────────────────
    before_hdr  = conn.execute('SELECT COUNT(*) FROM ob_header').fetchone()[0]
    before_epph = conn.execute('SELECT COUNT(*) FROM ob_epph').fetchone()[0]
    before_art  = conn.execute('SELECT COUNT(*) FROM ob_articles').fetchone()[0]
    before_rows = conn.execute('SELECT COUNT(*) FROM ob_rows').fetchone()[0]
    print(f'[regroup] BEFORE  ob_header={before_hdr}  ob_epph={before_epph}  '
          f'ob_articles={before_art}  ob_rows={before_rows}')

    hdrs = conn.execute('''
        SELECT h.id, h.model_name, h.eolr, h.run,
               h.season, h.material, h.category, h.created_at, h.updated_at,
               COALESCE(e.cutting,   0) cutting,
               COALESCE(e.stitching, 0) stitching,
               COALESCE(e.assembly,  0) assembly,
               COALESCE(e.stock,     0) stock,
               COALESCE(e.source, 'ie_file') source
        FROM ob_header h
        LEFT JOIN ob_epph e ON e.header_id = h.id
        ORDER BY h.id
    ''').fetchall()

    all_records = []
    for h in hdrs:
        d = dict(h)
        d['arts'] = [r['art'] for r in conn.execute(
            'SELECT art FROM ob_articles WHERE header_id=? ORDER BY id', (h['id'],)
        ).fetchall()]
        d['ob_rows'] = [dict(r) for r in conn.execute(
            'SELECT * FROM ob_rows WHERE header_id=? ORDER BY sheet_key, row_order', (h['id'],)
        ).fetchall()]
        all_records.append(d)

    # ── Group by (model_name, eolr, cutting, stitching, assembly, stock) ────
    groups = defaultdict(list)
    for rec in all_records:
        key = (
            rec['model_name'],
            rec['eolr'],
            round(float(rec['cutting']),   6),
            round(float(rec['stitching']), 6),
            round(float(rec['assembly']),  6),
            round(float(rec['stock']),     6),
        )
        groups[key].append(rec)

    merges = sum(1 for g in groups.values() if len(g) > 1)
    print(f'[regroup] Groups: {len(groups)}  '
          f'(merging {before_hdr - len(groups)} duplicate headers across {merges} groups)')

    # ── Build new tables ─────────────────────────────────────────────────────
    conn.executescript('''
        DROP TABLE IF EXISTS ob_header_ng;
        DROP TABLE IF EXISTS ob_epph_ng;
        DROP TABLE IF EXISTS ob_articles_ng;
        DROP TABLE IF EXISTS ob_rows_ng;

        CREATE TABLE ob_header_ng (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name  TEXT NOT NULL DEFAULT '',
            season      TEXT,
            material    TEXT,
            category    TEXT,
            eolr        INTEGER NOT NULL,
            run         INTEGER NOT NULL DEFAULT 1,
            created_at  TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
        CREATE TABLE ob_epph_ng (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            header_id INTEGER NOT NULL UNIQUE,
            cutting   REAL DEFAULT 0,
            stitching REAL DEFAULT 0,
            assembly  REAL DEFAULT 0,
            stock     REAL DEFAULT 0,
            source    TEXT DEFAULT 'ie_file'
        );
        CREATE TABLE ob_articles_ng (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            header_id INTEGER NOT NULL,
            art       TEXT NOT NULL,
            UNIQUE(art, header_id)
        );
        CREATE TABLE ob_rows_ng (
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
    ''')

    for key, recs in groups.items():
        model_name, eolr, cutting, stitching, assembly, stock = key
        first = recs[0]

        cur = conn.execute('''
            INSERT INTO ob_header_ng
              (model_name, season, material, category, eolr, run, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?)
        ''', (model_name, first['season'], first['material'], first['category'],
              eolr, first['run'], first['created_at'], first['updated_at']))
        new_id = cur.lastrowid

        conn.execute('''
            INSERT INTO ob_epph_ng (header_id, cutting, stitching, assembly, stock, source)
            VALUES (?,?,?,?,?,?)
        ''', (new_id, cutting, stitching, assembly, stock, first['source']))

        # Merge ARTs from all records in the group (dedup via INSERT OR IGNORE)
        seen_arts = set()
        for rec in recs:
            for art in rec['arts']:
                if art not in seen_arts:
                    conn.execute('INSERT OR IGNORE INTO ob_articles_ng (header_id, art) VALUES (?,?)',
                                 (new_id, art))
                    seen_arts.add(art)

        # Merge ob_rows from all records
        row_order = 0
        for rec in recs:
            for row in rec['ob_rows']:
                conn.execute('''
                    INSERT INTO ob_rows_ng
                      (header_id, sheet_key, row_order, part_viet, part_zh, mat_cat,
                       layers, qty_pr, knives, ct, allowance, st, ops,
                       marking, skiving, attaching, edge_paint, heat_press)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ''', (new_id, row['sheet_key'], row_order,
                      row['part_viet'], row['part_zh'], row['mat_cat'],
                      row['layers'], row['qty_pr'], row['knives'], row['ct'],
                      row['allowance'], row['st'], row['ops'],
                      row['marking'], row['skiving'], row['attaching'],
                      row['edge_paint'], row['heat_press']))
                row_order += 1

    # ── Swap tables ──────────────────────────────────────────────────────────
    conn.executescript('''
        DROP TABLE ob_epph;
        DROP TABLE ob_rows;
        DROP TABLE ob_articles;
        DROP TABLE ob_header;

        ALTER TABLE ob_header_ng   RENAME TO ob_header;
        ALTER TABLE ob_epph_ng     RENAME TO ob_epph;
        ALTER TABLE ob_articles_ng RENAME TO ob_articles;
        ALTER TABLE ob_rows_ng     RENAME TO ob_rows;

        CREATE INDEX IF NOT EXISTS idx_ob_articles_art    ON ob_articles(art);
        CREATE INDEX IF NOT EXISTS idx_ob_articles_header ON ob_articles(header_id);
        CREATE INDEX IF NOT EXISTS idx_ob_epph_header     ON ob_epph(header_id);
        CREATE INDEX IF NOT EXISTS idx_ob_rows_header     ON ob_rows(header_id, sheet_key);
    ''')

    conn.execute('PRAGMA foreign_keys = ON')
    conn.commit()

    # ── Verify ───────────────────────────────────────────────────────────────
    after_hdr  = conn.execute('SELECT COUNT(*) FROM ob_header').fetchone()[0]
    after_epph = conn.execute('SELECT COUNT(*) FROM ob_epph').fetchone()[0]
    after_art  = conn.execute('SELECT COUNT(*) FROM ob_articles').fetchone()[0]
    print(f'[regroup] AFTER   ob_header={after_hdr}  ob_epph={after_epph}  ob_articles={after_art}')
    print(f'[regroup] Merged {before_hdr - after_hdr} duplicate headers.')

    # GHOST SPRINT W verification
    ghost = conn.execute('''
        SELECT h.id, h.eolr, e.cutting, e.stitching, e.assembly, e.stock
        FROM ob_header h LEFT JOIN ob_epph e ON e.header_id=h.id
        WHERE h.model_name LIKE '%GHOST SPRINT%'
        ORDER BY h.eolr, h.id
    ''').fetchall()
    print(f'\n[regroup] GHOST SPRINT W: {len(ghost)} ob_header rows')
    for r in ghost:
        arts = [x[0] for x in conn.execute(
            'SELECT art FROM ob_articles WHERE header_id=?', (r['id'],)
        ).fetchall()]
        print(f'  id={r["id"]} eolr={r["eolr"]} '
              f'cut={r["cutting"]} stitch={r["stitching"]} '
              f'asm={r["assembly"]} sf={r["stock"]} | ARTs={arts}')

    conn.close()
    print('\n[regroup] Done.')


if __name__ == '__main__':
    run()
