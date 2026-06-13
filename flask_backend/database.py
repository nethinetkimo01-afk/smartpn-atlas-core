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
