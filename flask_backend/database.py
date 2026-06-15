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
            SELECT h.id, h.model_name, h.eolr, h.season, h.material,
                   e.cutting, e.stitching, e.assembly, e.stock, e.source
            FROM ob_header h
            LEFT JOIN ob_epph e ON e.header_id = h.id
            WHERE h.id = (
                SELECT id FROM ob_header
                WHERE model_name = h.model_name AND eolr = h.eolr
                ORDER BY created_at DESC LIMIT 1
            )
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
                'material':   r['material'] or '',
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


def get_ie_sheet_names(header_id):
    """Return ordered list of sheet names stored for this header."""
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT DISTINCT sheet_name FROM ie_sheet_data WHERE header_id=? ORDER BY MIN(id)',
            (header_id,)
        ).fetchall()
        return {'ok': True, 'sheets': [r['sheet_name'] for r in rows]}
    finally:
        conn.close()


def get_ie_matrix():
    """Return ART×Sheet matrix data for /ie/matrix page."""
    conn = get_conn()
    try:
        # Sheet types ordered
        type_rows = conn.execute(
            'SELECT type_key, display_name, sort_order FROM sheet_types ORDER BY sort_order'
        ).fetchall()
        if not type_rows:
            return {'ok': True, 'types': [], 'rows': [], 'no_data_arts': [], 'stats': {}}

        # ARTs whose header has NO ie_sheet_data at all
        no_ie_rows = conn.execute(
            '''SELECT a.art, h.model_name, h.eolr, h.id as header_id
               FROM ob_header h
               JOIN ob_articles a ON a.header_id=h.id
               WHERE h.id NOT IN (SELECT DISTINCT header_id FROM ie_sheet_data)
               ORDER BY a.art'''
        ).fetchall()
        no_data_arts = [{'art': r['art'], 'model': (r['model_name'] or '')[:40],
                          'eolr': r['eolr'], 'header_id': r['header_id']} for r in no_ie_rows]

        # Headers with data + their arts
        h_rows = conn.execute(
            '''SELECT DISTINCT a.header_id, a.art, h.model_name, h.eolr
               FROM ie_sheet_data sd
               JOIN ob_articles a ON a.header_id=sd.header_id
               JOIN ob_header h ON h.id=a.header_id
               ORDER BY a.art'''
        ).fetchall()

        # art_sheet_status
        status_rows = conn.execute(
            'SELECT header_id, art, sheet_type, status FROM art_sheet_status'
        ).fetchall()
        status_map = {}
        for sr in status_rows:
            status_map[(sr['header_id'], sr['art'], sr['sheet_type'])] = sr['status']

        types = [{'key': t['type_key'], 'display': t['display_name']} for t in type_rows]

        matrix_rows = []
        for hr in h_rows:
            hid = hr['header_id']
            art = hr['art']
            cells = []
            for t in type_rows:
                tk = t['type_key']
                st = status_map.get((hid, art, tk))
                cells.append({'status': st or 'na'})
            matrix_rows.append({
                'header_id': hid,
                'art': art,
                'model': (hr['model_name'] or '')[:40],
                'eolr': hr['eolr'],
                'cells': cells,
            })

        # Stats
        total_arts = conn.execute('SELECT COUNT(*) FROM ob_articles').fetchone()[0]
        gaps = sum(1 for r in matrix_rows for c in r['cells'] if c['status'] == 'missing')
        has_cnt = sum(1 for r in matrix_rows for c in r['cells'] if c['status'] == 'has_data')
        completion = round(has_cnt / (has_cnt + gaps) * 100, 1) if (has_cnt + gaps) > 0 else 0

        return {
            'ok': True,
            'types': types,
            'rows': matrix_rows,
            'no_data_arts': no_data_arts,
            'stats': {
                'total_arts': total_arts,
                'no_ie_count': len(no_data_arts),
                'gaps': gaps,
                'has_data': has_cnt,
                'completion_pct': completion,
            },
        }
    finally:
        conn.close()


def get_ie_sheet_grid(header_id, sheet_name):
    """Return all cells for one sheet as a 2-D dict {row: {col: {value, formula, cell_type}}}."""
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT row, col, value, formula, cell_type FROM ie_sheet_data WHERE header_id=? AND sheet_name=? ORDER BY row, col',
            (header_id, sheet_name)
        ).fetchall()
        grid = {}
        for r in rows:
            rk = r['row']
            if rk not in grid:
                grid[rk] = {}
            grid[rk][r['col']] = {'v': r['value'], 'f': r['formula'], 't': r['cell_type']}
        max_row = max(grid.keys()) if grid else 0
        max_col = max((max(cols.keys()) for cols in grid.values()), default=0)
        return {'ok': True, 'sheet_name': sheet_name, 'max_row': max_row, 'max_col': max_col, 'grid': grid}
    finally:
        conn.close()


