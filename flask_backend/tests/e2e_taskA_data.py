"""
Task A data-side driver (run from repo ROOT).
Uses ATLAS_DB env var -> isolated E2E DB (never touches real atlas.db).

Modes:
  setup   : init fresh DB + seed admin + Step1 import (real DS-04) + verify parse
  reimport: Step2 -> import a MODIFIED copy of DS-04, verify overwrite + change log
  verify  : print current ds04_orders stats
"""
import sys, os, io, json, shutil, re
# NOTE: do NOT wrap sys.stdout here — parse_ds04.py reassigns sys.stdout itself;
# a second wrapper gets GC'd and closes the underlying buffer. Run with PYTHONUTF8=1.
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'flask_backend'))
os.chdir(ROOT)
import database as db

SRC = r'data\source_files\廠務編制\2026年6月份正式进度表 5 30.xlsx'
MOD = r'flask_backend\test_output\ds04_MODIFIED.xlsx'


def _run_parse(src_path):
    """Execute the REAL parse_ds04.py logic against a given source file, return all_records."""
    code = open('parse_ds04.py', encoding='utf-8').read()
    # swap only the SRC constant line (keep all parse logic identical)
    code = re.sub(r"SRC = r'[^']*'", "SRC = r'%s'" % src_path.replace('\\', '\\\\'), code, count=1)
    ns = {}
    exec(compile(code, 'parse_ds04.py', 'exec'), ns)
    return ns['all_records']


def setup():
    print('== SETUP: fresh DB @', db.DB_PATH)
    db.init_db()
    r = db.create_user('jim', 'Jim (E2E)', 'admin', 'admin123')
    print('  seed admin jim/admin123:', r)
    recs = _run_parse(SRC)
    res = db.ds04_import(recs, user='e2e_setup')
    print('  Step1 import:', res)
    verify()


def make_modified():
    """Copy real DS-04, change exactly ONE order qty cell, save to MOD."""
    import openpyxl
    os.makedirs(os.path.dirname(MOD), exist_ok=True)
    wb = openpyxl.load_workbook(SRC)
    target = None
    mf_re = re.compile(r'^(MF\d{4})([A-Z]{1,2}\d{4,6})((?:-\d+)+)--(\d+)(\(\d+/\d+\).*)', re.DOTALL)
    for ws in wb.worksheets:
        if not re.match(r'^\d+部', ws.title.strip()):
            continue
        for row in ws.iter_rows():
            for cell in row:
                v = str(cell.value or '')
                m = mf_re.match(v.strip())
                if m and '外包' not in v:
                    old_qty = int(m.group(4))
                    new_qty = old_qty + 777  # distinctive delta
                    cell.value = f"{m.group(1)}{m.group(2)}{m.group(3)}--{new_qty}{m.group(5)}"
                    target = {'sheet': ws.title, 'coord': cell.coordinate,
                              'order_no': f"{m.group(1)}{m.group(2)}{m.group(3)}",
                              'art': m.group(2), 'old_qty': old_qty, 'new_qty': new_qty,
                              'old_cell': v.strip(), 'new_cell': cell.value}
                    break
            if target: break
        if target: break
    wb.save(MOD)
    print('  modified saved:', MOD)
    print('  target change:', json.dumps(target, ensure_ascii=False))
    with open(r'flask_backend\test_output\ds04_mod_target.json', 'w', encoding='utf-8') as f:
        json.dump(target, f, ensure_ascii=False, indent=2)
    return target


def reimport():
    print('== STEP2: make modified copy + re-import (overwrite + change log)')
    tgt = make_modified()
    recs = _run_parse(MOD)
    res = db.ds04_import(recs, user='e2e_reimport')
    print('  Step2 re-import:', res)
    # inspect change log
    conn = db.get_conn()
    logs = conn.execute(
        "SELECT action,field_name,old_value,new_value,user_name FROM ds04_edit_log "
        "WHERE action LIKE 'reimport%' ORDER BY id DESC LIMIT 20"
    ).fetchall()
    print('  --- ds04_edit_log reimport rows (latest 20) ---')
    for l in logs:
        print('   ', dict(l))
    # does the target order now show new qty and appear in log?
    if tgt:
        rows = conn.execute(
            'SELECT dept,lean,art,order_no,qty FROM ds04_orders WHERE order_no=? AND art=?',
            (tgt['order_no'], tgt['art'])
        ).fetchall()
        print('  --- target order rows after reimport ---')
        for r in rows:
            print('   ', dict(r))
    conn.close()


def ietables():
    """Create EMPTY ie_process/ie_stage/ie_process_group (schema only, ZERO rows).
    Purpose: let /bianche exercise the 'no IE locked version' path (決策③ 紅底不擋單)
    instead of 500ing on a missing table. This is NOT fabricated business data —
    zero rows. DDL mirrors the production import scripts (via seed_stress_db)."""
    from tests.seed_stress_db import IE_PROCESS_DDL, IE_OTHER_DDL
    conn = db.get_conn()
    conn.execute(IE_PROCESS_DDL)
    for ddl in IE_OTHER_DDL:
        conn.execute(ddl)
    conn.commit()
    conn.close()
    db.init_db()  # adds stage_id / is_approved via inline migration
    conn = db.get_conn()
    for t in ('ie_process', 'ie_stage', 'ie_process_group'):
        n = conn.execute('SELECT COUNT(*) FROM %s' % t).fetchone()[0]
        print(f'  {t}: {n} rows (empty as intended)')
    conn.close()


def verify():
    conn = db.get_conn()
    total = conn.execute('SELECT COUNT(*) FROM ds04_orders WHERE COALESCE(is_deleted,0)=0').fetchone()[0]
    depts = conn.execute('SELECT dept, COUNT(*) c, SUM(qty) q FROM ds04_orders GROUP BY dept ORDER BY dept').fetchall()
    leans = [r[0] for r in conn.execute('SELECT DISTINCT lean FROM ds04_orders ORDER BY lean').fetchall()]
    outs = conn.execute('SELECT COUNT(*) FROM ds04_orders WHERE is_outsource_upper=1').fetchone()[0]
    dept11 = conn.execute("SELECT dept, COUNT(*) FROM ds04_orders WHERE dept LIKE '11部%' GROUP BY dept").fetchall()
    print(f'  TOTAL ds04_orders rows = {total}')
    print(f'  distinct LEAN codes ({len(leans)}): {leans}')
    print(f'  is_outsource_upper=1 rows = {outs}')
    print('  per-dept:', [(r[0], r[1], r[2]) for r in depts])
    print('  11部 variants:', [(r[0], r[1]) for r in dept11])
    conn.close()


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'setup'
    {'setup': setup, 'reimport': reimport, 'verify': verify, 'ietables': ietables}[mode]()
