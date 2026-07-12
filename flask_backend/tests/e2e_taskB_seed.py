"""
Task B — seed a MINIMAL cutting fixture to reproduce the 裁斷合併 render bug.
This is a UI-repro fixture (a few synthetic 裁斷機 rows), NOT business data — it exists
only to make the cutting detail page render rows so the merge re-render can be observed.
Run from repo root with ATLAS_DB set to the E2E db.
Prints the new header id (HID) on the last line as: HID=<n>
"""
import sys, os, io
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'flask_backend'))
os.chdir(ROOT)
import database as db

def seed():
    db.init_db()
    conn = db.get_conn()
    ts = db.now_iso()
    # header + article
    cur = conn.execute(
        "INSERT INTO ob_header (model_name, season, material, category, eolr, run, created_at, updated_at) "
        "VALUES ('MERGE BUG REPRO','SS26','DA','SHOE',120,120,?,?)", (ts, ts))
    hid = cur.lastrowid
    conn.execute("INSERT INTO ob_articles (header_id, art) VALUES (?, 'ZZ9999')", (hid,))
    # stage (unlocked)
    cur = conn.execute("INSERT INTO ie_stage (header_id, stage_name, is_approved) VALUES (?, '初版', 0)", (hid,))
    sid = cur.lastrowid
    # 5 cutting rows in 裁斷機 (type A). Distinct layers/qty/cph so disappearance is visible.
    rows = [
        # seq, name, layers, qty, cph, actual
        (1, '鞋面 A', 2, 4, 11, 3),
        (2, '鞋面 B', 3, 6, 22, 2),
        (3, '鞋舌 C', 1, 2, 33, 1),
        (4, '後跟 D', 4, 8, 44, 5),
        (5, '補強 E', 2, 3, 55, 1),
    ]
    for seq, name, lay, qty, cph, act in rows:
        conn.execute(
            """INSERT INTO ie_process
               (header_id, art, segment, zone, stage, seq, process_name, process_name_zh,
                part_name, mat_cat, layers_per_cut, qty_per_pair, cut_per_hour,
                actual_operators, value_type, stage_id)
               VALUES (?, 'ZZ9999','cutting','裁斷機',1,?,?,?,?,?,?,?,?,?,'manual',?)""",
            (hid, seq, name, name, name, 'DA', lay, qty, cph, act, sid))
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM ie_process WHERE header_id=?", (hid,)).fetchone()[0]
    conn.close()
    print(f"seeded header {hid}: {n} cutting rows, stage {sid}")
    print(f"HID={hid}")

if __name__ == '__main__':
    seed()