def save_ie_sheet_data(header_id, sheet_rows):
    """Replace all ie_sheet_data for header_id with new rows.
    sheet_rows: list of (sheet_name, row, col, value, formula)
    """
    conn = get_conn()
    try:
        conn.execute('DELETE FROM ie_sheet_data WHERE header_id=?', (header_id,))
        conn.executemany(
            'INSERT INTO ie_sheet_data (header_id, sheet_name, row, col, value, formula) VALUES (?,?,?,?,?,?)',
            [(header_id,) + tuple(r) for r in sheet_rows]
        )
        conn.commit()
        return {'ok': True, 'rows_written': len(sheet_rows)}
    except Exception as e:
        conn.rollback()
        return {'ok': False, 'error': str(e)}
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
    """Return single header with arts, epph, and ie_sheet_data sheet name list."""
    conn = get_conn()
    try:
        h = conn.execute('SELECT * FROM ob_header WHERE id=?', (header_id,)).fetchone()
        if not h:
            return {'ok': False, 'error': 'Header not found'}
        arts = [r['art'] for r in conn.execute(
            'SELECT art FROM ob_articles WHERE header_id=? ORDER BY id', (header_id,)
        ).fetchall()]
        ep = conn.execute('SELECT * FROM ob_epph WHERE header_id=?', (header_id,)).fetchone()
        sheet_rows = conn.execute(
            'SELECT sheet_name FROM ie_sheet_data WHERE header_id=? GROUP BY sheet_name ORDER BY MIN(id)',
            (header_id,)
        ).fetchall()
        sheets = [r['sheet_name'] for r in sheet_rows]
        return {
            'ok': True,
            'header': {
                'id':         h['id'],
                'model_name': h['model_name'] or '',
                'season':     h['season'] or '',
                'eolr':       h['eolr'],
                'run':        h['run'],
                'material':   h['material'] or '',
                'category':   h['category'] or '',
                'arts':       arts,
                'epph':       dict(ep) if ep else {},
                'sheets':     sheets,
            }
        }
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


def get_ie_cutting_process(art=None, flag=None, limit=2000):
    conn = get_conn()
    try:
        where_parts = ["segment='cutting'"]
        params = []
        if art:
            where_parts.append("art=?")
            params.append(art)
        if flag:
            where_parts.append("flag=?")
            params.append(flag)
        where = ' AND '.join(where_parts)
        rows = conn.execute(
            f'''SELECT id, header_id, art, zone, seq, process_name, part_name,
                       tct, value_type, formula, source_sheet, source_row, flag
               FROM ie_process WHERE {where}
               ORDER BY art, source_row LIMIT ?''',
            params + [limit]).fetchall()
        # Stats
        stats_row = conn.execute(
            '''SELECT COUNT(*) as total,
                      COUNT(DISTINCT art) as arts,
                      SUM(CASE WHEN value_type='formula' THEN 1 ELSE 0 END) as formula_cnt,
                      SUM(CASE WHEN value_type='manual' THEN 1 ELSE 0 END) as manual_cnt,
                      SUM(CASE WHEN flag='待分區' THEN 1 ELSE 0 END) as pending_cnt,
                      SUM(CASE WHEN tct IS NOT NULL AND tct > 0 THEN 1 ELSE 0 END) as tct_cnt
               FROM ie_process WHERE segment='cutting' ''').fetchone()
        stats = dict(stats_row) if stats_row else {}
        return {
            'ok': True,
            'records': [dict(r) for r in rows],
            'stats': stats,
        }
    except Exception as e:
        return {'ok': False, 'error': str(e), 'records': [], 'stats': {}}
    finally:
        conn.close()


def get_ie_cutting_arts():
    conn = get_conn()
    try:
        rows = conn.execute(
            '''SELECT art, COUNT(*) as row_cnt,
                      SUM(CASE WHEN value_type='formula' THEN 1 ELSE 0 END) as formula_cnt,
                      SUM(CASE WHEN flag='待分區' THEN 1 ELSE 0 END) as pending_cnt,
                      SUM(CASE WHEN tct IS NOT NULL AND tct > 0 THEN 1 ELSE 0 END) as tct_cnt
               FROM ie_process WHERE segment='cutting'
               GROUP BY art ORDER BY art''').fetchall()
        return {'ok': True, 'arts': [dict(r) for r in rows]}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'arts': []}
    finally:
        conn.close()


def get_ie_process_by_header(header_id, segment='cutting'):
    conn = get_conn()
    try:
        rows = conn.execute(
            '''SELECT zone, seq, process_name, part_name, tct, value_type, formula, flag, source_sheet
               FROM ie_process
               WHERE header_id=? AND segment=?
               ORDER BY zone, seq, source_sheet, id''',
            (header_id, segment)).fetchall()
        zones = {}
        for r in rows:
            z = r['zone'] if not r['flag'] else '待分區'
            if z not in zones:
                zones[z] = []
            zones[z].append(dict(r))
        stats_row = conn.execute(
            '''SELECT COUNT(*) as total,
                      SUM(CASE WHEN value_type='formula' THEN 1 ELSE 0 END) as formula_cnt,
                      SUM(CASE WHEN value_type='manual'  THEN 1 ELSE 0 END) as manual_cnt,
                      SUM(CASE WHEN flag='待分區'        THEN 1 ELSE 0 END) as pending_cnt
               FROM ie_process WHERE header_id=? AND segment=?''',
            (header_id, segment)).fetchone()
        stats = dict(stats_row) if stats_row else {}
        return {'ok': True, 'segment': segment, 'zones': zones, 'stats': stats}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'zones': {}, 'stats': {}}
    finally:
        conn.close()


