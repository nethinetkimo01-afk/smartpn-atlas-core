"""Migration: add ob_header.lean + populate from Jun/IE folder structure."""
import sqlite3, os, re, glob, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('flask_backend/data/atlas.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Add lean column to ob_header
try:
    cur.execute('ALTER TABLE ob_header ADD COLUMN lean TEXT')
    print('+ ob_header.lean column added')
except Exception:
    print('~ ob_header.lean already exists')
conn.commit()

# 2. Scan Jun/IE folder to populate lean from subfolder names
IE_FOLDER = r"C:\Users\user\OneDrive\Desktop\Biên chế\Jun\IE"
ART_RE = re.compile(r'[A-Z]{2}\d{4,6}')

updated = 0
no_art_files = 0
art_not_in_db = 0
already_set = 0

for entry in sorted(os.listdir(IE_FOLDER)):
    lean_path = os.path.join(IE_FOLDER, entry)
    if not os.path.isdir(lean_path):
        continue
    lean_code = entry  # e.g. '1A', '1B', '2A'

    files = glob.glob(os.path.join(lean_path, '*.xlsx'))
    for fpath in files:
        bn = os.path.basename(fpath)
        if bn.startswith('~$'):
            continue
        arts = ART_RE.findall(bn)
        if not arts:
            no_art_files += 1
            continue

        for art in arts:
            # fetchall: handles multiple headers sharing the same ART (e.g. 120双 vs 60双 versions)
            rows_h = cur.execute(
                'SELECT h.id, h.lean FROM ob_header h '
                'JOIN ob_articles a ON a.header_id=h.id WHERE a.art=?',
                (art,)
            ).fetchall()
            if not rows_h:
                art_not_in_db += 1
                continue
            for row in rows_h:
                if row['lean'] and row['lean'] != lean_code:
                    already_set += 1
                    continue
                cur.execute('UPDATE ob_header SET lean=? WHERE id=?', (lean_code, row['id']))
                if cur.rowcount:
                    updated += 1

conn.commit()

print(f'Headers updated with lean: {updated}')
print(f'Files with no ART in name: {no_art_files}')
print(f'ARTs not in DB: {art_not_in_db}')
print(f'Already had different lean: {already_set}')
print()

# 3. Report result
rows = cur.execute(
    'SELECT lean, COUNT(*) as n FROM ob_header WHERE lean IS NOT NULL GROUP BY lean ORDER BY lean'
).fetchall()
print('ob_header lean distribution:')
for r in rows:
    print(f'  {r["lean"]:6s}  {r["n"]} headers')

no_lean = cur.execute('SELECT COUNT(*) FROM ob_header WHERE lean IS NULL').fetchone()[0]
print(f'  (NULL)  {no_lean} headers (no IE file found for these)')

conn.close()
print('\nDone. Next: run prefill to repopulate allocation_item with lean values.')
