#!/usr/bin/env python3
"""
DATA SYSTEM nightly tasks:
  0. Check if 24_DATA_SYSTEM.md / 07_RULES.md have been updated → remind Jim
  1. Scan Biên chế/Jun/IE for new multi-ART IE files → import ob_epph
  2. Regenerate comparison_table.xlsx (if 廠務組織編制表 accessible)
  3. Produce mp_allocation_analysis.txt
  4. Auto-compare result_table vs 廠務組織編制表 → compare_result.txt
  5. Write execution summary to 00_HANDOFF/24_DATA_SYSTEM.md
"""
import sys, os, hashlib, json, re, datetime

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


def _parse_compare_result(out_path):
    """Parse compare_result.txt, return summary dict."""
    summary = {}
    try:
        with open(out_path, 'r', encoding='utf-8') as f:
            text = f.read()
        m = re.search(r'✓ 一致:\s*(\d+)', text)
        if m:
            summary['lean_ok'] = int(m.group(1))
        m = re.search(r'LEAN不符(\d+)筆', text)
        if m:
            summary['lean_wrong'] = int(m.group(1))
        m = re.search(r'ART缺(\d+)筆', text)
        if m:
            summary['lean_missing'] = int(m.group(1))
        m = re.search(r'編制表多(\d+)筆', text)
        if m:
            summary['ref_only'] = int(m.group(1))
        if '100%一致' in text or '✓ 完全一致' in text:
            summary['ocs_status'] = '✓ 5 Tab 100% 一致'
        else:
            summary['ocs_status'] = '有差異（見報告）'
    except Exception:
        pass
    return summary


def _write_handoff_summary(logger, task_results, compare_summary):
    """Write/replace ## 最新執行結果 block in 00_HANDOFF/24_DATA_SYSTEM.md."""
    handoff_path = os.path.join(ROOT, '00_HANDOFF', '24_DATA_SYSTEM.md')
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    def _icon(st):
        if st.startswith('ok'):   return '✅'
        if st.startswith('skip'): return '⏭️'
        if st.startswith('error'): return '❌'
        return '❓'

    task_rows = '\n'.join(
        f'| {name} | {_icon(st)} {st} |'
        for name, st in task_results.items()
    )

    if compare_summary:
        lean_ok      = compare_summary.get('lean_ok', '?')
        lean_wrong   = compare_summary.get('lean_wrong', '?')
        lean_missing = compare_summary.get('lean_missing', '?')
        ref_only     = compare_summary.get('ref_only', '?')
        ocs_status   = compare_summary.get('ocs_status', '?')
        compare_block = (
            f'| LEAN 一致 | {lean_ok} 筆 |\n'
            f'| LEAN 不符 | {lean_wrong} 筆（跨部門業務差異，不處理） |\n'
            f'| ART DS04有/廠務無 | {lean_missing} 筆 |\n'
            f'| ART 廠務有/DS04無 | {ref_only} 筆 |\n'
            f'| OCS 固定單位 | {ocs_status} |'
        )
    else:
        compare_block = '（compare_result.txt 未產生或無法解析）'

    # Dynamic "需要確認" items
    confirm_items = [
        '- EOLR mapping：每個組別對應哪個 EOLR？（PENDING）',
        '- MP 分配規則：DB ob_epph 整條產線 MP vs 廠務編制表分配後 MP，差距約 2~3 倍（PENDING）',
    ]
    if compare_summary:
        if compare_summary.get('lean_missing', 0):
            confirm_items.append(
                f'- DS04 有/廠務無 ART **{compare_summary["lean_missing"]}** 筆 — 是否需補登廠務編制表？'
            )
        if compare_summary.get('ref_only', 0):
            confirm_items.append(
                f'- 廠務有/DS04 無 ART **{compare_summary["ref_only"]}** 筆（JS1068, LEAN=7A）— 廠務表是否刪除？'
            )
    confirm_block = '\n'.join(confirm_items)

    block = f"""

## 最新執行結果

**執行時間**：{now}

### 各任務狀態

| 任務 | 狀態 |
|------|------|
{task_rows}

### LEAN / OCS 比對摘要

| 項目 | 數值 |
|------|------|
{compare_block}

### 需要 Jim 確認的事項

{confirm_block}
"""

    try:
        with open(handoff_path, 'r', encoding='utf-8') as f:
            content = f.read()

        marker = '\n## 最新執行結果'
        if marker in content:
            content = content[:content.index(marker)]

        with open(handoff_path, 'w', encoding='utf-8') as f:
            f.write(content.rstrip() + block)

        logger.log('[data_system] 24_DATA_SYSTEM.md ## 最新執行結果 已更新')
    except Exception as e:
        logger.log(f'[data_system] 寫入 handoff 摘要失敗: {e}')