ZONE_ORDER = {
    'cutting':  ['裁斷機', 'ATOM', 'Laser', 'EMMA', 'YINGHUI', '移印', '轉印', '水蜘蛛', '_summary', '待分區'],
    'stitching':['主流', '支流', '電腦針車', '水蜘蛛', '待分區'],
    'assembly': ['成型', '成型UV', '水蜘蛛', '待分區'],
    'stf':      ['打粗', '照射', '水洗', '貼底', '水蜘蛛', '待分區'],
}
# Offline zones excluded from SUM C2B per-segment totals
OFFLINE_ZONES = {
    'cutting':   ['水蜘蛛'],
    'stitching': ['電腦針車', '水蜘蛛'],
    'assembly':  ['水蜘蛛', '成型UV'],
    'stf':       ['水蜘蛛'],
}


def get_ie_stages(header_id):
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT id, stage_name, created_at FROM ie_stage WHERE header_id=? ORDER BY id',
            (header_id,)
        ).fetchall()
        return {'ok': True, 'stages': [dict(r) for r in rows]}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def _calc_theory(standard_time, eolr):
    if standard_time is None:
        return None
    divisor = 3600.0 / eolr
    return round(standard_time / divisor, 4) if divisor else None


def get_ie_cell_data(header_id, segment='cutting', eolr=120):
    conn = get_conn()
    try:
        eolr = int(eolr)
        # Get latest stage
        stage_row = conn.execute(
            'SELECT id, stage_name FROM ie_stage WHERE header_id=? ORDER BY id DESC LIMIT 1',
            (header_id,)
        ).fetchone()
        stage = dict(stage_row) if stage_row else {'id': None, 'stage_name': '無'}

        rows = conn.execute('''
            SELECT id, zone, seq, process_name, part_name, flag,
                   normal_time, allowance_pct, standard_time, tct,
                   actual_operators, machine, cut_per_hour, qty_per_pair,
                   layers_per_cut, process_name_vi, process_name_zh, mat_cat,
                   post_marking_std, post_marking_ops,
                   post_skiving_std, post_skiving_ops,
                   post_attach_std, post_attach_ops,
                   post_edge_std, post_edge_ops,
                   post_heat_std, post_heat_ops,
                   value_type, is_locked, source_sheet
            FROM ie_process
            WHERE header_id=? AND segment=? AND (flag IS NULL OR flag != 'deleted')
            ORDER BY zone, seq ASC, id
        ''', (header_id, segment)).fetchall()

        # Also load process groups for this segment
        group_rows = conn.execute('''
            SELECT id, zone, process_ids, headcount, note
            FROM ie_process_group
            WHERE header_id=? AND segment=?
            ORDER BY id
        ''', (header_id, segment)).fetchall()
        # Build map: process_id -> (group_id, headcount)
        group_map = {}
        for gr in group_rows:
            import json as _json
            pids = _json.loads(gr['process_ids'])
            for pid in pids:
                group_map[pid] = {'group_id': gr['id'], 'headcount': gr['headcount'], 'note': gr['note']}

        zone_map = {}
        hand_total = 0.0

        for r in rows:
            z = r['zone']
            if not z:
                z = '待分區'

            rec = dict(r)
            # Recalculate theory from standard_time if not locked
            if r['is_locked']:
                rec['theory_operators'] = r['tct']  # fixed value
            else:
                rec['theory_operators'] = _calc_theory(r['standard_time'], eolr)

            # Attach group info if this process is grouped
            if r['id'] in group_map:
                rec['group_info'] = group_map[r['id']]
            else:
                rec['group_info'] = None

            if z not in zone_map:
                zone_map[z] = []
            zone_map[z].append(rec)

            # Accumulate hand total (non-裁斷機 + non-offline zones, non-summary)
            offline = OFFLINE_ZONES.get(segment, [])
            if segment == 'cutting' and z not in ('裁斷機', '_summary') and z not in offline and rec['theory_operators']:
                hand_total += rec['theory_operators']

        # Build ordered list of zones — always include 水蜘蛛 even if empty
        order = list(ZONE_ORDER.get(segment, []))
        seen = set(order)
        for z in zone_map:
            if z not in seen:
                order.append(z)

        zones = []
        for z in order:
            if z == '_summary':
                # Only include _summary if data rows exist for it
                if z in zone_map:
                    zones.append({'zone': z, 'rows': zone_map[z], 'always_show': False})
            elif z == '水蜘蛛':
                # Always show 水蜘蛛 section (even empty — + button available)
                zones.append({'zone': z, 'rows': zone_map.get(z, []), 'always_show': True})
            elif z in zone_map:
                zones.append({'zone': z, 'rows': zone_map[z], 'always_show': False})

        # Update _summary row theory_operators with computed hand_total
        for z_entry in zones:
            if z_entry['zone'] == '_summary':
                for row in z_entry['rows']:
                    row['theory_operators'] = round(hand_total, 4)

        return {
            'ok': True, 'header_id': header_id, 'segment': segment,
            'eolr': eolr, 'stage': stage, 'zones': zones,
            'hand_total': round(hand_total, 4),
        }
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def save_ie_edit(process_id, stage_id, field, value, user):
    conn = get_conn()
    try:
        old_row = conn.execute(
            f'SELECT {field} FROM ie_process WHERE id=?', (process_id,)
        ).fetchone()
        old_value = str(old_row[0]) if old_row and old_row[0] is not None else None
        conn.execute('''
            INSERT INTO ie_edit_log (process_id, stage_id, field, old_value, new_value, user, status)
            VALUES (?,?,?,?,?,?, 'pending')
        ''', (process_id, stage_id, field, old_value, str(value), user))
        conn.commit()
        log_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        return {'ok': True, 'log_id': log_id}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def approve_ie_edit(log_id, approver):
    conn = get_conn()
    try:
        log_row = conn.execute(
            'SELECT process_id, field, new_value FROM ie_edit_log WHERE id=? AND status=?',
            (log_id, 'pending')
        ).fetchone()
        if not log_row:
            return {'ok': False, 'error': 'log not found or already processed'}
        conn.execute(
            f'UPDATE ie_process SET {log_row["field"]}=? WHERE id=?',
            (log_row['new_value'], log_row['process_id'])
        )
        conn.execute(
            'UPDATE ie_edit_log SET status=?, user=? WHERE id=?',
            ('approved', approver, log_id)
        )
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def add_ie_process_row(header_id, segment, zone, process_name, standard_time, stage_id, user='demo', part_name=None, tct=None,
                       mat_cat=None, process_name_zh=None, cut_per_hour=None, qty_per_pair=None, layers_per_cut=None, actual_operators=None,
                       normal_time=None, allowance_pct=None):
    """Add a new process row and log the action."""
    conn = get_conn()
    try:
        # Look up art from existing rows for this header
        art_row = conn.execute(
            'SELECT art FROM ie_process WHERE header_id=? LIMIT 1', (header_id,)
        ).fetchone()
        art = art_row['art'] if art_row else str(header_id)
        # Find max seq in this zone
        max_seq = conn.execute(
            'SELECT MAX(seq) FROM ie_process WHERE header_id=? AND segment=? AND zone=?',
            (header_id, segment, zone)
        ).fetchone()[0] or 0
        conn.execute('''
            INSERT INTO ie_process (header_id, art, segment, zone, seq, process_name, part_name, tct, standard_time, flag,
                                    mat_cat, process_name_zh, cut_per_hour, qty_per_pair, layers_per_cut, actual_operators,
                                    normal_time, allowance_pct)
            VALUES (?,?,?,?,?,?,?,?,?, 'new',?,?,?,?,?,?,?,?)
        ''', (header_id, art, segment, zone, max_seq + 1, process_name, part_name, tct, standard_time,
              mat_cat, process_name_zh, cut_per_hour, qty_per_pair, layers_per_cut, actual_operators,
              normal_time, allowance_pct))
        conn.commit()
        new_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        # Log as edit
        conn.execute('''
            INSERT INTO ie_edit_log (process_id, stage_id, field, old_value, new_value, user, status)
            VALUES (?,?,'_add',NULL,?,?,'pending')
        ''', (new_id, stage_id, process_name, user))
        conn.commit()
        return {'ok': True, 'process_id': new_id}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def delete_ie_process_row(process_id, stage_id, user='demo'):
    """Soft-delete: mark flag='deleted' and log."""
    ALLOWED = {'actual_operators', 'standard_time', 'normal_time', 'cut_per_hour',
               'qty_per_pair', 'layers_per_cut', 'process_name', 'process_name_vi',
               'allowance_pct', 'flag', '_add', '_delete'}
    conn = get_conn()
    try:
        old_row = conn.execute(
            'SELECT process_name, flag FROM ie_process WHERE id=?', (process_id,)
        ).fetchone()
        if not old_row:
            return {'ok': False, 'error': 'row not found'}
        conn.execute("UPDATE ie_process SET flag='deleted' WHERE id=?", (process_id,))
        conn.execute('''
            INSERT INTO ie_edit_log (process_id, stage_id, field, old_value, new_value, user, status)
            VALUES (?,?,'_delete',?,'deleted',?,'pending')
        ''', (process_id, stage_id, old_row['process_name'], user))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def save_ie_process_group(header_id, segment, zone, stage_id, process_ids, headcount, note=''):
    """Save or update a process grouping."""
    import json as _json
    conn = get_conn()
    try:
        # Remove existing groups that overlap these process_ids
        existing = conn.execute(
            'SELECT id, process_ids FROM ie_process_group WHERE header_id=? AND segment=? AND zone=?',
            (header_id, segment, zone)
        ).fetchall()
        pid_set = set(int(p) for p in process_ids)
        for eg in existing:
            old_pids = set(_json.loads(eg['process_ids']))
            if old_pids & pid_set:
                conn.execute('DELETE FROM ie_process_group WHERE id=?', (eg['id'],))
        conn.execute('''
            INSERT INTO ie_process_group (header_id, segment, zone, stage_id, process_ids, headcount, note)
            VALUES (?,?,?,?,?,?,?)
        ''', (header_id, segment, zone, stage_id, _json.dumps([int(p) for p in process_ids]), headcount, note))
        conn.commit()
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_ie_process_groups(header_id, segment):
    """Return all groupings for a header/segment."""
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT id, zone, process_ids, headcount, note FROM ie_process_group WHERE header_id=? AND segment=?',
            (header_id, segment)
        ).fetchall()
        return {'ok': True, 'groups': [dict(r) for r in rows]}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def create_ie_stage(header_id, stage_name):
    conn = get_conn()
    try:
        conn.execute('INSERT INTO ie_stage (header_id, stage_name) VALUES (?,?)',
                     (header_id, stage_name))
        conn.commit()
        stage_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        return {'ok': True, 'stage_id': stage_id}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_ie_header_meta(header_id):
    conn = get_conn()
    try:
        r = conn.execute(
            'SELECT id, model_name, eolr, season, material FROM ob_header WHERE id=?',
            (header_id,)
        ).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()


