from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import database as db
import os
import tempfile
import json as _json

try:
    from analyze_ds04 import analyze as _ds04_analyze
    HAS_DS04 = True
except ImportError:
    HAS_DS04 = False

try:
    from analyze_ds05 import analyze as _ds05_analyze
    HAS_DS05 = True
except ImportError:
    HAS_DS05 = False

try:
    from analyze_gongcai import analyze as _gongcai_analyze
    HAS_GONGCAI = True
except ImportError:
    HAS_GONGCAI = False

try:
    import openpyxl
    HAS_XLSX = True
except ImportError:
    HAS_XLSX = False

# ── Excel column maps ────────────────────────────────────────────────────────

DS02_COL_MAP = {
    'article #':'art','article#':'art','article no':'art','article number':'art',
    'art':'art','art #':'art',
    'model #':'model_no','model#':'model_no','model no':'model_no','model name':'model_name',
    'silhouette number':'silhouette_no','silhouette no':'silhouette_no','sil. no':'silhouette_no',
    'factory':'factory','season':'season','category':'category',
    'lc total':'lc_total','lc_total':'lc_total',
    'lc ctb':'lc_ctb','lc_ctb':'lc_ctb','ctb':'lc_ctb',
    'cutting':'lc_cutting','lc cutting':'lc_cutting','lc_cutting':'lc_cutting',
    'stitching':'lc_stitching','lc stitching':'lc_stitching','lc_stitching':'lc_stitching',
    'stockfitting':'lc_stockfitting','lc stockfitting':'lc_stockfitting',
    'stock fitting':'lc_stockfitting','lc_stockfitting':'lc_stockfitting',
    'assembly':'lc_assembly','lc assembly':'lc_assembly','lc_assembly':'lc_assembly',
    'stage':'stage','valid from':'valid_from','valid_from':'valid_from',
}

DS01_COL_MAP = {
    'article id':'article_id','article #':'article_id','article no':'article_id',
    'article number':'article_id','article':'article_id','art':'article_id','art #':'article_id',
    'product type desc':'product_type_desc','product type description':'product_type_desc',
    'product type':'product_type_desc','type desc':'product_type_desc',
    'calendar month':'calendar_month','month':'calendar_month','cal. month':'calendar_month',
    'total':'quantity','quantity':'quantity','qty':'quantity','total qty':'quantity',
}


def _parse_excel(path, col_map, pk_field):
    if not HAS_XLSX:
        return None, 'openpyxl not installed — run: pip install openpyxl'
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    header_row_idx, headers = None, []
    for i, row in enumerate(ws.iter_rows(max_row=20, values_only=True)):
        cells = [str(c or '').strip().lower() for c in row]
        if sum(1 for c in cells if c in col_map) >= 2:
            header_row_idx = i + 1
            headers = [str(c or '').strip() for c in row]
            break
    if header_row_idx is None:
        return None, 'Cannot find header row (need ≥2 recognised column names)'
    col_to_field = {}
    unmapped = []
    for idx, h in enumerate(headers):
        key = h.lower().strip()
        if key in col_map:
            col_to_field[idx] = col_map[key]
        elif key:
            unmapped.append(h)
    if pk_field not in col_to_field.values():
        return None, f'Primary key column not found. Headers: {headers[:20]}'
    records = []
    for row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
        if not any(c is not None and str(c).strip() for c in row):
            continue
        rec, raw = {}, {}
        for idx, val in enumerate(row):
            hdr = headers[idx] if idx < len(headers) else f'col_{idx}'
            raw[hdr] = val
            if idx in col_to_field:
                rec[col_to_field[idx]] = val
        if not str(rec.get(pk_field, '') or '').strip():
            continue
        rec['raw_data'] = _json.dumps(raw, default=str)
        records.append(rec)
    return records, {'total': len(records), 'unmapped_cols': unmapped[:10]}

app = Flask(__name__, static_folder='..', static_url_path='')
CORS(app)

# ── Frontend ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('..', 'ds03_ob_interface.html')

