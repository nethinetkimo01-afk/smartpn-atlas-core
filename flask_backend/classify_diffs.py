#!/usr/bin/env python3
"""
分類 diff_report_jim.txt 為 3 類，只詳細輸出 Type 1
"""
import sys, re
from collections import defaultdict

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PATH = r'D:\smartpn-atlas-core\flask_backend\test_output\diff_report_jim.txt'


def parse_val(s):
    s = s.strip()
    if s in ('-', ''):
        return 'NO_MP'
    if s == '(new)':
        return 'NEW'   # ref has no value for this ART
    try:
        return float(s)
    except ValueError:
        return None


def parse_line(line):
    """Parse fixed-width diff line. Returns dict or None."""
    # Format: LEAN(4)  ART(12)  Model(28)  OurCut(7)  RefCut(7)  ΔCut(6)  OurS(6)  RefS(6)  ΔS(5)  OurA(6)  RefA(6)  ΔA(5)
    # Offsets based on format string: "{lean:4}  {art:12}  {model:28}  {oc:>7}  {rc:>7}  {dc:>6}  {os:>6}  {rs:>6}  {ds:>5}  {oa:>6}  {ra:>6}  {da:>5}"
    if len(line) < 40:
        return None
    lean  = line[0:4].strip()
    art   = line[6:18].strip()
    model = line[20:48].strip()
    rest  = line[48:].split()
    if not lean or not art:
        return None
    if len(rest) < 9:
        return None

    our_cut = parse_val(rest[0])
    ref_cut = parse_val(rest[1])
    # delta_cut = rest[2]
    our_s   = parse_val(rest[3])
    ref_s   = parse_val(rest[4])
    our_a   = parse_val(rest[6])
    ref_a   = parse_val(rest[7])

    return {
        'lean': lean, 'art': art, 'model': model,
        'our_cut': our_cut, 'ref_cut': ref_cut,
        'our_s':   our_s,   'ref_s':   ref_s,
        'our_a':   our_a,   'ref_a':   ref_a,
        'raw': line.rstrip(),
    }


def classify(r):
    oc, rc = r['our_cut'], r['ref_cut']
    os_, rs = r['our_s'], r['ref_s']
    oa, ra  = r['our_a'], r['ref_a']

    # Type 1: ART/鞋型/訂單 不一致
    # — LEAN=? → ART has MP but no ref match
    if r['lean'] == '?':
        return 1, 'LEAN=?  (DB有MP但編制表無此ART)'
    # — ref有 (new) on both cut & stitch → ref group doesn't record these MP columns
    if rc == 'NEW' and rs == 'NEW':
        if oc not in ('NO_MP', None):
            return 1, 'REF_BLANK  (編制表此欄位空白，DB有值)'
        else:
            return 1, 'BOTH_BLANK  (編制表和DB均無裁/針數值)'

    # Type 3: DB 完全無MP
    # — OurCut=NO_MP and RefCut is a real number
    if oc == 'NO_MP' and isinstance(rc, float):
        return 3, 'NO_DB_MP'

    # Type 2: 有MP但數值不一致
    if isinstance(oc, float) and isinstance(rc, float):
        return 2, 'MP_DIFF'

    # Edge: OurCut=NO_MP, RefCut=NEW → both absent but appeared due to asm diff
    return 1, 'OTHER_STRUCT'


