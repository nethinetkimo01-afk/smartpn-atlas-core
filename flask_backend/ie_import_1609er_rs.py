"""
IE Import — 1609ER RS
header_id=49 (EOLR=120), header_id=160 (EOLR=60)
All 4 segments with real STF data.
"""
import sqlite3, sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'data', 'atlas.db')
HEADERS = [
    {'id': 49,  'eolr': 120, 'art': 'KI9853-57,61'},
    {'id': 160, 'eolr': 60,  'art': 'KI9853-57,61'},
]

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode = WAL')
    return conn

def get_cells(conn, header_id, sheet_name):
    rows = conn.execute(
        "SELECT row, col, value FROM ie_sheet_data "
        "WHERE header_id=? AND sheet_name=? ORDER BY row, col",
        (header_id, sheet_name)
    ).fetchall()
    data = {}
    for row, col, val in rows:
        data.setdefault(row, {})[col] = val
    return data

def try_float(val):
    if val is None:
        return None
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return None

def is_int_str(val):
    if val is None:
        return False
    try:
        int(str(val).strip())
        return True
    except ValueError:
        return False

def is_skip_row(row_dict):
    for col, val in row_dict.items():
        if val and re.search(
            r'TỔNG|TOTAL|合計|Classification|STT|Seq\.?No|序号|序號',
            str(val), re.IGNORECASE
        ):
            return True
    return False

def insert_row(conn, d):
    conn.execute("""
        INSERT OR IGNORE INTO ie_process
          (header_id, art, segment, zone, stage, seq,
           process_name, part_name, tct, value_type,
           source_sheet, source_row, flag,
           normal_time, allowance_pct, standard_time,
           actual_operators, machine, is_locked)
        VALUES
          (?,?,?,?,?,?, ?,?,?,?, ?,?,?, ?,?,?, ?,?,?)
    """, (
        d['header_id'], d['art'], d['segment'], d['zone'], d.get('stage', 1), d.get('seq'),
        d.get('process_name'), d.get('part_name'), d.get('tct'), d.get('value_type', 'formula'),
        d['source_sheet'], d['source_row'], d.get('flag'),
        d.get('normal_time'), d.get('allowance_pct'), d.get('standard_time'),
        d.get('actual_operators'), d.get('machine'), d.get('is_locked', 0)
    ))

def insert_row_count(conn):
    return conn.execute('SELECT changes()').fetchone()[0]

# ── Standard OB format (stitching / assembly / STF) ──────────────────────────
def import_standard(conn, header_id, art, sheet_name, segment, zone):
    """
    Standard OB format: col2=seq, col3=name, col4=normal_time,
    col5=allowance%, col6=std_time, col8=theory, col9=actual, col10=machine.
    For assembly: detects 水蜘蛛 row (no col4 but has col8).
    """
    cells = get_cells(conn, header_id, sheet_name)
    if not cells:
        print(f"  [SKIP] {sheet_name!r} not found for header {header_id}")
        return 0

    inserted = 0
    pending = None

    for rn in sorted(cells.keys()):
        row = cells[rn]
        if is_skip_row(row):
            if pending:
                insert_row(conn, pending)
                inserted += insert_row_count(conn)
                pending = None
            continue

        col2_val = row.get(2)
        col3_val = row.get(3)

        if is_int_str(col2_val) and col3_val and str(col3_val).strip():
            if pending:
                insert_row(conn, pending)
                inserted += insert_row_count(conn)

            seq = int(str(col2_val).strip())
            c4  = try_float(row.get(4))
            c5  = try_float(row.get(5))
            c6  = try_float(row.get(6))
            c8  = try_float(row.get(8))
            c9  = try_float(row.get(9))
            c10 = row.get(10)
            machine = str(c10).strip().split('\n')[0] if c10 else None

            # Water spider detection (assembly only): no normal_time, has theory
            is_ws = (c4 is None and c8 is not None and segment == 'assembly')
            actual_zone = '水蜘蛛' if is_ws else zone

            pending = {
                'header_id': header_id, 'art': art,
                'segment': segment, 'zone': actual_zone,
                'seq': seq, 'process_name': str(col3_val).strip(),
                'normal_time': c4, 'allowance_pct': c5,
                'standard_time': None if is_ws else c6,
                'actual_operators': c9, 'machine': machine,
                'tct': c8 if is_ws else c6,
                'value_type': 'formula', 'is_locked': 1 if is_ws else 0,
                'source_sheet': sheet_name, 'source_row': rn,
            }

        elif col3_val and str(col3_val).strip() and pending and not is_int_str(col2_val):
            zh = str(col3_val).strip()
            if zh and zh not in pending['process_name']:
                pending['process_name'] += ' / ' + zh

    if pending:
        insert_row(conn, pending)
        inserted += insert_row_count(conn)

    conn.commit()
    print(f"  [{segment}] {sheet_name!r} zone={zone!r}: {inserted} rows")
    return inserted

