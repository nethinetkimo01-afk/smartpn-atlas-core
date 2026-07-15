# -*- coding: utf-8 -*-
"""
ie_ver_recon.py — IE-VER / BZ-VER 遷移前「步驟 1.5」兩份對帳（**唯讀，不改任何資料**）。

任務4 規定：遷移前先出兩份對帳給中樞核對，核對過才進遷移。本檔只產報告，不寫庫。

  報告①【計數】  每個「有 actual 的 header」逐一 count + sum，全庫合計（預期 ≈76357），
                 並印出**計數方法**（哪個欄位、怎麼算、排除了什麼）供中樞複核。
  報告②【遷移歸屬】依「有資料歸該版」規則（**不看 eolr 欄、不看標題**，看哪一版實際有資料）
                 產 header 歸屬表，並證明**零丟值**（歸屬前後 sum 相同、無 header 落空）。

★ 必須在**真庫**上跑（ME129）。本機 atlas.db 是舊副本（有 actual 的 header 只有 3 個，
  真庫應 ≈140）——見 27_WORKING_RULES 十二-7。本檔會自己檢查並在報告最上方標明。

用法：
  python ie_ver_recon.py                      對帳 flask_backend/data/atlas.db
  python ie_ver_recon.py <db路徑>             對帳指定 DB
  python ie_ver_recon.py <db路徑> --md out.md 另存 markdown 報告
"""
import os
import io
import re
import sys
import sqlite3
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, 'flask_backend', 'data', 'atlas.db')

# 計數方法（印在報告裡，讓中樞能複核「我是這樣算的」）
METHOD = """\
計數方法（可複核）：
  來源表   ：ie_process（工序列）JOIN ob_header（表頭）ON ie_process.header_id = ob_header.id
  計數欄位 ：ie_process.actual_operators（實際人數）
  納入條件 ：actual_operators IS NOT NULL AND actual_operators <> 0
             → 「有 actual 的 header」＝ 至少有一列符合上述條件的 header
  count    ：該 header 底下符合條件的**列數**
  sum      ：該 header 底下 actual_operators 的**總和**（SQL SUM，浮點）
  全庫合計 ：所有符合條件的列之 actual_operators 總和（不分 header）
  排除     ：actual_operators 為 NULL 或 0 的列（＝沒填實際人數，非「填了 0 人」）
  唯讀     ：mode=ro + PRAGMA query_only=ON，本檔不可能改到任何資料"""


def ro(path):
    uri = 'file:' + path.replace('\\', '/').replace('?', '%3f').replace('#', '%23') + '?mode=ro'
    c = sqlite3.connect(uri, uri=True)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only = ON')
    return c


def shoe_key(model_name):
    """鞋型 key：model_name 去掉 'Target Output ...' 產能尾巴 + 收斂空白。
    ie_version 父表的 shoe_key 就是這個；版本命名(version_name)另由匯入時給。"""
    s = (model_name or '').split('Target Output')[0]
    s = re.sub(r'\s+', ' ', s).strip(' :：-')
    return s.upper() or '(空白鞋型)'


def report_counts(conn):
    """報告①：逐 header count+sum + 全庫合計。"""
    # lean 欄僅供顯示，不參與計數；基準庫(C槽血脈)沒有這欄，缺欄時填 NULL 照跑。
    has_lean = any(r[1] == 'lean' for r in conn.execute('PRAGMA table_info(ob_header)'))
    lean_col = 'h.lean' if has_lean else 'NULL AS lean'
    rows = conn.execute(f"""
        SELECT h.id, h.model_name, h.season, h.eolr, {lean_col}, h.run,
               COUNT(*) AS n, SUM(p.actual_operators) AS s
        FROM ob_header h
        JOIN ie_process p ON p.header_id = h.id
        WHERE p.actual_operators IS NOT NULL AND p.actual_operators <> 0
        GROUP BY h.id
        ORDER BY h.id
    """).fetchall()
    total = conn.execute("""
        SELECT COUNT(*) AS n, SUM(actual_operators) AS s
        FROM ie_process
        WHERE actual_operators IS NOT NULL AND actual_operators <> 0
    """).fetchone()
    return rows, total


def report_ownership(conn, rows):
    """報告②：依「有資料歸該版」歸屬 + 零丟值證明。

    規則（任務4 明訂）：**不看 eolr 欄、不看標題**，看哪一版實際有資料。
    現況（39_VERSION_CONTROL_DESIGN G2）：ie_process 沒有 stage_id，所有版本共用同一份工序資料
    → 因此「哪一版有資料」在**現行 schema 下無法從版本欄推導**，只能以
      「該 header 實際有 actual 資料」為唯一事實來源：有資料的 header 才需要歸到版本底下。
    歸屬結構：ie_version(shoe_key, version_name) 為父 → ob_header 降為子(版本 × EOLR)。
    """
    groups = collections.defaultdict(list)
    for r in rows:
        groups[shoe_key(r['model_name'])].append(r)
    out = []
    for key in sorted(groups):
        hs = groups[key]
        eolrs = sorted({h['eolr'] for h in hs})
        out.append({
            'shoe_key': key,
            'headers': hs,
            'eolrs': eolrs,
            'sum': sum(h['s'] or 0 for h in hs),
            'rows': sum(h['n'] for h in hs),
            # 「60 選配、120 必有」：120 缺席即異常，報告要標出來讓中樞判
            'has_120': 120 in eolrs,
            'has_60': 60 in eolrs,
        })
    return out


