# -*- coding: utf-8 -*-
"""
ie_ver_eolr_evidence.py — 雙EOLR判定證據表（**唯讀，不改任何資料**）。

中樞裁決①要求：每個 header 的 EOLR 依兩軸各判一次，交中樞裁定「用哪一軸」與名單。
  軸(a) eolr 欄   ：ob_header.eolr 的值
  軸(b) 標題文字  ：model_name 裡的 Target Output 產能字樣推出的每小時雙數
                    主規則：括號內 "(120 Prs / Hour)" → 120
                    備規則：主規則無命中時，用 "Target Output : 960 Prs / 8H" → 960/8 = 120
本檔只產報告，不寫庫。
"""
import io
import os
import re
import sys
import sqlite3
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(HERE, 'real_db_for_recon', 'atlas.db')

METHOD = """\
判定方法（可複核）：
  軸(a) eolr 欄  ：直接取 ob_header.eolr
  軸(b) 標題文字 ：從 ob_header.model_name 解析
      主規則 R1：括號內每小時雙數  regex  \\((\\d+)\\s*Prs\\s*/\\s*Ho
                 例：'... 8H (120 Prs / Hour)' → 120
      備規則 R2：R1 無命中時，取 8 小時產能再除以 8   regex  Target\\s*Output\\s*:?\\s*(\\d+)\\s*Prs\\s*/\\s*8H
                 例：'Target Output : 960 Prs / 8H' → 960/8 = 120
      兩規則皆無命中 → 判定為 None（無法從標題判）
  納入範圍：有 actual 的 header（actual_operators IS NOT NULL AND <> 0），共 140 個
  shoe_key：model_name 去掉 'Target Output ...' 尾巴 + 收斂空白 + 轉大寫（與 ie_ver_recon.py 相同）
  唯讀    ：mode=ro + PRAGMA query_only=ON"""

R1 = re.compile(r'\((\d+)\s*Prs\s*/\s*Ho', re.I)
R2 = re.compile(r'Target\s*Output\s*:?\s*(\d+)\s*Prs\s*/\s*8\s*H', re.I)


def ro(path):
    uri = 'file:' + path.replace('\\', '/') + '?mode=ro'
    c = sqlite3.connect(uri, uri=True)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only = ON')
    return c


def shoe_key(model_name):
    s = (model_name or '').split('Target Output')[0]
    s = re.sub(r'\s+', ' ', s).strip(' :：-')
    return s.upper() or '(空白鞋型)'


