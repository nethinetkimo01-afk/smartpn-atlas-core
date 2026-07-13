"""
Task F — 裁斷機 standard_time 重算為 ×1.0（方案a）
================================================================
背景：2026-07-12 Jim 定案，裁斷機標準時間公式 3600÷刀÷層×件 取消 ×1.1 係數。
      細表(前端)已即時以 ×1.0 顯示；但 bianche 讀 DB 的 standard_time
      （早期匯入存的是來源 Excel×1.1 基礎值，或為 NULL）→ 兩者不一致。
      本腳本把「公式型裁斷機列」的 DB standard_time 重算為 ×1.0，
      讓 bianche(讀 DB) 與 細表(即時×1.0) 一致。

只重算「公式型裁斷機列」：
    segment='cutting' AND zone='裁斷機'
    AND cut_per_hour>0 AND layers_per_cut>0 AND qty_per_pair>0   ← 三要素齊全才是公式列
    AND (value_type IS NULL OR value_type != 'manual')            ← 手工列一律不動
    AND (flag IS NULL OR flag != 'deleted')

不動：ATOM / EMMA / Laser / YINGHUI / 移印 / 轉印（手工標時區），
      以及裁斷機區內缺三要素的手工列、已標記 manual 的列、已刪除列。

理論人數：系統各處(細表 _calc_theory / bianche zone_theory)皆即時由
      standard_time÷(3600÷eolr) 導出，未獨立存欄；重算 standard_time
      即連動更新理論人數，無需另改欄位。
      （allocation_item.theory_mp 是「撥人快照」另一機制，非本次目標；
        若要同步撥人結果需另跑撥人流程。）

用法（ME129 正式庫請先 --dry-run 看報告，確認後才 --apply）：
    python recalc_cutting_x10.py                 # dry-run，只報告不改
    python recalc_cutting_x10.py --apply         # 先自動備份 → 重算寫入
    python recalc_cutting_x10.py --db <path>     # 指定 DB（預設 ATLAS_DB 或 data/atlas.db）

--apply 會先把整個 DB 檔複製到 backup/ 作為還原點，備份路徑印在報告最後，
        並寫入 test_output/cutting_recalc/ 的變更明細(csv)+摘要(json)。
還原：python rollback_cutting_x10.py --backup <上面印出的備份檔路徑>
"""
import sqlite3, os, sys, shutil, csv, json, argparse
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.environ.get('ATLAS_DB') or os.path.join(HERE, 'data', 'atlas.db')

# 公式型裁斷機列 — 與前端 fmCutA()/_rowStd() 及 bianche zone_theory 定義一致
SCOPE = ("segment='cutting' AND zone='裁斷機' "
         "AND cut_per_hour>0 AND layers_per_cut>0 AND qty_per_pair>0 "
         "AND (value_type IS NULL OR value_type != 'manual') "
         "AND (flag IS NULL OR flag != 'deleted')")


def new_std(lay, qty, cph):
    # 與前端一致：3600 / 刀數 / 層數 × 件數 × 1.0（不四捨五入，存完整浮點）
    return 3600.0 / cph / lay * qty


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=DEFAULT_DB)
    ap.add_argument('--apply', action='store_true', help='實際寫入（預設只 dry-run）')
    ap.add_argument('--backup-dir', default=os.path.join(HERE, 'backup'))
    args = ap.parse_args()

    if not os.path.exists(args.db):
        print(f'[ERR] DB 不存在: {args.db}'); sys.exit(1)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    print('=' * 64)
    print(f'Task F — 裁斷機 standard_time ×1.0 重算')
    print(f'DB      : {args.db}')
    print(f'模式    : {"APPLY(寫入)" if args.apply else "DRY-RUN(只報告)"}')
    print(f'時間    : {ts}')
    print('=' * 64)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f'SELECT id, header_id, art, layers_per_cut, qty_per_pair, cut_per_hour, '
        f'standard_time FROM ie_process WHERE {SCOPE} ORDER BY id').fetchall()

    total = len(rows)
    changes = []   # (id, art, lay, qty, cph, old, new)
    for r in rows:
        nv = new_std(r['layers_per_cut'], r['qty_per_pair'], r['cut_per_hour'])
        old = r['standard_time']
        if old is None or abs(old - nv) > 1e-9:
            changes.append((r['id'], r['art'], r['layers_per_cut'], r['qty_per_pair'],
                            r['cut_per_hour'], old, nv))

    print(f'公式型裁斷機列(在範圍內)   : {total}')
    print(f'需變更(old NULL 或 ≠ ×1.0) : {len(changes)}')
    print()
    print('抽樣(最多 10 筆) old → new：')
    print(f'  {"id":>7} {"art":<12} {"層":>4} {"件":>4} {"刀":>6}   {"old":>14}   {"new(×1.0)":>14}')
    for cid, art, lay, qty, cph, old, nv in changes[:10]:
        os_ = 'NULL' if old is None else f'{old:.6f}'
        print(f'  {cid:>7} {str(art):<12} {lay:>4g} {qty:>4g} {cph:>6g}   {os_:>14}   {nv:>14.6f}')
    if not changes:
        print('  （無需變更 — 本 DB 的公式列已是 ×1.0，或無公式型裁斷機資料）')

    # 明細輸出
    out_dir = os.path.join(HERE, 'test_output', 'cutting_recalc')
    os.makedirs(out_dir, exist_ok=True)
    log_csv = os.path.join(out_dir, f'recalc_log_{ts}.csv')
    with open(log_csv, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['id', 'art', 'layers', 'qty', 'cut_per_hour', 'old_std', 'new_std_x10'])
        for row in changes:
            cid, art, lay, qty, cph, old, nv = row
            w.writerow([cid, art, lay, qty, cph, '' if old is None else old, nv])

    backup_path = None
    if args.apply and changes:
        os.makedirs(args.backup_dir, exist_ok=True)
        backup_path = os.path.join(args.backup_dir, f'atlas_precutrecalc_{ts}.db')
        conn.close()
        shutil.copy(args.db, backup_path)        # 還原點：整庫備份
        conn = sqlite3.connect(args.db)
        for cid, art, lay, qty, cph, old, nv in changes:
            conn.execute('UPDATE ie_process SET standard_time=? WHERE id=?', (nv, cid))
        conn.commit()
        print()
        print(f'[APPLY] 已更新 {len(changes)} 列。')
        print(f'[BACKUP] 還原點: {backup_path}')
    elif args.apply and not changes:
        print()
        print('[APPLY] 無需變更，未寫入、未備份。')

    summary = {
        'task': 'F-recalc-cutting-x10', 'ts': ts, 'db': args.db,
        'mode': 'apply' if args.apply else 'dry-run',
        'in_scope_rows': total, 'changed_rows': len(changes),
        'backup': backup_path, 'log_csv': log_csv,
        'formula': '3600 / cut_per_hour / layers_per_cut * qty_per_pair * 1.0',
        'scope_sql': SCOPE,
    }
    with open(os.path.join(out_dir, f'recalc_summary_{ts}.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    conn.close()
    print()
    print(f'變更明細 CSV : {log_csv}')
    print('提醒：ME129 正式庫實際受影響筆數以 ME129 上跑 --dry-run 的結果為準。')


if __name__ == '__main__':
    main()