def main():
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    db = args[0] if args else DEFAULT_DB
    md_out = None
    if '--md' in sys.argv:
        md_out = sys.argv[sys.argv.index('--md') + 1]
    if not os.path.isfile(db):
        raise SystemExit(f'❌ 找不到 DB：{db}')

    conn = ro(db)
    try:
        rows, total = report_counts(conn)
        owns = report_ownership(conn, rows)
        all_headers = conn.execute('SELECT COUNT(*) FROM ob_header').fetchone()[0]
        all_proc = conn.execute('SELECT COUNT(*) FROM ie_process').fetchone()[0]
    finally:
        conn.close()

    L = []
    A = L.append
    A('# IE-VER / BZ-VER 遷移前對帳（步驟 1.5）')
    A('')
    A(f'- DB：`{db}`')
    A(f'- ob_header 總數：{all_headers}　/　ie_process 總列數：{all_proc}')
    A(f'- **有 actual 的 header：{len(rows)}**　（真庫應 ≈140）')
    A('')

    # ★ 資料來源自證（27 規則十二-7）：先講清楚這是不是真庫，再談數字。
    real = len(rows) >= 100
    if not real:
        A('> ## ⚠️ 這不是 Jim 真庫 — 以下數字**不可用於核對**')
        A('>')
        A(f'> 有 actual 的 header 只有 **{len(rows)}** 個（真庫應 ≈140）；'
          f'ie_process 只有 **{all_proc}** 列（真庫應 ≈20434）。')
        A('> `flask_backend/data/` 在 .gitignore 內 → ME129 真庫不經 git 同步，'
          '本機這份是留在開發機的舊副本。')
        A('>')
        A('> **請在 ME129 真庫上重跑本檔**，或由中樞用真庫執行，再拿產出的報告核對。')
        A('')

    A('## 報告①｜計數')
    A('')
    A('```')
    A(METHOD)
    A('```')
    A('')
    A('| header_id | 鞋型(shoe_key) | season | EOLR | lean | count(列) | sum(實際人數) |')
    A('|---:|---|---|---:|---|---:|---:|')
    for r in rows:
        A(f'| {r["id"]} | {shoe_key(r["model_name"])} | {r["season"] or ""} | {r["eolr"]} | '
          f'{r["lean"] or ""} | {r["n"]} | {r["s"]:g} |')
    A('')
    grand = total['s'] or 0
    A(f'- **全庫合計（sum of actual_operators）＝ {grand:g}**　（預期 ≈76357）')
    A(f'- 全庫符合條件列數 ＝ {total["n"]}')
    A(f'- 逐 header sum 相加 ＝ {sum(r["s"] or 0 for r in rows):g} '
      f'→ {"✅ 與全庫合計一致" if abs(sum(r["s"] or 0 for r in rows) - grand) < 1e-6 else "❌ 與全庫合計不一致（有列沒歸到 header）"}')
    if real:
        A(f'- 與預期 76357 差異 ＝ {grand - 76357:g}')
    A('')

    A('## 報告②｜遷移歸屬（依「有資料歸該版」；不看 eolr 欄、不看標題）')
    A('')
    A('規則：以「該 header 實際有 actual 資料」為唯一事實來源。')
    A('結構：`ie_version(shoe_key, version_name)` 為父 → `ob_header` 降為子（版本 × EOLR）。')
    A('')
    A('| 鞋型(shoe_key) | 歸屬 header_id | EOLR 分布 | 120 必有 | 60 選配 | 列數 | sum |')
    A('|---|---|---|:--:|:--:|---:|---:|')
    for g in owns:
        ids = ','.join(str(h['id']) for h in g['headers'])
        A(f'| {g["shoe_key"]} | {ids} | {g["eolrs"]} | '
          f'{"✅" if g["has_120"] else "❌ 缺"} | {"有" if g["has_60"] else "—"} | '
          f'{g["rows"]} | {g["sum"]:g}')
    A('')
    A('### 零丟值證明')
    A('')
    own_sum = sum(g['sum'] for g in owns)
    own_rows = sum(g['rows'] for g in owns)
    own_ids = {h['id'] for g in owns for h in g['headers']}
    src_ids = {r['id'] for r in rows}
    A(f'- 歸屬後 sum 合計 ＝ {own_sum:g}　vs　歸屬前全庫合計 ＝ {grand:g} → '
      f'{"✅ 相同，零丟值" if abs(own_sum - grand) < 1e-6 else "❌ 不同，有丟值"}')
    A(f'- 歸屬後列數 ＝ {own_rows}　vs　歸屬前列數 ＝ {total["n"]} → '
      f'{"✅ 相同" if own_rows == total["n"] else "❌ 不同"}')
    A(f'- 有 actual 的 header 全部有歸屬？{len(own_ids)}/{len(src_ids)} → '
      f'{"✅ 無落空" if own_ids == src_ids else "❌ 落空：" + str(sorted(src_ids - own_ids))}')
    missing_120 = [g['shoe_key'] for g in owns if not g['has_120']]
    A(f'- 「120 必有」檢查：{"✅ 全部鞋型都有 120" if not missing_120 else "⚠️ 缺 120 的鞋型：" + str(missing_120)}')
    A('')
    A('---')
    A('')
    A('**本檔唯讀，未改任何資料。核對通過前不得進行遷移**（任務4 規定）。')

    md = '\n'.join(L)
    print(md)
    if md_out:
        with open(md_out, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f'\n▸ 已寫出：{md_out}')
    # 不是真庫 → 非 0 離開，避免被當成「對帳過了」
    sys.exit(0 if real else 2)


if __name__ == '__main__':
    main()
