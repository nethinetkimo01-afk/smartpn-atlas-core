#!/usr/bin/env python3
"""Analyze KI1387 MP allocation: schedule orders vs result table MP."""
import sys, os, re
from datetime import date

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SCHEDULE = r"C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份正式进度表 5 30.xlsx"
OUTPUT = os.path.join(os.path.dirname(__file__), 'test_output', 'mp_allocation_analysis.txt')

_ART_RE = re.compile(r'[A-Z]{2}\d{4,6}')
_QTY_RE = re.compile(r'--(\d+)\s*\(')

BOA27_ARTS = {
    'KI1387', 'KI5738', 'KI5739', 'KI5740', 'KI5741',
    'KI5752', 'KI5753', 'KI5754', 'KI1390', 'KK0660',
    'KI5746', 'KI5747',
}


def parse_order_cell(val):
    s = str(val or '').strip()
    arts = _ART_RE.findall(s)
    m = _QTY_RE.search(s)
    qty = int(m.group(1)) if m else 0
    if not arts:
        return []
    per = qty // len(arts)
    rem = qty % len(arts)
    return [(a, per + (rem if i == 0 else 0)) for i, a in enumerate(arts)]


def extract_schedule_orders(wb):
    results = {}
    for ws in wb.worksheets:
        title = ws.title.strip()
        orders = {}
        for row in ws.iter_rows(values_only=True):
            for cell in row:
                s = str(cell or '').strip()
                if _ART_RE.search(s) and '--' in s:
                    for art, qty in parse_order_cell(s):
                        orders[art] = orders.get(art, 0) + qty
        if orders:
            results[title] = orders
    return results


