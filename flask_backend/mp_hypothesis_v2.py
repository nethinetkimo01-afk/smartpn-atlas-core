#!/usr/bin/env python3
"""
MP 假說驗證 v2 — 全 LEAN 完整版
假說：廠務MP = ob_epph.section × (actual_EOLR / ob_header.eolr)
本次驗證第一因素（線速縮放），暫不扣外移。
"""
import sys, os, re, sqlite3
from datetime import date, datetime
from statistics import mean, median

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB_PATH  = r"D:\smartpn-atlas-core\flask_backend\data\atlas.db"
BIANCHE  = r"C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份廠務组织編制 20260524.xlsx"
SHEET    = "6.2026"
OUTPUT   = r"D:\smartpn-atlas-core\flask_backend\test_output\mp_hypothesis_test.txt"

# Actual EOLR per LEAN (from 電腦針車手工表 M 欄)
LEAN_ACTUAL_EOLR = {
    '1A': 75,  '1B': 145, '1C': 145,
    '2A': 120, '2C': 130,
    '3A': 150,
    '5A': 135,
    '6A': 130, '6B': 130, '6C': 75,
    '7B': 145,
    '8A': 140, '8B': 120,
    '9A': 140, '9C': 80,
    '10B': 75,
    '11A1': 70, '11A2': 70,
}
SKIP_LEANS = {'2B', '3B', '10A', '11B1', '11B2'}

_ART_RE   = re.compile(r'[A-Z]{2}\d{4,6}')
_LEAN_PAT = re.compile(r'^\d+[A-Z]\d*$')
OCS_SECTS = {'組底配套', '自動化', '電腦針車', '印刷', '設備工程', 'RB', 'QC', '品包', '品管',
             '大底課', 'C2B合計', '合計', '副總室', '現場技轉/ KTHT', '設備工程部', '印刷高周波'}