def get_ie_sum(header_id, eolr=120):
    """SUM C2B: aggregate actual_operators (fallback to theory) per segment.
    Offline zones: 電腦針車 (stitching), 水蜘蛛 + 成型UV (assembly).
    All water spiders are stored in assembly/水蜘蛛 and excluded from totals.
    """
    eolr = int(eolr)
    target_output = eolr * 8  # pairs / 8-hour shift

    meta = get_ie_header_meta(header_id)
    if not meta:
        return {'ok': False, 'error': f'header {header_id} not found'}

    SEGMENTS = ['cutting', 'stitching', 'assembly', 'stf']
    OFFLINE_ZONES = {
        'stitching': ['電腦針車'],
        'assembly':  ['水蜘蛛', '成型UV'],  # WS = overhead; 成型UV = UV machine op
    }
    # Segments with comprehensive actual_operators data: use strict actual (NULL=0)
    # cutting uses theory fallback because formula rows rarely have actual filled
    STRICT_ACTUAL_SEGS = {'assembly', 'stitching', 'stf'}

    result = {'ok': True, 'header_id': header_id, 'eolr': eolr,
               'target_output': target_output, 'meta': meta}
    total_ops = 0.0
    offline_list = []
    seg_results = {}

    for seg in SEGMENTS:
        cell = get_ie_cell_data(header_id, seg, eolr)
        ops_sum = 0.0
        tct_sum = 0.0
        offline_zones = OFFLINE_ZONES.get(seg, [])
        strict = seg in STRICT_ACTUAL_SEGS

        for zone_entry in cell.get('zones', []):
            zname = zone_entry['zone']
            if zname == '_summary':
                continue
            zone_ops = 0.0
            zone_tct = 0.0
            for row in zone_entry['rows']:
                actual = row.get('actual_operators')
                theory = row.get('theory_operators')
                if seg == 'cutting':
                    # cutting：theory 優先（公式基準），水蜘蛛(theory=None) fallback actual
                    t = theory if theory is not None else (actual or 0.0)
                elif actual is not None:
                    t = actual           # assembly/stitching/stf：有 actual 就用
                else:
                    t = 0.0              # 嚴格模式：actual=NULL → 不計入
                zone_ops += t
                zone_tct += row.get('standard_time') or 0.0

            if zname in offline_zones:
                pph_z = round(target_output / zone_ops / 8, 3) if zone_ops else None
                offline_list.append({
                    'name': f'{seg}/{zname}', 'eolr': eolr,
                    'operators': round(zone_ops, 4),
                    'tct': round(zone_tct, 2),
                    'pph': pph_z,
                })
            else:
                ops_sum += zone_ops
                tct_sum += zone_tct

        pph = round(target_output / ops_sum / 8, 3) if ops_sum else None
        seg_results[seg] = {
            'operators': round(ops_sum, 4),
            'pph': pph,
            'tct_sum': round(tct_sum, 2),
        }
        total_ops += ops_sum

    result['cutting']   = seg_results['cutting']
    result['stitching'] = seg_results['stitching']
    result['assembly']  = seg_results['assembly']
    result['stf']       = seg_results['stf']
    result['total']     = {
        'operators': round(total_ops, 4),
        'pph': round(target_output / total_ops / 8, 3) if total_ops else None,
    }
    result['offline'] = offline_list
    return result


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