# ── Computer stitching (电脑针车) ──────────────────────────────────────────────
def import_computer_stitching(conn, header_id, art, sheet_name):
    """电脑针车: col2=seq, col3=name, col11=normal, col12=allow, col13=std, col15=theory, col16=actual."""
    cells = get_cells(conn, header_id, sheet_name)
    if not cells:
        print(f"  [SKIP] {sheet_name!r} not found")
        return 0

    inserted = 0
    pending = None

    for rn in sorted(cells.keys()):
        row = cells[rn]
        if is_skip_row(row):
            if pending:
                insert_row(conn, pending)
                inserted += insert_row_count(conn)
                pending = None
            continue

        col2_val = row.get(2)
        col3_val = row.get(3)

        if is_int_str(col2_val) and col3_val and str(col3_val).strip():
            if pending:
                insert_row(conn, pending)
                inserted += insert_row_count(conn)

            c11 = try_float(row.get(11))
            c12 = try_float(row.get(12))
            c13 = try_float(row.get(13))
            c16 = try_float(row.get(16))
            c17 = row.get(17)
            machine = str(c17).strip() if c17 else None

            pending = {
                'header_id': header_id, 'art': art,
                'segment': 'stitching', 'zone': '電腦針車',
                'seq': int(str(col2_val).strip()),
                'process_name': str(col3_val).strip(),
                'normal_time': c11, 'allowance_pct': c12, 'standard_time': c13,
                'actual_operators': c16, 'machine': machine, 'tct': c13,
                'value_type': 'formula', 'is_locked': 0,
                'source_sheet': sheet_name, 'source_row': rn,
            }

        elif col3_val and str(col3_val).strip() and pending and not is_int_str(col2_val):
            zh = str(col3_val).strip()
            if zh and zh not in pending['process_name']:
                pending['process_name'] += ' / ' + zh

    if pending:
        insert_row(conn, pending)
        inserted += insert_row_count(conn)

    conn.commit()
    print(f"  [stitching] {sheet_name!r} zone=電腦針車: {inserted} rows")
    return inserted

# ── Cutting: wide-format (multi-operation per part) ───────────────────────────
# 1609ER RS Cutting sheet has columns:
#   col3=seq, col4=part name, col8=cycle_time, col9=allowance, col10=std(Cutting),
#   col13=std(Marking), col15=std(Buffing), col17=std(Skiving),
#   col19=std(Attaching), col21=std(EdgePaint), col23=std(HeatPress)
STD_COLS = [10, 13, 15, 17, 19, 21, 23]

def import_cutting_wide_format(conn, header_id, art, sheet_name, zone='裁斷機'):
    """
    Wide-format cutting sheet: multiple operation columns per row.
    For each part row, sums standard_times across all operation columns → single ie_process row.
    """
    cells = get_cells(conn, header_id, sheet_name)
    if not cells:
        print(f"  [SKIP] {sheet_name!r} not found")
        return 0

    current_part = None
    inserted = 0

    for rn in sorted(cells.keys()):
        row = cells[rn]
        if is_skip_row(row):
            continue

        col2_val = row.get(2)
        col3_val = row.get(3)
        col4_val = row.get(4)

        # Carry-forward material section from col2
        if col2_val and str(col2_val).strip() and not is_int_str(col2_val):
            skip_words = {'classification', 'phân loại', 'tổng cộng', 'total',
                          '合計', '材料类别', 'stt', 'seq.no', '序号'}
            v = str(col2_val).strip()
            if v.lower() not in skip_words and len(v) > 2:
                current_part = v

        if not is_int_str(col3_val):
            continue
        if not col4_val or not str(col4_val).strip():
            continue

        # Sum all operation standard_times across columns 10,13,15,17,19,21,23
        total_std = 0.0
        has_any_std = False
        for c in STD_COLS:
            v = try_float(row.get(c))
            if v is not None and v > 0:
                total_std += v
                has_any_std = True

        # Fallback: if no std_times in wide columns, try col10 alone
        if not has_any_std:
            total_std = None

        insert_row(conn, {
            'header_id': header_id, 'art': art,
            'segment': 'cutting', 'zone': zone,
            'seq': int(str(col3_val).strip()),
            'process_name': str(col4_val).strip(),
            'part_name': current_part,
            'normal_time': try_float(row.get(8)),   # cycle_time
            'allowance_pct': try_float(row.get(9)),  # allowance %
            'standard_time': total_std,
            'actual_operators': try_float(row.get(12)),  # actual machine operators
            'tct': total_std,
            'value_type': 'formula', 'is_locked': 0,
            'source_sheet': sheet_name, 'source_row': rn,
        })
        inserted += insert_row_count(conn)

    conn.commit()
    print(f"  [cutting] {sheet_name!r} zone={zone!r}: {inserted} rows")
    return inserted

