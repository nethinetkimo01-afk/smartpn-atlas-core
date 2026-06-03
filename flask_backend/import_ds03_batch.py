#!/usr/bin/env python3
"""
DS-03 OB Batch Importer.
Processes a folder of historical OB Excel files:
  1. Extracts Vietnamese→Chinese part name pairs → adds to lookup_viet_zh table
  2. Extracts header info (ART, Season, EOLR) and imports skeleton OB records

Usage:
    python import_ds03_batch.py <folder>
    python import_ds03_batch.py <folder> --dry-run
    python import_ds03_batch.py <folder> --lookup-only
    python import_ds03_batch.py <folder> --dry-run --lookup-only
"""
import sys, os, glob, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

# ── Language detection ────────────────────────────────────────────────────────

VIET_CHARS = set(
    'ăâđêôơưắặấầẩẫẻẽẹếềểễệịỉĩọỏõốồổỗộớờởỡợụủũứừửữựỳỵỷỹ'
    'àáãèéìíòóùúýắặấầẩẫẻẽẹếềểễệịỉĩọỏõốồổỗộớờởỡợụủũứừửữựỳỵỷỹ'
)

def has_viet(text):
    return any(c in VIET_CHARS for c in str(text or '').lower())

def has_chinese(text):
    return any('一' <= c <= '鿿' for c in str(text or ''))

# ── Sheet-to-department mapping ───────────────────────────────────────────────

DEPT_PATTERNS = {
    'cutting':     ['cutting', 'cắt', 'cat '],
    'atom':        ['atom', 'tự động', 'automat'],
    'tongcai':     ['tongcai', '同材', 'tong cai', 'dong'],
    'diannao':     ['diannao', '电脑', 'dian nao', 'computer', 'needle'],
    'stitch-zhi':  ['支流', 'zhi liu', 'tributary'],
    'stitch-zhu':  ['主流', 'zhu liu', 'main flow'],
    'assembly1':   ['assembly 1', 'lắp ráp 1', 'assembly1', 'ráp 1'],
    'assembly2':   ['assembly 2', 'lắp ráp 2', 'assembly2', 'ráp 2'],
    'dacui':       ['打粗', 'da cui', 'rough'],
    'xishi':       ['水洗', 'xi shi', 'wash'],
    'tiedadi':     ['贴大底', 'tie da di', 'sole attach'],
    'zhaoshe':     ['照射', 'zhao she', 'irradiat'],
    'chenxing':    ['成型', 'chen xing', 'mold'],
}

HEADER_KEYS = {
    'art':      ['art', 'article', 'article #', 'article no', 'article number'],
    'season':   ['season'],
    'model':    ['model', 'model name', 'model no', 'model #'],
    'material': ['material', 'upper material', 'vật liệu'],
    'category': ['category', 'loại', 'cat'],
    'eolr':     ['eolr', 'production rate', 'output rate', 'output/h'],
}


def match_dept(sheet_name):
    name = sheet_name.lower().strip()
    # Check for Stitching generically (both zhi and zhu)
    if 'stitch' in name or 'may' in name or '针车' in name or '縫' in name:
        if any(x in name for x in ['支', 'tributary', 'sub', '1', 'zhi']):
            return 'stitch-zhi'
        return 'stitch-zhu'
    for key, patterns in DEPT_PATTERNS.items():
        if any(p.lower() in name for p in patterns):
            return key
    return None


def extract_header(ws):
    """Scan first 15 rows for key-value header info."""
    header = {}
    rows = list(ws.iter_rows(max_row=15, values_only=True))
    for row in rows:
        for i, cell in enumerate(row):
            if cell is None:
                continue
            cell_s = str(cell).strip().lower()
            for field, patterns in HEADER_KEYS.items():
                if field in header:
                    continue
                if any(p in cell_s for p in patterns):
                    # Value is next non-empty cell in same row
                    for j in range(i + 1, len(row)):
                        if row[j] is not None and str(row[j]).strip():
                            header[field] = str(row[j]).strip()
                            break
    return header


def extract_viet_zh(ws):
    """Return dict of viet_lower → zh from adjacent Viet+Chinese cell pairs."""
    pairs = {}
    for row in ws.iter_rows(values_only=True):
        vals = [str(v).strip() if v is not None else '' for v in row]
        for i in range(len(vals) - 1):
            v1, v2 = vals[i], vals[i + 1]
            if len(v1) < 2 or len(v2) < 2:
                continue
            if has_viet(v1) and has_chinese(v2) and not has_chinese(v1):
                pairs[v1.lower()] = v2
            elif has_chinese(v1) and has_viet(v2) and not has_chinese(v2):
                pairs[v2.lower()] = v1
    return pairs