def axis_b(model_name):
    """回傳 (值, 依據規則, 命中的原文片段)。"""
    m = R1.search(model_name or '')
    if m:
        return int(m.group(1)), 'R1(括號每小時)', m.group(0)
    m = R2.search(model_name or '')
    if m:
        v = int(m.group(1))
        return (v // 8 if v % 8 == 0 else round(v / 8, 2)), 'R2(8H產能/8)', m.group(0)
    return None, '無命中', ''


def main():
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    db = args[0] if args else DEFAULT_DB
    md_out = sys.argv[sys.argv.index('--md') + 1] if '--md' in sys.argv else None

    conn = ro(db)
    rows = conn.execute("""
        SELECT h.id, h.model_name, h.season, h.eolr,
               COUNT(*) AS n, SUM(p.actual_operators) AS s,
               (SELECT GROUP_CONCAT(DISTINCT x.art) FROM ie_process x WHERE x.header_id = h.id) AS arts
        FROM ob_header h
        JOIN ie_process p ON p.header_id = h.id
        WHERE p.actual_operators IS NOT NULL AND p.actual_operators <> 0
        GROUP BY h.id ORDER BY h.id
    """).fetchall()

    recs = []
    for r in rows:
        b, rule, frag = axis_b(r['model_name'])
        recs.append({
            'id': r['id'], 'model_name': r['model_name'], 'key': shoe_key(r['model_name']),
            'season': r['season'], 'a': r['eolr'], 'b': b, 'rule': rule, 'frag': frag,
            'arts': (r['arts'] or '')[:40], 'n': r['n'], 's': r['s'] or 0,
        })
    conn.close()

    L = []
    A = L.append
    A('# 雙EOLR判定證據表（中樞裁決①）\n')
    A(f'- DB：`{db}`')
    A(f'- 納入：有 actual 的 header ＝ {len(recs)}\n')
    A('```\n' + METHOD + '\n```\n')

    # ---- 1. 兩軸不一致清單
    bad = [r for r in recs if r['b'] is not None and r['a'] != r['b']]
    none_b = [r for r in recs if r['b'] is None]
    A('## 1｜兩軸不一致的 header\n')
    A(f'- 兩軸一致：{len(recs) - len(bad) - len(none_b)} / {len(recs)}')
    A(f'- **兩軸不一致：{len(bad)}**')
    A(f'- 標題無法判（軸b None）：{len(none_b)}\n')
    if bad:
        A('| header_id | 鞋型(shoe_key) | season | 軸a eolr欄 | 軸b 標題 | 依據 | 標題命中片段 | 列數 | sum |')
        A('|---:|---|---|---:|---:|---|---|---:|---:|')
        for r in bad:
            A(f'| {r["id"]} | {r["key"]} | {r["season"]} | **{r["a"]}** | **{r["b"]}** | {r["rule"]} | `{r["frag"]}` | {r["n"]} | {r["s"]:.3f} |')
        A('')
        A(f'- 不一致 header 的 sum 合計 ＝ **{sum(r["s"] for r in bad):.3f}**')
        A(f'- 不一致 header 的列數合計 ＝ **{sum(r["n"] for r in bad)}**\n')
    if none_b:
        A('### 標題無法判的 header\n')
        A('| header_id | 鞋型 | 軸a | model_name |')
        A('|---:|---|---:|---|')
        for r in none_b:
            A(f'| {r["id"]} | {r["key"]} | {r["a"]} | `{r["model_name"]}` |')
        A('')

    # ---- 2. 兩軸各自的雙EOLR鞋型清單
    def dual_by(axis):
        g = collections.defaultdict(list)
        for r in recs:
            v = r[axis]
            if v is not None:
                g[r['key']].append(r)
        out = {}
        for k, hs in g.items():
            vals = sorted({h[axis] for h in hs})
            if len(vals) > 1:
                out[k] = (vals, hs)
        return g, out

    for axis, name in [('a', '軸(a) eolr 欄'), ('b', '軸(b) 標題文字')]:
        g, dual = dual_by(axis)
        A(f'## 2{axis}｜{name} 判出的雙EOLR鞋型\n')
        A(f'- 鞋型總數：{len(g)}　/　**雙EOLR鞋型：{len(dual)}**')
        distrib = collections.Counter()
        for k, hs in g.items():
            distrib[tuple(sorted({h[axis] for h in hs}))] += 1
        A(f'- EOLR 組合分布：{dict((str(list(k)), v) for k, v in sorted(distrib.items(), key=lambda x: -x[1]))}\n')
        if dual:
            A('| 鞋型(shoe_key) | EOLR分布 | header_id | 該值 | ART | 列數 | sum |')
            A('|---|---|---:|---:|---|---:|---:|')
            for k in sorted(dual):
                vals, hs = dual[k]
                for h in sorted(hs, key=lambda x: (x[axis], x['id'])):
                    A(f'| {k} | {vals} | {h["id"]} | {h[axis]} | {h["arts"]} | {h["n"]} | {h["s"]:.3f} |')
            A('')

    # ---- 3. shoe_key 收斂造成的合併案例
    A('## 3｜shoe_key 收斂造成的合併案例\n')
    A('（收斂前 model_name 不同、收斂後同一個 key → 被當成同一鞋型）\n')
    byk = collections.defaultdict(set)
    for r in recs:
        byk[r['key']].add(r['model_name'])
    merged = {k: v for k, v in byk.items() if len(v) > 1}
    A(f'- 受合併影響的鞋型：**{len(merged)}** / {len(byk)}\n')
    for k in sorted(merged):
        names = sorted(merged[k])
        ids = sorted(r['id'] for r in recs if r['key'] == k)
        A(f'### {k}　（header_id: {ids}）\n')
        A(f'收斂前 {len(names)} 種不同 model_name：\n')
        for nm in names:
            hid = sorted(r['id'] for r in recs if r['model_name'] == nm)
            ea = sorted({r['a'] for r in recs if r['model_name'] == nm})
            eb = sorted({str(r['b']) for r in recs if r['model_name'] == nm})
            A(f'- `{nm}`　→ id={hid}　軸a={ea}　軸b={eb}')
        A('')

    out = '\n'.join(L)
    print(out)
    if md_out:
        with open(md_out, 'w', encoding='utf-8') as f:
            f.write(out)
        print(f'\n[已存檔] {md_out}', file=sys.stderr)


if __name__ == '__main__':
    main()