def cell_num(v):
    """Extract numeric value from cell — handles datetime-as-serial-number."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return (v.date() - date(1900, 1, 1)).days + 1
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s in ('', '.', '編制', '-'):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


# ── Read BIANCHE ──────────────────────────────────────────────────────────────

def load_bianche():
    """
    Returns: dict {lean: {art: {'cut': float, 'stitch': float, 'asm': float}}}
    Multiple rows for same (lean, art) → last row wins.
    """
    import openpyxl
    wb = openpyxl.load_workbook(BIANCHE, data_only=True)
    ws = wb[SHEET]

    result   = {}   # lean -> {art: {...}}
    cur_lean = None

    for row in ws.iter_rows(values_only=True):
        col_a = str(row[0] or '').strip() if row else ''
        col_b = str(row[1] or '').strip() if len(row) > 1 else ''

        # LEAN group header (e.g. "1A", "11A2")
        if _LEAN_PAT.match(col_a):
            cur_lean = col_a if col_a in LEAN_ACTUAL_EOLR and col_a not in SKIP_LEANS else None
            # First model may be on the same row as the LEAN code (col_b non-empty)
            if cur_lean and col_b:
                _store_row(result, cur_lean, col_b, row)
            continue

        # Section label ("LEAN 1", "LEAN 2", OCS section names, summary lines, etc.)
        # Any non-empty col_a that is NOT a LEAN pattern → reset current lean
        if col_a:
            cur_lean = None
            continue

        # Continuation row: col_a empty, col_b has model+arts for current lean
        if cur_lean and col_b and len(col_b) > 2:
            _store_row(result, cur_lean, col_b, row)

    wb.close()
    return result


def _store_row(result, lean, col_b, row):
    arts = _ART_RE.findall(col_b)
    if not arts:
        return
    cut    = cell_num(row[7] if len(row) > 7 else None)
    stitch = cell_num(row[8] if len(row) > 8 else None)
    asm    = cell_num(row[9] if len(row) > 9 else None)
    if lean not in result:
        result[lean] = {}
    for art in arts:
        # Last row wins (取最新)
        result[lean][art] = {'cut': cut, 'stitch': stitch, 'asm': asm}


# ── DB Lookup ─────────────────────────────────────────────────────────────────

def get_db_epph(art):
    """
    Return latest ob_epph for art.
    → (design_eolr, cutting, stitching, assembly) or None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            '''SELECT h.eolr, e.cutting, e.stitching, e.assembly, h.updated_at
               FROM ob_epph e
               JOIN ob_header h ON h.id = e.header_id
               JOIN ob_articles a ON a.header_id = h.id
               WHERE a.art = ?
               ORDER BY h.updated_at DESC, h.id DESC
               LIMIT 1''',
            (art,)
        ).fetchone()
    finally:
        conn.close()
    if rows is None:
        return None
    return rows['eolr'], rows['cutting'], rows['stitching'], rows['assembly']


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import os
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    print("Loading BIANCHE 6.2026 ...")
    bianche = load_bianche()
    print(f"  LEANs loaded: {sorted(bianche.keys())}")
    for lean in sorted(bianche.keys()):
        print(f"  {lean}: {len(bianche[lean])} ARTs")

    lines   = []
    ratios  = []   # all non-null (scaled/actual) ratios
    detail_rows = []  # for summary stats

    W = 100
    lines.append('=' * W)
    lines.append('  MP 假說驗證報告 v2 — 全 LEAN 完整版')
    lines.append('  假說: 廠務MP ≈ ob_epph.section × (actual_EOLR / design_EOLR)')
    lines.append('  (第一因素驗證：線速縮放；外移扣除待後續)')
    lines.append('  判讀: 縮放後≥廠務 且 比值集中 1.0~1.5 → 假說方向正確')
    lines.append('')
    lines.append('  LEAN 實際EOLR: ' + ', '.join(f'{k}={v}' for k, v in sorted(LEAN_ACTUAL_EOLR.items())))
    lines.append('  跳過 LEAN: ' + ', '.join(sorted(SKIP_LEANS)))
    lines.append('=' * W)
    lines.append('')

    unmatched = []

    for lean in sorted(bianche.keys(), key=lambda x: (int(re.match(r'\d+', x).group()), x)):
        actual_eolr = LEAN_ACTUAL_EOLR.get(lean)
        if not actual_eolr:
            continue

        art_map = bianche[lean]
        if not art_map:
            continue

        lines.append(f'─── LEAN {lean}  (actual EOLR = {actual_eolr}) ' + '─' * (W - 20 - len(lean)))
        lines.append('')
        hdr = (f"  {'ART':<10}  {'段':<8}  {'ob原值':>8}  {'縮放後':>8}  {'廠務實際':>8}  {'比值':>6}  note")
        lines.append(hdr)
        lines.append('  ' + '─' * (W - 4))

        for art in sorted(art_map.keys()):
            fac = art_map[art]
            epph = get_db_epph(art)

            if epph is None:
                unmatched.append({'lean': lean, 'art': art})
                lines.append(f"  {art:<10}  (未找到 IE 資料)")
                continue

            design_eolr, db_cut, db_stitch, db_asm = epph
            if not design_eolr:
                lines.append(f"  {art:<10}  (design_eolr=0, 無法縮放)")
                continue

            scale = actual_eolr / design_eolr

            sections = [
                ('裁斷', db_cut,    fac['cut']),
                ('針車', db_stitch, fac['stitch']),
                ('成型', db_asm,    fac['asm']),
            ]

            for sec_name, ob_val, fac_val in sections:
                if ob_val is None:
                    lines.append(f"  {art:<10}  {sec_name:<8}  {'–':>8}  {'–':>8}  {fmt(fac_val):>8}  {'–':>6}")
                    continue

                scaled = round(ob_val * scale, 2)

                if fac_val is None or fac_val == 0:
                    ratio_str = '–'
                    note = '廠務無值'
                else:
                    ratio = scaled / fac_val
                    ratio_str = f'{ratio:.3f}'
                    note = ''
                    if scaled >= fac_val:
                        if 1.0 <= ratio <= 1.5:
                            note = 'OK'
                        else:
                            note = f'比值偏高({ratio:.2f})'
                    else:
                        note = f'縮放低於廠務({ratio:.2f})'
                    ratios.append(ratio)
                    detail_rows.append({
                        'lean': lean, 'art': art, 'sec': sec_name,
                        'ob': ob_val, 'scaled': scaled, 'fac': fac_val,
                        'ratio': ratio, 'design_eolr': design_eolr,
                    })

                lines.append(
                    f"  {art:<10}  {sec_name:<8}  {fmt(ob_val):>8}  {scaled:>8.2f}"
                    f"  {fmt(fac_val):>8}  {ratio_str:>6}  {note}"
                )

        lines.append('')

    # ── Unmatched ─────────────────────────────────────────────────────────────
    if unmatched:
        lines.append('=' * W)
        lines.append('  UNMATCHED (廠務有但 IE DB 無資料)')
        lines.append('=' * W)
        for u in unmatched:
            lines.append(f"  LEAN {u['lean']:<8}  ART {u['art']}")
        lines.append('')

    # ── Summary ───────────────────────────────────────────────────────────────
    lines.append('=' * W)
    lines.append('  SUMMARY')
    lines.append('=' * W)

    total_arts  = sum(len(v) for v in bianche.values())
    matched     = total_arts - len(unmatched)
    n_ratios    = len(ratios)

    lines.append(f"  廠務 ART 總數:   {total_arts}")
    lines.append(f"  有 IE 資料:      {matched}")
    lines.append(f"  無 IE 資料:      {len(unmatched)}")
    lines.append(f"  有效比值筆數:    {n_ratios}  (section × ART)")
    lines.append('')

    if ratios:
        r_mean   = mean(ratios)
        r_median = median(ratios)
        r_min    = min(ratios)
        r_max    = max(ratios)
        in_range = sum(1 for r in ratios if 1.0 <= r <= 1.5)
        below_1  = sum(1 for r in ratios if r < 1.0)
        above_15 = sum(1 for r in ratios if r > 1.5)

        lines.append(f"  比值分佈 (scaled / 廠務):")
        lines.append(f"    平均值:         {r_mean:.3f}")
        lines.append(f"    中位數:         {r_median:.3f}")
        lines.append(f"    最小值:         {r_min:.3f}")
        lines.append(f"    最大值:         {r_max:.3f}")
        lines.append(f"    1.0~1.5 筆數:   {in_range}  ({in_range/n_ratios*100:.1f}%)")
        lines.append(f"    < 1.0  筆數:    {below_1}  ({below_1/n_ratios*100:.1f}%)")
        lines.append(f"    > 1.5  筆數:    {above_15}  ({above_15/n_ratios*100:.1f}%)")
        lines.append('')

        # By section
        for sec in ['裁斷', '針車', '成型']:
            sec_rows = [d for d in detail_rows if d['sec'] == sec]
            if not sec_rows:
                continue
            sec_ratios = [d['ratio'] for d in sec_rows]
            lines.append(f"  [{sec}] n={len(sec_ratios)}  mean={mean(sec_ratios):.3f}  median={median(sec_ratios):.3f}"
                         f"  min={min(sec_ratios):.3f}  max={max(sec_ratios):.3f}")
        lines.append('')

        lines.append('  判讀:')
        if r_median >= 1.0 and in_range / n_ratios >= 0.50:
            lines.append(f'  ✓ 假說方向正確：縮放後中位數 {r_median:.3f} ≥ 1.0，'
                         f'{in_range/n_ratios*100:.1f}% 比值在 1.0~1.5 區間')
            lines.append(f'    多出的部分（比值 - 1.0）對應外移單位勾走的 MP')
        elif r_median >= 1.0:
            lines.append(f'  ~ 方向可能正確但比值分散：中位數 {r_median:.3f} ≥ 1.0，'
                         f'但只有 {in_range/n_ratios*100:.1f}% 在 1.0~1.5 區間')
            lines.append(f'    需進一步檢查比值偏高/偏低的 ART')
        else:
            lines.append(f'  ✗ 假說有問題：縮放後中位數 {r_median:.3f} < 廠務值，'
                         f'縮放後低於廠務值的佔 {below_1/n_ratios*100:.1f}%')
    else:
        lines.append('  無有效比值資料，無法判讀')

    lines.append('')
    lines.append('  Note: 純讀取驗證，未修改任何資料。')
    lines.append('=' * W)

    text = '\n'.join(lines)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(text + '\n')
    print(f'\n[Written to {OUTPUT}]')
    print(text)


def fmt(v):
    if v is None:
        return '–'
    return f'{v:.2f}'


if __name__ == '__main__':
    main()