def process_file(path, dry_run=False, lookup_only=False):
    if not HAS_OPENPYXL:
        return {'ok': False, 'error': 'openpyxl not installed'}
    try:
        wb = openpyxl.load_workbook(path, data_only=True)
    except Exception as e:
        return {'ok': False, 'error': f'Cannot open: {e}'}

    result = {
        'file': os.path.basename(path),
        'lookup_pairs': {},
        'header': {},
        'depts': [],
        'ok': True,
    }

    # Collect Viet-Chinese pairs from all sheets
    for ws in wb.worksheets:
        result['lookup_pairs'].update(extract_viet_zh(ws))

    # Header from first sheet
    if wb.worksheets:
        result['header'] = extract_header(wb.worksheets[0])

    # Identify department sheets
    for ws in wb.worksheets:
        dept = match_dept(ws.title)
        if dept:
            result['depts'].append({'sheet': ws.title, 'dept': dept})

    if not dry_run:
        # Save lookup pairs
        if result['lookup_pairs']:
            conn = db.get_conn()
            ts = db.now_iso()
            try:
                for viet, zh in result['lookup_pairs'].items():
                    conn.execute(
                        'INSERT INTO lookup_viet_zh (viet, zh, created_at) VALUES (?,?,?) '
                        'ON CONFLICT(viet) DO UPDATE SET zh=excluded.zh',
                        (viet, zh, ts))
                conn.commit()
            finally:
                conn.close()

        # Import OB skeleton if header has ART and not lookup-only
        if not lookup_only:
            h = result['header']
            art = str(h.get('art', '')).strip()
            if art:
                try:
                    eolr = int(float(str(h.get('eolr', 60)).strip()))
                except (ValueError, TypeError):
                    eolr = 60
                ob_data = {
                    'header': {
                        'art': art, 'season': h.get('season', ''),
                        'model': h.get('model', ''), 'material': h.get('material', ''),
                        'category': h.get('category', ''), 'eolr': eolr, 'run': 1
                    },
                    'epph':   {'cutting': 0, 'stitching': 0, 'assembly': 0, 'stock': 0},
                    'sheets': {}
                }
                result['ob_save'] = db.save_ob_record(ob_data)

    return result


def batch_process(folder, dry_run=False, lookup_only=False):
    files = glob.glob(os.path.join(folder, '**', '*.xlsx'), recursive=True)
    files += glob.glob(os.path.join(folder, '**', '*.xls'), recursive=True)
    files = [f for f in files if not os.path.basename(f).startswith('~$')]  # skip temp files

    if not files:
        print(f'No Excel files found in: {folder}')
        return

    print(f'Found {len(files)} Excel file(s)')
    if dry_run:
        print('DRY RUN — no data written to DB\n')

    all_pairs = {}
    ok_count = 0
    err_count = 0

    for path in files:
        rel = os.path.relpath(path, folder)
        print(f'Processing: {rel}')
        r = process_file(path, dry_run=dry_run, lookup_only=lookup_only)

        if not r['ok']:
            print(f'  ERROR: {r["error"]}')
            err_count += 1
            continue

        ok_count += 1
        pairs = r.get('lookup_pairs', {})
        all_pairs.update(pairs)

        if pairs:
            print(f'  Lookup pairs: {len(pairs)}')
            for v, z in list(pairs.items())[:3]:
                print(f'    {v} → {z}')
            if len(pairs) > 3:
                print(f'    ... +{len(pairs) - 3} more')

        h = r.get('header', {})
        if h:
            art_disp = h.get('art', '?')
            print(f'  Header: ART={art_disp} | Season={h.get("season","?")} | EOLR={h.get("eolr","?")}')

        depts = r.get('depts', [])
        if depts:
            print(f'  Dept sheets: {", ".join(d["dept"] for d in depts)}')

        ob = r.get('ob_save', {})
        if ob and not ob.get('ok'):
            print(f'  OB save warning: {ob.get("error")}')

    print(f'\n{"=" * 50}')
    print(f'Done: {ok_count} files OK, {err_count} errors')
    print(f'Total unique lookup pairs: {len(all_pairs)}')
    if dry_run:
        print('(DRY RUN — nothing saved)')


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f'Not a directory: {folder}')
        sys.exit(1)

    dry_run     = '--dry-run' in sys.argv
    lookup_only = '--lookup-only' in sys.argv

    if not dry_run:
        db.init_db()

    batch_process(folder, dry_run=dry_run, lookup_only=lookup_only)