rows = []
with open(PATH, encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if i <= 3:
            continue
        r = parse_line(line)
        if r:
            rows.append(r)

# ── Detect duplicates ──────────────────────────────────────────────────────────
art_lean_count = defaultdict(list)
for r in rows:
    art_lean_count[(r['art'], r['lean'])].append(r)

# ── Classify ───────────────────────────────────────────────────────────────────
t1, t2, t3 = [], [], []
for r in rows:
    t, reason = classify(r)
    r['reason'] = reason
    if t == 1:
        t1.append(r)
    elif t == 2:
        t2.append(r)
    else:
        t3.append(r)

# ── Identify duplicates in Type 1 ─────────────────────────────────────────────
# (same ART+LEAN combo appears multiple times = comparison matched same ref row multiple times)
art_lean_seen = defaultdict(int)
for r in t1:
    art_lean_seen[(r['art'], r['lean'])] += 1

# ── Output Type 1 ─────────────────────────────────────────────────────────────
SEP = '─' * 100

print(f'=== 分類摘要 (共 {len(rows)} 筆差異) ===')
print(f'  Type 1 (ART/鞋型/訂單不一致): {len(t1)} 筆')
print(f'  Type 2 (有MP但數值不一致):    {len(t2)} 筆')
print(f'  Type 3 (DB無MP):             {len(t3)} 筆')
print()

# --- Type 1 ---
print(f'{"=" * 100}')
print(f'  TYPE 1：ART / 鞋型 / 訂單 不一致（{len(t1)} 筆）')
print(f'{"=" * 100}')

# Group by sub-type
sub = defaultdict(list)
for r in t1:
    sub[r['reason']].append(r)

# 1a: LEAN=? (completely unmatched)
if sub['LEAN=?  (DB有MP但編制表無此ART)']:
    print()
    print(f'【A】DB有MP但編制表完全找不到此ART  ({len(sub["LEAN=?  (DB有MP但編制表無此ART)"])} 筆）')
    print(f'  {"ART":<12}  {"Model":<35}  {"OurCut":>7}  {"OurS":>7}  {"OurA":>7}')
    print(f'  {SEP}')
    for r in sub['LEAN=?  (DB有MP但編制表無此ART)']:
        oc = f"{r['our_cut']:.1f}" if isinstance(r['our_cut'], float) else '-'
        os_ = f"{r['our_s']:.1f}" if isinstance(r['our_s'], float) else '-'
        oa = f"{r['our_a']:.1f}" if isinstance(r['our_a'], float) else '-'
        print(f"  {r['art']:<12}  {r['model']:<35}  {oc:>7}  {os_:>7}  {oa:>7}")

# 1b: REF_BLANK (ref columns empty, our DB has values)
if sub['REF_BLANK  (編制表此欄位空白，DB有值)']:
    entries = sub['REF_BLANK  (編制表此欄位空白，DB有值)']
    # Group by LEAN
    by_lean = defaultdict(list)
    for r in entries:
        by_lean[r['lean']].append(r)
    print()
    print(f'【B】ART在編制表找到所屬LEAN，但編制表裁斷/針車欄位空白，DB有值  ({len(entries)} 筆）')
    print(f'     ＊可能原因：編制表該LEAN組只填成型，或尚未填裁/針MP')
    print()
    for lean in sorted(by_lean):
        group = by_lean[lean]
        # Deduplicate by ART (show unique ARTs)
        seen = {}
        for r in group:
            if r['art'] not in seen:
                seen[r['art']] = r
        unique = list(seen.values())
        print(f'  LEAN {lean}  ({len(unique)} 個唯一ART，{len(group)} 筆記錄，重複{len(group)-len(unique)}筆）：')
        for r in unique:
            oc = f"{r['our_cut']:.1f}" if isinstance(r['our_cut'], float) else '-'
            ra = f"{r['ref_a']:.1f}"   if isinstance(r['ref_a'],  float) else '-'
            print(f"    {r['art']:<12}  {r['model'][:35]:<35}  DB裁={oc:>6}  RefASM={ra:>6}")
        print()

# 1c: BOTH_BLANK
if sub['BOTH_BLANK  (編制表和DB均無裁/針數值)']:
    entries = sub['BOTH_BLANK  (編制表和DB均無裁/針數值)']
    by_lean = defaultdict(list)
    for r in entries:
        by_lean[r['lean']].append(r)
    print()
    print(f'【C】編制表與DB均無裁斷/針車值，差異來自成型（RefA有值，OurA無）  ({len(entries)} 筆）')
    for lean in sorted(by_lean):
        group = by_lean[lean]
        seen = {}
        for r in group:
            if r['art'] not in seen:
                seen[r['art']] = r
        unique = list(seen.values())
        print(f'  LEAN {lean}  ({len(unique)} 個唯一ART，{len(group)} 筆記錄）：')
        for r in unique:
            ra = f"{r['ref_a']:.1f}" if isinstance(r['ref_a'], float) else '-'
            print(f"    {r['art']:<12}  {r['model'][:35]:<35}  RefASM={ra:>6}")
        print()

# 1d: OTHER_STRUCT
if sub['OTHER_STRUCT']:
    print()
    print(f'【D】其他結構性不一致  ({len(sub["OTHER_STRUCT"])} 筆）')
    for r in sub['OTHER_STRUCT']:
        print(f"  {r['raw']}")

# ── Duplicate summary ─────────────────────────────────────────────────────────
dupes = {k: v for k, v in art_lean_seen.items() if v > 1}
if dupes:
    print()
    print(f'{"=" * 100}')
    print(f'  TYPE 1 中重複比對的 ART（同一組合出現多次，比對演算法問題）  ({len(dupes)} 個 ART+LEAN）')
    print(f'{"=" * 100}')
    for (art, lean), cnt in sorted(dupes.items()):
        model = next(r['model'] for r in t1 if r['art'] == art and r['lean'] == lean)
        print(f"  {lean:4}  {art:<12}  {model[:35]:<35}  出現 {cnt} 次")

print()
print(f'=== Type 2 / Type 3 摘要（不展開，MP邏輯未定義） ===')
print(f'  Type 2 差異筆數: {len(t2)}')
lean_counts2 = defaultdict(int)
for r in t2:
    lean_counts2[r['lean']] += 1
for lean in sorted(lean_counts2):
    print(f'    {lean}: {lean_counts2[lean]}')
print(f'  Type 3 無MP筆數: {len(t3)}')
lean_counts3 = defaultdict(int)
for r in t3:
    lean_counts3[r['lean']] += 1
for lean in sorted(lean_counts3):
    print(f'    {lean}: {lean_counts3[lean]}')
