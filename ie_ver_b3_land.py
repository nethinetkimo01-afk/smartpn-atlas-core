# -*- coding: utf-8 -*-
"""
ie_ver_b3_land.py — B3 落格：把 ie_process 的實際人數 (actual_operators)
落到 ie_process_actual（版本×ART×EOLR 分格），依中樞裁決①決定每個 header 的 EOLR。

★入規27：真鞋型名/ART 料號一律不寫進原始碼（本檔會進 git）。矛盾 header 一律以 header_id 指涉；
  需要鞋型名時執行期從 DB 讀、只留在記憶體（與 ie_ver_recon.py / data_leak_gate.py 同法）。

★識別單位＝版本×ART（中樞裁決 2026-07-15）：鞋型名僅顯示分組，遷移不合併任何 header。
  每個 ART 恰好對應一個 EOLR、一份標時/工序（140 ART ↔ 140 有 actual 的 header，1:1）。
  故落格＝每個工序把它的實際人數放進「它所屬 EOLR」那一格，另一格留空（裁決②不繼承）。

裁決①落格規則（EOLR 歸位）：
  預設 assigned_eolr = ob_header.eolr（eolr 欄為準）
  15 筆 eolr欄↔標題(R2)矛盾的 header 分兩群（以 header_id 指涉）：
    群組G1（eolr欄=120、標題=60，11 筆）→ 落 120（eolr欄為準，不覆蓋）
    群組G2（eolr欄=60、標題=120， 4 筆）→ 落 120（標題為準，覆蓋 eolr 欄）
  這 15 筆全部寫入 ie_eolr_confirm(status=pending)，等 B8 現場確認。落完格不等於當真。
  另格留空：每個工序只落一列（其 assigned_eolr），另一格由 v_ie_process_cell 以 NULL 呈現。

零丟值斷言（落格後、commit 前，任一不符 → ROLLBACK、印 STOP、exit 2）：
  A 子表 count == 舊欄 count == 16,501
  B 子表 sum   ≈  舊欄 sum
  C 一工序一格：COUNT(*) == COUNT(DISTINCT process_id)
  D 逐格：每列 ie_process_actual.actual_operators == 對應 ie_process.actual_operators（IS NOT 比對）
  E 全覆蓋：每個有 actual 的工序都有一格
  F 基準未漂移：舊欄 count==16,501 且 sum 在 76,357.19±0.01

唯讀基準、寫入隔離副本：DB 由環境變數 ATLAS_DB 指定。拒絕在基準庫/正式庫上跑。

用法：
  ATLAS_DB=/path/to/work_copy.db python ie_ver_b3_land.py
"""
import io
import os
import re
import sys
import sqlite3
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ACTUAL_COND = 'actual_operators IS NOT NULL AND actual_operators <> 0'
EXPECT_COUNT = 16501
EXPECT_SUM = 76357.19
SUM_TOL = 0.01           # 基準漂移比對用（cent 級）
SUB_SUM_TOL = 1e-6       # 子表 vs 舊欄：同值搬運，容差取極小

# 中樞裁決①命名的 15 筆矛盾 header（eolr欄 ↔ 標題 R2 相斥）。只用 header_id，不寫鞋型名。
#   G1：eolr欄=120、標題=60 → 落120（欄為準，不需覆蓋）
#   G2：eolr欄=60、標題=120 → 落120（標題為準，需把 eolr 欄的 60 覆蓋成 120）
CONFLICT_G1 = [29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39]   # eolr_col=120, eolr_title=60,  assigned=120
CONFLICT_G2 = [140, 141, 142, 143]                            # eolr_col=60,  eolr_title=120, assigned=120
OVERRIDE_TO_120 = set(CONFLICT_G2)                            # 落格時唯一需要覆蓋 eolr 欄的一群

# 這兩條路徑神聖不可寫：基準庫、正式庫
SACRED = {
    os.path.normcase(os.path.abspath(os.path.join('real_db_for_recon', 'atlas.db'))),
    os.path.normcase(os.path.abspath(os.path.join('flask_backend', 'data', 'atlas.db'))),
}


def shoe_key(model_name):
    """執行期從 model_name 導出鞋型 key（與 ie_ver_recon.py 同法）；只用於群組一致性守門，不落地、不寫進 git。"""
    s = re.split(r'Target\s*Output', model_name or '', flags=re.I)[0]
    return re.sub(r'\s+', ' ', s).strip(' :：-').upper()


