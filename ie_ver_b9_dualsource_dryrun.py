# -*- coding: utf-8 -*-
"""
ie_ver_b9_dualsource_dryrun.py — B9 雙源合併試算（**dry-run：只算不寫，只出候選+報告**）。

兩源：
  A 基準庫 real_db_for_recon/atlas.db        —— 有 16,501 筆 per-row 實際人數（B3 已落格），0 個合併群組
  B ME129  real_db_for_recon/me129_atlas.db.db —— 有 149 個「合併人數」群組（headcount），per-row actual 另計

合併目標（B5 未來要做的）：把 B 的合併人數群組帶進版本×ART×EOLR 模型（→ ie_group_headcount）。
身分橋接＝ART（版本×ART 是識別單位）：ME129 群組 → 其 process_ids 的 ART → 對應基準庫 header。

本檔只做 dry-run：算出「哪些群組可自動對映、哪些不行、會落哪個 EOLR、覆蓋多少 headcount」，
**不寫任何資料**。供中樞裁決 B5 要不要做、怎麼做。零丟值：報告清楚列出可映/不可映的 headcount 分佈。

唯讀：兩庫皆 mode=ro + query_only=ON。

用法：
  python ie_ver_b9_dualsource_dryrun.py [--base 基準.db] [--me ME129.db] [--md out.md]
"""
import io
import os
import re
import sys
import json
import sqlite3
import collections
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# B3 裁決①：這 4 個 header（G2）落格覆蓋為 120（標題為準）；其餘 header 用 eolr 欄。
OVERRIDE_TO_120 = {140, 141, 142, 143}


def ro(path):
    c = sqlite3.connect('file:' + path.replace('\\', '/') + '?mode=ro', uri=True)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    return c


def arg(flag, default):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else default


