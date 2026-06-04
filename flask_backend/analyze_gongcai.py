#!/usr/bin/env python3
"""
同材共裁明細自動生成腳本 (Tongcai Gongcai Detail Generator)

Generates 同材共裁 (same-material co-cutting) detail report for a DS-04 group.

Workflow:
  1. Parse DS-04 schedule → ART + order quantity for the requested group.
  2. For each ART, find the matching IE Excel file (by ART code in filename).
  3. Parse the IE Cutting sheet:
       - Find the column whose header contains "刀" (標准刀数).
       - Rows where that column value is NOT a number → machine-cut parts
         (ATOM / GCN / LASER / DK / YINGHIU …).
       - Extract: part name (col D) + layers (col E) + pieces (col F) + machine type.
  4. Build output rows:
       STT | LEAN | 鞋型 | ART | 訂單量 | 部件名稱 | 機器類型 | 層數 | 片數 | 勾選

Usage:
    python analyze_gongcai.py <schedule.xlsx> --group 加一A組 [--eolr 120]
    python analyze_gongcai.py <schedule.xlsx> --group 加一A組 --dry-run
"""
import sys, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

import database as db

# ── Config ────────────────────────────────────────────────────────────────────

IE_FOLDER_DEFAULT = r'C:\Users\user\OneDrive\Desktop\IE'

_ART_RE   = re.compile(r'[A-Z]{2}\d{4,6}')
_QTY_RE   = re.compile(r'--(\d+)\s*\(')

# Values that appear in the knife column meaning "machine cut" (not a plain number)
_MACHINE_KEYWORDS = {'ATOM', 'GCN', 'LASER', 'DK', 'YINGHIU', 'YINGHUI', 'AUTO'}


# ── IE file index ─────────────────────────────────────────────────────────────

def build_ie_index(ie_folder):
    """
    Scan ie_folder for *.xlsx files.
    Returns {ART_UPPER: [(filepath, eolr_or_None), ...]}
    Each file can carry multiple ARTs extracted from its filename.
    """
    index = {}
    for path in glob.glob(os.path.join(ie_folder, '*.xlsx')):
        fn = os.path.basename(path)
        if fn.startswith('~$'):
            continue
        arts = _ART_RE.findall(fn)
        eolr = None
        if '120' in fn and '双' in fn:
            eolr = 120
        elif '60' in fn and '双' in fn:
            eolr = 60
        for art in arts:
            index.setdefault(art.upper(), []).append((path, eolr))
    return index


def find_ie_file(art, eolr, ie_index):
    """Return best IE filepath for art+eolr, or None."""
    candidates = ie_index.get(art.upper(), [])
    if not candidates:
        return None
    for path, e in candidates:
        if e == eolr:
            return path
    return candidates[0][0]


# ── DS-04 schedule parsing ────────────────────────────────────────────────────

def _is_order_cell(val):
    s = str(val or '').strip()
    return bool(_ART_RE.search(s) and '--' in s)


def _parse_order_cell(val):
    """Return list of (art, qty) from one order-number cell."""
    s = str(val or '').strip()
    arts = _ART_RE.findall(s)
    m = _QTY_RE.search(s)
    qty = int(m.group(1)) if m else 0
    if not arts:
        return []
    per = qty // len(arts)
    rem = qty % len(arts)
    return [(a, per + (rem if i == 0 else 0)) for i, a in enumerate(arts)]


def extract_group_orders(wb, group_hint):
    """
    Find the sheet matching group_hint and extract {art: total_qty}.
    Returns (orders_dict, sheet_title_used).
    """
    gh = group_hint.strip().lower()
    ws = None
    for sheet in wb.worksheets:
        if gh in sheet.title.strip().lower():
            ws = sheet
            break
    if ws is None:
        ws = wb.worksheets[0]

    orders = {}
    for row in ws.iter_rows(values_only=True):
        for cell in row:
            if not _is_order_cell(cell):
                continue
            for art, qty in _parse_order_cell(cell):
                orders[art] = orders.get(art, 0) + qty

    return orders, getattr(ws, 'title', ws.title if ws else '')