@app.route('/ie')
def ie_interface():
    return send_from_directory('..', 'ie_interface.html')

@app.route('/ie/<int:header_id>')
def ie_detail(header_id):
    return send_from_directory('..', 'ie_detail.html')

# ── IE Interface API ─────────────────────────────────────────────────────────

@app.route('/api/ie/list', methods=['GET'])
def ie_list():
    return jsonify(db.list_ie_records())

@app.route('/api/ie/detail/<int:header_id>')
def ie_detail_api(header_id):
    return jsonify(db.get_ie_model_detail(header_id))

@app.route('/api/ie/update_mp', methods=['POST'])
def ie_update_mp():
    data = request.get_json(force=True)
    header_id = data.get('header_id')
    if not header_id:
        return jsonify({'ok': False, 'error': 'header_id required'}), 400
    return jsonify(db.update_ie_mp(
        int(header_id),
        data.get('cutting'), data.get('stitching'),
        data.get('assembly'), data.get('stock')
    ))

# ── DS-03 OB ─────────────────────────────────────────────────────────────────

@app.route('/api/ds03/save', methods=['POST'])
def save_ob():
    data = request.get_json(force=True)
    return jsonify(db.save_ob_record(data))

@app.route('/api/ds03/load', methods=['GET'])
def load_ob():
    art  = request.args.get('art', '')
    eolr = request.args.get('eolr', 60)
    run  = request.args.get('run', 1)
    if not art:
        return jsonify({'ok': False, 'error': 'art is required'}), 400
    return jsonify(db.load_ob_record(art, eolr, run))

@app.route('/api/ds03/list', methods=['GET'])
def list_ob():
    return jsonify(db.list_ob_records())

@app.route('/api/ds03/delete', methods=['DELETE'])
def delete_ob():
    art  = request.args.get('art', '')
    eolr = request.args.get('eolr', 60)
    run  = request.args.get('run', 1)
    return jsonify(db.delete_ob_record(art, eolr, run))

@app.route('/api/ds03/add_art', methods=['POST'])
def add_art():
    data = request.get_json(force=True)
    art = data.get('art', '').strip()
    header_id = data.get('header_id')
    if not art or not header_id:
        return jsonify({'ok': False, 'error': 'art and header_id required'}), 400
    return jsonify(db.add_art_to_header(art, int(header_id)))

# ── Lookup ────────────────────────────────────────────────────────────────────

@app.route('/api/lookup/all', methods=['GET'])
def get_lookup():
    return jsonify(db.get_all_lookup())

@app.route('/api/lookup/add', methods=['POST'])
def add_lookup():
    data = request.get_json(force=True)
    return jsonify(db.add_lookup_entry(data.get('viet',''), data.get('zh','')))

# ── DS-02 cross-table helper ─────────────────────────────────────────────────

@app.route('/api/ds02/epph', methods=['GET'])
def get_epph():
    art = request.args.get('art', '')
    if not art:
        return jsonify({'ok': False, 'error': 'art is required'}), 400
    return jsonify(db.get_epph_by_art(art))

# ── Import Admin ──────────────────────────────────────────────────────────────

@app.route('/admin')
def admin_page():
    return send_from_directory('..', 'import_admin.html')

@app.route('/api/stats', methods=['GET'])
def get_stats():
    return jsonify(db.get_db_stats())

