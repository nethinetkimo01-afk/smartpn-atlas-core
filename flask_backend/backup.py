#!/usr/bin/env python3
"""
Atlas Data System - SQLite Backup Utility.
Usage:
    python backup.py
    python backup.py --keep-days=60

Creates a date-stamped backup in flask_backend/backups/.
Default: keeps last 30 days.
"""
import sys, os, shutil
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db

DEFAULT_KEEP_DAYS = 30
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')


def do_backup(keep_days=DEFAULT_KEEP_DAYS):
    if not os.path.exists(db.DB_PATH):
        print(f'Database not found: {db.DB_PATH}')
        print('Run the server first to create the database.')
        return False

    os.makedirs(BACKUP_DIR, exist_ok=True)

    ts          = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'atlas_{ts}.db'
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    shutil.copy2(db.DB_PATH, backup_path)
    size_kb = os.path.getsize(backup_path) / 1024
    print(f'Backup created: {backup_name} ({size_kb:.1f} KB)')

    # Remove old backups beyond retention window
    cutoff = datetime.now() - timedelta(days=keep_days)
    removed = 0
    for fname in os.listdir(BACKUP_DIR):
        if not (fname.startswith('atlas_') and fname.endswith('.db')):
            continue
        fpath = os.path.join(BACKUP_DIR, fname)
        if fpath == backup_path:
            continue
        mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
        if mtime < cutoff:
            os.remove(fpath)
            removed += 1

    if removed:
        print(f'Removed {removed} old backup(s) (older than {keep_days} days)')

    remaining = sorted(f for f in os.listdir(BACKUP_DIR) if f.endswith('.db'))
    print(f'Backups in store: {len(remaining)}')
    return True


if __name__ == '__main__':
    keep_days = DEFAULT_KEEP_DAYS
    for arg in sys.argv[1:]:
        if arg.startswith('--keep-days='):
            try:
                keep_days = int(arg.split('=', 1)[1])
            except ValueError:
                pass

    success = do_backup(keep_days)
    sys.exit(0 if success else 1)
