#!/usr/bin/env python3
"""
generate_bianche.py
自動生成廠務組織編制表 (auto_bianche.xlsx)

CSA section: 由 DS-04 進度表產生 (LEAN/鞋型/ART/訂單)
OCS/RB/QC:  直接從現行廠務組織編制表讀取
MP欄位 (裁斷/針車/成型/協理給/合計/編制): 留空

輸出: test_output/auto_bianche.xlsx
"""
import sys, os, re, shutil, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

import build_result_table as brt

BIANCHE_ORIG = r'C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份廠務组织編制 20260524.xlsx'
BIANCHE_TMP  = r'C:\Users\user\AppData\Local\Temp\bianche_gen.xlsx'
OUT_PATH     = r'D:\smartpn-atlas-core\flask_backend\test_output\auto_bianche.xlsx'

# Patch brt file paths to temp copies (source files may be locked by Excel)
import tempfile
def _tmp(orig):
    dst = os.path.join(tempfile.gettempdir(), os.path.basename(orig))
    shutil.copy2(orig, dst)
    return dst
brt.SCHEDULE = _tmp(brt.SCHEDULE)
brt.BIANCHE  = _tmp(brt.BIANCHE)
MONTH_SH     = '6.2026'
_ART_RE      = re.compile(r'[A-Z]{2}\d{4,6}')

# ── Styles ────────────────────────────────────────────────────────────────────
THIN      = Side(style='thin')
THIN_BDR  = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
HDR_FILL  = PatternFill('solid', fgColor='4472C4')
LEAN_FILL = PatternFill('solid', fgColor='FFF2CC')
SEC_FILL  = PatternFill('solid', fgColor='D9D9D9')
BLANK_FILL= PatternFill('solid', fgColor='FFE2CC')   # orange tint = no data
HDR_FONT  = Font(bold=True, color='FFFFFF', size=10)
BOLD      = Font(bold=True, size=10)
NORM      = Font(size=10)
CENTER    = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT      = Alignment(horizontal='left', vertical='center', wrap_text=True)
RIGHT     = Alignment(horizontal='right', vertical='center')

OCS_SECTIONS = ['組底配套', '自動化', '電腦針車', '印刷', '設備工程']
RB_QC_SECTIONS = ['RB', 'QC']


def _safe_bianche():
    try:
        with open(BIANCHE_ORIG, 'rb'): pass
        return BIANCHE_ORIG
    except (PermissionError, FileNotFoundError):
        if not os.path.exists(BIANCHE_TMP):
            shutil.copy2(BIANCHE_ORIG, BIANCHE_TMP)
        return BIANCHE_TMP


def _lean_sort_key(lean):
    m = re.match(r'^(\d+)([A-Z])(\d*)$', lean)
    if m:
        return (int(m.group(1)), m.group(2), int(m.group(3)) if m.group(3) else 0)
    return (999, lean, 0)


def load_ds04_by_lean():
    """Each DS-04 sheet is independent — no cross-sheet aggregation.
    Returns {lean: [{art, qty, sheet}]} where each (sheet, lean, art) is a separate row.
    If the same (lean, art) appears in multiple sheets → multiple rows in that LEAN group.
    """
    print('Loading DS-04...')
    sheets = brt.load_schedule()
    lean_rows = collections.defaultdict(list)  # lean -> [{art, qty, sheet}]
    for s in sheets:
        sheet_title = s['sheet']
        for r in s['rows']:
            lean = r['lean'].strip()
            if not lean:
                continue
            lean_rows[lean].append({'art': r['art'], 'qty': r['qty'], 'sheet': sheet_title})

    result = {}
    for lean in sorted(lean_rows, key=_lean_sort_key):
        rows = sorted(lean_rows[lean], key=lambda x: (x['art'], x['sheet']))
        result[lean] = rows

    total = sum(len(v) for v in result.values())
    print(f'  {len(result)} LEAN groups, {total} (sheet,lean,art) rows')
    return result


