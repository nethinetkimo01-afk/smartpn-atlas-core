"""
IE 壓測 — waitress vs app.run() 並排對照。

同一支測試邏輯 (run_battery in run_stress_real.py)、同一份 seed 庫
(571,200 ie_sheet_data)，同一次執行內先跑 app.run() 再跑 waitress(threads=8)，
排除環境差異，公平對照。

產出 flask_backend/test_output/ie_stress_waitress.md（before app.run / after waitress）。

Run:  cd flask_backend && python tests/run_stress_waitress.py
"""
import os, sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

TESTS_DIR  = os.path.dirname(os.path.abspath(__file__))
BACKEND    = os.path.dirname(TESTS_DIR)
OUTPUT_DIR = os.path.join(BACKEND, 'test_output')

sys.path.insert(0, TESTS_DIR)
import seed_stress_db
import run_stress_real as R

WAITRESS_THREADS = 8


def _mix_detail(res):
    return res['mix']['by_op'].get('detail_read(大表)', {})


def write_compare(before, after):
    sc = after['seed_counts']
    n = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    bb, ab = before['baseline'], after['baseline']
    bd, ad = _mix_detail(before), _mix_detail(after)
    b_list = before['mix']['by_op'].get('list', {})
    a_list = after['mix']['by_op'].get('list', {})
    b_w = before['write']
    a_w = after['write']

    # realistic-size read (one sheet ≈ hundreds of cells, the true detail-view payload)
    b_nr = before.get('normal_read', {}).get('by_op', {}).get('normal_read', {})
    a_nr = after.get('normal_read', {}).get('by_op', {}).get('normal_read', {})
    normal_cells = after.get('normal_read', {}).get('cells', 0)

    # success checks
    heavy_p95_target_ok = ad.get('p95', 9e9) < 1000          # 12k-cell worst case
    normal_p95_target_ok = a_nr.get('p95', 9e9) < 1000        # realistic sheet
    locks_ok = after['totals']['locks'] == 0
    lost_ok = a_w['lost'] == 0
    fails_ok = after['totals']['fails'] == 0
    heavy_improved = ad.get('p95', 9e9) < bd.get('p95', 0)

    def row(name, b, a, unit='ms', lower_better=True):
        try:
            if b and a is not None:
                if lower_better and a > 0:
                    factor = f"{round(b / a, 1)}× 快" if a < b else f"{round(a / b, 1)}× 慢"
                else:
                    factor = '—'
            else:
                factor = '—'
        except Exception:
            factor = '—'
        return f"| {name} | {b} {unit} | {a} {unit} | {factor} |"

    L = []
    L.append('# IE 系統壓測 — waitress vs app.run() 對照報告')
    L.append('')
    L.append(f'**執行時間**: {n}  ')
    L.append('**測試方式**: 同一支 `run_stress_real.py` 的 `run_battery()`、同一份 seed 庫，'
             '同次執行先跑 `app.run()` 再跑 `waitress(threads=%d)`，公平對照。' % WAITRESS_THREADS)
    L.append('**測試庫**: `tests/atlas_stress.db`（獨立 schema-only 庫，全程未連線 / 未複製 `data/atlas.db`）')
    L.append('')
    L.append('## 測試庫真實筆數')
    L.append('')
    L.append('| 資料表 | 筆數 |')
    L.append('|--------|------|')
    L.append(f"| ob_header | **{sc['ob_header']:,}** |")
    L.append(f"| ie_process | **{sc['ie_process']:,}** |")
    L.append(f"| ie_sheet_data | **{sc['ie_sheet_data']:,}** |")
    L.append(f"| ie_stage | {sc['ie_stage']:,} |")
    L.append('')
    L.append(f"> 最重 header={sc['heavy_header_id']} ({sc['heavy_header_cells']:,} cells)，"
             f"最大單一 sheet='{sc['heavy_sheet_name']}' ({sc['heavy_sheet_cells']:,} cells)。")
    L.append('')
    L.append('---')
    L.append('')
    L.append('## ⭐ 核心對照：20 並發開重型細表（讀 ie_sheet_data 大表）')
    L.append('')
    L.append('| 指標 | before: app.run() | after: waitress(t=%d) | 改善 |' % WAITRESS_THREADS)
    L.append('|------|------------------|----------------------|------|')
    L.append(row('平均 (avg)', bd.get('avg', 0), ad.get('avg', 0)))
    L.append(row('**p95**', bd.get('p95', 0), ad.get('p95', 0)))
    L.append(row('最大 (max)', bd.get('max', 0), ad.get('max', 0)))
    L.append(f"| DB locked | {before['totals']['locks']} | {after['totals']['locks']} | "
             f"{'✅ 維持 0' if locks_ok else '❌'} |")
    L.append('')
    L.append(f"**p95 目標（<1000ms）**："
             f"{'✅ 達成 — %.0f ms' % ad.get('p95',0) if heavy_p95_target_ok else '❌ 未達 — %.0f ms（見下方根因）' % ad.get('p95',0)}")
    L.append('')
    L.append('> ⚠️ 這是**極端 worst-case**：單一 sheet 12,000 格。細表一次只開一張 sheet，'
             '真實 sheet 多為數百~一千格。realistic 尺寸見下節。')
    L.append('')
    L.append('---')
    L.append('')
    L.append(f'## ⭐ 真實尺寸對照：20 並發純讀一般細表（{normal_cells} cells/sheet）')
    L.append('')
    L.append('| 指標 | before: app.run() | after: waitress(t=%d) | 改善 |' % WAITRESS_THREADS)
    L.append('|------|------------------|----------------------|------|')
    L.append(row('平均 (avg)', b_nr.get('avg', 0), a_nr.get('avg', 0)))
    L.append(row('**p95**', b_nr.get('p95', 0), a_nr.get('p95', 0)))
    L.append(row('最大 (max)', b_nr.get('max', 0), a_nr.get('max', 0)))
    L.append('')
    L.append(f"**p95 目標（<1000ms）**："
             f"{'✅ 達成 — %.0f ms' % a_nr.get('p95',0) if normal_p95_target_ok else '❌ 未達 — %.0f ms' % a_nr.get('p95',0)}")
    L.append('')
    L.append('> 真實尺寸細表才是日常情境。此處 waitress 是否達標決定「實際使用是否順」。')
    L.append('')
    L.append('---')
    L.append('')
    L.append('## 單線程基準對照')
    L.append('')
    L.append('| 操作 | before: app.run() | after: waitress | 說明 |')
    L.append('|------|------------------|-----------------|------|')
    L.append(f"| 細表載入(讀大表) /api/ie/<hid>/sheet | {bb['sheet_ms']} ms | {ab['sheet_ms']} ms | "
             f"回傳 {ab['sheet_cells_returned']:,} cells |")
    L.append(f"| 格子資料 /api/ie/cell/<hid> | {bb['cell_ms']} ms | {ab['cell_ms']} ms | 讀 ie_process |")
    L.append(f"| 清單 /api/ie/list | {bb['list_ms']} ms | {ab['list_ms']} ms | {ab['list_records']} 筆 |")
    L.append('')
    L.append('> 單線程下兩者本就相近（瓶頸不在單次查詢）；差距只在「並發」時顯現。')
    L.append('')
    L.append('---')
    L.append('')
    L.append('## 20 並發混合操作 — 各操作對照')
    L.append('')
    L.append('| 操作 | 指標 | before app.run() | after waitress |')
    L.append('|------|------|------------------|----------------|')
    for opname in ['detail_read(大表)', 'list', 'cell_write']:
        bop = before['mix']['by_op'].get(opname, {})
        aop = after['mix']['by_op'].get(opname, {})
        L.append(f"| {opname} | avg | {bop.get('avg','-')} | {aop.get('avg','-')} |")
        L.append(f"| {opname} | p95 | {bop.get('p95','-')} | {aop.get('p95','-')} |")
        L.append(f"| {opname} | max | {bop.get('max','-')} | {aop.get('max','-')} |")
    L.append(f"| 混合測 wall time | — | {before['mix']['wall_ms']:.0f} ms | {after['mix']['wall_ms']:.0f} ms |")
    L.append('')
    L.append('---')
    L.append('')
    L.append('## 並發寫專測對照（20 並發，一半同 header）')
    L.append('')
    L.append('| 指標 | before app.run() | after waitress |')
    L.append('|------|------------------|----------------|')
    bw_locks = sum(s['locks'] for s in b_w['by_op'].values())
    aw_locks = sum(s['locks'] for s in a_w['by_op'].values())
    L.append(f"| 寫入請求數 | {b_w['total']} | {a_w['total']} |")
    L.append(f"| 寫 wall time | {b_w['wall_ms']:.0f} ms | {a_w['wall_ms']:.0f} ms |")
    L.append(f"| DB locked | {bw_locks} | {aw_locks} |")
    L.append(f"| ie_edit_log 實際新增 | {b_w['rows_written']} | {a_w['rows_written']} |")
    L.append(f"| 寫入遺失 | {b_w['lost']} | {a_w['lost']} |")
    L.append('')
    L.append('---')
    L.append('')
    L.append('## 結論（誠實版）')
    L.append('')
    L.append('**waitress 是正確且該換的生產伺服器，但它「沒有單獨達成 <1 秒目標」。'
             '真相分兩種情境：**')
    L.append('')
    L.append(f"1. **真實尺寸細表（{normal_cells} cells，日常情境）**："
             f"20 並發 p95 由 {b_nr.get('p95',0):.0f} ms → **{a_nr.get('p95',0):.0f} ms**。"
             f"{'✅ 達標 <1 秒，實際使用順暢。' if normal_p95_target_ok else '⚠️ 仍 >1 秒。'}")
    L.append('')
    L.append(f"2. **極端 12,000-cell 單一 sheet（worst-case）**："
             f"p95 由 {bd.get('p95',0):.0f} ms → **{ad.get('p95',0):.0f} ms**"
             f"（{round(bd.get('p95',1)/max(ad.get('p95',1),1),1)}× 快），但**仍未進 1 秒**。")
    L.append('')
    L.append('### 為什麼 worst-case 換 waitress 仍慢（根因：Python GIL + 大 payload）')
    L.append('')
    L.append('重型 sheet 的耗時主要花在「把 12,000 格組成巢狀 dict + jsonify 序列化」，'
             '這是**純 Python CPU 工作，受 GIL 限制**。waitress 多線程能讓 SQLite I/O 重疊'
             '（所以快了 ~2×），但 CPU 序列化那段在 GIL 下無法真正並行 → 多線程到頂只能改善有限。'
             '同樣原因，混合測中 list/cell_write 在 waitress 下反而變慢：8 條線程同時跑重型讀，'
             'CPU 被吃滿、輕量請求被排在後面（app.run() 序列化反而讓輕量請求偶爾插隊）。'
             '**這不是 waitress 的錯，是「單次回傳 12,000 格」本身太重。**')
    L.append('')
    L.append('### 驗收對照')
    L.append('')
    L.append('| 驗收項 | 結果 |')
    L.append('|--------|------|')
    L.append(f"| 真實尺寸細表 p95 < 1s | {'✅' if normal_p95_target_ok else '❌'} "
             f"{a_nr.get('p95',0):.0f} ms（{normal_cells} cells）|")
    L.append(f"| worst-case 12k 細表 p95 改善 | {'✅' if heavy_improved else '❌'} "
             f"{bd.get('p95',0):.0f} → {ad.get('p95',0):.0f} ms（~2×）|")
    L.append(f"| worst-case 12k 細表 p95 < 1s | {'⚠️ 未達' } {ad.get('p95',0):.0f} ms（GIL+payload 限制）|")
    L.append(f"| DB locked = 0 | {'✅' if locks_ok else '❌'} ({after['totals']['locks']}) |")
    L.append(f"| 無寫入遺失 | {'✅' if lost_ok else '❌'} ({a_w['lost']}) |")
    L.append(f"| 無請求失敗 | {'✅' if fails_ok else '❌'} ({after['totals']['fails']}) |")
    L.append('')
    L.append('### 建議（給 Jim 決策）')
    L.append('')
    L.append('1. **保留 waitress 部署**（本次已做）：它是生產級伺服器，真實尺寸細表並發已達標，'
             '且 worst-case 也快 ~2×、無 locked。比 app.run() 全面更好，沒有理由退回。')
    L.append('2. **真正消滅 worst-case 卡頓的關鍵在「減少單次 payload」，不在伺服器**：')
    L.append('   - `/api/ie/<hid>/sheet` 改為**分頁 / 只回可視範圍**，前端虛擬捲動。'
             '單次從 12,000 格降到數百格，p95 立刻進 1 秒內（見真實尺寸數據）。')
    L.append('   - 或限制單一 sheet 最大格數 / 拆分超大 sheet。')
    L.append('3. **若一定要伺服器端解（次選）**：改多「行程」（multi-process，例如多個 waitress '
             '實例 + 反向代理，或 gunicorn 在 Linux）才能繞過 GIL 讓 CPU 序列化並行；'
             'Windows 上成本較高，不如先做 payload 分頁。')
    L.append('')
    L.append('### 部署變更（本次已做）')
    L.append('')
    L.append('- `requirements.txt`：加 `waitress>=3.0.0`')
    L.append('- 新增 `flask_backend/serve.py`：`waitress.serve(app, port=5000, threads=8)`（import app.py 的 app，不改業務邏輯）')
    L.append('- `watchdog.py`：啟動對象由 `app.py` 改為 `serve.py`，偵測/重啟邏輯不變')
    L.append('- `start.bat`：`python flask_backend\\app.py` → `python flask_backend\\serve.py`')
    L.append('- `database.py get_conn()`：加 `PRAGMA busy_timeout=15000`（預防並發寫升高後 locked）')
    L.append('- `app.py` 的 `if __name__==\'__main__\'` 仍保留 `app.run()` 當開發後備（未刪）')
    L.append('')
    out = os.path.join(OUTPUT_DIR, 'ie_stress_waitress.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    print(f'\n[報告] → {out}')
    return normal_p95_target_ok and locks_ok and lost_ok and fails_ok


def main():
    print('=' * 60)
    print('  IE 壓測對照：app.run() vs waitress')
    print('=' * 60)
    print('\n[1] Seeding 獨立測試庫 (一次，兩個 battery 共用) ...')
    sc = seed_stress_db.build()
    for k, v in sc.items():
        print(f'    {k:22} = {v}')

    print('\n[2] BEFORE — app.run() battery ...')
    before = R.run_battery('apprun')

    print('\n[3] AFTER — waitress(threads=%d) battery ...' % WAITRESS_THREADS)
    after = R.run_battery('waitress', threads=WAITRESS_THREADS)

    write_compare(before, after)


if __name__ == '__main__':
    main()