@app.route('/api/ds02/upload', methods=['POST'])
def upload_ds02():
    if 'file' not in request.files:
        return jsonify({'ok': False, 'error': 'No file uploaded'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'ok': False, 'error': 'Empty filename'}), 400
    suffix = '.xlsx' if f.filename.lower().endswith('.xlsx') else '.xls'
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        f.save(tmp_path)
        records, info = _parse_excel(tmp_path, DS02_COL_MAP, 'art')
        if records is None:
            return jsonify({'ok': False, 'error': info})
        result = db.import_ds02_records(records)
        result['file_info'] = info
        return jsonify(result)
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route('/api/ds01/upload', methods=['POST'])
def upload_ds01():
    if 'file' not in request.files:
        return jsonify({'ok': False, 'error': 'No file uploaded'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'ok': False, 'error': 'Empty filename'}), 400
    suffix = '.xlsx' if f.filename.lower().endswith('.xlsx') else '.xls'
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        f.save(tmp_path)
        records, info = _parse_excel(tmp_path, DS01_COL_MAP, 'article_id')
        if records is None:
            return jsonify({'ok': False, 'error': info})
        result = db.import_ds01_records(records)
        result['file_info'] = info
        return jsonify(result)
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.route('/api/ds02/list', methods=['GET'])
def list_ds02():
    limit  = int(request.args.get('limit', 200))
    offset = int(request.args.get('offset', 0))
    return jsonify(db.list_ds02_records(limit, offset))

@app.route('/api/ds01/list', methods=['GET'])
def list_ds01():
    limit  = int(request.args.get('limit', 200))
    offset = int(request.args.get('offset', 0))
    return jsonify(db.list_ds01_records(limit, offset))

# ── DS-04 Schedule Analyzer ───────────────────────────────────────────────────

@app.route('/api/ds04/analyze', methods=['GET'])
def ds04_analyze():
    if not HAS_DS04:
        return jsonify({'ok': False, 'error': 'analyze_ds04 module not available'}), 500
    file_path = request.args.get('file', '').strip()
    dept      = request.args.get('dept', '').strip()
    group     = request.args.get('group', '').strip()
    try:
        eolr = int(request.args.get('eolr', 120))
    except ValueError:
        eolr = 120
    if not file_path:
        return jsonify({'ok': False, 'error': 'file parameter required'}), 400
    result = _ds04_analyze(file_path, dept, group, eolr)
    return jsonify(result)

# ── DS-05 大底課進度表 Analyzer ───────────────────────────────────────────────

@app.route('/api/ds05/analyze', methods=['GET'])
def ds05_analyze():
    if not HAS_DS05:
        return jsonify({'ok': False, 'error': 'analyze_ds05 module not available'}), 500
    file_path    = request.args.get('file', '').strip()
    group_filter = request.args.get('group', '').strip()
    if not file_path:
        return jsonify({'ok': False, 'error': 'file parameter required'}), 400
    result = _ds05_analyze(file_path, group_filter)
    return jsonify(result)

# ── 同材共裁 Analyzer ─────────────────────────────────────────────────────────

@app.route('/api/gongcai/analyze', methods=['GET'])
def gongcai_analyze():
    if not HAS_GONGCAI:
        return jsonify({'ok': False, 'error': 'analyze_gongcai module not available'}), 500
    file_path  = request.args.get('file', '').strip()
    group      = request.args.get('group', '').strip()
    ie_folder  = request.args.get('ie_folder', '').strip() or None
    try:
        eolr = int(request.args.get('eolr', 120))
    except ValueError:
        eolr = 120
    if not file_path:
        return jsonify({'ok': False, 'error': 'file parameter required'}), 400
    if not group:
        return jsonify({'ok': False, 'error': 'group parameter required'}), 400
    result = _gongcai_analyze(file_path, group, eolr, ie_folder)
    return jsonify(result)

# ── Result correction import ─────────────────────────────────────────────────

