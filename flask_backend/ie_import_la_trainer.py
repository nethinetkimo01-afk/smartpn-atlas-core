"""
IE Import — LA TRAINER OG (header_id=32)
All 4 segments: cutting / stitching / assembly / stf
"""
import sqlite3, sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

DB = os.path.join(os.path.dirname(__file__), 'data', 'atlas.db')
HEADER_ID = 32
ART = 'KH9680-81'  # primary ART for LA TRAINER

# ── Schema migration ──────────────────────────────────────────────────────────
def migrate_schema(conn):
    existing = {r[1] for r in conn.execute("PRAGMA table_info(ie_process)").fetchall()}
    new_cols = [
        ("normal_time",    "REAL"),
        ("allowance_pct",  "REAL"),
        ("standard_time",  "REAL"),
        ("actual_operators","REAL"),
        ("machine",        "TEXT"),
        ("cut_per_hour",   "REAL"),
        ("qty_per_pair",   "REAL"),
        ("is_locked",      "INTEGER DEFAULT 0"),
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE ie_process ADD COLUMN {col_name} {col_type}")
            print(f"  [schema] Added column: {col_name}")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS ie_stage (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            header_id  INTEGER NOT NULL,
            stage_name TEXT    NOT NULL,
            created_at TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ie_edit_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            process_id INTEGER NOT NULL,
            stage_id   INTEGER,
            field      TEXT NOT NULL,
            old_value  TEXT,
            new_value  TEXT,
            user       TEXT,
            status     TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("[schema] Migration complete.")

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_cells(conn, header_id, sheet_name):
    rows = conn.execute(
        "SELECT row, col, value, formula FROM ie_sheet_data "
        "WHERE header_id=? AND sheet_name=? ORDER BY row, col",
        (header_id, sheet_name)
    ).fetchall()
    data = {}
    for row, col, val, fml in rows:
        data.setdefault(row, {})[col] = (val, fml)
    return data

def cell_val(rows_data, row_num, col_num):
    return rows_data.get(row_num, {}).get(col_num, (None, None))[0]

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
    """Skip totals, headers, empty rows."""
    for col, (val, _) in row_dict.items():
        if val and re.search(r'TỔNG|TOTAL|合計|Classification|STT|Seq\.?No|序号|序號', str(val), re.IGNORECASE):
            return True
    return False

def insert_row(conn, d):
    conn.execute("""
        INSERT OR IGNORE INTO ie_process
          (header_id, art, segment, zone, stage, seq,
           process_name, part_name, tct, value_type, formula,
           source_sheet, source_row, flag,
           normal_time, allowance_pct, standard_time,
           actual_operators, machine, cut_per_hour, qty_per_pair, is_locked)
        VALUES
          (?,?,?,?,?,?, ?,?,?,?,?, ?,?,?, ?,?,?, ?,?,?,?,?)
    """, (
        d['header_id'], d['art'], d['segment'], d['zone'], d.get('stage', 1), d.get('seq'),
        d.get('process_name'), d.get('part_name'), d.get('tct'), d.get('value_type', 'formula'), d.get('formula'),
        d['source_sheet'], d['source_row'], d.get('flag'),
        d.get('normal_time'), d.get('allowance_pct'), d.get('standard_time'),
        d.get('actual_operators'), d.get('machine'), d.get('cut_per_hour'), d.get('qty_per_pair'),
        d.get('is_locked', 0)
    ))

# ── Cutting: da thật format ────────────────────────────────────────────────────
def import_cutting_da_that(conn, sheet_name, zone):
    """Cutting (da thật) and Cutting_EMMA format.
    col3=seq, col4=process_name, col7or8=cut_per_hour, col8or9=std_time."""
    cells = get_cells(conn, HEADER_ID, sheet_name)
    if not cells:
        print(f"  [SKIP] sheet not found: {sheet_name!r}")
        return 0

    # Detect column offsets: look for 'Cut' header in row 11
    row11 = cells.get(11, {})
    col7_text = str(row11.get(7, ('',))[0] or '')
    # If col7 header mentions 'Cut' → EMMA format; else da thật format
    emma_fmt = 'Cut' in col7_text or '刀' in col7_text

    current_part = None
    inserted = 0

    for rn in sorted(cells.keys()):
        row = cells[rn]
        if is_skip_row(row):
            continue

        col2_val = (row.get(2) or (None,))[0]
        col3_val = (row.get(3) or (None,))[0]
        col4_val = (row.get(4) or (None,))[0]

        # Carry-forward part name from col2 (classification material)
        if col2_val and str(col2_val).strip() and not is_int_str(col2_val):
            skip_words = {'classification', 'phân loại', 'classification material',
                          'tổng cộng', 'total', '合計', '材料类别'}
            if str(col2_val).strip().lower() not in skip_words:
                current_part = str(col2_val).strip()

        if not is_int_str(col3_val):
            continue
        if not col4_val or not str(col4_val).strip():
            continue

        seq = int(str(col3_val).strip())
        process_name = str(col4_val).strip()

        # Column positions depend on format
        if emma_fmt:
            c7 = (row.get(7) or (None,))[0]
            c8 = (row.get(8) or (None,))[0]
            c9 = (row.get(9) or (None,))[0]
            c10 = (row.get(10) or (None,))[0]
            c6 = (row.get(6) or (None,))[0]
            f7 = try_float(c7)
            if f7 is not None:
                cut_h = f7
                std_t = try_float(c8)
                theory = try_float(c9)
                actual = try_float(c10)
                machine = None
            else:
                cut_h = None
                machine = str(c7).strip() if c7 else None
                std_t = try_float(c8)
                theory = try_float(c9)
                actual = try_float(c10)
            qty_pair = try_float(c6)
        else:
            c7 = (row.get(7) or (None,))[0]
            c8 = (row.get(8) or (None,))[0]
            c9 = (row.get(9) or (None,))[0]
            c10 = (row.get(10) or (None,))[0]
            c11 = (row.get(11) or (None,))[0]
            cut_h = try_float(c8)
            std_t = try_float(c9)
            theory = try_float(c10)
            actual = try_float(c11)
            qty_pair = try_float(c7)
            machine = None

        insert_row(conn, {
            'header_id': HEADER_ID, 'art': ART, 'segment': 'cutting', 'zone': zone,
            'seq': seq, 'process_name': process_name, 'part_name': current_part,
            'standard_time': std_t, 'cut_per_hour': cut_h, 'qty_per_pair': qty_pair,
            'actual_operators': actual, 'machine': machine,
            'value_type': 'formula', 'tct': std_t,
            'source_sheet': sheet_name, 'source_row': rn,
        })
        inserted += 1

    conn.commit()
    print(f"  [cutting] {sheet_name!r} zone={zone!r}: {inserted} rows")
    return inserted

# ── Cutting: ATOM format ──────────────────────────────────────────────────────
ZONE_MAP = {
    'ATOM': 'ATOM', 'LASER': 'Laser', 'EMMA': 'EMMA',
    'YINGHUI': 'YINGHUI', '移印': '移印', 'PAD PRINTING': '移印',
    '转印': '轉印', '裁斷': '裁斷機', '手動': '裁斷機',
}

def import_atom_format(conn, sheet_name, default_zone=None, use_col12_zone=False):
    """ATOM / 自动裁 format:
    col2=seq, col3=process_name(viet), next-row col3=Chinese label,
    col6=normal_time, col7=allowance%, col8=standard_time,
    col10=theory_operators, col11=actual_operators, col12=machine."""
    cells = get_cells(conn, HEADER_ID, sheet_name)
    if not cells:
        print(f"  [SKIP] sheet not found: {sheet_name!r}")
        return 0

    # Build ordered rows, carry Chinese label
    row_nums = sorted(cells.keys())
    pending = None  # pending insert waiting for label
    inserted = 0

    for i, rn in enumerate(row_nums):
        row = cells[rn]
        if is_skip_row(row):
            if pending:
                insert_row(conn, pending)
                inserted += 1
                pending = None
            continue

        col2_val = (row.get(2) or (None,))[0]
        col3_val = (row.get(3) or (None,))[0]

        if is_int_str(col2_val) and col3_val and str(col3_val).strip():
            # This is a new data row — flush previous pending
            if pending:
                insert_row(conn, pending)
                inserted += 1

            seq = int(str(col2_val).strip())
            process_name = str(col3_val).strip()
            c6 = try_float((row.get(6) or (None,))[0])
            c7 = try_float((row.get(7) or (None,))[0])
            c8 = try_float((row.get(8) or (None,))[0])
            c10 = try_float((row.get(10) or (None,))[0])
            c11 = try_float((row.get(11) or (None,))[0])
            c12 = (row.get(12) or (None,))[0]
            machine = str(c12).strip() if c12 else None

            if use_col12_zone and machine:
                # Determine zone from machine name
                zone = ZONE_MAP.get(machine.upper(), ZONE_MAP.get(machine, default_zone or '裁斷機'))
            else:
                zone = default_zone

            pending = {
                'header_id': HEADER_ID, 'art': ART, 'segment': 'cutting', 'zone': zone,
                'seq': seq, 'process_name': process_name,
                'normal_time': c6, 'allowance_pct': c7, 'standard_time': c8,
                'actual_operators': c11, 'machine': machine, 'tct': c8,
                'value_type': 'formula',
                'source_sheet': sheet_name, 'source_row': rn,
            }

        elif col3_val and str(col3_val).strip() and pending and not is_int_str(col2_val):
            # Chinese label row → append to pending process_name
            zh = str(col3_val).strip()
            if zh and zh not in pending['process_name']:
                pending['process_name'] += ' / ' + zh

    if pending:
        insert_row(conn, pending)
        inserted += 1

    conn.commit()
    print(f"  [cutting] {sheet_name!r}: {inserted} rows (atom format)")
    return inserted

# ── Stitching / Assembly format ───────────────────────────────────────────────
def import_stitch_assembly(conn, sheet_name, segment, zone, is_computer=False):
    """Stitching / Sub.Stitching / Assembly.1 / Assembly.2.
    Standard: col2=seq, col3=name, col4=normal_time, col5=allowance, col6=std_time, col8=theory, col9=actual.
    Computer (电脑针车): col2=seq, col3=name, col11=normal, col12=allowance, col13=std, col15=theory, col16=actual."""
    cells = get_cells(conn, HEADER_ID, sheet_name)
    if not cells:
        print(f"  [SKIP] sheet not found: {sheet_name!r}")
        return 0

    row_nums = sorted(cells.keys())
    pending = None
    inserted = 0
    water_spider_seqs = set()  # detect 水蜘蛛

    for rn in row_nums:
        row = cells[rn]
        if is_skip_row(row):
            if pending:
                insert_row(conn, pending)
                inserted += 1
                pending = None
            continue

        col2_val = (row.get(2) or (None,))[0]
        col3_val = (row.get(3) or (None,))[0]

        if is_int_str(col2_val) and col3_val and str(col3_val).strip():
            # New data row
            if pending:
                insert_row(conn, pending)
                inserted += 1

            seq = int(str(col2_val).strip())
            process_name = str(col3_val).strip()

            if is_computer:
                c11 = try_float((row.get(11) or (None,))[0])
                c12 = try_float((row.get(12) or (None,))[0])
                c13 = try_float((row.get(13) or (None,))[0])
                c15 = try_float((row.get(15) or (None,))[0])
                c16 = try_float((row.get(16) or (None,))[0])
                c17 = (row.get(17) or (None,))[0]
                machine = str(c17).strip() if c17 else None
                pending = {
                    'header_id': HEADER_ID, 'art': ART, 'segment': segment, 'zone': zone,
                    'seq': seq, 'process_name': process_name,
                    'normal_time': c11, 'allowance_pct': c12, 'standard_time': c13,
                    'actual_operators': c16, 'machine': machine, 'tct': c13,
                    'value_type': 'formula',
                    'source_sheet': sheet_name, 'source_row': rn,
                }
            else:
                c4 = try_float((row.get(4) or (None,))[0])
                c5 = try_float((row.get(5) or (None,))[0])
                c6 = try_float((row.get(6) or (None,))[0])
                c8 = try_float((row.get(8) or (None,))[0])
                c9 = try_float((row.get(9) or (None,))[0])
                c10 = (row.get(10) or (None,))[0]
                machine = str(c10).strip().split('\n')[0] if c10 else None

                # Detect 水蜘蛛: no normal_time (col4) but has theory (col8)
                is_water_spider = (c4 is None and c8 is not None and segment == 'assembly')
                actual_zone = '水蜘蛛' if is_water_spider else zone

                pending = {
                    'header_id': HEADER_ID, 'art': ART, 'segment': segment, 'zone': actual_zone,
                    'seq': seq, 'process_name': process_name,
                    'normal_time': c4, 'allowance_pct': c5, 'standard_time': c6,
                    'actual_operators': c9, 'machine': machine, 'tct': c6,
                    'value_type': 'formula',
                    'is_locked': 1 if is_water_spider else 0,
                    'source_sheet': sheet_name, 'source_row': rn,
                }
                if is_water_spider:
                    pending['standard_time'] = None
                    pending['tct'] = c8  # fixed theory_operators stored in tct for locked row

        elif col3_val and str(col3_val).strip() and pending and not is_int_str(col2_val):
            # Chinese label → append
            zh = str(col3_val).strip()
            if zh and zh not in pending['process_name']:
                pending['process_name'] += ' / ' + zh

    if pending:
        insert_row(conn, pending)
        inserted += 1

    conn.commit()
    print(f"  [{segment}] {sheet_name!r} zone={zone!r}: {inserted} rows")
    return inserted

# ── STF placeholder ───────────────────────────────────────────────────────────
def import_stf_placeholders(conn):
    inserted = 0
    placeholders = [
        ('打粗', '打粗（STF待補）', None, None, '待補', 0),
        ('照射', '照射（STF待補）', None, None, '待補', 0),
        ('水洗', '水洗（固定5人）', 5.0, 5.0, None, 1),  # 固定5人
        ('貼底', '貼底工序1（待補）', None, None, '待補', 0),
        ('貼底', '貼底工序2（待補）', None, None, '待補', 0),
        ('貼底', '貼底工序3（待補）', None, None, '待補', 0),
    ]
    for i, (zone, name, theory, actual, flag, locked) in enumerate(placeholders):
        conn.execute("""
            INSERT OR IGNORE INTO ie_process
              (header_id, art, segment, zone, stage, seq, process_name,
               value_type, actual_operators, is_locked, flag,
               source_sheet, source_row)
            VALUES (?,?,?,?,?,?,?, ?,?,?,?, ?,?)
        """, (
            HEADER_ID, ART, 'stf', zone, 1, i + 1, name,
            'manual', actual, locked, flag,
            '_placeholder', i + 1
        ))
        inserted += 1
    conn.commit()
    print(f"  [stf] Created {inserted} placeholder rows")
    return inserted

# ── Hand total synthetic row ───────────────────────────────────────────────────
def insert_hand_total(conn):
    """Insert synthetic 手工總人數 row = Σ theory_operators (zones ≠ 裁斷機)."""
    # Remove any existing
    conn.execute("DELETE FROM ie_process WHERE header_id=? AND segment='cutting' AND source_sheet='_computed'",
                 (HEADER_ID,))
    # Sum of standard_time for non-裁斷機 zones (we'll compute in API at runtime)
    # Store as a marker row; actual value computed by API
    conn.execute("""
        INSERT INTO ie_process
          (header_id, art, segment, zone, stage, seq, process_name,
           value_type, is_locked, flag, source_sheet, source_row)
        VALUES (?,?,?,?,?,?,?, ?,?,?, ?,?)
    """, (HEADER_ID, ART, 'cutting', '_summary', 1, 9999, '手工總人數',
          'formula', 1, None, '_computed', 1))
    conn.commit()
    print("  [cutting] Inserted 手工總人數 marker row")

# ── SUM.C2B → ob_header ──────────────────────────────────────────────────────
def update_header_from_sumcb2(conn):
    cells = get_cells(conn, HEADER_ID, 'SUM.C2B')
    if not cells:
        print("  [skip] SUM.C2B not found")
        return

    # R4 col2 = material label (full text may include material value)
    # R5 col2 = season label
    # R6 col2 = category
    material_text = (cells.get(4, {}).get(2) or (None,))[0] or ''
    season_text   = (cells.get(5, {}).get(2) or (None,))[0] or ''
    category_text = (cells.get(6, {}).get(2) or (None,))[0] or ''

    # Extract season (FW26, SS26, etc.)
    season_match = re.search(r'(FW|SS)\d{2,4}', season_text, re.IGNORECASE)
    season = season_match.group(0).upper() if season_match else None

    # Extract material (part after last ':' or just take the whole text)
    mat_parts = material_text.split(':')
    material = mat_parts[-1].strip() if len(mat_parts) > 1 else material_text.strip()

    if not material:
        material = None
    if not season:
        season = None

    if season or material:
        conn.execute(
            "UPDATE ob_header SET season=COALESCE(?,season), material=COALESCE(?,material) WHERE id=?",
            (season, material, HEADER_ID)
        )
        conn.commit()
        print(f"  [SUM.C2B] season={season!r} material={str(material)[:40]!r}")
    else:
        print("  [SUM.C2B] No data extracted")

# ── Stage setup ───────────────────────────────────────────────────────────────
def setup_stage(conn):
    existing = conn.execute("SELECT id FROM ie_stage WHERE header_id=? AND stage_name=?",
                            (HEADER_ID, '初版 v1.0')).fetchone()
    if not existing:
        conn.execute("INSERT INTO ie_stage (header_id, stage_name) VALUES (?,?)",
                     (HEADER_ID, '初版 v1.0'))
        conn.commit()
    print("  [stage] Stage '初版 v1.0' ready")

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    print("=== Schema migration ===")
    migrate_schema(conn)

    print(f"\n=== Clear existing hdr {HEADER_ID} ie_process data ===")
    n = conn.execute("SELECT COUNT(*) FROM ie_process WHERE header_id=?", (HEADER_ID,)).fetchone()[0]
    conn.execute("DELETE FROM ie_process WHERE header_id=?", (HEADER_ID,))
    conn.commit()
    print(f"  Cleared {n} existing rows")

    print("\n=== CUTTING segment ===")
    import_cutting_da_that(conn, "Cutting (da thật)", "裁斷機")
    import_cutting_da_that(conn, "Cutting_EMMA", "EMMA")
    import_atom_format(conn, "ATOM", default_zone="ATOM")
    # Skip 自动裁 (identical to ATOM for this file)
    insert_hand_total(conn)

    print("\n=== STITCHING segment ===")
    import_stitch_assembly(conn, "Stitching",      "stitching", "主流")
    import_stitch_assembly(conn, "Sub.Stitching ", "stitching", "支流")
    import_stitch_assembly(conn, "电脑针车 ",       "stitching", "電腦針車", is_computer=True)

    print("\n=== ASSEMBLY segment ===")
    import_stitch_assembly(conn, "Assembly.1", "assembly", "成型")
    import_stitch_assembly(conn, "Assembly.2", "assembly", "成型")

    print("\n=== STF segment ===")
    import_stf_placeholders(conn)

    print("\n=== SUM.C2B → ob_header ===")
    update_header_from_sumcb2(conn)

    print("\n=== Stage setup ===")
    setup_stage(conn)

    print("\n=== Summary ===")
    for seg in ['cutting', 'stitching', 'assembly', 'stf']:
        rows = conn.execute(
            "SELECT zone, COUNT(*) as n FROM ie_process WHERE header_id=? AND segment=? GROUP BY zone",
            (HEADER_ID, seg)
        ).fetchall()
        print(f"  {seg}:")
        for r in rows:
            print(f"    {r['zone']:20s} {r['n']} rows")

    conn.close()
    print("\nDone.")

if __name__ == '__main__':
    main()
