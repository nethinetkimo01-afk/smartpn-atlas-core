#!/usr/bin/env python3
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

db.init_db()
conn = db.get_conn()

tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

if 'ie_sheet_data' in tables:
    cnt = conn.execute("SELECT COUNT(*) FROM ie_sheet_data").fetchone()[0]
    print(f"ie_sheet_data total rows: {cnt}")
    rows = conn.execute("SELECT header_id, COUNT(*) as n FROM ie_sheet_data GROUP BY header_id").fetchall()
    for r in rows:
        print(f"  header_id={r[0]}: {r[1]} rows")
    sheets = conn.execute("SELECT header_id, sheet_name, COUNT(*) as n FROM ie_sheet_data GROUP BY header_id, sheet_name").fetchall()
    for s in sheets:
        print(f"    header_id={s[0]} sheet={s[1]!r}: {s[2]} cells")
else:
    print("ie_sheet_data table does NOT exist")

# Check ob_header for the header_id that was imported
if cnt > 0 if 'ie_sheet_data' in tables else False:
    pass

conn.close()