def load_ocs_rb_qc(bianche_path):
    """Read OCS fixed units and RB/QC sections from factory table."""
    print('Loading OCS/RB/QC from factory table...')
    wb = openpyxl.load_workbook(bianche_path, data_only=True)
    ws = next((wb[s] for s in wb.sheetnames if s.strip() == MONTH_SH), None)
    if ws is None:
        wb.close()
        return {}, {}

    def _hc(row, *idxs):
        for idx in idxs:
            v = row[idx] if len(row) > idx else None
            if v is not None and str(v).strip() not in ('', '.', '編制'):
                try: return int(float(v))
                except: pass
        return None

    ocs = {s: [] for s in OCS_SECTIONS}
    rbqc = {s: [] for s in RB_QC_SECTIONS}
    cur_ocs = None
    cur_rbqc = None

    for row in ws.iter_rows(values_only=True):
        col1 = str(row[0] or '').strip() if row else ''
        col2 = str(row[1] or '').strip() if len(row) > 1 else ''

        if col1 in OCS_SECTIONS:
            cur_ocs = col1; cur_rbqc = None
            if col2 and col2 not in ('編制', ''):
                ocs[cur_ocs].append({'unit': col2, 'hc': _hc(row, 12, 10, 14)})
        elif col1 in RB_QC_SECTIONS:
            cur_rbqc = col1; cur_ocs = None
            if col2 and col2 not in ('編制', ''):
                last_m = _hc(row, 12)
                this_m = _hc(row, 14)
                rbqc[cur_rbqc].append({'unit': col2, 'last_month': last_m, 'this_month': this_m or last_m})
        elif col1 and col1 not in OCS_SECTIONS and col1 not in RB_QC_SECTIONS:
            cur_ocs = None
            if col1 not in ('設備工程', '副總室', '現場技轉/ KTHT'):
                cur_rbqc = None
        else:
            if cur_ocs and not col1 and col2 and col2 not in ('編制', ''):
                ocs[cur_ocs].append({'unit': col2, 'hc': _hc(row, 12, 10, 14)})
            elif cur_rbqc and not col1 and col2 and col2 not in ('編制', ''):
                last_m = _hc(row, 12)
                this_m = _hc(row, 14)
                rbqc[cur_rbqc].append({'unit': col2, 'last_month': last_m, 'this_month': this_m or last_m})

    wb.close()
    for s in OCS_SECTIONS:
        print(f'  OCS {s}: {len(ocs[s])} units')
    for s in RB_QC_SECTIONS:
        print(f'  {s}: {len(rbqc[s])} units')
    return ocs, rbqc


def wc(ws, r, c, val, font=None, fill=None, align=None, border=None, num_fmt=None):
    cell = ws.cell(row=r, column=c, value=val)
    if font:   cell.font = font
    if fill:   cell.fill = fill
    if align:  cell.alignment = align
    if border: cell.border = border
    if num_fmt: cell.number_format = num_fmt
    return cell