# ── ATOM / 自动化 format ──────────────────────────────────────────────────────
ZONE_MAP = {
    'ATOM': 'ATOM', 'LASER': 'Laser', 'EMMA': 'EMMA',
    'YINGHUI': 'YINGHUI', '移印': '移印', 'PAD PRINTING': '移印',
}
def import_atom(conn, header_id, art, sheet_name):
    """自动化 format: col2=seq, col3=viet_name, col6=normal, col7=allow, col8=std, col10=theory, col11=actual, col12=machine."""
    cells = get_cells(conn, header_id, sheet_name)
    if not cells:
        print(f"  [SKIP] {sheet_name!r} not found")
        return 0

    inserted = 0
    pending = None

    for rn in sorted(cells.keys()):
        row = cells[rn]
        if is_skip_row(row):
            if pending:
                insert_row(conn, pending)
                inserted += insert_row_count(conn)
                pending = None
            continue

        col2_val = row.get(2)
        col3_val = row.get(3)

        if is_int_str(col2_val) and col3_val and str(col3_val).strip():
            if pending:
                insert_row(conn, pending)
                inserted += insert_row_count(conn)

            c6  = try_float(row.get(6))
            c7  = try_float(row.get(7))
            c8  = try_float(row.get(8))
            c12 = row.get(12)
            machine = str(c12).strip() if c12 else None
            zone = ZONE_MAP.get((machine or '').upper(), 'ATOM')

            pending = {
                'header_id': header_id, 'art': art,
                'segment': 'cutting', 'zone': zone,
                'seq': int(str(col2_val).strip()),
                'process_name': str(col3_val).strip(),
                'normal_time': c6, 'allowance_pct': c7, 'standard_time': c8,
                'machine': machine, 'tct': c8,
                'value_type': 'formula', 'is_locked': 0,
                'source_sheet': sheet_name, 'source_row': rn,
            }

        elif col3_val and str(col3_val).strip() and pending and not is_int_str(col2_val):
            zh = str(col3_val).strip()
            if zh and zh not in pending['process_name']:
                pending['process_name'] += ' / ' + zh

    if pending:
        insert_row(conn, pending)
        inserted += insert_row_count(conn)

    conn.commit()
    print(f"  [cutting] {sheet_name!r} ATOM/auto: {inserted} rows")
    return inserted

def insert_hand_total(conn, header_id, art):
    conn.execute(
        "DELETE FROM ie_process WHERE header_id=? AND segment='cutting' AND source_sheet='_computed'",
        (header_id,)
    )
    conn.execute("""
        INSERT INTO ie_process
          (header_id, art, segment, zone, stage, seq, process_name,
           value_type, is_locked, source_sheet, source_row)
        VALUES (?,?,?,?,?,?,?, ?,?,?,?)
    """, (header_id, art, 'cutting', '_summary', 1, 9999, '手工總人數',
          'formula', 1, '_computed', 1))
    conn.commit()
    print(f"  [cutting] 手工總人數 marker inserted for header {header_id}")

# ── Main ──────────────────────────────────────────────────────────────────────
def run_header(header_id, art):
    print(f"\n{'='*60}")
    print(f"Importing header_id={header_id} (art={art})")
    print('='*60)

    conn = get_conn()
    try:
        # Clear existing ie_process rows for this header
        deleted = conn.execute("DELETE FROM ie_process WHERE header_id=?", (header_id,)).rowcount
        conn.commit()
        print(f"  Cleared {deleted} existing ie_process rows")

        total = 0

        # ── Cutting ──────────────────────────────────────────────────────
        total += import_cutting_wide_format(conn, header_id, art, 'Cutting', '裁斷機')
        total += import_cutting_wide_format(conn, header_id, art, '  同材共裁', '裁斷機')
        total += import_atom(conn, header_id, art, '自动化')

        # ── Stitching ─────────────────────────────────────────────────────
        total += import_standard(conn, header_id, art, 'Stitching（主流）', 'stitching', '主流')
        total += import_standard(conn, header_id, art, 'Sub.Stitching(支流)', 'stitching', '支流')
        total += import_standard(conn, header_id, art, '折边', 'stitching', '支流')
        total += import_computer_stitching(conn, header_id, art, '电脑针车')

        # ── Assembly ──────────────────────────────────────────────────────
        total += import_standard(conn, header_id, art, 'Assembly 1', 'assembly', '成型')
        total += import_standard(conn, header_id, art, 'Assembly 2', 'assembly', '成型')
        total += import_standard(conn, header_id, art, '成型面照射', 'assembly', '成型')

        # ── STF (real data, not placeholders) ────────────────────────────
        total += import_standard(conn, header_id, art, ' 打粗', 'stf', '打粗')
        total += import_standard(conn, header_id, art, '水洗', 'stf', '水洗')
        total += import_standard(conn, header_id, art, '组底面照射 ', 'stf', '照射')
        total += import_standard(conn, header_id, art, '贴大底', 'stf', '貼底')

        insert_hand_total(conn, header_id, art)

        print(f"\n  Total rows imported: {total}")

        # ── Create default production stage ──────────────────────────────
        conn.execute("DELETE FROM ie_stage WHERE header_id=?", (header_id,))
        conn.execute(
            "INSERT INTO ie_stage (header_id, stage_name) VALUES (?, '量產')",
            (header_id,)
        )
        conn.commit()
        print(f"  Stage '量產' created")

    finally:
        conn.close()

if __name__ == '__main__':
    for h in HEADERS:
        run_header(h['id'], h['art'])
    print("\nDone.")