# ══════════════════════════════════════════════════════════════════════════════
# 勾選分配系統 (Allocation Phase 1)
# ══════════════════════════════════════════════════════════════════════════════

# 後製工序 zone → 外移單位
ZONE_TO_UNIT = {
    'ATOM': '同材共裁自動化', 'LASER': '同材共裁自動化', 'EMMA': '同材共裁自動化',
    '裁斷機': '同材共裁自動化', 'YINGHUI': '同材共裁自動化',
    '電腦針車': '電腦針車折邊', '折边': '電腦針車折邊',
    '打粗': '打粗水洗照射', '照射': '打粗水洗照射',
}
# 後製工序 zone → IE 段（用於 CSA MP 扣除歸段）
ZONE_TO_SEGMENT = {
    'ATOM': 'cutting', 'LASER': 'cutting', 'EMMA': 'cutting',
    '裁斷機': 'cutting', 'YINGHUI': 'cutting',
    '電腦針車': 'stitching', '折边': 'stitching',
    '打粗': 'stf', '照射': 'stf',
}
ALLOCATION_UNITS = ['同材共裁自動化', '電腦針車折邊', '打粗水洗照射']
TARGET_ZONES = ['ATOM', 'Laser', 'EMMA', '裁斷機', 'YINGHUI', '電腦針車', '折边', '打粗', '照射']

# 各外移單位顯示的 zone（同材共裁含裁斷機但不可切換外移）
UNIT_DISPLAY_ZONES = {
    '同材共裁自動化': ['ATOM', 'Laser', 'EMMA', 'YINGHUI', '裁斷機'],
    '電腦針車折邊':   ['電腦針車', '折边'],
    '打粗水洗照射':   ['打粗', '照射'],
}
ALL_DISPLAY_ZONES = [z for zones in UNIT_DISPLAY_ZONES.values() for z in zones]
NON_TOGGLEABLE_ZONES = frozenset(['裁斷機'])  # 主裁斷：永遠留CSA，前端不顯示勾選框