def main():
    import database as db
    import openpyxl

    db.init_db()
    conn = db.get_conn()

    lines = []
    lines.append('=== MP 分配邏輯分析報告 ===')
    lines.append(f'生成時間: {date.today()}')
    lines.append('')
    lines.append('--- 問題描述 ---')
    lines.append('ob_epph 存的是整條產線 MP（No.of Operators），')
    lines.append('但結果表（廠務組織編制表）是按各組訂單量比例分配的份額。')
    lines.append('需要 Jim 確認正確的分配公式。')
    lines.append('')

    ki_row = conn.execute(
        '''SELECT a.art, h.eolr, h.season, e.cutting, e.stitching, e.assembly, e.stock
           FROM ob_header h JOIN ob_epph e ON e.header_id=h.id
           JOIN ob_articles a ON a.header_id=h.id
           WHERE a.art='KI1387' ORDER BY h.id DESC LIMIT 1'''
    ).fetchone()

    lines.append('=== 案例一：KI1387 (CODECHAOS BOA 27) ===')
    if ki_row:
        lines.append(f'ob_epph: ART={ki_row[0]} EOLR={ki_row[1]} Season={ki_row[2]}')
        lines.append(f'  裁斷(Cutting) = {ki_row[3]}')
        lines.append(f'  針車(Stitching) = {ki_row[4]}')
        lines.append(f'  成型(Assembly) = {ki_row[5]}')
        lines.append(f'  大底(Stock) = {ki_row[6]}')
    lines.append('結果表(廠務組織編制表 LEAN 1A):')
    lines.append('  裁斷(Cutting) = 6.0')
    lines.append('  針車(Stitching) = 16.0')
    lines.append('  成型(Assembly) = 21.0')
    lines.append('')
    lines.append('差異: 計算19 vs 結果表6')
    lines.append('比例: 6/19 = 31.6%')
    lines.append('')

    lines.append('--- 進度表訂單分析（CODECHAOS BOA 27 家族） ---')
    try:
        wb = openpyxl.load_workbook(SCHEDULE, data_only=True, read_only=True)
        schedule = extract_schedule_orders(wb)
        wb.close()

        boa27_by_sheet = {}
        for sheet, orders in schedule.items():
            boa_orders = {art: qty for art, qty in orders.items() if art in BOA27_ARTS}
            if boa_orders:
                boa27_by_sheet[sheet] = boa_orders

        lines.append('')
        lines.append('各進度表 sheet 的 CODECHAOS BOA 27 訂單:')
        total_boa27 = 0
        for sheet, orders in sorted(boa27_by_sheet.items()):
            subtotal = sum(orders.values())
            total_boa27 += subtotal
            lines.append(f'  {sheet}: {subtotal:,} prs')
            for art, qty in sorted(orders.items()):
                lines.append(f'    {art}: {qty:,}')
        lines.append(f'  總計: {total_boa27:,} prs')
        lines.append('')

        ki1387_qty = 0
        for sheet, orders in schedule.items():
            if 'KI1387' in orders:
                ki1387_qty = orders['KI1387']
                lines.append(f'KI1387 所在 sheet: {sheet}')
                break

        lines.append(f'KI1387 訂單量: {ki1387_qty:,} prs')
        if total_boa27 > 0:
            lines.append(f'KI1387 占 CODECHAOS BOA 27 總量比例: {ki1387_qty/total_boa27*100:.1f}%')
        lines.append('')

        if total_boa27 > 0 and ki_row:
            full_cut = ki_row[3] or 19.0
            alloc = full_cut * ki1387_qty / total_boa27
            match = '✓ 一致' if abs(alloc - 6.0) < 1.5 else '✗ 不一致'
            lines.append('--- 假說：按訂單比例分配 ---')
            lines.append('公式: 分配MP = 整條產線MP × (本組訂單 / 總訂單)')
            lines.append(f'裁斷: {full_cut} × ({ki1387_qty}/{total_boa27}) = {alloc:.1f}')
            lines.append(f'結果表值 = 6.0   計算值 = {alloc:.1f}   {match}')
            lines.append('')
    except Exception as e:
        lines.append(f'讀取進度表失敗: {e}')

    lines.append('--- CODECHAOS BOA 27 家族 ob_epph 一覽 ---')
    rows = conn.execute(
        'SELECT a.art, h.eolr, e.cutting, e.stitching, e.assembly '
        'FROM ob_header h JOIN ob_epph e ON e.header_id=h.id '
        'JOIN ob_articles a ON a.header_id=h.id '
        'WHERE a.art IN ({}) ORDER BY a.art, h.eolr'.format(
            ','.join(['?' for _ in BOA27_ARTS])),
        tuple(BOA27_ARTS)
    ).fetchall()

    lines.append(f"{'ART':12} {'EOLR':6} {'Cut':>6} {'Stitch':>8} {'Asm':>6}")
    lines.append('-' * 45)
    for r in rows:
        lines.append(f"{r[0]:12} {r[1]:6} {r[2]:>6.1f} {r[3]:>8.1f} {r[4]:>6.1f}")

    lines.append('')
    lines.append('--- 73筆 mp_mismatch 分析 ---')
    lines.append('所有計算值 > 結果表的案例，原因相同：')
    lines.append('  ob_epph 存的是整條產線人數，結果表是各組分配值。')
    lines.append('')
    lines.append('可能的分配邏輯（等 Jim 確認）：')
    lines.append('  1. 按訂單比例: MP × (本組訂單 / 全部組訂單)')
    lines.append('  2. 按 LEAN 組數平均: MP / N組（固定分配）')
    lines.append('  3. 依 Jim 手工指定（每款每組各自設定）')
    lines.append('')
    lines.append('建議 Jim 明天確認:')
    lines.append('  a) CODECHAOS BOA 27 在各 LEAN 組的訂單比例是否與 6/19 相符？')
    lines.append('  b) 是否所有款式都用同一公式？')
    lines.append('  c) 確認後修正 analyze_result_table.py 的 MP 計算邏輯。')

    conn.close()

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print(f'Written to: {OUTPUT}')
    for line in lines:
        print(line)


if __name__ == '__main__':
    main()
