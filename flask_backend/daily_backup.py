"""
Daily backup script — runs at 2:00 AM, keeps last 30 days.
Register with Windows Task Scheduler:
  schtasks /create /tn "AtlasBackup" /tr "python D:\smartpn-atlas-core\flask_backend\daily_backup.py" /sc DAILY /st 02:00 /f
"""
import os, shutil, sys
from datetime import datetime, timedelta

BASE   = os.path.dirname(os.path.abspath(__file__))
DB     = os.path.join(BASE, 'data', 'atlas.db')
BACKUP = os.path.join(BASE, 'backup')
KEEP   = 30

def run():
    if not os.path.exists(DB):
        print(f'[backup] DB not found: {DB}'); return
    os.makedirs(BACKUP, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d')
    dest  = os.path.join(BACKUP, f'atlas_{stamp}.db')
    shutil.copy2(DB, dest)
    print(f'[backup] {dest}')
    # Delete backups older than KEEP days
    cutoff = datetime.now() - timedelta(days=KEEP)
    for f in os.listdir(BACKUP):
        if not f.startswith('atlas_') or not f.endswith('.db'): continue
        fpath = os.path.join(BACKUP, f)
        mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
        if mtime < cutoff:
            os.remove(fpath)
            print(f'[backup] removed old: {f}')

if __name__ == '__main__':
    run()