def _zone_unit(zone):
    return ZONE_TO_UNIT.get((zone or '').upper(), ZONE_TO_UNIT.get(zone or ''))

def _zone_segment(zone):
    return ZONE_TO_SEGMENT.get((zone or '').upper(), ZONE_TO_SEGMENT.get(zone or ''))


def _ensure_alloc_tables(conn):
    """Create allocation tables on any DB (works even when init_db never ran here)."""
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS allocation_item (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        header_id INTEGER, art TEXT, lean TEXT, zone TEXT, seq INTEGER,
        process_name TEXT, part_name TEXT, post_process TEXT,
        theory_mp REAL, target_unit TEXT,
        is_checked INTEGER DEFAULT 0,
        checked_by TEXT, checked_at TEXT, confirmed_by TEXT, confirmed_at TEXT,
        month TEXT,
        UNIQUE(header_id, art, zone, seq, process_name, part_name, month)
    );
    CREATE TABLE IF NOT EXISTS allocation_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lean TEXT, art TEXT, segment TEXT, unit TEXT, total_mp REAL, month TEXT, confirmed INTEGER DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_alloc_item_lookup ON allocation_item(month, target_unit, lean, art);
    CREATE INDEX IF NOT EXISTS idx_alloc_item_header ON allocation_item(header_id);
    ''')
    conn.commit()


def _art_order_qty(conn, art):
    """Defensive order-qty lookup (DS-04 ob_articles.ob_qty if present, else DS-01 quantity, else 0)."""
    try:
        cols = [r[1] for r in conn.execute('PRAGMA table_info(ob_articles)').fetchall()]
        if 'ob_qty' in cols:
            r = conn.execute('SELECT SUM(ob_qty) FROM ob_articles WHERE art=?', (art,)).fetchone()
            if r and r[0]:
                return float(r[0])
    except Exception:
        pass
    try:
        r = conn.execute('SELECT SUM(quantity) FROM ds01_sp WHERE article_id=?', (art,)).fetchone()
        if r and r[0]:
            return float(r[0])
    except Exception:
        pass
    return 0.0


def prefill_allocation(header_id=None, month=None):
    """Step 2: scan ie_process target zones → seed allocation_item rows.
    header_id=None → prefill every ob_header. Idempotent (INSERT OR IGNORE on unique key).
    """
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        month = month or now_iso()[:7]
        if header_id:
            hdr_ids = [header_id]
        else:
            hdr_ids = [r[0] for r in conn.execute('SELECT id FROM ob_header').fetchall()]

        inserted = 0
        for hid in hdr_ids:
            meta = conn.execute('SELECT eolr, lean FROM ob_header WHERE id=?', (hid,)).fetchone()
            if not meta:
                continue
            eolr = int(meta['eolr'] or 120)
            lean_val = meta['lean']
            divisor = 3600.0 / eolr
            arts = [r['art'] for r in conn.execute(
                'SELECT art FROM ob_articles WHERE header_id=? ORDER BY id', (hid,)).fetchall()]
            if not arts:
                arts = [None]
            try:
                rows = conn.execute('''
                    SELECT zone, seq, process_name, part_name, standard_time
                    FROM ie_process
                    WHERE header_id=? AND (flag IS NULL OR flag != 'deleted')
                      AND zone IN ({})
                    ORDER BY zone, seq, id
                '''.format(','.join('?' * len(TARGET_ZONES))),
                    [hid] + TARGET_ZONES).fetchall()
            except Exception:
                rows = []
            for art in arts:
                for r in rows:
                    zone = r['zone']
                    st = r['standard_time']
                    theory_mp = round(st / divisor, 4) if st else None
                    cur = conn.execute('''
                        INSERT OR IGNORE INTO allocation_item
                        (header_id, art, lean, zone, seq, process_name, part_name,
                         post_process, theory_mp, target_unit, is_checked, month)
                        VALUES (?,?,?,?,?,?,?,?,?,?,0,?)
                    ''', (hid, art, lean_val, zone, r['seq'], r['process_name'], r['part_name'],
                          zone, theory_mp, _zone_unit(zone), month))
                    inserted += cur.rowcount
        conn.commit()
        return {'ok': True, 'inserted': inserted, 'month': month, 'headers': len(hdr_ids)}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_allocation_items(month=None, unit=None, lean=None, art=None, header_id=None):
    """Step 3: return allocation items grouped by ART for the 勾選 grid."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        month = month or now_iso()[:7]
        where = ['month=?']
        params = [month]
        if unit:      where.append('target_unit=?'); params.append(unit)
        if lean:      where.append('lean=?');         params.append(lean)
        if art:       where.append('art=?');          params.append(art)
        if header_id: where.append('header_id=?');    params.append(header_id)
        rows = conn.execute(
            'SELECT * FROM allocation_item WHERE ' + ' AND '.join(where) +
            ' ORDER BY art, zone, seq, id', params).fetchall()

        groups = {}
        for r in rows:
            d = dict(r)
            a = d['art'] or '(無ART)'
            g = groups.setdefault(a, {'art': a, 'lean': d['lean'], 'items': [],
                                      'allocated_mp': 0.0, 'csa_mp': 0.0, 'total_mp': 0.0})
            g['items'].append(d)
            mp = d['theory_mp'] or 0.0
            g['total_mp'] += mp
            if d['is_checked']:
                g['allocated_mp'] += mp
            else:
                g['csa_mp'] += mp
        out = []
        for g in groups.values():
            g['allocated_mp'] = round(g['allocated_mp'], 4)
            g['csa_mp'] = round(g['csa_mp'], 4)
            g['total_mp'] = round(g['total_mp'], 4)
            out.append(g)
        out.sort(key=lambda x: x['art'])
        return {'ok': True, 'month': month, 'unit': unit, 'groups': out,
                'item_count': len(rows)}
    except Exception as e:
        return {'ok': False, 'error': str(e), 'groups': []}
    finally:
        conn.close()


def get_allocation_item(item_id):
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        r = conn.execute('SELECT * FROM allocation_item WHERE id=?', (item_id,)).fetchone()
        return dict(r) if r else None
    finally:
        conn.close()


def set_allocation_check(item_id, is_checked, user='demo'):
    """Toggle 外移/留CSA for one allocation item."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        conn.execute(
            'UPDATE allocation_item SET is_checked=?, checked_by=?, checked_at=? WHERE id=?',
            (1 if is_checked else 0, user, now_iso(), item_id))
        conn.commit()
        return {'ok': True, 'id': item_id, 'is_checked': 1 if is_checked else 0}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_allocation_leans(month=None):
    """Return all assigned LEANs from ob_header (month-independent)."""
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT DISTINCT lean FROM ob_header WHERE lean IS NOT NULL ORDER BY lean'
        ).fetchall()
        return {'ok': True, 'leans': [r[0] for r in rows]}
    finally:
        conn.close()


def _seg_ie_mp(conn, header_id, segment, divisor):
    try:
        r = conn.execute(
            "SELECT SUM(standard_time) FROM ie_process WHERE header_id=? AND segment=? "
            "AND (flag IS NULL OR flag != 'deleted')", (header_id, segment)).fetchone()
        s = r[0] if r else None
        return round((s or 0.0) / divisor, 4) if s else 0.0
    except Exception:
        return 0.0


def get_csa_mp(lean=None, art=None, eolr=120, month=None):
    """Step 4: per-segment IE / allocated / CSA MP for one ART."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        eolr = int(eolr)
        divisor = 3600.0 / eolr
        month = month or now_iso()[:7]
        hdr = conn.execute(
            'SELECT header_id FROM ob_articles WHERE art=? ORDER BY header_id DESC LIMIT 1',
            (art,)).fetchone()
        header_id = hdr['header_id'] if hdr else None

        SEGS = ['cutting', 'stitching', 'assembly', 'stf']
        out = {'ok': True, 'art': art, 'lean': lean, 'eolr': eolr, 'header_id': header_id}
        for seg in SEGS:
            ie_mp = _seg_ie_mp(conn, header_id, seg, divisor) if header_id else 0.0
            seg_zones = [z for z in TARGET_ZONES if _zone_segment(z) == seg]
            allocated = 0.0
            if seg_zones:
                ar = conn.execute(
                    'SELECT SUM(theory_mp) FROM allocation_item '
                    'WHERE art=? AND is_checked=1 AND month=? AND zone IN ({})'.format(
                        ','.join('?' * len(seg_zones))),
                    [art, month] + seg_zones).fetchone()
                allocated = round((ar[0] or 0.0), 4) if ar and ar[0] else 0.0
            out[f'{seg}_ie_mp'] = ie_mp
            out[f'{seg}_allocated_mp'] = allocated
            out[f'{seg}_csa_mp'] = round(ie_mp - allocated, 4)
        return out
    except Exception as e:
        return {'ok': False, 'error': str(e)}
    finally:
        conn.close()


def get_allocation_parts(month=None, unit=None, lean=None):
    """LEAN → model×ART → parts, filtered by unit display zones (excluding 裁斷機 from toggle)."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        month = month or now_iso()[:7]

        # Zone whitelist: filter by unit's display zones, not target_unit
        display_zones = UNIT_DISPLAY_ZONES.get(unit, ALL_DISPLAY_ZONES) if unit else ALL_DISPLAY_ZONES
        zone_ph = ','.join('?' * len(display_zones))

        where_clauses = ['ai.month=?', f'ai.zone IN ({zone_ph})']
        params_after = [month] + list(display_zones)
        if lean:
            where_clauses.append('ai.lean=?')
            params_after.append(lean)

        rows = conn.execute(f'''
            SELECT
                ai.id, ai.art, ai.lean, ai.zone, ai.seq,
                ai.process_name, ai.part_name,
                ai.theory_mp, ai.is_checked, ai.target_unit,
                ip.cut_per_hour, ip.layers_per_cut, ip.qty_per_pair, ip.standard_time,
                h.model_name, h.eolr,
                COALESCE(s.qty, 0) AS order_qty
            FROM allocation_item ai
            LEFT JOIN (
                SELECT header_id, zone, seq,
                       MAX(cut_per_hour) AS cut_per_hour,
                       MAX(layers_per_cut) AS layers_per_cut,
                       MAX(qty_per_pair) AS qty_per_pair,
                       MAX(standard_time) AS standard_time
                FROM ie_process
                WHERE flag IS NULL OR flag != 'deleted'
                GROUP BY header_id, zone, seq
            ) ip ON ip.header_id=ai.header_id AND ip.zone=ai.zone AND ip.seq=ai.seq
            LEFT JOIN ob_header h ON h.id=ai.header_id
            LEFT JOIN (
                SELECT article_id, SUM(quantity) AS qty
                FROM ds01_sp GROUP BY article_id
            ) s ON s.article_id=ai.art
            WHERE {" AND ".join(where_clauses)}
            ORDER BY
                CASE WHEN ai.lean IS NULL THEN 1 ELSE 0 END,
                ai.lean, h.model_name, ai.art,
                CASE ai.zone WHEN '裁斷機' THEN 1 ELSE 0 END,
                ai.zone, ai.seq, ai.id
        ''', params_after).fetchall()

        lean_groups = {}
        lean_order = []

        for r in rows:
            d = dict(r)
            lk = d.get('lean') or None
            label = lk if lk else '—'
            if label not in lean_groups:
                lean_groups[label] = {
                    'lean': lk,
                    'allocated_mp': 0.0, 'csa_mp': 0.0, 'ie_mp': 0.0,
                    '_models': {}
                }
                lean_order.append(label)

            lg = lean_groups[label]
            model_raw = d.get('model_name') or ''
            model = model_raw.split('Target Output')[0].strip()
            art = d.get('art') or '(無ART)'
            mk = f'{art}||{model}'

            if mk not in lg['_models']:
                lg['_models'][mk] = {
                    'model_name': model,
                    'art': art,
                    'eolr': d.get('eolr') or 120,
                    'order_qty': float(d.get('order_qty') or 0),
                    'allocated_mp': 0.0, 'csa_mp': 0.0, 'ie_mp': 0.0,
                    'items': []
                }

            mg = lg['_models'][mk]
            mp = float(d.get('theory_mp') or 0.0)
            zone = d.get('zone') or ''
            is_csa_locked = zone in NON_TOGGLEABLE_ZONES
            is_checked = 0 if is_csa_locked else (1 if d.get('is_checked') else 0)
            ct = d.get('standard_time')
            qty_pp = d.get('qty_per_pair')
            order_qty = float(d.get('order_qty') or 0)

            mg['ie_mp'] += mp
            lg['ie_mp'] += mp
            if is_checked and not is_csa_locked:
                mg['allocated_mp'] += mp
                lg['allocated_mp'] += mp
            else:
                mg['csa_mp'] += mp
                lg['csa_mp'] += mp

            mg['items'].append({
                'id': d['id'],
                'seq': d['seq'],
                'zone': zone,
                'part_name': d.get('process_name') or d.get('part_name') or '',
                'cut_per_hour': d.get('cut_per_hour'),
                'layers': d.get('layers_per_cut'),
                'qty_per_pair': qty_pp,
                'total_pieces': round(order_qty * float(qty_pp)) if qty_pp and order_qty else None,
                'ct_sec': round(float(ct), 3) if ct else None,
                'output': round(3600.0 / float(ct), 1) if ct else None,
                'theory_mp': round(mp, 4),
                'is_checked': is_checked,
                'is_csa_locked': is_csa_locked,
                'target_unit': d.get('target_unit'),
            })

        out = []
        for lk in lean_order:
            lg = lean_groups[lk]
            models_list = []
            for mg in lg.pop('_models').values():
                mg['allocated_mp'] = round(mg['allocated_mp'], 4)
                mg['csa_mp'] = round(mg['csa_mp'], 4)
                mg['ie_mp'] = round(mg['ie_mp'], 4)
                models_list.append(mg)
            lg['models'] = models_list
            lg['allocated_mp'] = round(lg['allocated_mp'], 4)
            lg['csa_mp'] = round(lg['csa_mp'], 4)
            lg['ie_mp'] = round(lg['ie_mp'], 4)
            out.append(lg)

        return {'ok': True, 'month': month, 'unit': unit, 'leans': out}
    except Exception as e:
        import traceback
        return {'ok': False, 'error': str(e), 'trace': traceback.format_exc(), 'leans': []}
    finally:
        conn.close()


def get_allocation_export_rows(unit, month=None):
    """Step 5: rows for a unit's reference xlsx (checked items only)."""
    conn = get_conn()
    try:
        _ensure_alloc_tables(conn)
        month = month or now_iso()[:7]
        rows = conn.execute('''
            SELECT ai.lean, ai.art, ai.part_name, ai.zone AS process, ai.theory_mp,
                   ip.standard_time AS tct
            FROM allocation_item ai
            LEFT JOIN ie_process ip
              ON ip.header_id=ai.header_id AND ip.zone=ai.zone AND ip.seq=ai.seq
             AND ip.process_name=ai.process_name
            WHERE ai.target_unit=? AND ai.month=? AND ai.is_checked=1
            ORDER BY ai.lean, ai.art, ai.zone, ai.seq
        ''', (unit, month)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d['order_qty'] = _art_order_qty(conn, d['art']) if d['art'] else 0.0
            tct = d.get('tct') or 0.0
            # 打粗水洗：需求人力 = 訂單 ÷ (3600 ÷ TCT) ÷ 222
            d['headcount'] = round(d['order_qty'] / (3600.0 / tct) / 222.0, 4) if tct else None
            out.append(d)
        return {'ok': True, 'unit': unit, 'month': month, 'rows': out}
    finally:
        conn.close()