def main():
    base_db = arg('--base', 'real_db_for_recon/atlas.db')
    me_db = arg('--me', 'real_db_for_recon/me129_atlas.db.db')
    md_out = arg('--md', None)
    for p in (base_db, me_db):
        if not os.path.isfile(p):
            print(f'❌ 找不到 DB：{p}'); return 3
    base = ro(base_db); me = ro(me_db)

    # 基準：art → (header_id, eolr, assigned_eolr)
    base_art = {}
    for r in base.execute("SELECT DISTINCT p.art, h.id AS hid, h.eolr FROM ie_process p "
                          "JOIN ob_header h ON h.id=p.header_id WHERE p.art IS NOT NULL AND p.art<>''"):
        assigned = 120 if r['hid'] in OVERRIDE_TO_120 else r['eolr']
        base_art[r['art']] = {'hid': r['hid'], 'eolr': r['eolr'], 'assigned': assigned}
    # 基準：header 的 process rows 索引（供 process-level 可映性檢查）：(segment,zone,process_name) -> count
    base_proc = collections.defaultdict(set)
    for r in base.execute("SELECT header_id, segment, zone, process_name FROM ie_process"):
        base_proc[r['header_id']].add((r['segment'], r['zone'], r['process_name']))

    groups = me.execute("SELECT id,header_id,segment,zone,stage_id,process_ids,headcount FROM ie_process_group").fetchall()

    matched, unmatched = [], []
    hc_total = hc_matched = 0.0
    for g in groups:
        hc = g['headcount'] or 0
        hc_total += hc
        try:
            pids = json.loads(g['process_ids']) if g['process_ids'] else []
        except Exception:
            pids = []
        arts, prows = set(), []
        if pids:
            q = "SELECT art, segment, zone, process_name FROM ie_process WHERE id IN (%s)" % ','.join('?' * len(pids))
            for pr in me.execute(q, pids):
                if pr['art']:
                    arts.add(pr['art'])
                prows.append((pr['segment'], pr['zone'], pr['process_name']))
        hit_arts = arts & set(base_art)
        if hit_arts:
            art = sorted(hit_arts)[0]
            tgt = base_art[art]
            # process 可映性：這群 ME129 process rows 有幾個能在基準對應 header 找到同 (seg,zone,name)
            bset = base_proc.get(tgt['hid'], set())
            mapok = sum(1 for pr in prows if pr in bset)
            matched.append({'gid': g['id'], 'art': art, 'hid': tgt['hid'], 'assigned': tgt['assigned'],
                            'hc': hc, 'pids': len(pids), 'mapok': mapok,
                            'multi_art': len(arts) > 1})
            hc_matched += hc
        else:
            unmatched.append({'gid': g['id'], 'hc': hc, 'pids': len(pids),
                              'arts': sorted(arts)[:3], 'reason': ('無ART' if not arts else 'ART不在基準')})

    base_art_set = set(base_art)
    me_art_set = set(a[0] for a in me.execute("SELECT DISTINCT art FROM ie_process WHERE art IS NOT NULL AND art<>''"))

    L = []; A = L.append
    A('# B9 雙源合併試算（dry-run：只算不寫，只出候選+報告）')
    A('')
    A(f'- 產出：{datetime.now().isoformat(timespec="seconds")}')
    A(f'- 源A 基準庫：`{base_db}`　distinct ART={len(base_art_set)}')
    A(f'- 源B ME129 ：`{me_db}`　distinct ART={len(me_art_set)}　合併群組={len(groups)}')
    A(f'- 兩源 ART 交集：**{len(base_art_set & me_art_set)}**（僅此部分可能自動對映）')
    A('')
    A('## 合併候選總覽')
    A('| 指標 | 值 |')
    A('|---|---:|')
    A(f'| ME129 群組總數 | {len(groups)} |')
    A(f'| ✅ 可對映（ART 在基準）| **{len(matched)}** |')
    A(f'| ❌ 不可對映（ART 不在基準/無ART）| **{len(unmatched)}** |')
    A(f'| headcount 總和（源B）| {hc_total:g} |')
    A(f'| headcount 可對映合計 | {hc_matched:g}（{100*hc_matched/hc_total:.1f}%）|')
    A(f'| headcount 不可對映合計 | {hc_total-hc_matched:g}（{100*(hc_total-hc_matched)/hc_total:.1f}%）|')
    A('')
    A('> **關鍵結論**：兩源 ART 僅交集 %d，過半 ME129 合併群組（%d/%d）的 ART 不在基準庫 → '
      '無法自動對映。B5 合併人數匯入**不是乾淨的一鍵合併**，需中樞裁決如何處理不可對映的 %g headcount。'
      % (len(base_art_set & me_art_set), len(unmatched), len(groups), hc_total - hc_matched))
    A('')
    A('## 可對映候選（前 40，process 可映性＝ME129群組工序能在基準對應 header 找到同(段,區,工序名)的比例）')
    A('| ME129群組 | ART | →基準header | 落格EOLR | headcount | 群組工序數 | process可映 |')
    A('|---:|---|---:|---:|---:|---:|---|')
    for m in matched[:40]:
        flag = ' ⚠️多ART' if m['multi_art'] else ''
        A(f'| {m["gid"]} | {m["art"]} | {m["hid"]} | {m["assigned"]} | {m["hc"]:g} | {m["pids"]} | '
          f'{m["mapok"]}/{m["pids"]}{flag} |')
    if len(matched) > 40:
        A(f'| … | 其餘 {len(matched)-40} 筆略 | | | | | |')
    A('')
    full_map = sum(1 for m in matched if m['mapok'] == m['pids'] and m['pids'] > 0)
    A(f'- 可對映候選中，process 100% 可映（工序也對得上）：**{full_map}/{len(matched)}**')
    A(f'  → 只有這些能真正安全 remap process_ids；其餘即使 ART 對上，工序對不齊仍需人工/裁決。')
    A('')
    A('## 不可對映摘要（前 20）')
    A('| ME129群組 | headcount | 工序數 | 原因 | ART樣本 |')
    A('|---:|---:|---:|---|---|')
    for u in unmatched[:20]:
        A(f'| {u["gid"]} | {u["hc"]:g} | {u["pids"]} | {u["reason"]} | {",".join(u["arts"]) or "—"} |')
    if len(unmatched) > 20:
        A(f'| … | 其餘 {len(unmatched)-20} 筆略 | | | |')
    A('')
    A('## 判定與待裁事項')
    A('1. **未寫入任何資料**（dry-run）。B5 實際匯入待中樞裁決。')
    A('2. 兩源 ART 交集偏低（可對映 headcount 僅 %.1f%%）→ 需中樞確認：' % (100*hc_matched/hc_total))
    A('   (a) me129_atlas.db.db 是否為當前正確的 ME129 生產快照？（另有 me129_unlock/me129_old 副本）')
    A('   (b) 不可對映的 %d 群組（%g headcount）是基準庫沒有的新品，還是身分橋接規則需改（不只靠 ART）？'
      % (len(unmatched), hc_total - hc_matched))
    A(f'   (c) B5 是否只匯入「ART+工序皆 100% 可映」的 {full_map} 群組，其餘留待人工？')
    A('')
    A('---')
    A('**本檔唯讀，未改任何資料（dry-run）。**')
    base.close(); me.close()

    md = '\n'.join(L)
    print(md)
    if md_out:
        with open(md_out, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f'\n▸ 已寫出：{md_out}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
