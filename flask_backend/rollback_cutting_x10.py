"""
Task F 還原 — 把 recalc_cutting_x10.py --apply 的變更還原
================================================================
recalc_cutting_x10.py --apply 會在 backup/ 產生一個整庫備份
（atlas_precutrecalc_<時間>.db）。本腳本用該備份把 DB 還原回重算前狀態。

用法：
    python rollback_cutting_x10.py --backup backup/atlas_precutrecalc_YYYYMMDD_HHMMSS.db
    python rollback_cutting_x10.py --list        # 列出可用的備份還原點
    python rollback_cutting_x10.py               # 自動選最新的還原點（會再次確認印出）

--db 指定要還原的目標 DB（預設 ATLAS_DB 或 data/atlas.db）。
還原前會先把「目前的 DB」另存一份 atlas_prerollback_<時間>.db，避免誤操作無法回頭。
"""
import os, sys, shutil, argparse, glob
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.environ.get('ATLAS_DB') or os.path.join(HERE, 'data', 'atlas.db')
BACKUP_DIR = os.path.join(HERE, 'backup')


def list_backups():
    pat = os.path.join(BACKUP_DIR, 'atlas_precutrecalc_*.db')
    return sorted(glob.glob(pat))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', default=DEFAULT_DB)
    ap.add_argument('--backup', default=None, help='要還原的備份檔；不給則用最新')
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args()

    backups = list_backups()
    if args.list:
        print('可用還原點：')
        for b in backups:
            print('  ', b)
        if not backups:
            print('   （無）')
        return

    src = args.backup or (backups[-1] if backups else None)
    if not src:
        print('[ERR] 找不到還原點；請先跑 recalc_cutting_x10.py --apply，或用 --backup 指定。')
        sys.exit(1)
    if not os.path.exists(src):
        print(f'[ERR] 備份檔不存在: {src}'); sys.exit(1)

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    # 還原前先保護目前 DB
    if os.path.exists(args.db):
        guard = os.path.join(BACKUP_DIR, f'atlas_prerollback_{ts}.db')
        os.makedirs(BACKUP_DIR, exist_ok=True)
        shutil.copy(args.db, guard)
        print(f'[SAFETY] 已保存目前 DB → {guard}')

    shutil.copy(src, args.db)
    print(f'[ROLLBACK] 已用 {src} 還原 → {args.db}')
    print('完成。')


if __name__ == '__main__':
    main()
