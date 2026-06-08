#!/usr/bin/env python3
"""
ds04_pipeline.py — DS-04 製令取值流程（Rule 20 設計）

Step 1: 讀取所有製令明細 → test_output/ds04_order_detail.txt
Step 2: 每筆製令對應廠務組織編制表（ART + LEAN）
Step 3: 輸出對比報告 → test_output/ds04_vs_bianche.txt
Step 4: 重建 auto_bianche.xlsx（含製令明細 tab）

執行: python ds04_pipeline.py
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from itertools import groupby
import generate_bianche as gb
from full_compare_report import load_bianche

OUT_DIR    = r'D:\smartpn-atlas-core\flask_backend\test_output'
DETAIL_TXT = os.path.join(OUT_DIR, 'ds04_order_detail.txt')
DIFF_TXT   = os.path.join(OUT_DIR, 'ds04_vs_bianche.txt')
W = 120


# ── Step 1 ────────────────────────────────────────────────────────────────────

def step1_extract(records):
    """Write ds04_order_detail.txt — one row per MF order."""
    recs = sorted(records,
                  key=lambda r: (gb._lean_sort_key(r['lean']), r['art'], r['mf_order']))

    lean_stat = {}
    for r in recs:
        s = lean_stat.setdefault(r['lean'], {'n': 0, 'qty': 0})
        s['n']   += 1
        s['qty'] += r['qty']

    HDR = ('  {:<28} {:<12} {:<7} {:<14} {:<8} {:>8}  {}'
           .format('製令號碼', 'ART', 'LEAN', '部門(Sheet)', '段落', '訂單量', '交期'))
    FMT = '  {mf_order:<28} {art:<12} {lean:<7} {sheet:<14} {section:<8} {qty:>8,}  {date}'

    lines = []
    lines.append('=' * W)
    lines.append(f'  DS-04 製令明細 — {gb.MONTH_SH}  |  共 {len(recs)} 張製令')
    lines.append('=' * W)
    lines.append('')
    lines.append(HDR)
    lines.append('  ' + '-' * (W - 2))

    cur_lean = None
    for r in recs:
        if r['lean'] != cur_lean:
            s = lean_stat[r['lean']]
            lines.append(
                f'\n── LEAN {r["lean"]}  ({s["n"]} 張製令 / 合計 {s["qty"]:,} 對)'
            )
            cur_lean = r['lean']
        lines.append(FMT.format(**r))

    lines.append('')
    lines.append('=' * W)
    lines.append('  LEAN 小計')
    lines.append('  ' + '-' * 60)
    total_n = total_qty = 0
    for lean in sorted(lean_stat, key=gb._lean_sort_key):
        s = lean_stat[lean]
        lines.append(f'  LEAN {lean:<8}  {s["n"]:>4} 張製令  合計 {s["qty"]:>9,} 對')
        total_n  += s['n']
        total_qty += s['qty']
    lines.append(f'  {"─"*60}')
    lines.append(f'  {"總計":<10}  {total_n:>4} 張製令  合計 {total_qty:>9,} 對')
    lines.append('=' * W)

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(DETAIL_TXT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'  → {DETAIL_TXT}  ({len(recs)} 筆)')
    return recs  # sorted


# ── Step 2+3 ──────────────────────────────────────────────────────────────────

def step2_3_compare(recs_sorted, art_to_ref):
    """Match each MF order to factory table; write ds04_vs_bianche.txt."""

    # Build per-(lean, art) groups with comparison mark
    groups = []
    for (lean, art), grp_it in groupby(recs_sorted, key=lambda r: (r['lean'], r['art'])):
        buf        = list(grp_it)
        ds04_total = sum(o['qty'] for o in buf)
        ref        = art_to_ref.get(art, {})
        fac_lean   = ref.get('lean', '')
        fac_qty    = ref.get('order')

        if art not in art_to_ref:
            mark = '廠務無此ART'
        elif fac_lean != lean:
            mark = f'廠務LEAN不符 (廠務={fac_lean})'
        elif fac_qty is None:
            mark = '廠務無訂單量'
        elif abs(ds04_total - int(fac_qty)) < 1:
            mark = '✓ 一致'
        else:
            diff = ds04_total - int(fac_qty)
            pct  = abs(diff) / max(int(fac_qty), 1) * 100
            mark = f'數量差異 {diff:+,} ({pct:.0f}%)'

        groups.append({
            'lean': lean, 'art': art,
            'ds04': ds04_total,
            'fac':  fac_qty,
            'fac_lean': fac_lean,
            'mark': mark,
            'orders': buf,
        })

    ok_n   = sum(1 for g in groups if '一致'        in g['mark'])
    noart  = sum(1 for g in groups if '廠務無此ART' in g['mark'])
    lean_n = sum(1 for g in groups if 'LEAN不符'   in g['mark'])
    diff_n = sum(1 for g in groups if '數量差異'   in g['mark'])

    print(f'  ✓ 一致: {ok_n}  |  廠務無此ART: {noart}  |  LEAN不符: {lean_n}  |  數量差異: {diff_n}')

    # Build report
    lines = []

    def hdr(t):
        lines.extend(['=' * W, f'  {t}', '=' * W])

    def sub(t):
        lines.append('')
        lines.append(f'── {t} ' + '─' * max(0, W - len(t) - 4))

    hdr(f'DS-04 vs 廠務組織編制表 — 製令明細對比 — {gb.MONTH_SH}')
    lines.append(
        f'  DS-04: {len(recs_sorted)} 張製令 ({len(groups)} 個 ART×LEAN 組) '
        f'| 廠務: {len(art_to_ref)} 筆 ART'
    )
    lines.append('')
    lines.append(f'  ✓ 一致            : {ok_n:4d} 筆 (ART+LEAN 匹配，訂單量一致)')
    lines.append(f'  廠務無此ART       : {noart:4d} 筆 (廠務表找不到此 ART)')
    lines.append(f'  廠務 LEAN 不符    : {lean_n:4d} 筆 (ART 存在但 LEAN 指派不同)')
    lines.append(f'  數量差異          : {diff_n:4d} 筆 (ART+LEAN 匹配，訂單量不同)')

    GFMT = '  {art:<12}  LEAN={lean:<6}  DS-04={ds04:>8,}  廠務={fac_s:>8}  {mark}'
    OFMT = '    {mf_order:<28} {section:<8} {qty:>6,}  {date}'

    def write_groups(grps, show_orders=True):
        if not grps:
            lines.append('  （無）')
            return
        for g in grps:
            fac_s = f'{int(g["fac"]):,}' if g['fac'] is not None else '—'
            lines.append('')
            lines.append(GFMT.format(**{**g, 'fac_s': fac_s}))
            if show_orders:
                for o in g['orders']:
                    lines.append(OFMT.format(**o))

    # Section 1: 數量差異（最重要，按差異大小排）
    diffs = sorted(
        [g for g in groups if '數量差異' in g['mark']],
        key=lambda g: abs(g['ds04'] - (int(g['fac']) if g['fac'] else 0)),
        reverse=True
    )
    sub(f'1. 數量差異 ({diff_n} 筆，按差異絕對值排序)')
    write_groups(diffs)

    # Section 2: 廠務無此ART
    sub(f'2. 廠務無此ART ({noart} 筆)')
    write_groups([g for g in groups if '廠務無此ART' in g['mark']])

    # Section 3: LEAN 不符
    sub(f'3. 廠務LEAN不符 ({lean_n} 筆)')
    write_groups([g for g in groups if 'LEAN不符' in g['mark']], show_orders=False)

    # Section 4: 一致（只顯示清單，不展開製令）
    sub(f'4. ✓ 一致 ({ok_n} 筆)')
    write_groups([g for g in groups if '一致' in g['mark']], show_orders=False)

    # Footer
    lines.append('')
    hdr('總結')
    lines.append(f'  ✓ 一致     : {ok_n:4d}')
    lines.append(f'  廠務無此ART: {noart:4d}  ← 需 Jim 確認（補登廠務 or DS-04 誤填）')
    lines.append(f'  LEAN 不符  : {lean_n:4d}  → 正常業務差異（跨部門共用ART / 廠務重新指派）')
    lines.append(f'  數量差異   : {diff_n:4d}  ← 需 Jim 確認（廠務漏登或 DS-04 更新未同步）')

    with open(DIFF_TXT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'  → {DIFF_TXT}')

    return groups


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print('=' * 60)
    print('  DS-04 取值流程（Rule 20）')
    print('=' * 60)

    bianche_path = gb._safe_bianche()

    print('\n載入廠務組織編制表...')
    try:
        art_to_ref, _ = load_bianche(bianche_path)
        print(f'  {len(art_to_ref)} 筆 ART')
    except Exception as e:
        print(f'  Error: {e}')
        art_to_ref = {}

    print('\nStep 1: 讀取 DS-04 製令明細...')
    records = gb.load_schedule_detail()
    print(f'  {len(records)} 筆製令記錄（含成型进度 + 外包鞋面）')
    recs_sorted = step1_extract(records)

    print('\nStep 2+3: 對比廠務組織編制表...')
    groups = step2_3_compare(recs_sorted, art_to_ref)

    print('\nStep 4: 重建 auto_bianche.xlsx（含製令明細 tab）...')
    gb.run()

    print('\n' + '=' * 60)
    print('  流程完成')
    print('=' * 60)
    print(f'  ds04_order_detail.txt : {DETAIL_TXT}')
    print(f'  ds04_vs_bianche.txt   : {DIFF_TXT}')
    print(f'  auto_bianche.xlsx     : {gb.OUT_PATH}')


if __name__ == '__main__':
    main()
