#!/usr/bin/env python3
"""
full_compare_report.py
Detailed row-by-row comparison of result_table_v2.xlsx vs 廠務組織編制表 6.2026.
For every CSA row: LEAN / 鞋型 / ART / 訂單 → OK or DIFF.
For every OCS tab unit: headcount → OK or DIFF.
Outputs to test_output/full_compare_report.txt.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import openpyxl

RESULT_PATH  = r'D:\smartpn-atlas-core\flask_backend\test_output\result_table_v2.xlsx'
BIANCHE_PATH = r'C:\Users\user\AppData\Local\Temp\bianche_tmp.xlsx'
OUT_PATH     = r'D:\smartpn-atlas-core\flask_backend\test_output\full_compare_report.txt'
MONTH_SH     = '6.2026'
OCS_SECTIONS = ['組底配套', '自動化', '電腦針車', '印刷', '設備工程']
_ART_RE      = re.compile(r'[A-Z]{2}\d{4,6}')


# ── Load 廠務組織編制表 ──────────────────────────────────────────────────────────
def load_bianche(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = next((wb[s] for s in wb.sheetnames if s.strip() == MONTH_SH), None)
    if ws is None:
        wb.close(); return {}, {}

    def _num(row, idx):
        v = row[idx] if len(row) > idx else None
        if v is None or str(v).strip() in ('.', '', '編制'): return None
        try: return float(v)
        except: return None

    def _hc(row):
        for idx in [12, 10, 14]:
            v = row[idx] if len(row) > idx else None
            if v is not None and str(v).strip() not in ('', '.', '編制'):
                try: return int(float(v))
                except: pass
        return None

    art_to_ref  = {}   # {art: {lean, model, order}}
    ocs_ref     = {s: [] for s in OCS_SECTIONS}
    lean        = ''
    ocs_sec     = None

    for row in ws.iter_rows(values_only=True):
        col1 = str(row[0] or '').strip() if row else ''
        col2 = str(row[1] or '').strip() if len(row) > 1 else ''

        if re.match(r'^\d+[A-Z]\d*$', col1):
            lean    = col1
            ocs_sec = None
            if col2 and col2 not in ('編制', ''):
                entry = {'lean': lean, 'model': col2, 'order': _num(row, 6)}
                for a in _ART_RE.findall(col2):
                    if a not in art_to_ref:
                        art_to_ref[a] = entry
            continue

        if col1 in OCS_SECTIONS:
            ocs_sec = col1
            lean    = ''
            if col2 and col2 not in ('編制', ''):
                ocs_ref[ocs_sec].append({'unit': col2, 'hc': _hc(row)})
            continue

        if lean and not col1 and col2 and col2 not in ('編制', ''):
            entry = {'lean': lean, 'model': col2, 'order': _num(row, 6)}
            for a in _ART_RE.findall(col2):
                if a not in art_to_ref:
                    art_to_ref[a] = entry
            continue

        if ocs_sec and not col1 and col2 and col2 not in ('編制', ''):
            ocs_ref[ocs_sec].append({'unit': col2, 'hc': _hc(row)})
            continue

        if col1 and col1 not in OCS_SECTIONS:
            lean    = ''
            ocs_sec = None

    wb.close()
    return art_to_ref, ocs_ref


# ── Load result_table CSA ────────────────────────────────────────────────────
def load_result_csa(path):
    wb  = openpyxl.load_workbook(path, data_only=True)
    ws  = wb['CSA']
    out = []
    cur_section = ''
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        if i <= 2:
            continue
        col_a = str(row[0] or '').strip()
        col_b = str(row[1] or '').strip() if len(row) > 1 else ''
        col_c = str(row[2] or '').strip() if len(row) > 2 else ''
        col_d = row[3] if len(row) > 3 else None
        # Detect section headers (merged rows like ── 1部 ──)
        if col_b.startswith('──') or col_a.startswith('──') or (not col_c and not col_d and col_b):
            if '──' in col_a or '──' in col_b:
                cur_section = col_a or col_b
                continue
        if not _ART_RE.fullmatch(col_c):
            if col_a.startswith('──') or col_b.startswith('──'):
                cur_section = col_a or col_b
            continue
        try:
            qty = int(float(col_d)) if col_d is not None else 0
        except (ValueError, TypeError):
            qty = 0
        out.append({
            'section': cur_section,
            'lean':    col_a,
            'model':   col_b,
            'art':     col_c,
            'order':   qty,
        })
    wb.close()
    return out


# ── Load result OCS tabs ─────────────────────────────────────────────────────
def load_result_ocs(path):
    wb  = openpyxl.load_workbook(path, data_only=True)
    out = {}
    for sec in OCS_SECTIONS:
        tab = f'OCS_{sec}'
        if tab not in wb.sheetnames:
            out[sec] = None
            continue
        ws   = wb[tab]
        rows = []
        for i, row in enumerate(ws.iter_rows(values_only=True), 1):
            if i <= 2: continue
            col_a = str(row[0] or '').strip()
            col_b = row[1] if len(row) > 1 else None
            if not col_a or col_a in ('單位', '合計') or col_a.startswith('（'):
                continue
            try:
                hc = int(float(col_b)) if col_b is not None else None
            except (ValueError, TypeError):
                hc = None
            rows.append({'unit': col_a, 'hc': hc})
        out[sec] = rows
    wb.close()
    return out


# ── Main ────────────────────────────────────────────────────────────────────
def run(result_path=RESULT_PATH, bianche_path=BIANCHE_PATH, out_path=OUT_PATH):
    art_to_ref, ocs_ref = load_bianche(bianche_path)
    csa_rows            = load_result_csa(result_path)
    ocs_result          = load_result_ocs(result_path)

    lines = []
    W = 110

    def hdr(title):
        lines.append('=' * W)
        lines.append(f'  {title}')
        lines.append('=' * W)

    def sub(title):
        lines.append('')
        lines.append(f'── {title} ' + '─' * max(0, W - len(title) - 4))

    hdr('完整比對報告：result_table_v2.xlsx  vs  廠務組織編制表 6.2026')
    lines.append(f'結果表: {os.path.basename(result_path)}')
    lines.append(f'廠務表: {os.path.basename(bianche_path)}')
    lines.append(f'廠務 ART 索引: {len(art_to_ref)} 筆    CSA 行數: {len(csa_rows)} 筆')

    # ── CSA Section ───────────────────────────────────────────────────────────
    sub('CSA — LEAN / 鞋型 / ART / 訂單 逐行比對')
    lines.append('')
    FMT  = '{status:<6}  {art:<12}  {r_lean:<8}  {b_lean:<8}  {lean_ok:<5}  {r_order:>7}  {b_order:>7}  {ord_ok:<5}  {note}'
    lines.append(FMT.format(
        status='STATUS', art='ART', r_lean='結果LEAN', b_lean='廠務LEAN',
        lean_ok='LEAN?', r_order='結果訂單', b_order='廠務訂單', ord_ok='訂單?', note='鞋型/備註'
    ))
    lines.append('-' * W)

    cur_section = ''
    lean_ok_n = lean_diff_n = lean_missing_n = order_ok_n = order_diff_n = 0
    art_not_in_ref = []

    for r in csa_rows:
        art    = r['art']
        r_lean = r['lean']
        r_ord  = r['order']
        r_mod  = r['model']

        if r['section'] != cur_section:
            cur_section = r['section']
            lines.append('')
            lines.append(f'  >>> {cur_section}')
            lines.append('')

        if art.startswith('MF'):
            lines.append(FMT.format(
                status='SKIP', art=art, r_lean=r_lean, b_lean='—',
                lean_ok='n/a', r_order=r_ord, b_order='—', ord_ok='n/a',
                note='MF前綴跳過'
            ))
            continue

        if art not in art_to_ref:
            art_not_in_ref.append(r)
            lean_missing_n += 1
            lines.append(FMT.format(
                status='MISS', art=art, r_lean=r_lean, b_lean='?',
                lean_ok='??', r_order=r_ord, b_order='?', ord_ok='??',
                note='不在廠務編制表'
            ))
            continue

        ref     = art_to_ref[art]
        b_lean  = ref['lean']
        b_ord   = ref['order']
        b_mod   = ref['model']

        lean_match = (r_lean == b_lean)
        if lean_match:
            lean_ok_n   += 1
            lean_flag    = 'OK'
        else:
            lean_diff_n += 1
            lean_flag    = 'DIFF'

        if b_ord is not None:
            ord_match = (abs(r_ord - b_ord) < 0.5)
            ord_flag  = 'OK' if ord_match else 'DIFF'
            if ord_match: order_ok_n += 1
            else:         order_diff_n += 1
        else:
            ord_flag  = 'N/A'

        status = 'OK' if (lean_match and (b_ord is None or ord_flag == 'OK')) else 'DIFF'

        note = ''
        if r_mod[:30] != b_mod[:30]:
            note = f'鞋型: 結={r_mod[:25]!r}  廠={b_mod[:25]!r}'

        b_ord_str = str(int(b_ord)) if b_ord is not None else '—'
        lines.append(FMT.format(
            status=status, art=art,
            r_lean=r_lean or '(空)', b_lean=b_lean,
            lean_ok=lean_flag,
            r_order=r_ord, b_order=b_ord_str,
            ord_ok=ord_flag,
            note=note
        ))

    lines.append('')
    lines.append('─' * W)
    lines.append(f'CSA 總計: OK={lean_ok_n}  LEAN不符={lean_diff_n}  ART缺={lean_missing_n}')
    lines.append(f'訂單:     OK={order_ok_n}  DIFF={order_diff_n}')

    # List missing ARTs
    if art_not_in_ref:
        lines.append('')
        lines.append(f'⚠  不在廠務編制表的 ART ({len(art_not_in_ref)} 筆):')
        for r in art_not_in_ref:
            lines.append(f"   {r['art']:12s}  LEAN={r['lean']!r:8s}  DS-04訂單={r['order']}")

    # ARTs in ref but not in result
    result_arts = {r['art'] for r in csa_rows if not r['art'].startswith('MF')}
    ref_only    = sorted(a for a in art_to_ref if a not in result_arts)
    if ref_only:
        lines.append('')
        lines.append(f'⚠  廠務編制表有但結果表無的 ART ({len(ref_only)} 筆):')
        for a in ref_only:
            ref = art_to_ref[a]
            lines.append(f"   {a:12s}  廠務LEAN={ref['lean']!r:8s}  廠務鞋型={ref['model'][:40]!r}")

    # ── OCS Sections ─────────────────────────────────────────────────────────
    sub('OCS 固定單位 — 逐 Tab 比對')

    ocs_total_ok   = 0
    ocs_total_diff = 0

    for sec in OCS_SECTIONS:
        lines.append('')
        lines.append(f'  Tab: OCS_{sec}')
        ref_units = ocs_ref.get(sec, [])
        res_units = ocs_result.get(sec)

        if res_units is None:
            lines.append(f'    ✗ Tab 缺失')
            ocs_total_diff += 1
            continue

        ref_map = {u['unit']: u['hc'] for u in ref_units}
        res_map = {u['unit']: u['hc'] for u in res_units}
        sec_ok = sec_diff = 0

        all_units = sorted(set(list(ref_map.keys()) + list(res_map.keys())))
        for unit in all_units:
            r_hc  = res_map.get(unit)
            b_hc  = ref_map.get(unit)
            if unit in ref_map and unit in res_map:
                match = (r_hc == b_hc)
                flag  = 'OK  ' if match else 'DIFF'
                if match: sec_ok += 1
                else:     sec_diff += 1
                lines.append(f'    {flag}  {unit:<30}  結果={str(r_hc):>4}  廠務={str(b_hc):>4}')
            elif unit in ref_map:
                sec_diff += 1
                lines.append(f'    MISS  {unit:<30}  結果=   ?  廠務={str(b_hc):>4}')
            else:
                sec_diff += 1
                lines.append(f'    XTRA  {unit:<30}  結果={str(r_hc):>4}  廠務=   ?')

        verdict = '✓ 全部一致' if sec_diff == 0 else f'✗ {sec_diff} 筆差異'
        lines.append(f'    {"─"*50}  小計: OK={sec_ok}  DIFF={sec_diff}  {verdict}')
        ocs_total_ok   += sec_ok
        ocs_total_diff += sec_diff

    # ── Final Summary ──────────────────────────────────────────────────────────
    lines.append('')
    hdr('總結')
    csa_label = '✓ LEAN 100%一致' if lean_diff_n == 0 and lean_missing_n == 0 and not ref_only \
                else f'✗  LEAN不符={lean_diff_n}  ART缺={lean_missing_n}  廠務多={len(ref_only)}'
    ocs_label = '✓ 100%一致' if ocs_total_diff == 0 else f'✗ {ocs_total_diff} 筆差異'
    lines.append(f'CSA LEAN:  {csa_label}')
    lines.append(f'OCS 單位:  {ocs_label}')
    overall   = (lean_diff_n == 0 and lean_missing_n == 0 and not ref_only and ocs_total_diff == 0)
    lines.append('')
    lines.append('整體結論: ' + ('✓ 100% 一致' if overall else '✗ 有差異（見上方清單）'))

    text = '\n'.join(lines)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(text)
    return text


if __name__ == '__main__':
    run()
