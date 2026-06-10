#!/usr/bin/env python3
import sys, os, re, collections
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
conn.close()

FUNC_RE  = re.compile(r'([A-Z][A-Z0-9\.]+)\s*\(', re.IGNORECASE)
ARITH_RE = re.compile(r'[\+\-\*\/]')

def classify(formula):
    funcs = [m.upper() for m in FUNC_RE.findall(formula)]
    if funcs:
        for f in funcs:
            if f in {'SUM','SUMIF','SUMIFS'}:      return 'SUM'
            if f in {'IF','IFERROR','AND','OR'}:   return 'IF'
            if f in {'VLOOKUP','INDEX','MATCH','INDIRECT','OFFSET'}: return 'LOOKUP'
        return funcs[0]
    if ARITH_RE.search(formula):
        return 'ARITHMETIC'
    return 'CELL_REF'

sheet_counts = collections.Counter()
type_counts  = collections.Counter()
func_counts  = collections.Counter()

lines = []
for r in rows:
    sn, row, col, val, formula = r['sheet_name'], r['row'], r['col'], r['value'], r['formula']
    ftype = classify(formula)
    sheet_counts[sn] += 1
    type_counts[ftype] += 1
    for fn in FUNC_RE.findall(formula):
        func_counts[fn.upper()] += 1
    lines.append(f"{sn}\t{row}\t{col}\t{formula}\t{val or ''}")

out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_output', 'formula_report.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(f"header_id=32  formula cells: {len(rows)}\n")
    f.write("="*80 + "\n\n")

    f.write("── Per-sheet count ──────────────────────────────────────────────────────────\n")
    for sn, n in sheet_counts.most_common():
        f.write(f"  {n:4d}  {sn}\n")

    f.write("\n── Formula type summary ─────────────────────────────────────────────────────\n")
    f.write("  (ARITHMETIC = pure math ops; CELL_REF = =Sheet!A1; SUM/IF/LOOKUP = functions)\n")
    for t, n in type_counts.most_common():
        f.write(f"  {n:4d}  {t}\n")

    f.write("\n── Top individual functions ─────────────────────────────────────────────────\n")
    for fn, n in func_counts.most_common():
        f.write(f"  {n:4d}  {fn}\n")

    f.write("\n── Detail: sheet_name | row | col | formula | value ──────────────────────\n")
    f.write("sheet_name\trow\tcol\tformula\tvalue\n")
    for line in lines:
        f.write(line + "\n")

print(f"Total formula cells : {len(rows)}")
print(f"\nPer-sheet (sorted by count):")
for sn, n in sheet_counts.most_common():
    print(f"  {n:4d}  {sn}")
print(f"\nFormula types:")
for t, n in type_counts.most_common():
    print(f"  {n:4d}  {t}")
print(f"\nAll functions seen:")
for fn, n in func_counts.most_common():
    print(f"  {n:4d}  {fn}")
print(f"\nWritten: {out_path}")
