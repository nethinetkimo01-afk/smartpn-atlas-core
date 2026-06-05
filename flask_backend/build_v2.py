#!/usr/bin/env python3
"""Rebuild result_table_v2.xlsx."""
import sys, os, shutil, tempfile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import openpyxl
import database as db
import build_result_table as brt


def _use_temp_copy(orig_path):
    """Copy file to temp dir if original path raises PermissionError."""
    tmp = os.path.join(tempfile.gettempdir(), os.path.basename(orig_path))
    try:
        shutil.copy2(orig_path, tmp)
        return tmp
    except Exception as e:
        print(f'  WARNING: could not copy {os.path.basename(orig_path)} to temp: {e}')
        return orig_path


db.init_db()
OUTPUT_NEW = r'D:\smartpn-atlas-core\flask_backend\test_output\result_table_v2.xlsx'
os.makedirs(os.path.dirname(OUTPUT_NEW), exist_ok=True)

# Copy potentially-locked source files to temp paths
brt.SCHEDULE = _use_temp_copy(brt.SCHEDULE)
brt.BIANCHE  = _use_temp_copy(brt.BIANCHE)

print('Loading DS-04...')
schedule_groups = brt.load_schedule()
lean_found = sum(len(g['art_lean']) for g in schedule_groups)
print(f'  {len(schedule_groups)} sheets, {sum(len(g["orders"]) for g in schedule_groups)} ARTs')
print(f'  {lean_found} ARTs with LEAN from DS-04 group titles')

print('Loading DS-05 OCS...')
ocs_rows, ocs_err = brt.load_ocs()
if ocs_err:
    print(f'  WARNING: {ocs_err}')
else:
    print(f'  {len(ocs_rows)} T-group rows')

print('Loading 廠務組織編制表...')
bianche_rows = brt.load_bianche_structure()
print(f'  {len(bianche_rows)} ref rows')

print('Loading OCS fixed units...')
ocs_fixed = brt.load_ocs_fixed_units()
for sec, units in ocs_fixed.items():
    print(f'  {sec}: {len(units)} units')

print('Loading RB / QC units...')
rb_qc = brt.load_rb_qc_units()
for sec, units in rb_qc.items():
    print(f'  {sec}: {len(units)} units')

print('Building Excel...')
wb = openpyxl.Workbook()
wb.remove(wb.active)
brt.build_csa(wb, schedule_groups, bianche_rows)
brt.build_ocs(wb, ocs_rows, ocs_err)
for sec in brt.OCS_SECTIONS:
    brt.build_ocs_fixed_tab(wb, sec, ocs_fixed.get(sec, []))
brt.build_rb_qc_tab(wb, 'RB', rb_qc.get('RB', []))
brt.build_rb_qc_tab(wb, 'QC', rb_qc.get('QC', []))
brt.build_ref(wb, bianche_rows)
ws_diff, n1, n2 = brt.build_diff_sheet(wb, schedule_groups, bianche_rows)
wb.save(OUTPUT_NEW)
print(f'Saved: {OUTPUT_NEW}')
print(f'Sheets: {[s.title for s in wb.worksheets]}')
print(f'非MP差異: 進度表有/編制表無={n1}, 編制表有/進度表無={n2}')