def run(logger):
    """Entry point called by run_nightly.py. Returns True on success."""
    import database as db
    db.init_db()

    task_results = {}

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
            stored.update({n: current[n] for n in updated if current[n]})
            with open(HASH_STATE, 'w', encoding='utf-8') as f:
                json.dump(stored, f, indent=2)
        else:
            logger.log('[data_system] Handoff files unchanged')
        task_results['T0 檔案版本檢查'] = 'ok'
    except Exception as e:
        logger.log(f'[data_system] File check error: {e}')
        task_results['T0 檔案版本檢查'] = 'error'

    # ── Task 1: Import new IE files ────────────────────────────────────────
    logger.log('[data_system] Task 1: Import new Jun/IE files')
    try:
        old_argv = sys.argv[:]
        sys.argv = ['import_jun_ie.py']
        _new = _run_jun_ie_import(logger)
        sys.argv = old_argv
        logger.log(f'[data_system] IE import: {_new} new records')
        task_results['T1 IE 匯入'] = f'ok ({_new} new)'
    except Exception as e:
        logger.log(f'[data_system] IE import error: {e}')
        task_results['T1 IE 匯入'] = 'error'

    # ── Task 2: Regenerate comparison_table.xlsx ───────────────────────────
    logger.log('[data_system] Task 2: Build comparison_table.xlsx')
    try:
        from build_comparison_xlsx import main as xlsx_main
        xlsx_main()
        logger.log('[data_system] comparison_table.xlsx written')
        task_results['T2 comparison_table.xlsx'] = 'ok'
    except Exception as e:
        logger.log(f'[data_system] xlsx error: {e}')
        task_results['T2 comparison_table.xlsx'] = 'error'

    # ── Task 3: MP allocation analysis ────────────────────────────────────
    logger.log('[data_system] Task 3: MP allocation analysis')
    try:
        from analyze_ki1387 import main as alloc_main
        alloc_main()
        logger.log('[data_system] mp_allocation_analysis.txt written')
        task_results['T3 MP 分配分析'] = 'ok'
    except Exception as e:
        logger.log(f'[data_system] allocation analysis error: {e}')
        task_results['T3 MP 分配分析'] = 'error'

    # ── Task 4: Auto-compare result_table vs 廠務組織編制表 ────────────────
    logger.log('[data_system] Task 4: Auto-compare result_table non-MP fields')
    compare_summary = {}
    out_path = os.path.join(OUTPUT_DIR, 'compare_result.txt')
    try:
        result_path = os.path.join(OUTPUT_DIR, 'result_table_v2.xlsx')
        if os.path.exists(result_path) and os.path.exists(BIANCHE):
            from auto_compare import compare as auto_compare
            overall, lean_wrong, lean_missing, ref_only, ocs_diffs = auto_compare(
                result_path=result_path,
                bianche_path=BIANCHE,
                out_path=out_path,
            )
            if overall:
                logger.log('[data_system] compare_result: ✓ 100% 一致')
                task_results['T4 LEAN/OCS 比對'] = 'ok ✓ 100%一致'
            else:
                logger.log(f'[data_system] compare_result: ✗ 差異 LEAN不符={lean_wrong} ART缺={lean_missing} 編制多={ref_only} OCS={ocs_diffs}')
                task_results['T4 LEAN/OCS 比對'] = f'ok (差異: LEAN不符={lean_wrong} 缺={lean_missing})'
            compare_summary = _parse_compare_result(out_path)
        else:
            logger.log('[data_system] result_table or 廠務組織編制表 not found, skip compare')
            task_results['T4 LEAN/OCS 比對'] = 'skip'
            # Try to parse existing compare_result.txt if available
            if os.path.exists(out_path):
                compare_summary = _parse_compare_result(out_path)
    except Exception as e:
        logger.log(f'[data_system] auto-compare error: {e}')
        task_results['T4 LEAN/OCS 比對'] = 'error'
        if os.path.exists(out_path):
            compare_summary = _parse_compare_result(out_path)

    # ── Task 5: DS-04 成型进度 section fix + rebuild auto_bianche.xlsx ────────
    logger.log('[data_system] Task 5: Generate auto_bianche.xlsx (成型进度 section fix)')
    try:
        import shutil, tempfile
        import build_result_table as brt

        # Patch brt to use temp copies (source files may be locked by Excel)
        def _tmp(orig):
            dst = os.path.join(tempfile.gettempdir(), os.path.basename(orig))
            shutil.copy2(orig, dst)
            return dst

        brt.SCHEDULE = _tmp(SCHEDULE)
        brt.BIANCHE  = _tmp(BIANCHE)

        # Verify JQ0597 = 5,268 after section fix
        sheets = brt.load_schedule()
        jq0597_qty = 0
        for s in sheets:
            for r in s['rows']:
                if r['art'] == 'JQ0597' and r['lean'] == '7B':
                    jq0597_qty += r['qty']

        if jq0597_qty == 5268:
            logger.log(f'[data_system] JQ0597 LEAN=7B = {jq0597_qty:,} ✓ (expected 5,268)')
        else:
            logger.log(f'[data_system] WARNING: JQ0597 LEAN=7B = {jq0597_qty:,} (expected 5,268)')

        # Rebuild auto_bianche.xlsx
        import generate_bianche as gb
        gb.brt.SCHEDULE = brt.SCHEDULE
        gb.brt.BIANCHE  = brt.BIANCHE
        lean_by_art = gb.load_ds04_by_lean()
        bianche_path = gb._safe_bianche()
        ocs, rbqc = gb.load_ocs_rb_qc(bianche_path)
        import openpyxl
        wb_out = openpyxl.Workbook()
        ws_out = wb_out.active
        ws_out.title = gb.MONTH_SH
        gb.build_sheet(ws_out, lean_by_art, ocs, rbqc)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        wb_out.save(gb.OUT_PATH)
        total_rows = sum(len(v) for v in lean_by_art.values())
        logger.log(f'[data_system] auto_bianche.xlsx rebuilt: {len(lean_by_art)} LEAN groups, {total_rows} rows')
        task_results['T5 auto_bianche生成'] = f'ok (JQ0597={jq0597_qty:,})'
    except Exception as e:
        logger.log(f'[data_system] Task 5 error: {e}')
        task_results['T5 auto_bianche生成'] = f'error: {e}'

    # ── Task 6: Run bianche_diff → bianche_diff.txt + bianche_diff_v2.txt ──
    logger.log('[data_system] Task 6: Run bianche_diff')
    try:
        from bianche_diff import run as bianche_diff_run
        bianche_diff_run()

        # Copy to bianche_diff_v2.txt for versioned archive
        src = os.path.join(OUTPUT_DIR, 'bianche_diff.txt')
        dst = os.path.join(OUTPUT_DIR, 'bianche_diff_v2.txt')
        if os.path.exists(src):
            shutil.copy2(src, dst)
            logger.log(f'[data_system] bianche_diff.txt + bianche_diff_v2.txt written')

        task_results['T6 bianche_diff'] = 'ok'
    except Exception as e:
        logger.log(f'[data_system] Task 6 error: {e}')
        task_results['T6 bianche_diff'] = f'error: {e}'

    # ── Task 7: Write summary to 24_DATA_SYSTEM.md ────────────────────────
    logger.log('[data_system] Task 7: Write summary to 24_DATA_SYSTEM.md')
    _write_handoff_summary(logger, task_results, compare_summary)

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