@app.route('/api/result/import_corrections', methods=['POST'])
def import_corrections():
    """
    Accept a corrected comparison_table.xlsx and write Jim's manual MP values
    to ob_epph (source='manual_correction').

    Expects multipart/form-data with file='comparison_table.xlsx'.
    Reads rows where 狀態 == 'MISMATCH' or 'MISSING_IE' and 結果表Cut/Stitch/Asm
    columns have values — those are Jim's corrected values.
    """
    if not HAS_XLSX:
        return jsonify({'ok': False, 'error': 'openpyxl not available'}), 500

    if 'file' not in request.files:
        return jsonify({'ok': False, 'error': 'file field required'}), 400

    f = request.files['file']
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        wb = openpyxl.load_workbook(tmp_path, data_only=True)
        ws = wb.active
        headers = [str(c.value or '').strip() for c in next(ws.iter_rows(max_row=1))]

        # Column indices (0-based after converting to list)
        def col(name):
            try: return headers.index(name)
            except ValueError: return None

        c_art    = col('ART')
        c_lean   = col('LEAN')
        c_qty    = col('訂單')
        c_status = col('狀態')
        c_rc     = col('結果表Cut')
        c_rs     = col('結果表Stitch')
        c_ra     = col('結果表Asm')

        if c_art is None:
            return jsonify({'ok': False, 'error': 'ART column not found'}), 400

        updated = []
        skipped = []

        conn = db.get_conn()
        ts = db.now_iso()

        for row in ws.iter_rows(min_row=2, values_only=True):
            art    = str(row[c_art] or '').strip() if c_art is not None else ''
            status = str(row[c_status] or '').strip() if c_status is not None else ''
            if not art or status == 'OK':
                continue

            def _fv(idx):
                if idx is None: return None
                v = row[idx]
                if v is None or str(v).strip() in ('', '-', 'None'): return None
                try: return float(v)
                except: return None

            ref_cut = _fv(c_rc)
            ref_s   = _fv(c_rs)
            ref_asm = _fv(c_ra)

            if ref_cut is None and ref_s is None and ref_asm is None:
                skipped.append(art)
                continue

            # Find or create ob_header for this ART via ob_articles (EOLR=120 default)
            h_row = conn.execute(
                '''SELECT a.header_id AS id FROM ob_articles a
                   WHERE a.art=? ORDER BY a.id DESC LIMIT 1''', (art,)
            ).fetchone()

            if h_row:
                header_id = h_row[0]
                e_row = conn.execute(
                    'SELECT id FROM ob_epph WHERE header_id=?', (header_id,)
                ).fetchone()
                if e_row:
                    fields = []
                    vals = []
                    if ref_cut is not None: fields.append('cutting=?');   vals.append(ref_cut)
                    if ref_s   is not None: fields.append('stitching=?'); vals.append(ref_s)
                    if ref_asm is not None: fields.append('assembly=?');  vals.append(ref_asm)
                    fields.append("source='manual_correction'")
                    conn.execute(
                        f'UPDATE ob_epph SET {",".join(fields)} WHERE header_id=?',
                        vals + [header_id]
                    )
                else:
                    conn.execute(
                        '''INSERT INTO ob_epph (header_id, cutting, stitching, assembly, stock, source)
                           VALUES (?,?,?,?,0,'manual_correction')''',
                        (header_id, ref_cut or 0, ref_s or 0, ref_asm or 0)
                    )
            else:
                cur = conn.execute(
                    '''INSERT INTO ob_header (model_name, season, material, category, eolr, run, created_at, updated_at)
                       VALUES ('', '', '', '', 120, 1, ?, ?)''', (ts, ts)
                )
                header_id = cur.lastrowid
                conn.execute(
                    'INSERT INTO ob_articles (header_id, art) VALUES (?,?)', (header_id, art)
                )
                conn.execute(
                    '''INSERT INTO ob_epph (header_id, cutting, stitching, assembly, stock, source)
                       VALUES (?,?,?,?,0,'manual_correction')''',
                    (header_id, ref_cut or 0, ref_s or 0, ref_asm or 0)
                )

            updated.append({'art': art, 'cut': ref_cut, 'stitch': ref_s, 'asm': ref_asm})

        conn.commit()
        conn.close()

        return jsonify({
            'ok': True,
            'updated': len(updated),
            'skipped': len(skipped),
            'rows': updated[:20],
        })

    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
    finally:
        try: os.unlink(tmp_path)
        except: pass


# ── Health check ─────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'ok': True, 'version': '1.5'})

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    db.init_db()
    print('Atlas Data System starting on http://0.0.0.0:5000')
    app.run(host='0.0.0.0', port=5000, debug=False)
