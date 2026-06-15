"""
IE Cutting 段重導入 — header_id=32 (LA TRAINER OG)
來源：ie_sheet_data（AC / Cutting_TC / Cutting_EMMA / 自动裁）
"""
import sqlite3, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB = '../flask_backend/data/atlas.db'
import os
DB = os.path.join(os.path.dirname(__file__), 'data', 'atlas.db')
HEADER_ID = 32
ART = 'KH9680-81'

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def tf(v):
    if v is None: return None
    try: return float(str(v).replace(',','').strip())
    except: return None

def ti(v):
    if v is None: return None
    try:
        n = int(str(v).strip().split('.')[0])
        return n if n > 0 else None
    except: return None

def split_vn_zh(name):
    if not name: return '', ''
    s = str(name).strip()
    for i, c in enumerate(s):
        if '一' <= c <= '鿿' or '㐀' <= c <= '䶿' or '＀' <= c <= '￯':
            return s[:i].strip(), s[i:].strip()
    return s, ''

def get_grid(conn, sheet_name):
    rows = conn.execute(
        'SELECT row,col,value FROM ie_sheet_data WHERE header_id=? AND sheet_name=? ORDER BY row,col',
        (HEADER_ID, sheet_name)
    ).fetchall()
    grid = {}
    for r in rows:
        grid.setdefault(r['row'], {})[r['col']] = r['value']
    return grid

