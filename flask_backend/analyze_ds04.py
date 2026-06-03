#!/usr/bin/env python3
"""
DS-04 Production Schedule Analyzer.

Reads a monthly production schedule Excel file and returns per-group analysis:
  Model Name + ART | Orders | Cutting LC | Stitching LC | Assembly LC |
  Cutting MP | Stitching MP | Forming MP

Order number format: MF2604KJ8322-03--900(5/29)
  ART       = alphanumeric code extracted after MF+date prefix, e.g. KJ8322
  Quantity  = number between '--' and '(' (summed for dual-ART orders)
  Deadline  = date inside parentheses

Usage:
    python analyze_ds04.py <schedule.xlsx> --dept <dept> --group <group>
    python analyze_ds04.py <schedule.xlsx> --dept <dept> --group <group> --eolr 120
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


# ── Order number parsing ──────────────────────────────────────────────────────

_ART_RE = re.compile(r'[A-Z]{2}\d{4,6}')
_QTY_RE = re.compile(r'--(\d+)\s*\(')
_DATE_RE = re.compile(r'\((\d+/\d+)\)')


def parse_order(cell_text):
    """
    Parse order number cell.
    Returns list of (art, qty, deadline) tuples (multi-ART cells yield multiple).
    """
    if not cell_text:
        return []
    s = str(cell_text).strip()
    arts = _ART_RE.findall(s)
    qty_match = _QTY_RE.search(s)
    date_match = _DATE_RE.search(s)
    qty = int(qty_match.group(1)) if qty_match else 0
    deadline = date_match.group(1) if date_match else ''
    if not arts:
        return []
    per_art = qty // len(arts) if arts else 0
    remainder = qty % len(arts) if arts else 0
    result = []
    for i, art in enumerate(arts):
        q = per_art + (1 if i == 0 and remainder else 0)
        result.append((art, q, deadline))
    return result


def is_order_cell(val):
    """Return True if cell looks like an order number."""
    s = str(val or '').strip()
    return bool(_ART_RE.search(s) and '--' in s)


# ── Sheet parser ───────────────────────────────────────────────────────────────

def find_sheet(wb, dept_hint, group_hint):
    """Find best matching worksheet for dept + group."""
    dh = dept_hint.lower().strip()
    gh = group_hint.lower().strip()
    # Try exact or partial match on sheet name
    for ws in wb.worksheets:
        name = ws.title.lower()
        if dh in name or gh in name:
            return ws
    # Fallback: first sheet
    return wb.worksheets[0] if wb.worksheets else None


def extract_orders(ws):
    """
    Scan all cells in worksheet for order number cells.
    Returns list of {'art': str, 'qty': int, 'deadline': str}.
    """
    orders = []
    seen = {}  # art → total qty
    for row in ws.iter_rows(values_only=True):
        for cell in row:
            if cell is None:
                continue
            entries = parse_order(cell)
            for art, qty, deadline in entries:
                if art not in seen:
                    seen[art] = {'art': art, 'qty': 0, 'deadline': deadline}
                seen[art]['qty'] += qty
    return list(seen.values())


# ── DB lookups ────────────────────────────────────────────────────────────────

def get_lc(art):
    """Return {'lc_cutting', 'lc_stitching', 'lc_assembly', 'lc_stockfitting', 'model_name'} from DS-02."""
    conn = db.get_conn()
    try:
        row = conn.execute(
            'SELECT model_name, lc_cutting, lc_stitching, lc_assembly, lc_stockfitting '
            'FROM ds02_fob WHERE art = ?', (art,)
        ).fetchone()
        if row:
            return {
                'model_name': row[0] or '',
                'lc_cutting': row[1],
                'lc_stitching': row[2],
                'lc_assembly': row[3],
                'lc_stockfitting': row[4],
            }
        return None
    finally:
        conn.close()


def get_mp(art, eolr=120):
    """Return {'cutting_mp', 'stitching_mp', 'assembly_mp'} from DS-03 ob_epph for given EOLR."""
    conn = db.get_conn()
    try:
        row = conn.execute(
            'SELECT h.id FROM ob_header h WHERE h.art = ? AND h.eolr = ? ORDER BY h.id DESC LIMIT 1',
            (art, eolr)
        ).fetchone()
        if not row:
            return None
        hid = row[0]
        # ob_epph stores per-section EP-PPH values; MP is stored in ob_header aggregates
        # or we can compute from ob_rows SUM of actual_ops per section
        # Use SUM_C2B aggregated MP from ob_rows
        mp = {}
        for section, key in [('cutting', 'cutting_mp'), ('stitching', 'stitching_mp'), ('assembly', 'assembly_mp')]:
            r = conn.execute(
                "SELECT SUM(actual_ops) FROM ob_rows WHERE header_id = ? AND sheet_type LIKE ?",
                (hid, f'%{section}%')
            ).fetchone()
            mp[key] = r[0] if r and r[0] is not None else None
        return mp if any(v is not None for v in mp.values()) else None
    finally:
        conn.close()


# ── Main analysis ─────────────────────────────────────────────────────────────

def analyze(file_path, dept, group, eolr=120):
    """
    Run DS-04 analysis on a schedule Excel file.
    Returns list of row dicts.
    """
    if not HAS_OPENPYXL:
        return {'ok': False, 'error': 'openpyxl not installed'}
    if not os.path.exists(file_path):
        return {'ok': False, 'error': f'File not found: {file_path}'}

    try:
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
    except Exception as e:
        return {'ok': False, 'error': f'Cannot open file: {e}'}

    ws = find_sheet(wb, dept, group)
    if ws is None:
        wb.close()
        return {'ok': False, 'error': f'No matching sheet for dept={dept} group={group}'}

    orders = extract_orders(ws)
    wb.close()

    # Build result rows, join DS-02 and DS-03
    rows = []
    no_ds02 = []
    no_ds03 = []
    lc_groups = {}  # key: (model_name, lc_cutting, lc_stitching, lc_assembly) → aggregated row

    for order in orders:
        art = order['art']
        qty = order['qty']
        deadline = order['deadline']

        lc = get_lc(art)
        mp = get_mp(art, eolr)

        if lc is None:
            no_ds02.append(art)
            model_name = ''
            lc_cutting = lc_stitching = lc_assembly = None
        else:
            model_name = lc['model_name']
            lc_cutting = lc['lc_cutting']
            lc_stitching = lc['lc_stitching']
            lc_assembly = lc['lc_assembly']

        if mp is None:
            no_ds03.append(art)
            cutting_mp = stitching_mp = assembly_mp = None
        else:
            cutting_mp = mp.get('cutting_mp')
            stitching_mp = mp.get('stitching_mp')
            assembly_mp = mp.get('assembly_mp')

        # Group by model_name + LC profile (merge rows with identical LC)
        gkey = (model_name, lc_cutting, lc_stitching, lc_assembly)
        if gkey in lc_groups:
            g = lc_groups[gkey]
            g['arts'].append(art)
            g['qty'] += qty
            g['deadlines'].append(deadline)
            # MP: take first non-None or flag as missing
            if cutting_mp is not None and g['cutting_mp'] is None:
                g['cutting_mp'] = cutting_mp
            if stitching_mp is not None and g['stitching_mp'] is None:
                g['stitching_mp'] = stitching_mp
            if assembly_mp is not None and g['assembly_mp'] is None:
                g['assembly_mp'] = assembly_mp
            if cutting_mp is None:
                g['mp_missing'] = True
        else:
            lc_groups[gkey] = {
                'model_name': model_name,
                'arts': [art],
                'qty': qty,
                'deadlines': [deadline],
                'lc_cutting': lc_cutting,
                'lc_stitching': lc_stitching,
                'lc_assembly': lc_assembly,
                'cutting_mp': cutting_mp,
                'stitching_mp': stitching_mp,
                'assembly_mp': assembly_mp,
                'mp_missing': mp is None,
                'lc_missing': lc is None,
            }

    rows = list(lc_groups.values())

    return {
        'ok': True,
        'dept': dept,
        'group': group,
        'eolr': eolr,
        'sheet_used': ws.title if ws else '',
        'total_arts': len(orders),
        'rows': rows,
        'no_ds02': no_ds02,   # ARTs missing in DS-02
        'no_ds03': no_ds03,   # ARTs missing in DS-03
    }


if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser(description='DS-04 Schedule Analyzer')
    parser.add_argument('file', help='Schedule Excel path')
    parser.add_argument('--dept', default='', help='Department name')
    parser.add_argument('--group', default='', help='Group name')
    parser.add_argument('--eolr', type=int, default=120, help='EOLR (default 120)')
    args = parser.parse_args()

    db.init_db()
    result = analyze(args.file, args.dept, args.group, args.eolr)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
