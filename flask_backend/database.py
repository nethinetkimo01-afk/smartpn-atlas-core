import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'atlas.db')
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
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    with open(SCHEMA_PATH, encoding='utf-8') as f:
        conn.executescript(f.read())
    # Seed default lookup if empty
    count = conn.execute('SELECT COUNT(*) FROM lookup_viet_zh').fetchone()[0]
    if count == 0:
        ts = now_iso()
        conn.executemany(
            'INSERT OR IGNORE INTO lookup_viet_zh (viet, zh, created_at) VALUES (?,?,?)',
            [(v, z, ts) for v, z in DEFAULT_LOOKUP.items()]
        )
    conn.commit()
    conn.close()

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
        existing = conn.execute(
            'SELECT id FROM ob_header WHERE art=? AND eolr=? AND run=?',
            (art, eolr, run)
        ).fetchone()

        if existing:
            header_id = existing['id']
            conn.execute(
                '''UPDATE ob_header SET season=?, model=?, material=?, category=?, updated_at=?
                   WHERE id=?''',
                (h.get('season',''), h.get('model',''), h.get('material',''),
                 h.get('category',''), ts, header_id)
            )
            conn.execute('DELETE FROM ob_rows WHERE header_id=?', (header_id,))
            conn.execute('DELETE FROM ob_epph  WHERE header_id=?', (header_id,))
        else:
            cur = conn.execute(
                '''INSERT INTO ob_header (art, season, model, material, category, eolr, run, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)''',
                (art, h.get('season',''), h.get('model',''), h.get('material',''),
                 h.get('category',''), eolr, run, ts, ts)
            )
            header_id = cur.lastrowid

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
        return {'ok': True, 'header_id': header_id}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def load_ob_record(art, eolr, run):
    conn = get_conn()
    try:
        row = conn.execute(
            'SELECT * FROM ob_header WHERE art=? AND eolr=? AND run=?',
            (art, int(eolr), int(run))
        ).fetchone()
        if not row:
            return {'ok': False, 'error': 'Record not found'}

        header_id = row['id']
        header = dict(row)

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
            '''SELECT art, season, model, eolr, run, updated_at
               FROM ob_header ORDER BY updated_at DESC'''
        ).fetchall()
        return {'ok': True, 'records': [dict(r) for r in rows]}
    finally:
        conn.close()


def delete_ob_record(art, eolr, run):
    conn = get_conn()
    try:
        conn.execute(
            'DELETE FROM ob_header WHERE art=? AND eolr=? AND run=?',
            (art, int(eolr), int(run))
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
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
