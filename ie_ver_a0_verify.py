# -*- coding: utf-8 -*-
"""
ie_ver_a0_verify.py — A0 驗身：基準庫快照無損驗證（IE-VER 批次的第一道，每次續跑必先過）。

★為什麼有這支：
  IE-VER 遷移的每一步都拿「基準庫快照」當輸入。快照若在某次操作中被改到/截斷/損壞，
  後面所有對帳、落格、零丟值斷言全部建立在爛地基上，而且**不會有人發現**——
  因為斷言比對的也是同一份爛快照。A0 就是每次續跑前重新驗身：地基還是原來那塊嗎？

驗什麼（全部唯讀）：
  A0-1 PRAGMA integrity_check ＝ ok（檔案結構沒壞）
  A0-2 ie_process 總列數
  A0-3 ob_header 總數 / 有 actual 的 header 數
  A0-4 有 actual 的相異 ART 數
  A0-5 actual 列數（count）
  A0-6 actual 總和（sum）——浮點，用容差比對，不用 ==
  A0-7 header ↔ ART 嚴格 1:1（識別單位＝版本×ART 的前提，破了整個資料模型要重談）

★期望值不寫在本檔：
  20,434 / 140 / 76,357.19 這些是**真庫匯出的統計**＝入規27 定義的真實生產資料。
  寫進本檔＝把真數字 commit 進 git。故一律從 `real_db_for_recon/baseline_expect.json`
  （gitignored，不在 repo 內）讀取。讀不到 → exit 2 擋下（fail-closed：不能舉證＝不算過）。

用法：
  python ie_ver_a0_verify.py                    驗預設快照（設定檔內的 baseline.db）
  python ie_ver_a0_verify.py <db路徑>           驗指定 DB
"""
import io
import os
import sys
import json
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.abspath(__file__))
CFG = os.path.join(ROOT, 'real_db_for_recon', 'baseline_expect.json')

ACTUAL_COND = 'actual_operators IS NOT NULL AND actual_operators <> 0'

R = []


def rec(name, ok, got='', want=''):
    R.append((name, ok))
    line = f'  {"✅" if ok else "❌"} {name}'
    if got != '' or want != '':
        line += f' — 實得 {got}' + (f' / 應為 {want}' if want != '' else '')
    print(line, flush=True)


def ro(db):
    c = sqlite3.connect('file:' + db.replace('\\', '/') + '?mode=ro', uri=True)
    c.execute('PRAGMA query_only=ON')
    return c


def main():
    print('=' * 68)
    print('ie_ver_a0_verify — A0 驗身：基準庫快照無損驗證')
    print('=' * 68)

    if not os.path.isfile(CFG):
        print(f'❌ 讀不到期望值設定：{CFG}')
        print('   入規27：真庫統計不進 git，期望值一律放本機 gitignored 設定檔。')
        print('   fail-closed：沒有期望值就無法舉證「無損」→ 擋下。')
        return 2
    with open(CFG, 'r', encoding='utf-8') as f:
        exp = json.load(f)['baseline']

    db = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, *exp['db'].split('/'))
    if not os.path.isfile(db):
        print(f'❌ 找不到 DB：{db}')
        return 2
    print(f'DB（唯讀）：{db}')
    print(f'大小：{os.path.getsize(db):,} bytes')
    print()

    c = ro(db)

    rec('A0-1 integrity_check', c.execute('PRAGMA integrity_check').fetchone()[0] == 'ok',
        c.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    got = c.execute('SELECT COUNT(*) FROM ie_process').fetchone()[0]
    rec('A0-2 ie_process 總列數', got == exp['ie_process_rows'], f'{got:,}', f"{exp['ie_process_rows']:,}")

    got = c.execute('SELECT COUNT(*) FROM ob_header').fetchone()[0]
    rec('A0-3a ob_header 總數', got == exp['ob_header_total'], got, exp['ob_header_total'])

    got = c.execute(f'SELECT COUNT(DISTINCT header_id) FROM ie_process WHERE {ACTUAL_COND}').fetchone()[0]
    rec('A0-3b 有 actual 的 header 數', got == exp['headers_with_actual'], got, exp['headers_with_actual'])

    got = c.execute(f'SELECT COUNT(DISTINCT art) FROM ie_process WHERE {ACTUAL_COND}').fetchone()[0]
    rec('A0-4 有 actual 的相異 ART 數', got == exp['distinct_art_with_actual'], got, exp['distinct_art_with_actual'])

    got = c.execute(f'SELECT COUNT(*) FROM ie_process WHERE {ACTUAL_COND}').fetchone()[0]
    rec('A0-5 actual 列數', got == exp['actual_count'], f'{got:,}', f"{exp['actual_count']:,}")

    got = c.execute(f'SELECT SUM(actual_operators) FROM ie_process WHERE {ACTUAL_COND}').fetchone()[0]
    tol = exp.get('sum_tolerance', 1e-6)
    # 浮點總和不能用 == 比：SQLite SUM 的累加順序一變，末位就可能差。用容差。
    rec('A0-6 actual 總和', got is not None and abs(got - exp['actual_sum']) <= tol,
        repr(got), f"{exp['actual_sum']!r} ±{tol}")

    # A0-7：識別單位＝版本×ART 的前提。這條破了 → B3 的資料模型從根本錯，必須停下重談。
    h_multi = c.execute(
        'SELECT COUNT(*) FROM (SELECT header_id FROM ie_process '
        'GROUP BY header_id HAVING COUNT(DISTINCT art) > 1)').fetchone()[0]
    a_multi = c.execute(
        'SELECT COUNT(*) FROM (SELECT art FROM ie_process WHERE art IS NOT NULL AND art <> "" '
        'GROUP BY art HAVING COUNT(DISTINCT header_id) > 1)').fetchone()[0]
    rec('A0-7 header ↔ ART 嚴格 1:1（版本×ART 識別單位前提）', h_multi == 0 and a_multi == 0,
        f'header多ART={h_multi} / ART跨header={a_multi}', '0 / 0')

    c.close()
    npass = sum(1 for _, ok in R if ok)
    allgreen = npass == len(R) and len(R) >= 8
    print('\n' + '=' * 68)
    print(f'  A0 驗身：{npass}/{len(R)} → '
          f'{"✅ ALL GREEN（快照無損，可續跑）" if allgreen else "❌ FAIL（快照與期望不符 → 停工回報，不得續跑）"}')
    if not allgreen:
        print('  地基不對就不要往上蓋：先查快照是被誰改到，不要改期望值去遷就快照。')
    print('=' * 68)
    return 0 if allgreen else 1


if __name__ == '__main__':
    sys.exit(main())
