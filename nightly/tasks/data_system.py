#!/usr/bin/env python3
"""
DATA SYSTEM nightly tasks:
  0. Check if 24_DATA_SYSTEM.md / 07_RULES.md have been updated → remind Jim
  1. Scan Biên chế/Jun/IE for new multi-ART IE files → import ob_epph
  2. Regenerate comparison_table.xlsx (if 廠務組織編制表 accessible)
  3. Produce mp_allocation_analysis.txt
  4. Auto-compare result_table vs 廠務組織編制表 → compare_result.txt
"""
import sys, os, hashlib, json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FLASK = os.path.join(ROOT, 'flask_backend')
sys.path.insert(0, FLASK)

IE_FOLDER  = r"C:\Users\user\OneDrive\Desktop\Biên chế\Jun\IE"
BIANCHE    = r"C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份廠務组织編制 20260524.xlsx"
SCHEDULE   = r"C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份正式进度表 5 30.xlsx"
OUTPUT_DIR = os.path.join(FLASK, 'test_output')
HASH_STATE = os.path.join(ROOT, 'nightly', 'tasks', '_file_hashes.json')

HANDOFF_FILES = {
    '24_DATA_SYSTEM.md': os.path.join(ROOT, '00_HANDOFF', '24_DATA_SYSTEM.md'),
    '07_RULES.md':       os.path.join(ROOT, '00_HANDOFF', '07_RULES.md'),
}


def _sha256(path):
    try:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def run(logger):
    """Entry point called by run_nightly.py. Returns True on success."""
    import database as db
    db.init_db()

    # ── Task 0: Check for updated handoff files ────────────────────────────
    logger.log('[data_system] Task 0: Check handoff file versions')
    try:
        stored = {}
        if os.path.exists(HASH_STATE):
            with open(HASH_STATE, 'r', encoding='utf-8') as f:
                stored = json.load(f)

        current = {name: _sha256(path) for name, path in HANDOFF_FILES.items()}
        updated = [name for name, h in current.items() if h and h != stored.get(name)]

        if updated:
            logger.log('[ACTION REQUIRED] Project files updated - Jim must re-upload to DATA SYSTEM Project:')
            for name in updated:
                logger.log(f'  - D:\\smartpn-atlas-core\\00_HANDOFF\\{name}')
            # Save new hashes
            stored.update({n: current[n] for n in updated if current[n]})
            with open(HASH_STATE, 'w', encoding='utf-8') as f:
                json.dump(stored, f, indent=2)
        else:
            logger.log('[data_system] Handoff files unchanged')
    except Exception as e:
        logger.log(f'[data_system] File check error: {e}')

    # ── Task 1: Import new IE files ────────────────────────────────────────
    logger.log('[data_system] Task 1: Import new Jun/IE files')
    try:
        from import_jun_ie import main as jun_ie_main
        # Temporarily redirect sys.argv so main() doesn't exit
        old_argv = sys.argv[:]
        sys.argv = ['import_jun_ie.py']
        _new = _run_jun_ie_import(logger)
        sys.argv = old_argv
        logger.log(f'[data_system] IE import: {_new} new records')
    except Exception as e:
        logger.log(f'[data_system] IE import error: {e}')

    # ── Task 2: Regenerate comparison_table.xlsx ───────────────────────────
    logger.log('[data_system] Task 2: Build comparison_table.xlsx')
    try:
        from build_comparison_xlsx import main as xlsx_main
        xlsx_main()
        logger.log('[data_system] comparison_table.xlsx written')
    except Exception as e:
        logger.log(f'[data_system] xlsx error: {e}')

    # ── Task 3: MP allocation analysis ────────────────────────────────────
    logger.log('[data_system] Task 3: MP allocation analysis')
    try:
        from analyze_ki1387 import main as alloc_main
        alloc_main()
        logger.log('[data_system] mp_allocation_analysis.txt written')
    except Exception as e:
        logger.log(f'[data_system] allocation analysis error: {e}')

    # ── Task 4: Auto-compare result_table vs 廠務組織編制表 ────────────────
    logger.log('[data_system] Task 4: Auto-compare result_table non-MP fields')
    try:
        result_path = os.path.join(OUTPUT_DIR, 'result_table_v2.xlsx')
        out_path    = os.path.join(OUTPUT_DIR, 'compare_result.txt')
        if os.path.exists(result_path) and os.path.exists(BIANCHE):
            from auto_compare import compare as auto_compare
            overall, lean_wrong, lean_missing, ref_only, ocs_diffs = auto_compare(
                result_path=result_path,
                bianche_path=BIANCHE,
                out_path=out_path,
            )
            if overall:
                logger.log('[data_system] compare_result: ✓ 100% 一致')
            else:
                logger.log(f'[data_system] compare_result: ✗ 差異 LEAN不符={lean_wrong} ART缺={lean_missing} 編制多={ref_only} OCS={ocs_diffs}')
        else:
            logger.log('[data_system] result_table or 廠務組織編制表 not found, skip compare')
    except Exception as e:
        logger.log(f'[data_system] auto-compare error: {e}')

    return True


def _run_jun_ie_import(logger):
    """Run Jun IE import inline, return count of new records."""
    import glob, re
    from import_jun_ie import all_arts_from_filename, art_already_in_db, save_secondary_art
    from import_ds03_batch import process_file, fn_eolr
    import database as db

    _SKIP = {'120双_FW26_GHOST SPRINT W_HQ3330..xlsx'}
    _ART_RE = re.compile(r'[A-Z]{2}\d{4,6}')

    files = glob.glob(os.path.join(IE_FOLDER, '**', '*.xlsx'), recursive=True)
    files = [f for f in files
             if not os.path.basename(f).startswith('~$')
             and os.path.basename(f) not in _SKIP]
    files.sort()

    total_new = 0

    for path in files:
        arts = _ART_RE.findall(os.path.basename(path))
        if not arts:
            continue
        eolr = fn_eolr(path) or 120
        primary = arts[0]
        secondaries = arts[1:]

        conn = db.get_conn()
        primary_exists = art_already_in_db(conn, primary, eolr)
        conn.close()

        if primary_exists:
            conn = db.get_conn()
            row = conn.execute(
                '''SELECT h.season, h.model, e.cutting, e.stitching, e.assembly, e.stock
                   FROM ob_header h JOIN ob_epph e ON e.header_id=h.id
                   WHERE h.art=? AND h.eolr=? ORDER BY h.id DESC LIMIT 1''',
                (primary, eolr)
            ).fetchone()
            conn.close()
            if not row:
                continue
            season, model = row[0], row[1]
            mp = {'cutting': row[2], 'stitching': row[3], 'assembly': row[4], 'stock': row[5]}
        else:
            r = process_file(path)
            if not r.get('ok'):
                continue
            mp = r.get('mp', {})
            hdr = r.get('header', {})
            season = hdr.get('season', '')
            model  = hdr.get('model', '')
            ob = r.get('ob_save', {})
            if ob and ob.get('new'):
                total_new += 1

        for art in secondaries:
            conn = db.get_conn()
            exists = art_already_in_db(conn, art, eolr)
            conn.close()
            if exists:
                continue
            r2 = save_secondary_art(art, eolr, season, model, mp)
            if r2.get('ok') and r2.get('new'):
                total_new += 1

    return total_new