# ── Cutting sheet parser ──────────────────────────────────────────────────────

def _find_knife_col(ws):
    """
    Scan first 20 rows for the column whose header contains '刀'.
    Returns 0-based column index, or None.
    """
    for row in ws.iter_rows(max_row=20, values_only=True):
        for ci, val in enumerate(row):
            if val is not None and '刀' in str(val):
                return ci
    return None


def _try_float(val):
    """Return float(val) or raise ValueError."""
    return float(str(val).strip())


def parse_cutting_gongcai(wb):
    """
    Parse the Cutting sheet in wb.
    Returns list of dicts for rows where the "刀" column value is NOT numeric
    (i.e. machine-cut rows for 同材共裁).

    Standard column layout (0-based index relative to knife_col at index 6):
      col 1 = material category (材料类别)
      col 2 = seq no (序号)
      col 3 = part name (部件名称)   ← D column
      col 4 = layers (层数)          ← E column
      col 5 = pieces/pair (片数)     ← F column
      col 6 = knife standard (刀)    ← detected column

    Relative to knife_col k:
      mat_cat  = k - 5
      stt_col  = k - 4
      part_col = k - 3
      lay_col  = k - 2
      pcs_col  = k - 1
    """
    ws = None
    for sh in wb.sheetnames:
        sl = sh.lower()
        if 'cutting' in sl or 'pha cắt' in sl or ('cat' in sl and 'concat' not in sl):
            ws = wb[sh]
            break
    if ws is None:
        return []

    k = _find_knife_col(ws)
    if k is None:
        return []

    mat_col  = k - 5
    stt_col  = k - 4
    part_col = k - 3
    lay_col  = k - 2
    pcs_col  = k - 1

    def _get(row, ci):
        if ci < 0 or ci >= len(row):
            return None
        return row[ci]

    result = []
    last_mat = ''

    for rn, row in enumerate(ws.iter_rows(values_only=True), 1):
        if rn < 12:
            continue
        if k >= len(row):
            continue
        knife_val = _get(row, k)
        if knife_val is None or str(knife_val).strip() in ('', '.'):
            continue

        s = str(knife_val).strip()

        # Update running material category
        mat_cell = _get(row, mat_col)
        if mat_cell and str(mat_cell).strip() not in ('', '.'):
            last_mat = str(mat_cell).strip()

        try:
            _try_float(s)
            continue  # numeric → normal cutting row, skip
        except ValueError:
            pass  # non-numeric → possible machine-cut row

        # Skip header cells (contain '刀' in their text = column header)
        if '刀' in s:
            continue

        part_raw = _get(row, part_col)
        lay_raw  = _get(row, lay_col)
        pcs_raw  = _get(row, pcs_col)
        stt_raw  = _get(row, stt_col)

        part_name = str(part_raw).strip() if part_raw is not None else ''
        machine   = s.upper()
        try:
            layers = float(lay_raw) if lay_raw is not None else None
        except (ValueError, TypeError):
            layers = None
        try:
            pieces = float(pcs_raw) if pcs_raw is not None else None
        except (ValueError, TypeError):
            pieces = None

        result.append({
            'stt_src': stt_raw,
            'part_name': part_name,
            'machine_type': machine,
            'layers': layers,
            'pieces': pieces,
            'mat_cat': last_mat,
        })

    return result


# ── DS-02 model name lookup ───────────────────────────────────────────────────

def _get_model_name(art):
    try:
        conn = db.get_conn()
        row = conn.execute(
            'SELECT model_name FROM ds02_fob WHERE art = ? LIMIT 1', (art,)
        ).fetchone()
        conn.close()
        return (row[0] or '').strip() if row else ''
    except Exception:
        return ''


# ── Main analyze ──────────────────────────────────────────────────────────────

