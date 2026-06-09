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
    # Migration: add source column to ob_epph if missing
    cols = [r[1] for r in conn.execute("PRAGMA table_info(ob_epph)").fetchall()]
    if 'source' not in cols:
        conn.execute("ALTER TABLE ob_epph ADD COLUMN source TEXT DEFAULT 'ie_file'")
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


def list_ie_records():
    """Return all ob_header rows with their ARTs and MP values for the IE interface."""
    conn = get_conn()
    try:
        rows = conn.execute('''
            SELECT h.id, h.model_name, h.eolr, h.season,
                   e.cutting, e.stitching, e.assembly, e.stock, e.source
            FROM ob_header h
            LEFT JOIN ob_epph e ON e.header_id = h.id
            ORDER BY h.model_name, h.eolr, h.id
        ''').fetchall()
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


def get_ie_model_detail(header_id):
    """Return all headers sharing the same model_name as header_id, with arts, epph, and ob_rows."""
    conn = get_conn()
    try:
        base = conn.execute('SELECT model_name FROM ob_header WHERE id=?', (header_id,)).fetchone()
        if not base:
            return {'ok': False, 'error': 'Header not found'}
        model_name = base['model_name']
        headers = conn.execute(
            'SELECT * FROM ob_header WHERE model_name=? ORDER BY eolr, id', (model_name,)
        ).fetchall()
        result = []
        for h in headers:
            hid = h['id']
            arts = [r['art'] for r in conn.execute(
                'SELECT art FROM ob_articles WHERE header_id=? ORDER BY id', (hid,)
            ).fetchall()]
            ep = conn.execute('SELECT * FROM ob_epph WHERE header_id=?', (hid,)).fetchone()
            sheets = {}
            for r in conn.execute(
                'SELECT * FROM ob_rows WHERE header_id=? ORDER BY sheet_key, row_order', (hid,)
            ).fetchall():
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
            result.append({
                'id':     hid,
                'eolr':   h['eolr'],
                'run':    h['run'],
                'season': h['season'] or '',
                'arts':   arts,
                'epph':   dict(ep) if ep else {},
                'sheets': sheets,
            })
        return {'ok': True, 'model_name': model_name, 'headers': result}
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