def die(msg, code=2):
    print('\n' + '=' * 68)
    print(f'  ❌ STOP：{msg}')
    print('  B3 未提交任何資料（交易已回滾）。此為②零丟值/資料前提失敗＝必停點。')
    print('=' * 68)
    sys.exit(code)


def main():
    db = os.environ.get('ATLAS_DB')
    if not db:
        die('未設定 ATLAS_DB。B3 只在隔離副本上跑，拒絕預設路徑。', 3)
    db = os.path.abspath(db)
    if os.path.normcase(db) in SACRED:
        die(f'ATLAS_DB 指向神聖庫（基準/正式）：{db}。B3 一律在隔離副本上跑。', 3)
    if not os.path.isfile(db):
        die(f'找不到 DB：{db}', 3)

    print('=' * 68)
    print('ie_ver_b3_land — B3 落格：實際人數 → ie_process_actual（版本×ART×EOLR）')
    print('=' * 68)
    print(f'DB（隔離副本，可寫）：{db}')

    conn = sqlite3.connect(db)
    conn.execute('PRAGMA foreign_keys=ON')
    cur = conn.cursor()

    # ── 前置：schema 就緒 & 目標表為空（保證這是乾淨落格，不疊加） ──────────────
    for t in ('ie_process_actual', 'ie_eolr_confirm'):
        if not cur.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone():
            die(f'缺表 {t}：working copy 未過 M012 migrate。先跑 migrate 再落格。', 3)
        n = cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        if n != 0:
            die(f'{t} 已有 {n} 列，非乾淨副本。請用新 migrate 副本重跑，避免疊加。', 3)

    # ── F前段：基準未漂移（落格前先驗身，地基不對不落格） ──────────────────────
    old_cnt = cur.execute(f'SELECT COUNT(*) FROM ie_process WHERE {ACTUAL_COND}').fetchone()[0]
    old_sum = cur.execute(f'SELECT SUM(actual_operators) FROM ie_process WHERE {ACTUAL_COND}').fetchone()[0]
    if old_cnt != EXPECT_COUNT or old_sum is None or abs(old_sum - EXPECT_SUM) > SUM_TOL:
        die(f'落格前基準漂移：count={old_cnt}（應{EXPECT_COUNT}）sum={old_sum}（應~{EXPECT_SUM}）。', 2)
    print(f'落格前基準：count={old_cnt:,} sum={old_sum!r} ✅ 未漂移')

    # ── 守門：15 筆矛盾 header 的 DB 簽章要對得上裁決①，否則不照裁決盲落 ─────────
    #   驗 eolr 欄值 + 同群 header 共享同一 shoe_key（一致性），不把鞋型名寫進原始碼。
    def check_group(ids, want_eolr, label):
        keys = set()
        for hid in ids:
            row = cur.execute('SELECT eolr, model_name FROM ob_header WHERE id=?', (hid,)).fetchone()
            if row is None:
                die(f'裁決①指名的 header {hid} 不存在於此庫。資料前提不符，停下。', 2)
            eolr, mn = row
            if eolr != want_eolr:
                die(f'header {hid} eolr 欄={eolr}，應={want_eolr}（{label}）。不照裁決盲落。', 2)
            keys.add(shoe_key(mn))
        if len(keys) != 1:
            die(f'{label} 群組 {ids} 的 shoe_key 不一致（{len(keys)} 種）→ 不是同一鞋型群，前提不符。', 2)
    check_group(CONFLICT_G1, 120, 'G1(欄120/標60)')
    check_group(CONFLICT_G2, 60, 'G2(欄60/標120)')
    print(f'守門：15 筆矛盾 header 簽章全部對上裁決①（G1={len(CONFLICT_G1)} @欄120 + G2={len(CONFLICT_G2)} @欄60）✅')

    now = datetime.now().isoformat(timespec='seconds')

    try:
        cur.execute('BEGIN')

        # ① 落格：一工序一列，assigned_eolr = G2→120（覆蓋），其餘＝ob_header.eolr
        placeholders = ','.join('?' * len(OVERRIDE_TO_120))
        cur.execute(f'''
            INSERT INTO ie_process_actual (process_id, eolr, actual_operators, updated_at)
            SELECT p.id,
                   CASE WHEN p.header_id IN ({placeholders}) THEN 120 ELSE h.eolr END,
                   p.actual_operators,
                   ?
            FROM ie_process p
            JOIN ob_header h ON h.id = p.header_id
            WHERE p.{ACTUAL_COND}
        ''', (*sorted(OVERRIDE_TO_120), now))
        landed = cur.execute('SELECT COUNT(*) FROM ie_process_actual').fetchone()[0]
        print(f'落格：ie_process_actual 寫入 {landed:,} 列')

        # ② 現場確認清單：15 筆矛盾 header（以 header_id 記錄，不寫鞋型名）
        conf_rows = []
        for hid in CONFLICT_G1:
            conf_rows.append((hid, 120, 120, 60,
                              '裁決①：eolr欄120為準（標題R2解得60）；現場確認', 'pending', now))
        for hid in CONFLICT_G2:
            conf_rows.append((hid, 120, 60, 120,
                              '裁決①：標題R2解得120為準（覆蓋eolr欄60）；現場確認', 'pending', now))
        cur.executemany('''INSERT INTO ie_eolr_confirm
            (header_id, assigned_eolr, eolr_column, eolr_title, ruling, status, created_at)
            VALUES (?,?,?,?,?,?,?)''', conf_rows)
        nconf = cur.execute('SELECT COUNT(*) FROM ie_eolr_confirm').fetchone()[0]
        print(f'現場確認清單：ie_eolr_confirm 寫入 {nconf} 列（應 15）')

        # ── 零丟值斷言 ──────────────────────────────────────────────────────
        sub_cnt = cur.execute('SELECT COUNT(*) FROM ie_process_actual').fetchone()[0]
        sub_sum = cur.execute('SELECT SUM(actual_operators) FROM ie_process_actual').fetchone()[0]
        distinct_pid = cur.execute('SELECT COUNT(DISTINCT process_id) FROM ie_process_actual').fetchone()[0]
        mism = cur.execute('''SELECT COUNT(*) FROM ie_process_actual a
                              JOIN ie_process p ON p.id = a.process_id
                              WHERE a.actual_operators IS NOT p.actual_operators''').fetchone()[0]
        missing = cur.execute(f'''SELECT COUNT(*) FROM ie_process p
                              WHERE p.{ACTUAL_COND}
                                AND NOT EXISTS (SELECT 1 FROM ie_process_actual a WHERE a.process_id = p.id)
                              ''').fetchone()[0]

        checks = [
            ('A 子表count==舊欄count==16,501', sub_cnt == old_cnt == EXPECT_COUNT, f'{sub_cnt} vs {old_cnt}'),
            ('B 子表sum≈舊欄sum', sub_sum is not None and abs(sub_sum - old_sum) <= SUB_SUM_TOL,
             f'{sub_sum!r} vs {old_sum!r}'),
            ('C 一工序一格 count==distinct(pid)', sub_cnt == distinct_pid, f'{sub_cnt} vs {distinct_pid}'),
            ('D 逐格值相符 mismatch==0', mism == 0, f'mismatch={mism}'),
            ('E 全覆蓋 missing==0', missing == 0, f'missing={missing}'),
            ('confirm==15', nconf == 15, f'{nconf}'),
        ]
        print('\n零丟值斷言：')
        allok = True
        for name, ok, detail in checks:
            print(f'  {"✅" if ok else "❌"} {name} — {detail}')
            allok = allok and ok

        if not allok:
            conn.rollback()
            die('零丟值斷言未過 → 已 ROLLBACK，未寫入。', 2)

        conn.commit()
        print('\n' + '=' * 68)
        print('  ✅ B3 落格完成並提交（零丟值斷言全過）。')
        print(f'  ie_process_actual={sub_cnt:,}　ie_eolr_confirm={nconf}　sum={sub_sum!r}')
        print('=' * 68)

        dist = cur.execute('SELECT eolr, COUNT(*) FROM ie_process_actual GROUP BY eolr ORDER BY eolr').fetchall()
        print('落格 EOLR 分布：', dict(dist))
        return 0

    except sqlite3.IntegrityError as e:
        conn.rollback()
        die(f'IntegrityError（可能同 (process_id,eolr) 碰撞）：{e}', 2)
    except Exception as e:
        conn.rollback()
        die(f'例外 → 已 ROLLBACK：{e}', 2)
    finally:
        conn.close()


if __name__ == '__main__':
    sys.exit(main())