def analyze(ds04_path, group, eolr=120, ie_folder=None):
    """
    Generate 同材共裁 detail for a DS-04 group.

    Args:
        ds04_path:  Path to the DS-04 schedule Excel file.
        group:      Group name (e.g. "加一A組") — matched against sheet titles.
        eolr:       Expected output rate (60 or 120) for IE file selection.
        ie_folder:  Folder containing IE Excel files (defaults to IE_FOLDER_DEFAULT).

    Returns dict:
        ok, group, eolr, sheet_used, total_arts, total_rows,
        missing_ie, rows
    """
    if not HAS_OPENPYXL:
        return {'ok': False, 'error': 'openpyxl not installed'}
    if not os.path.exists(ds04_path):
        return {'ok': False, 'error': f'DS-04 file not found: {ds04_path}'}

    _folder = ie_folder or IE_FOLDER_DEFAULT
    if not os.path.isdir(_folder):
        return {'ok': False, 'error': f'IE folder not found: {_folder}'}

    # ── Step 1: parse DS-04 schedule ──────────────────────────────────────
    try:
        wb04 = openpyxl.load_workbook(ds04_path, data_only=True, read_only=True)
    except Exception as e:
        return {'ok': False, 'error': f'Cannot open DS-04 file: {e}'}

    orders, sheet_used = extract_group_orders(wb04, group)
    wb04.close()

    if not orders:
        return {
            'ok': False,
            'error': f'No orders found for group "{group}"',
            'sheet_used': sheet_used,
        }

    # ── Step 2: build IE index ────────────────────────────────────────────
    ie_index = build_ie_index(_folder)

    # ── Step 3: parse each ART's IE Cutting sheet ─────────────────────────
    rows = []
    missing_ie = []
    stt = 1

    # Sort ARTs for deterministic output
    for art in sorted(orders):
        qty = orders[art]
        ie_path = find_ie_file(art, eolr, ie_index)

        if ie_path is None:
            missing_ie.append(art)
            continue

        model_name = _get_model_name(art)

        try:
            wb_ie = openpyxl.load_workbook(ie_path, data_only=True)
            parts = parse_cutting_gongcai(wb_ie)
            wb_ie.close()
        except Exception:
            missing_ie.append(art)
            continue

        for part in parts:
            rows.append({
                'stt':          stt,
                'lean':         '',
                'model_name':   model_name,
                'art':          art,
                'qty':          qty,
                'part_name':    part['part_name'],
                'machine_type': part['machine_type'],
                'layers':       part['layers'],
                'pieces':       part['pieces'],
                'checked':      '',
            })
            stt += 1

    return {
        'ok': True,
        'group': group,
        'eolr': eolr,
        'sheet_used': sheet_used,
        'total_arts': len(orders),
        'total_rows': len(rows),
        'missing_ie': missing_ie,
        'rows': rows,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse, json

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(description='同材共裁明細自動生成')
    parser.add_argument('file', help='DS-04 schedule Excel path')
    parser.add_argument('--group', required=True, help='Group name (e.g. 加一A組)')
    parser.add_argument('--eolr', type=int, default=120, help='EOLR (default 120)')
    parser.add_argument('--ie-folder', default=IE_FOLDER_DEFAULT,
                        help='IE Excel folder path')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print summary table, no DB writes')
    args = parser.parse_args()

    db.init_db()
    result = analyze(args.file, args.group, args.eolr, args.ie_folder)

    if not result.get('ok'):
        print(f"ERROR: {result.get('error')}")
        sys.exit(1)

    if args.dry_run:
        print(f"Group:      {result['group']}  EOLR={result['eolr']}")
        print(f"Sheet:      {result['sheet_used']}")
        print(f"ARTs:       {result['total_arts']}  |  Rows: {result['total_rows']}")
        if result['missing_ie']:
            print(f"Missing IE: {', '.join(result['missing_ie'])}")
        print()
        hdr = f"{'STT':>4}  {'ART':12}  {'QTY':>7}  {'Machine':10}  {'Lay':>4}  {'Pcs':>4}  Part Name"
        print(hdr)
        print('-' * len(hdr))
        for r in result['rows']:
            lay = str(int(r['layers'])) if r['layers'] is not None else '-'
            pcs = str(int(r['pieces'])) if r['pieces'] is not None else '-'
            print(f"{r['stt']:>4}  {r['art']:12}  {r['qty']:>7}  "
                  f"{r['machine_type']:10}  {lay:>4}  {pcs:>4}  {r['part_name'][:35]}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