def build_sheet(ws, lean_by_art, ocs, rbqc):
    # Column widths
    widths = {1: 8, 2: 45, 3: 8, 4: 8, 5: 8, 6: 10, 7: 8, 8: 8, 9: 8, 10: 8, 11: 8, 12: 8}
    for ci, w in widths.items():
        ws.column_dimensions[get_column_letter(ci)].width = w

    row = 1

    # ── Title ────────────────────────────────────────────────────────────────
    ws.merge_cells(f'A{row}:L{row}')
    wc(ws, row, 1, f'廠務組織編制表（自動產生 auto_bianche）— {MONTH_SH}',
       font=Font(bold=True, size=13), align=CENTER)
    row += 1

    ws.merge_cells(f'A{row}:L{row}')
    wc(ws, row, 1,
       '★ 橙色欄位 = 本月無資料（MP、協理給等待 Jim 填入）| 此表由 DS-04 自動產生',
       font=Font(size=9, italic=True, color='CC4400'), align=LEFT)
    row += 2

    # ── Column headers ───────────────────────────────────────────────────────
    headers = ['LEAN', '鞋型 + ART', '', '', '', '訂單', '',
               '裁斷MP', '針車MP', '成型MP', '協理給', '合計']
    ws.row_dimensions[row].height = 28
    for ci, h in enumerate(headers, 1):
        wc(ws, row, ci, h, font=HDR_FONT, fill=HDR_FILL, align=CENTER, border=THIN_BDR)
    row += 1
    ws.freeze_panes = f'A{row}'

    # ── CSA section ──────────────────────────────────────────────────────────
    # Determine LEAN number groups (1, 2, ... 12)
    lean_num_groups = {}
    for lean in lean_by_art:
        m = re.match(r'^(\d+)', lean)
        n = int(m.group(1)) if m else 99
        lean_num_groups.setdefault(n, []).append(lean)

    for dept_num in sorted(lean_num_groups):
        # Dept section header
        ws.merge_cells(f'A{row}:L{row}')
        wc(ws, row, 1, f'LEAN {dept_num} （加{dept_num}部）',
           font=Font(bold=True, size=10, color='1F4E79'), fill=SEC_FILL, align=LEFT)
        row += 1

        for lean in sorted(lean_num_groups[dept_num], key=_lean_sort_key):
            arts = lean_by_art[lean]

            # LEAN group header row
            ws.row_dimensions[row].height = 18
            wc(ws, row, 1, lean, font=BOLD, fill=LEAN_FILL, align=CENTER, border=THIN_BDR)
            ws.merge_cells(f'B{row}:E{row}')
            wc(ws, row, 2, '鞋型 + ART', font=BOLD, fill=LEAN_FILL, align=CENTER, border=THIN_BDR)
            wc(ws, row, 6, '訂單', font=BOLD, fill=LEAN_FILL, align=CENTER, border=THIN_BDR)
            for ci in [7, 8, 9, 10, 11, 12]:
                wc(ws, row, ci, None, fill=BLANK_FILL, border=THIN_BDR)
            row += 1

            # Data rows
            for r_data in arts:
                art = r_data['art']
                qty = r_data['qty']
                model = brt.get_model(art)
                if model:
                    model_text = f'{model} ( {art} )'
                else:
                    model_text = f'( {art} )'

                ws.row_dimensions[row].height = 15
                wc(ws, row, 1, None, border=THIN_BDR)
                ws.merge_cells(f'B{row}:E{row}')
                wc(ws, row, 2, model_text, font=NORM, align=LEFT, border=THIN_BDR)
                wc(ws, row, 6, qty, font=NORM, align=RIGHT, border=THIN_BDR, num_fmt='#,##0')
                for ci in [7, 8, 9, 10, 11, 12]:
                    wc(ws, row, ci, None, fill=BLANK_FILL, border=THIN_BDR)
                row += 1

    row += 1  # spacer

    # ── OCS sections ─────────────────────────────────────────────────────────
    ws.merge_cells(f'A{row}:L{row}')
    wc(ws, row, 1, 'OCS 固定單位（直接從廠務組織編制表讀入）',
       font=Font(bold=True, size=11, color='1F4E79'), fill=SEC_FILL, align=LEFT)
    row += 1

    for sec in OCS_SECTIONS:
        units = ocs.get(sec, [])
        # Section header
        ws.merge_cells(f'A{row}:L{row}')
        wc(ws, row, 1, sec, font=BOLD, fill=LEAN_FILL, align=LEFT, border=THIN_BDR)
        row += 1
        for u in units:
            wc(ws, row, 1, None, border=THIN_BDR)
            ws.merge_cells(f'B{row}:K{row}')
            wc(ws, row, 2, u['unit'], font=NORM, align=LEFT, border=THIN_BDR)
            wc(ws, row, 12, u['hc'], font=NORM, align=RIGHT, border=THIN_BDR, num_fmt='#,##0')
            row += 1
        row += 1

    # ── RB / QC sections ─────────────────────────────────────────────────────
    ws.merge_cells(f'A{row}:L{row}')
    wc(ws, row, 1, 'RB / QC（直接從廠務組織編制表讀入）',
       font=Font(bold=True, size=11, color='1F4E79'), fill=SEC_FILL, align=LEFT)
    row += 1

    for sec in RB_QC_SECTIONS:
        units = rbqc.get(sec, [])
        ws.merge_cells(f'A{row}:L{row}')
        wc(ws, row, 1, sec, font=BOLD, fill=LEAN_FILL, align=LEFT, border=THIN_BDR)
        row += 1

        # Sub-headers
        ws.row_dimensions[row].height = 18
        ws.merge_cells(f'A{row}:J{row}')
        wc(ws, row, 1, '單位', font=HDR_FONT, fill=HDR_FILL, align=CENTER, border=THIN_BDR)
        wc(ws, row, 11, '上月人數', font=HDR_FONT, fill=HDR_FILL, align=CENTER, border=THIN_BDR)
        wc(ws, row, 12, '本月人數', font=HDR_FONT, fill=HDR_FILL, align=CENTER, border=THIN_BDR)
        row += 1

        for u in units:
            ws.merge_cells(f'A{row}:J{row}')
            wc(ws, row, 1, u['unit'], font=NORM, align=LEFT, border=THIN_BDR)
            wc(ws, row, 11, u['last_month'], font=NORM, align=RIGHT, border=THIN_BDR, num_fmt='#,##0')
            wc(ws, row, 12, u['this_month'], font=NORM, align=RIGHT, border=THIN_BDR, num_fmt='#,##0')
            row += 1
        row += 1


def run():
    bianche_path = _safe_bianche()
    lean_by_art = load_ds04_by_lean()
    ocs, rbqc = load_ocs_rb_qc(bianche_path)

    print('Building auto_bianche.xlsx...')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = MONTH_SH
    build_sheet(ws, lean_by_art, ocs, rbqc)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    wb.save(OUT_PATH)
    print(f'Saved: {OUT_PATH}')

    # Quick diff summary vs factory table
    print()
    print('=== 與廠務組織編制表 差異摘要 ===')
    from column_compare_report import run as ccr_run
    ccr_run()


if __name__ == '__main__':
    run()
