"""
Restore atlas.db from a backup file.
Usage:
  python flask_backend/restore.py --date 20260616
  python flask_backend/restore.py --file flask_backend/backup/pre_update_20260617_140000.db
"""
import argparse, os, shutil
from datetime import datetime

BASE   = os.path.dirname(os.path.abspath(__file__))
DB     = os.path.join(BASE, 'data', 'atlas.db')
BACKUP = os.path.join(BASE, 'backup')

def main():
    parser = argparse.ArgumentParser(description='Restore atlas.db from backup')
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument('--date', help='Date in YYYYMMDD format, e.g. 20260616')
    g.add_argument('--file', help='Exact backup file path')
    args = parser.parse_args()

    if args.date:
        src = os.path.join(BACKUP, f'atlas_{args.date}.db')
    else:
        src = args.file

    if not os.path.exists(src):
        print(f'[restore] ERROR: backup not found: {src}')
        available = [f for f in os.listdir(BACKUP) if f.endswith('.db')]
        if available:
            print('[restore] Available backups:')
            for f in sorted(available):
                print(f'  {f}')
        return

    # Safety: backup current DB before restoring
    if os.path.exists(DB):
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safety = os.path.join(BACKUP, f'pre_restore_{stamp}.db')
        shutil.copy2(DB, safety)
        print(f'[restore] Current DB saved to: {safety}')

    shutil.copy2(src, DB)
    print(f'[restore] Restored from: {src}')
    print(f'[restore] Target: {DB}')
    print('[restore] Done. Restart Flask to apply.')

if __name__ == '__main__':
    main()
