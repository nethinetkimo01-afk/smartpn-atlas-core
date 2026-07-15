# -*- coding: utf-8 -*-
"""
ie_ver_b8_confirm_list.py — B8 現場確認清單：把 B3 落格時標記 pending 的
ie_eolr_confirm（eolr欄↔標題矛盾、靠裁決①落格的 header）產成人可讀清單，供現場實測確認。

★入規27：本腳本原始碼不含任何真鞋型名/ART；鞋型名、ART、季別一律執行期從 DB 讀，
  只寫進 gitignored 的報告檔（real_db_for_recon/…），不進 git。

唯讀：mode=ro + PRAGMA query_only=ON。只產報告，不改任何資料。

用法：
  ATLAS_DB=/path/to/b3_work.db python ie_ver_b8_confirm_list.py [--md 輸出路徑.md]
"""
import io
import os
import re
import sys
import sqlite3
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def shoe_key(model_name):
    s = re.split(r'Target\s*Output', model_name or '', flags=re.I)[0]
    return re.sub(r'\s+', ' ', s).strip(' :：-').upper() or '(空白)'


def ro(path):
    c = sqlite3.connect('file:' + path.replace('\\', '/') + '?mode=ro', uri=True)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    return c


def main():
    db = os.environ.get('ATLAS_DB')
    if not db:
        print('❌ 未設定 ATLAS_DB（應指向已落格的 b3_work.db）'); return 3
    if not os.path.isfile(db):
        print(f'❌ 找不到 DB：{db}'); return 3
    md_out = None
    if '--md' in sys.argv:
        md_out = sys.argv[sys.argv.index('--md') + 1]

    c = ro(db)
    if not c.execute("SELECT 1 FROM sqlite_master WHERE name='ie_eolr_confirm'").fetchone():
        print('❌ 此庫無 ie_eolr_confirm（尚未 B3 落格？）'); return 3

    rows = c.execute('''
        SELECT f.header_id, f.assigned_eolr, f.eolr_column, f.eolr_title, f.ruling, f.status,
               h.model_name, h.season
        FROM ie_eolr_confirm f JOIN ob_header h ON h.id = f.header_id
        ORDER BY f.eolr_column, f.header_id
    ''').fetchall()

    L = []
    A = L.append
    A('# B8 現場確認清單（EOLR 矛盾 header，裁決①落格待實測確認）')
    A('')
    A(f'- 來源 DB（唯讀）：`{db}`')
    A(f'- 產出時間：{datetime.now().isoformat(timespec="seconds")}')
    A(f'- 待確認 header 數：**{len(rows)}**（全部 status=pending）')
    A('')
    A('> 這些 header 的「eolr 欄」與「標題 R2 解析」互相矛盾，B3 已依裁決①暫時落格，')
    A('> 但**落完格不等於當真**——需現場確認該 header 實際產線節拍是 60 還是 120 Prs/Hour。')
    A('> 確認後由中樞更新 ie_eolr_confirm.status，若與落格 EOLR 不符則需回改 ie_process_actual 的格位。')
    A('')
    A('| # | header_id | 鞋型 | season | ART | eolr欄 | 標題R2 | 落格採用 | 依據 | actual列數 | actual sum |')
    A('|---:|---:|---|---|---|---:|---:|---:|---|---:|---:|')
    for i, r in enumerate(rows, 1):
        arts = [a[0] for a in c.execute(
            "SELECT DISTINCT art FROM ie_process WHERE header_id=? AND art IS NOT NULL AND art<>''",
            (r['header_id'],)).fetchall()]
        art = ','.join(arts) if arts else '—'
        agg = c.execute(
            'SELECT COUNT(*), SUM(actual_operators) FROM ie_process '
            'WHERE header_id=? AND actual_operators IS NOT NULL AND actual_operators<>0',
            (r['header_id'],)).fetchone()
        n, s = agg[0], (agg[1] or 0)
        basis = '標題為準(覆蓋欄)' if r['assigned_eolr'] == r['eolr_title'] else 'eolr欄為準'
        A(f'| {i} | {r["header_id"]} | {shoe_key(r["model_name"])} | {r["season"] or ""} | {art} | '
          f'{r["eolr_column"]} | {r["eolr_title"]} | **{r["assigned_eolr"]}** | {basis} | {n} | {s:g} |')
    A('')

    # 分群小結
    g1 = [r for r in rows if r['eolr_column'] == 120]
    g2 = [r for r in rows if r['eolr_column'] == 60]
    A('## 分群小結')
    A('')
    A(f'- **G1（eolr欄=120、標題=60）共 {len(g1)} 筆**：落格採 120（eolr欄為準，未覆蓋）。'
      f'現場若實測為 60 → 需把這些 header 的格位由 120 改回 60。')
    A(f'- **G2（eolr欄=60、標題=120）共 {len(g2)} 筆**：落格採 120（標題為準，已覆蓋 eolr 欄）。'
      f'現場若實測為 60 → 需把這些 header 的格位由 120 改回 60。')
    A('')
    A('---')
    A('**本檔唯讀，未改任何資料。確認結果由中樞回填 ie_eolr_confirm.status。**')
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
