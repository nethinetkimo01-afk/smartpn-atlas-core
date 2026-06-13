"""Validation script for Task 025 — LA TRAINER OG import + API."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
import database as db

print("=== Task 025 Validation ===\n")

# S1: /ie list shows LA TRAINER with FW26 + material
r = db.list_ie_records()
la = [x for x in r['records'] if 'LA TRAINER' in (x.get('model_name') or '')]
if la:
    rec = la[0]
    print("S1 PASS — LA TRAINER in /ie list")
    print(f"     season={rec.get('season')!r}  material={str(rec.get('material',''))[:35]!r}")
else:
    print("S1 FAIL — LA TRAINER not found in list")

# S2: all 4 tabs have data
print()
all_pass = True
for seg in ['cutting','stitching','assembly','stf']:
    r2 = db.get_ie_cell_data(32, seg, 120)
    zones = r2.get('zones', [])
    total = sum(len(z['rows']) for z in zones)
    zone_names = [z['zone'] for z in zones]
    ok = total > 0
    if not ok: all_pass = False
    print("S2 %s — %10s: %2d rows, zones=%s" % ('PASS' if ok else 'FAIL', seg, total, zone_names))
if all_pass:
    print("S2 ALL PASS")

# S3: EOLR 60<->120
print()
r120 = db.get_ie_cell_data(32, 'cutting', 120)
r60  = db.get_ie_cell_data(32, 'cutting', 60)
atom120 = next((z for z in r120['zones'] if z['zone']=='ATOM'), None)
atom60  = next((z for z in r60['zones'] if z['zone']=='ATOM'), None)
if atom120 and atom60:
    t120 = atom120['rows'][0]['theory_operators']
    t60  = atom60['rows'][0]['theory_operators']
    ratio = round(t120/t60, 3) if t60 else 0
    ok = abs(ratio - 2.0) < 0.01
    print("S3 %s — EOLR ratio 120/60=%.3f  t120=%s  t60=%s" % ('PASS' if ok else 'FAIL', ratio, t120, t60))
else:
    print("S3 FAIL — ATOM zone not found")

# S4: 手工總人數
print()
ht120 = r120['hand_total']
ht60  = r60['hand_total']
ok = ht120 > 0 and round(ht120/ht60, 1) == 2.0
print("S4 %s — 手工總人數 @120=%.4f @60=%.4f" % ('PASS' if ok else 'FAIL', ht120, ht60))

# S5: 水蜘蛛 independent
print()
r_asm = db.get_ie_cell_data(32, 'assembly', 120)
ws = next((z for z in r_asm['zones'] if z['zone']=='水蜘蛛'), None)
if ws and ws['rows']:
    row = ws['rows'][0]
    ok = row['theory_operators'] == 2.0 and row['is_locked'] == 1 and row['standard_time'] is None
    print("S5 %s — 水蜘蛛 theory=%.1f locked=%d std_time=%s" % (
        'PASS' if ok else 'FAIL', row['theory_operators'], row['is_locked'], row['standard_time']))
else:
    print("S5 FAIL — 水蜘蛛 zone not found")

# S6: Formula spot-checks
print()
# S6a: ATOM row1 std_time=22.4 @eolr=120 → theory=22.4/30≈0.7467
r1 = atom120['rows'][0]
exp = round(22.4/30, 4)
ok6a = abs(r1['theory_operators'] - exp) < 0.001
print("S6a %s — ATOM R1 theory=%.4f (expect %.4f)" % ('PASS' if ok6a else 'FAIL', r1['theory_operators'], exp))

# S6b: Cutting (da thật) row1 std_time check
cut_zone = next((z for z in r120['zones'] if z['zone']=='裁斷機'), None)
if cut_zone and cut_zone['rows']:
    cr = cut_zone['rows'][0]
    if cr['standard_time']:
        exp6b = round(cr['standard_time'] / 30, 4)
        ok6b = cr['theory_operators'] is not None
        print("S6b %s — 裁斷機 R1 std=%.1f theory=%.4f" % ('PASS' if ok6b else 'FAIL', cr['standard_time'], cr['theory_operators'] or 0))
    else:
        print("S6b SKIP — no standard_time for 裁斷機 R1")
else:
    print("S6b FAIL — 裁斷機 zone not found")

# S6c: STF placeholder
stf_d = db.get_ie_cell_data(32, 'stf', 120)
wash = next((r for z in stf_d['zones'] if z['zone']=='水洗' for r in z['rows']), None)
if wash:
    ok6c = wash['is_locked'] == 1 and wash['actual_operators'] == 5.0
    print("S6c %s — 水洗 locked=%d actual_ops=%s" % ('PASS' if ok6c else 'FAIL', wash['is_locked'], wash['actual_operators']))
else:
    print("S6c FAIL — 水洗 row not found")

print("\n=== Done ===")
