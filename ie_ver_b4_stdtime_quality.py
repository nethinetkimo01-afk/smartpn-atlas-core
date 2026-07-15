# -*- coding: utf-8 -*-
"""
ie_ver_b4_stdtime_quality.py — B4 標時清洗 · 唯讀資料品質分析。

背景：舊裁決⑤（版本×鞋型共用一份標時、跨 ART 去重）已被 b3_blocker 推翻為「去重必毀資料」
（17 鞋型 79 header 標時互異）。新裁決：標時/工序留在 ie_process、一 ART 一份、不跨 ART 合併。
因此 B4「清洗」**不是去重**，而是每個 ART 內部的標時正規化/校驗。但「怎樣才算髒、要怎麼洗」
**無正式規格**，屬中樞/Jim 裁決範疇。本檔只做唯讀盤點：把可疑處量化出來，供裁決，**不寫任何資料**。

盤點（唯讀）：
  Q1 standard_time 缺漏：NULL / =0 / <0
  Q2 公式相符度：standard_time ?= round(normal_time*(1+allowance_pct/100), 4)（ap 空值視為 10）
  Q3 allowance_pct 分布與異常（NULL / 負 / 過大）
  Q4 normal_time 有值但 standard_time 缺（該算沒算）
  Q5 後製程標時欄位（post_*_std）非空列數（供了解範圍）

唯讀：mode=ro + PRAGMA query_only=ON。

用法：
  ATLAS_DB=/path/to/atlas.db python ie_ver_b4_stdtime_quality.py [--md out.md]
"""
import io
import os
import sys
import sqlite3
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def ro(path):
    c = sqlite3.connect('file:' + path.replace('\\', '/') + '?mode=ro', uri=True)
    c.execute('PRAGMA query_only=ON')
    return c


def main():
    db = os.environ.get('ATLAS_DB')
    if not db or not os.path.isfile(db):
        print(f'❌ ATLAS_DB 無效：{db}'); return 3
    md_out = sys.argv[sys.argv.index('--md') + 1] if '--md' in sys.argv else None
    c = ro(db)

    total = c.execute('SELECT COUNT(*) FROM ie_process').fetchone()[0]
    st_null = c.execute('SELECT COUNT(*) FROM ie_process WHERE standard_time IS NULL').fetchone()[0]
    st_zero = c.execute('SELECT COUNT(*) FROM ie_process WHERE standard_time = 0').fetchone()[0]
    st_neg = c.execute('SELECT COUNT(*) FROM ie_process WHERE standard_time < 0').fetchone()[0]
    st_pos = c.execute('SELECT COUNT(*) FROM ie_process WHERE standard_time > 0').fetchone()[0]

    # Q2 公式相符：ap 空視為 10；容差 1e-3
    formula_mismatch = c.execute('''
        SELECT COUNT(*) FROM ie_process
        WHERE normal_time IS NOT NULL AND standard_time IS NOT NULL
          AND ABS(standard_time - ROUND(normal_time * (1 + COALESCE(allowance_pct,10)/100.0), 4)) > 1e-3
    ''').fetchone()[0]
    formula_checked = c.execute('''
        SELECT COUNT(*) FROM ie_process
        WHERE normal_time IS NOT NULL AND standard_time IS NOT NULL
    ''').fetchone()[0]

    ap_null = c.execute('SELECT COUNT(*) FROM ie_process WHERE allowance_pct IS NULL').fetchone()[0]
    ap_neg = c.execute('SELECT COUNT(*) FROM ie_process WHERE allowance_pct < 0').fetchone()[0]
    ap_big = c.execute('SELECT COUNT(*) FROM ie_process WHERE allowance_pct > 100').fetchone()[0]
    ap_vals = c.execute('SELECT DISTINCT allowance_pct FROM ie_process ORDER BY allowance_pct').fetchall()

    q4 = c.execute('''SELECT COUNT(*) FROM ie_process
                      WHERE normal_time IS NOT NULL AND normal_time <> 0
                        AND (standard_time IS NULL OR standard_time = 0)''').fetchone()[0]

    post_cols = ['post_marking_std', 'post_skiving_std', 'post_attach_std', 'post_edge_std',
                 'post_heat_std', 'post_polish_std']
    post_counts = {}
    have = [r[1] for r in c.execute('PRAGMA table_info(ie_process)')]
    for col in post_cols:
        if col in have:
            post_counts[col] = c.execute(
                f'SELECT COUNT(*) FROM ie_process WHERE {col} IS NOT NULL AND {col}<>0').fetchone()[0]

    L = []; A = L.append
    A('# B4 標時清洗 · 唯讀資料品質分析（不寫任何資料）')
    A('')
    A(f'- DB（唯讀）：`{db}`　產出：{datetime.now().isoformat(timespec="seconds")}')
    A(f'- ie_process 總列數：{total:,}')
    A('')
    A('## Q1 standard_time 缺漏/異常')
    A('| 狀況 | 列數 |')
    A('|---|---:|')
    A(f'| NULL | {st_null:,} |')
    A(f'| = 0 | {st_zero:,} |')
    A(f'| < 0（負值，異常）| {st_neg:,} |')
    A(f'| > 0（正常）| {st_pos:,} |')
    A('')
    A('## Q2 公式相符度  standard_time ?= round(normal_time*(1+ap/100),4)')
    A(f'- 可驗列（normal_time 與 standard_time 皆非空）：{formula_checked:,}')
    A(f'- **不相符（差>1e-3）：{formula_mismatch:,}**'
      f'（{100*formula_mismatch/formula_checked:.2f}%）' if formula_checked else '- 無可驗列')
    A('> 不相符不一定是錯：可能是手動覆寫、後製程加成、或匯入源本就非此公式。屬清洗規格待裁。')
    A('')
    A('## Q3 allowance_pct')
    A(f'- NULL：{ap_null:,}　負值：{ap_neg:,}　>100：{ap_big:,}')
    A(f'- 相異值：{[ (float(v[0]) if v[0] is not None else None) for v in ap_vals][:20]}')
    A('')
    A('## Q4 normal_time 有值但 standard_time 缺（該算沒算）')
    A(f'- 列數：{q4:,}')
    A('')
    A('## Q5 後製程標時欄位非空列數')
    for col, n in post_counts.items():
        A(f'- {col}：{n:,}')
    A('')
    A('## 結論')
    A('B4「清洗」的具體規則（何謂髒、如何洗、是否重算公式、如何處理不相符/缺漏）**無既有規格**，')
    A('屬中樞/Jim 裁決。本檔已把可疑量化，**未改任何資料**；實際清洗待裁後再以交易+零丟值方式執行。')
    A('')
    A('---')
    A('**本檔唯讀，未改任何資料。**')
    c.close()

    md = '\n'.join(L)
    print(md)
    if md_out:
        with open(md_out, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f'\n▸ 已寫出：{md_out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
