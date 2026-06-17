"""Called by pre_update.bat — creates a timestamped backup before git pull."""
import os, shutil
from datetime import datetime

BASE   = os.path.dirname(os.path.abspath(__file__))
DB     = os.path.join(BASE, 'data', 'atlas.db')
BACKUP = os.path.join(BASE, 'backup')

if not os.path.exists(DB):
    print(f'[pre_update_backup] DB not found: {DB}')
    raise SystemExit(0)

os.makedirs(BACKUP, exist_ok=True)
stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
dest  = os.path.join(BACKUP, f'pre_update_{stamp}.db')
shutil.copy2(DB, dest)
print(f'[pre_update_backup] Saved: {dest}')
