#!/usr/bin/env python3
"""
column_compare_report.py
比對 result_table_v2.xlsx (CSA sheet) vs 廠務組織編制表 6.2026
聚焦三個欄位：鞋型 / ART / 訂單

輸出分類：
  邏輯差異   - 結構性原因（廠務合批多ART、鞋型含ART括弧），非填寫錯誤
  人為填寫差異 - 同一ART但數量不符，需人工核查
"""
import sys, os, re, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from full_compare_report import (
    load_bianche, load_result_csa,
    _safe_bianche_path,
    R_ORD_BATCH, R_ORD_MISMATCH,
    _ART_RE,
)

RESULT_PATH = r'D:\smartpn-atlas-core\flask_backend\test_output\result_table_v2.xlsx'
OUT_PATH    = r'D:\smartpn-atlas-core\flask_backend\test_output\column_compare_report.txt'
W = 120


def _strip_art_parens(text):
    """Remove embedded ART codes and their parentheses from factory model name."""
    cleaned = re.sub(r'\s*[\(\（][^()]*[A-Z]{2}\d{4,6}[^()]*[\)\）]', '', text)
    return cleaned.strip()


def run():
    bianche_path = _safe_bianche_path()
    art_to_ref, _ = load_bianche(bianche_path)
    csa_rows = load_result_csa(RESULT_PATH)

    art_section_count = {}
    for r in csa_rows:
        if not r['art'].startswith('MF'):
            art_section_count[r['art']] = art_section_count.get(r['art'], 0) + 1

    lines = []

    def hdr(t): lines.extend(['=' * W, f'  {t}', '=' * W])
    def sub(t): lines.extend(['', f'── {t} ' + '─' * max(0, W - len(t) - 4)])

    hdr('欄位比對報告：result_table_v2.xlsx  vs  廠務組織編制表 6.2026')
    lines.append(f'  比對欄位：鞋型 / ART / 訂單')
    lines.append(f'  CSA 行數: {len(csa_rows)} 筆  |  廠務 ART 索引: {len(art_to_ref)} 筆')
    lines.append('')

    # ── ART 匹配狀況 ──────────────────────────────────────────────────────────
    sub('1. ART 匹配狀況')
    non_mf = [r for r in csa_rows if not r['art'].startswith('MF')]
    matched_arts   = [r for r in non_mf if r['art'] in art_to_ref]
    ds04_only      = [r for r in non_mf if r['art'] not in art_to_ref]
    all_result_arts = {r['art'] for r in non_mf}
    ref_only_arts   = sorted(a for a in art_to_ref if a not in all_result_arts)

    lines.append(f'  DS-04 CSA 非MF 總筆數  : {len(non_mf):4d}')
    lines.append(f'  雙方都有 (可比對)       : {len(matched_arts):4d}')
    lines.append(f'  DS-04有 / 廠務無        : {len(ds04_only):4d}  → 需 Jim 確認（補登廠務或DS-04誤填）')
    lines.append(f'  廠務有 / DS-04無        : {len(ref_only_arts):4d}  → 需 Jim 確認（廠務多餘？）')

    if ds04_only:
        lines.append('')
        lines.append('  DS-04有/廠務無 清單：')
        for r in ds04_only:
            lines.append(f"    {r['art']:12s}  LEAN={r['lean'] or '?'!r:8s}  DS-04訂單={r['order']:>6}  部門={r['section']}")

    if ref_only_arts:
        lines.append('')
        lines.append('  廠務有/DS-04無 清單：')
        for a in ref_only_arts:
            ref = art_to_ref[a]
            lines.append(f"    {a:12s}  廠務LEAN={ref['lean']!r:8s}  廠務鞋型={ref['model'][:50]!r}")

    # ── 鞋型 比對 ─────────────────────────────────────────────────────────────
    sub('2. 鞋型 比對（僅雙方都有的 ART）')
    model_ok = model_diff_logic = model_diff_human = 0
    model_diff_rows = []

    for r in matched_arts:
        ref = art_to_ref[r['art']]
        ds04_model = r['model'].strip()
        factory_model_raw = ref['model'].strip()
        factory_model_clean = _strip_art_parens(factory_model_raw)

        # Normalize: lowercase, collapse spaces
        def norm(s): return re.sub(r'\s+', ' ', s).upper()
        match = (norm(ds04_model) == norm(factory_model_clean))

        if match:
            model_ok += 1
        else:
            # Classify: if factory model has ART codes embedded → logical (structural)
            has_art_in_factory = bool(_ART_RE.search(factory_model_raw))
            if has_art_in_factory:
                model_diff_logic += 1
            else:
                model_diff_human += 1
                model_diff_rows.append({
                    'art': r['art'], 'lean': r['lean'],
                    'ds04': ds04_model, 'factory': factory_model_raw,
                })

    total_model = len(matched_arts)
    lines.append(f'  可比對 ART 筆數                 : {total_model:4d}')
    lines.append(f'  ✓ 一致                          : {model_ok:4d}')
    lines.append(f'  △ 邏輯差異 (廠務含ART括弧附記)  : {model_diff_logic:4d}  → 非填寫錯誤，廠務格式慣例')
    lines.append(f'  ✗ 人為填寫差異 (名稱不符)       : {model_diff_human:4d}  → 需人工核查')

    if model_diff_rows:
        lines.append('')
        lines.append('  鞋型人為差異清單：')
        FMT2 = '    {art:12s}  LEAN={lean:<6}  DS-04={ds04:<30}  廠務={factory}'
        for row in model_diff_rows:
            lines.append(FMT2.format(**row, factory=row['factory'][:40]))

    # ── 訂單 比對 ─────────────────────────────────────────────────────────────
    sub('3. 訂單 比對（僅雙方都有的 ART）')
    ord_ok = 0
    ord_diff_batch = 0        # 邏輯差異
    ord_diff_human = 0        # 人為填寫差異
    ord_no_ref_qty = 0
    ord_diff_human_rows = []

    for r in matched_arts:
        ref = art_to_ref[r['art']]
        b_ord = ref['order']
        b_arts = _ART_RE.findall(ref['model'])
        r_ord = r['order']

        if b_ord is None:
            ord_no_ref_qty += 1
            continue

        if abs(r_ord - b_ord) < 0.5:
            ord_ok += 1
        else:
            if len(b_arts) > 1:
                ord_diff_batch += 1
            else:
                ord_diff_human += 1
                ord_diff_human_rows.append({
                    'art': r['art'], 'lean': r['lean'],
                    'r_ord': r_ord, 'b_ord': int(b_ord),
                    'diff': r_ord - int(b_ord),
                    'section': r['section'],
                })

    total_ord = len(matched_arts) - ord_no_ref_qty
    lines.append(f'  可比對 ART 筆數                 : {total_ord:4d}  (廠務無訂單數={ord_no_ref_qty})')
    lines.append(f'  ✓ 完全一致                      : {ord_ok:4d}')
    lines.append(f'  △ 邏輯差異 (廠務合批多ART)      : {ord_diff_batch:4d}  → 廠務一行含多ART合計量，個別ART量必然不同，非錯誤')
    lines.append(f'  ✗ 人為填寫差異 (數量不符)       : {ord_diff_human:4d}  → 廠務只記一個ART，但數量不同，需人工核查')

    if ord_diff_human_rows:
        lines.append('')
        lines.append('  訂單人為差異清單（數量不符）：')
        FMT3 = '    {art:12s}  LEAN={lean:<6}  DS-04={r_ord:>6}  廠務={b_ord:>6}  差={diff:+}  部門={section}'
        # Sort by abs diff descending
        for row in sorted(ord_diff_human_rows, key=lambda x: abs(x['diff']), reverse=True):
            lines.append(FMT3.format(**row))

    # ── 總結 ──────────────────────────────────────────────────────────────────
    lines.append('')
    hdr('總結')
    lines.append('')
    lines.append(f'  ART 完全匹配 (雙方都有)     : {len(matched_arts):4d} / {len(non_mf)} 筆')
    lines.append(f'  ART DS-04有廠務無           : {len(ds04_only):4d} 筆  ← 待 Jim 確認')
    lines.append(f'  ART 廠務有DS-04無           : {len(ref_only_arts):4d} 筆  ← 待 Jim 確認')
    lines.append('')
    lines.append(f'  鞋型 一致                   : {model_ok:4d} / {total_model} 筆')
    lines.append(f'  鞋型 邏輯差異 (廠務格式)    : {model_diff_logic:4d} 筆  → 非錯誤')
    lines.append(f'  鞋型 人為填寫差異           : {model_diff_human:4d} 筆  → 需確認')
    lines.append('')
    lines.append(f'  訂單 一致                   : {ord_ok:4d} / {total_ord} 筆')
    lines.append(f'  訂單 邏輯差異 (廠務合批)    : {ord_diff_batch:4d} 筆  → 非錯誤')
    lines.append(f'  訂單 人為填寫差異           : {ord_diff_human:4d} 筆  → 需確認')
    lines.append('')
    lines.append('  結論分類：')
    lines.append(f'    邏輯/結構差異 (正常，無需修正) : 鞋型{model_diff_logic} + 訂單{ord_diff_batch} = {model_diff_logic + ord_diff_batch} 筆')
    lines.append(f'    人為填寫差異 (需 Jim 核查)      : ART缺{len(ds04_only)+len(ref_only_arts)} + 鞋型{model_diff_human} + 訂單{ord_diff_human} 筆')

    text = '\n'.join(lines)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(text)
    print(text)
    return text


if __name__ == '__main__':
    run()