# ── Schema migration ──────────────────────────────────────────────────────────
def migrate(conn):
    existing = {r[1] for r in conn.execute('PRAGMA table_info(ie_process)').fetchall()}
    new_cols = [
        ('mat_cat',          'TEXT'),
        ('process_name_zh',  'TEXT'),
        ('post_marking_std', 'REAL'),
        ('post_marking_ops', 'REAL'),
        ('post_skiving_std', 'REAL'),
        ('post_skiving_ops', 'REAL'),
        ('post_attach_std',  'REAL'),
        ('post_attach_ops',  'REAL'),
        ('post_edge_std',    'REAL'),
        ('post_edge_ops',    'REAL'),
        ('post_heat_std',    'REAL'),
        ('post_heat_ops',    'REAL'),
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing:
            conn.execute(f'ALTER TABLE ie_process ADD COLUMN {col_name} {col_type}')
            print(f'  [schema] Added: {col_name}')
    conn.commit()
    print('[schema] Migration done.')

# ── Insert helper ─────────────────────────────────────────────────────────────
def insert_row(conn, zone, seq, mat_cat, name_raw, layers, qty, cut_h,
               std_time, theory_ops, actual_ops,
               mk_std=None, mk_ops=None, ski_std=None, ski_ops=None,
               att_std=None, att_ops=None, edg_std=None, edg_ops=None,
               ht_std=None, ht_ops=None, normal_time=None, allowance_pct=None,
               flag=None, source_sheet=''):
    viet, zh = split_vn_zh(name_raw)
    conn.execute('''
        INSERT INTO ie_process
        (header_id, art, segment, zone, seq, process_name, process_name_zh,
         mat_cat, layers_per_cut, qty_per_pair, cut_per_hour,
         normal_time, allowance_pct, standard_time, actual_operators, is_locked,
         post_marking_std, post_marking_ops,
         post_skiving_std, post_skiving_ops,
         post_attach_std,  post_attach_ops,
         post_edge_std,    post_edge_ops,
         post_heat_std,    post_heat_ops,
         flag, source_sheet, stage)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        HEADER_ID, ART, 'cutting', zone, seq,
        viet or name_raw, zh,
        (mat_cat or '').strip().replace('\n',' '),
        layers, qty, cut_h,
        normal_time, allowance_pct, std_time, actual_ops, 1,
        mk_std, mk_ops, ski_std, ski_ops,
        att_std, att_ops, edg_std, edg_ops,
        ht_std, ht_ops,
        flag, source_sheet, 1
    ))

# ── Import 裁斷機 from Cutting_TC ─────────────────────────────────────────────
def import_cutting_tc(conn):
    grid = get_grid(conn, 'Cutting_TC')
    count = 0
    last_mat = ''
    for rn in sorted(grid.keys()):
        d = grid[rn]
        seq = ti(d.get(3))
        if seq is None:
            continue
        if d.get(2) and str(d.get(2)).strip() and len(str(d.get(2)).strip()) > 1:
            m = str(d.get(2)).strip()
            if not any(kw in m for kw in ['Tổng', 'Tộng', 'Mục', 'IE prep', 'ME/IE', 'Thuyết']):
                last_mat = m
        cut_raw = d.get(7)
        cut_val = tf(cut_raw)
        # Skip if cut_per_hour is a machine name (non-numeric)
        if cut_val is None:
            if cut_raw and str(cut_raw).strip():
                continue
            # cut is None AND no numeric value → also skip if no standard_time
            if tf(d.get(8)) is None:
                continue
        name_raw = str(d.get(4, '') or '').strip()
        if not name_raw:
            continue
        insert_row(conn, '裁斷機', seq, last_mat, name_raw,
                   tf(d.get(5)), tf(d.get(6)), cut_val,
                   tf(d.get(8)), tf(d.get(9)), tf(d.get(10)),
                   mk_std=tf(d.get(11)), mk_ops=tf(d.get(12)),
                   ski_std=tf(d.get(13)), ski_ops=tf(d.get(14)),
                   att_std=tf(d.get(15)), att_ops=tf(d.get(16)),
                   edg_std=tf(d.get(17)), edg_ops=tf(d.get(18)),
                   ht_std=tf(d.get(19)), ht_ops=tf(d.get(20)),
                   source_sheet='Cutting_TC')
        count += 1
    print(f'[裁斷機] {count} rows inserted.')
    return count

# ── Import EMMA from Cutting_EMMA ─────────────────────────────────────────────
def import_cutting_emma(conn):
    grid = get_grid(conn, 'Cutting_EMMA')
    count = 0
    last_mat = ''
    for rn in sorted(grid.keys()):
        d = grid[rn]
        seq = ti(d.get(3))
        if seq is None:
            continue
        if d.get(2) and str(d.get(2)).strip() and len(str(d.get(2)).strip()) > 1:
            m = str(d.get(2)).strip()
            if not any(kw in m for kw in ['Tổng', 'Tộng', 'Mục', 'IE prep', 'ME/IE', 'Thuyết']):
                last_mat = m
        cut_raw = d.get(7)
        cut_val = tf(cut_raw)
        # For EMMA: include rows where cut is numeric OR cut is 'EMMA' (EMMA machine)
        if cut_val is None and cut_raw and str(cut_raw).strip():
            cut_name = str(cut_raw).strip().upper()
            if cut_name == 'EMMA':
                cut_val = None  # machine cut, no numeric value
            else:
                continue  # skip ATOM/LASER/Yinghui refs in EMMA sheet
        name_raw = str(d.get(4, '') or '').strip()
        if not name_raw:
            continue
        insert_row(conn, 'EMMA', seq, last_mat, name_raw,
                   tf(d.get(5)), tf(d.get(6)), cut_val,
                   tf(d.get(8)), tf(d.get(9)), tf(d.get(10)),
                   mk_std=tf(d.get(11)), mk_ops=tf(d.get(12)),
                   ski_std=tf(d.get(13)), ski_ops=tf(d.get(14)),
                   att_std=tf(d.get(15)), att_ops=tf(d.get(16)),
                   edg_std=tf(d.get(17)), edg_ops=tf(d.get(18)),
                   ht_std=tf(d.get(19)), ht_ops=tf(d.get(20)),
                   source_sheet='Cutting_EMMA')
        count += 1
    print(f'[EMMA] {count} rows inserted.')
    return count

# ── Import ATOM/LASER/YINGHUI from 自动裁 ─────────────────────────────────────
def import_zidongcai(conn):
    grid = get_grid(conn, '自动裁')
    counts = {}
    rows_sorted = sorted(grid.keys())
    i = 0
    while i < len(rows_sorted):
        rn = rows_sorted[i]
        d = grid[rn]
        seq = ti(d.get(2))
        mach = str(d.get(12, '') or '').strip()
        name_viet = str(d.get(3, '') or '').strip()

        if seq is None or not name_viet or not mach:
            i += 1
            continue

        # Next row may have Chinese name
        name_zh = ''
        if i + 1 < len(rows_sorted):
            next_rn = rows_sorted[i + 1]
            nd = grid[next_rn]
            if ti(nd.get(2)) is None and nd.get(3):
                name_zh = str(nd.get(3, '') or '').strip()
                i += 1  # consume next row

        # Map machine to zone
        mach_upper = mach.upper()
        if 'ATOM' in mach_upper:
            zone = 'ATOM'
        elif 'LASER' in mach_upper:
            zone = 'LASER'
        elif 'YINGHUI' in mach_upper:
            zone = 'YINGHUI'
        elif '移印' in mach:
            zone = '移印'
        elif '轉印' in mach or '转印' in mach:
            zone = '轉印'
        else:
            zone = mach  # fallback

        full_name = name_viet + (' ' + name_zh if name_zh else '')
        insert_row(conn, zone, seq, '', full_name,
                   tf(d.get(4)), None, None,
                   tf(d.get(8)), tf(d.get(10)), tf(d.get(11)),
                   normal_time=tf(d.get(6)),
                   allowance_pct=tf(d.get(7)),
                   source_sheet='自动裁')
        counts[zone] = counts.get(zone, 0) + 1
        i += 1

    for z, c in counts.items():
        print(f'[{z}] {c} rows inserted.')
    return counts

# ── Import 移印/轉印 from Cutting_TC if they appear ────────────────────────────
def import_yinyin(conn):
    """Extract 移印/轉印/YINGHUI rows from Cutting_TC referenced rows"""
    grid = get_grid(conn, 'Cutting_TC')
    count = 0
    last_mat = ''
    seq_counter = {'移印': 1, '轉印': 1, 'YINGHUI': 100}
    for rn in sorted(grid.keys()):
        d = grid[rn]
        if d.get(2) and str(d.get(2)).strip() and len(str(d.get(2)).strip()) > 1:
            m = str(d.get(2)).strip()
            if not any(kw in m for kw in ['Tổng', 'Tộng', 'Mục', 'IE prep', 'ME/IE', 'Thuyết']):
                last_mat = m
        cut_raw = d.get(7)
        if cut_raw is None:
            continue
        cut_str = str(cut_raw).strip().upper()
        if 'YINGHUI' in cut_str or 'YINHUI' in cut_str:
            zone = 'YINGHUI'
        elif '移印' in cut_str:
            zone = '移印'
        elif '轉印' in cut_str or '转印' in cut_str.lower():
            zone = '轉印'
        else:
            continue
        name_raw = str(d.get(4, '') or '').strip()
        if not name_raw:
            continue
        seq = seq_counter.get(zone, 100)
        seq_counter[zone] = seq + 1
        insert_row(conn, zone, seq, last_mat, name_raw,
                   tf(d.get(5)), tf(d.get(6)), None,
                   tf(d.get(8)), tf(d.get(9)), tf(d.get(10)),
                   mk_std=tf(d.get(11)), mk_ops=tf(d.get(12)),
                   ski_std=tf(d.get(13)), ski_ops=tf(d.get(14)),
                   att_std=tf(d.get(15)), att_ops=tf(d.get(16)),
                   edg_std=tf(d.get(17)), edg_ops=tf(d.get(18)),
                   ht_std=tf(d.get(19)), ht_ops=tf(d.get(20)),
                   normal_time=None, allowance_pct=None,
                   source_sheet='Cutting_TC')
        count += 1
    if count:
        print(f'[移印/轉印/YINGHUI] {count} rows from Cutting_TC.')
    return count

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    conn = get_conn()
    print('=== Step 1: Schema migration ===')
    migrate(conn)

    print('\n=== Step 2: Clear cutting rows for header_id=32 ===')
    n = conn.execute("DELETE FROM ie_process WHERE header_id=? AND segment='cutting'",
                     (HEADER_ID,)).rowcount
    conn.commit()
    print(f'  Deleted {n} old rows.')

    print('\n=== Step 3: Import ===')
    import_cutting_tc(conn)
    import_cutting_emma(conn)
    import_zidongcai(conn)
    import_yinyin(conn)
    conn.commit()

    print('\n=== Step 4: Verify ===')
    zones = conn.execute(
        "SELECT zone, COUNT(*) as c FROM ie_process WHERE header_id=? AND segment='cutting' GROUP BY zone ORDER BY zone",
        (HEADER_ID,)
    ).fetchall()
    total = 0
    for z in zones:
        print(f'  {z["zone"]}: {z["c"]} rows')
        total += z['c']
    print(f'  TOTAL: {total} rows')
    conn.close()
    print('\nDone.')

if __name__ == '__main__':
    main()
