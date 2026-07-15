# -*- coding: utf-8 -*-
"""
ie_ver_b6_rename_analysis.py — B6 改名 · 唯讀分析 + ①同名碰撞停點檢查。

B6「改名」＝由 model_name 導出顯示分組名 shoe_key。中樞裁決 2026-07-15：
識別單位＝版本×ART，鞋型名僅顯示分組、不合併任何 header。故本步的關鍵風險＝
**①同名碰撞**：是否有兩個「不同的識別單位」被改名後擠進同一個儲存鍵、互相覆蓋＝丟資料。

本檔只做唯讀分析，回答「能不能安全改名」，**不寫任何資料**（改名的實際寫入目標＝
B7 的 ie_version 父表，尚未建；故 B6 寫入待 B7/中樞裁決）。

①同名碰撞的可驗定義（本檔據此判 go/stop）：
  識別單位＝(art)。若 art 對每個 header 1:1、且每個 art 全庫唯一 → 改名（顯示分組）
  不可能讓兩個識別單位共用一格。反之若有 art 跨多 header、或 (shoe_key,art) 需二選一命名 → 碰撞。

唯讀：mode=ro + PRAGMA query_only=ON。

用法：
  ATLAS_DB=/path/to/atlas.db python ie_ver_b6_rename_analysis.py [--md out.md]
"""
import io
import os
import re
import sys
import sqlite3
import collections
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ACTUAL_COND = "actual_operators IS NOT NULL AND actual_operators <> 0"


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
    if not db or not os.path.isfile(db):
        print(f'❌ ATLAS_DB 無效：{db}'); return 3
    md_out = sys.argv[sys.argv.index('--md') + 1] if '--md' in sys.argv else None
    c = ro(db)

    # 取有 actual 的 header（識別單位母體）：id, model_name, eolr, season, 對應 ART 集合
    hdrs = c.execute(f'''
        SELECT h.id, h.model_name, h.eolr, h.season
        FROM ob_header h
        WHERE EXISTS (SELECT 1 FROM ie_process p WHERE p.header_id=h.id AND p.{ACTUAL_COND})
        ORDER BY h.id
    ''').fetchall()

    # 每個 header 的 ART 集合
    hdr_arts = {}
    for h in hdrs:
        arts = [a[0] for a in c.execute(
            "SELECT DISTINCT art FROM ie_process WHERE header_id=? AND art IS NOT NULL AND art<>''",
            (h['id'],)).fetchall()]
        hdr_arts[h['id']] = arts

    # ── 碰撞檢查 ──────────────────────────────────────────────────────────
    # C1: art → 幾個 header（跨 header 的 art＝識別不唯一）
    art2hdr = collections.defaultdict(set)
    for h in hdrs:
        for a in hdr_arts[h['id']]:
            art2hdr[a].add(h['id'])
    art_multi = {a: hs for a, hs in art2hdr.items() if len(hs) > 1}

    # C2: art → 幾個 shoe_key（同一 art 落到多個顯示名＝改名歧義）
    art2key = collections.defaultdict(set)
    for h in hdrs:
        for a in hdr_arts[h['id']]:
            art2key[a].add(shoe_key(h['model_name']))
    art_key_multi = {a: ks for a, ks in art2key.items() if len(ks) > 1}

    # C3: header 是否恰好 1 個 ART（版本×ART 前提）
    hdr_multi_art = {h['id']: hdr_arts[h['id']] for h in hdrs if len(hdr_arts[h['id']]) != 1}

    # 顯示分組：shoe_key → headers / arts / eolrs（資訊性，非碰撞）
    key2hdrs = collections.defaultdict(list)
    for h in hdrs:
        key2hdrs[shoe_key(h['model_name'])].append(h)
    converge = {k: hs for k, hs in key2hdrs.items() if len(hs) > 1}

    no_collision = (not art_multi) and (not art_key_multi) and (not hdr_multi_art)

    L = []; A = L.append
    A('# B6 改名 · 唯讀分析 + ①同名碰撞停點檢查')
    A('')
    A(f'- DB（唯讀）：`{db}`　產出：{datetime.now().isoformat(timespec="seconds")}')
    A(f'- 有 actual 的 header（識別單位母體）：{len(hdrs)}')
    A(f'- 相異 shoe_key（顯示分組名）：{len(key2hdrs)}')
    A('')
    A('## ①同名碰撞停點判定')
    A('')
    A(f'| 檢查 | 意義 | 命中數 | 判定 |')
    A(f'|---|---|---:|---|')
    A(f'| C1 art 跨多 header | 識別不唯一→改名會擠一格 | {len(art_multi)} | {"✅" if not art_multi else "❌ 碰撞"} |')
    A(f'| C2 art 落多 shoe_key | 同一識別單位多個名→歧義 | {len(art_key_multi)} | {"✅" if not art_key_multi else "❌ 碰撞"} |')
    A(f'| C3 header 非恰好1 ART | 破壞版本×ART 前提 | {len(hdr_multi_art)} | {"✅" if not hdr_multi_art else "❌"} |')
    A('')
    if no_collision:
        A('**判定：✅ 無同名碰撞。** 每個識別單位＝一個 art、art 全庫 1:1 對應 header、')
        A('且每個 art 只落一個 shoe_key。改名（顯示分組）不可能讓兩個識別單位共用一格、互相覆蓋。')
        A('→ **①停點未觸發**，B6 顯示分組安全。')
    else:
        A('**判定：❌ 偵測到同名碰撞 → 觸發①停點，需中樞裁。** 明細見下。')
        for a, hs in list(art_multi.items())[:20]:
            A(f'- C1 art 跨 header：{a} → headers {sorted(hs)}')
        for a, ks in list(art_key_multi.items())[:20]:
            A(f'- C2 art 多名：{a} → {sorted(ks)}')
        for hid, arts in list(hdr_multi_art.items())[:20]:
            A(f'- C3 header {hid} 有 {len(arts)} 個 ART')
    A('')
    A('## 顯示分組收斂（資訊性，非碰撞——版本×ART 下不丟值）')
    A('')
    A(f'- shoe_key 對應多個 header 的收斂組：**{len(converge)}** 組')
    A('> 這些是「不同 ART 共用同一顯示名」的正常分組。舊裁決⑤（合併成一份標時/工序）會在此毀資料')
    A('> （見 b3_blocker：17 鞋型 79 header 標時互異），但已被「版本×ART、名僅顯示」新裁決取代 → 不合併、不丟值。')
    A('')
    A('| shoe_key | header 數 | ART 數 | EOLR 分布 |')
    A('|---|---:|---:|---|')
    for k in sorted(converge, key=lambda x: -len(converge[x])):
        hs = converge[k]
        arts = sorted({a for h in hs for a in hdr_arts[h['id']]})
        eolrs = sorted({h['eolr'] for h in hs})
        A(f'| {k} | {len(hs)} | {len(arts)} | {eolrs} |')
    A('')
    A('## B6 寫入為何待裁')
    A('改名的實際寫入目標＝B7 `ie_version(shoe_key, version_name)` 父表，**目前不存在**（需 M013 + 命名規則裁決）。')
    A('故 B6 只出本唯讀分析證明「可安全改名、無碰撞」，實際寫入待 B7/中樞裁。')
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
    # 有碰撞 → 非 0 離開，讓批次驅動能偵測①停點
    return 0 if no_collision else 1


if __name__ == '__main__':
    sys.exit(main())
