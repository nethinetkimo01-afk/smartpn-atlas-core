#!/usr/bin/env python3
import sys, os, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

db.init_db()
conn = db.get_conn()
rows = conn.execute(
    "SELECT sheet_name, row, col, value, formula FROM ie_sheet_data "
    "WHERE header_id=32 AND formula IS NOT NULL AND formula != '' "
    "ORDER BY sheet_name, row, col"
).fetchall()

FUNC_RE = re.compile(r'[A-Z][A-Z0-9\.]+\s*\(', re.IGNORECASE)
ref_only = [r for r in rows if not FUNC_RE.search(r['formula'])]

# Categorise REF_ONLY
arith   = [r for r in ref_only if re.search(r'[\+\-\*\/]', r['formula'])]
ref_eq  = [r for r in ref_only if not re.search(r'[\+\-\*\/]', r['formula'])]

print(f"REF_ONLY total: {len(ref_only)}")
print(f"  arithmetic (+/-/*/÷): {len(arith)}")
print(f"  pure cell ref (=A1):  {len(ref_eq)}")

print("\n-- Arithmetic samples (20) --")
for r in arith[:20]:
    print(f"  [{r['sheet_name']}] R{r['row']}C{r['col']}  {r['formula']}  => {r['value']}")

print("\n-- Pure ref samples (20) --")
for r in ref_eq[:20]:
    print(f"  [{r['sheet_name']}] R{r['row']}C{r['col']}  {r['formula']}  => {r['value']}")

conn.close()
