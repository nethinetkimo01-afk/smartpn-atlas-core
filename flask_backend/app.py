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

# ── Health check ─────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'ok': True, 'version': '1.3'})

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    db.init_db()
    print('Atlas Data System starting on http://0.0.0.0:5000')
    app.run(host='0.0.0.0', port=5000, debug=False)
