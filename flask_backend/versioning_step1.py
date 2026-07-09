"""
版本控制 Step 1 — 資料分版 backfill（一次性，可重複執行 idempotent）

做的事：
  1. 備份 DB（pre_step1_<timestamp>.db）
  2. ie_process 加 stage_id 欄位（若無）
  3. ie_stage 加 is_approved 欄位（若無）
  4. 每個「在 ie_process 有工序的 header」：
       - 若該 header 尚無 ie_stage → 建一個「初版」
       - 把該 header 所有 stage_id 為 NULL 的 ie_process rows 指到該 header 最早的 stage
       - ie_process_group 同步回填 stage_id
  5. 印出驗證：總 rows 前後一致、每個 header 恰好一個 stage、無 NULL stage_id

嚴禁弄丟現有工序資料：只做 ADD COLUMN / UPDATE stage_id（NULL→v1）/ INSERT ie_stage，
不 DELETE、不改任何工時數值。

用法：python flask_backend/versioning_step1.py
"""
import os, shutil, sqlite3, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
DB   = os.environ.get('ATLAS_DB') or os.path.join(BASE, 'data', 'atlas.db')
BACKUP_DIR = os.path.join(BASE, 'backup')


def _col_exists(conn, table, col):
    return col in [r[1] for r in conn.execute(f'PRAGMA table_info({table})')]


def ensure_columns(conn):
    """ADD COLUMN 只做一次，idempotent。"""
    if not _col_exists(conn, 'ie_process', 'stage_id'):
        conn.execute('ALTER TABLE ie_process ADD COLUMN stage_id INTEGER')
        print('[step1] + ie_process.stage_id')
    else:
        print('[step1] ie_process.stage_id 已存在')
    if not _col_exists(conn, 'ie_stage', 'is_approved'):
        conn.execute('ALTER TABLE ie_stage ADD COLUMN is_approved INTEGER DEFAULT 0')
        print('[step1] + ie_stage.is_approved')
    else:
        print('[step1] ie_stage.is_approved 已存在')
    conn.commit()


def backfill_v1(conn):
    """每個有工序的 header 綁一個初始版本，NULL stage_id → 該版本。"""
    headers = [r[0] for r in conn.execute(
        'SELECT DISTINCT header_id FROM ie_process ORDER BY header_id')]
    print(f'[step1] {len(headers)} 個 header 有工序，開始回填…')
    created, linked = 0, 0
    for hid in headers:
        # 該 header 最早的 stage；沒有就建「初版」
        srow = conn.execute(
            'SELECT id FROM ie_stage WHERE header_id=? ORDER BY id ASC LIMIT 1', (hid,)
        ).fetchone()
        if srow:
            sid = srow[0]
        else:
            conn.execute(
                "INSERT INTO ie_stage (header_id, stage_name, is_approved) VALUES (?, '初版', 0)",
                (hid,))
            sid = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
            created += 1
        # 只回填 NULL 的（已綁的不動）
        cur = conn.execute(
            'UPDATE ie_process SET stage_id=? WHERE header_id=? AND stage_id IS NULL',
            (sid, hid))
        linked += cur.rowcount
        conn.execute(
            'UPDATE ie_process_group SET stage_id=? '
            'WHERE header_id=? AND (stage_id IS NULL OR stage_id=0)',
            (sid, hid))
    conn.commit()
    print(f'[step1] 新建 {created} 個初版 stage，回填 {linked} 筆工序 stage_id')


def verify(conn, before_total):
    after_total = conn.execute('SELECT COUNT(*) FROM ie_process').fetchone()[0]
    null_stage  = conn.execute(
        'SELECT COUNT(*) FROM ie_process WHERE stage_id IS NULL').fetchone()[0]
    multi = conn.execute('''
        SELECT header_id, COUNT(*) c FROM ie_stage GROUP BY header_id HAVING c > 1
    ''').fetchall()
    headers_with_proc = conn.execute(
        'SELECT COUNT(DISTINCT header_id) FROM ie_process').fetchone()[0]
    stages_total = conn.execute('SELECT COUNT(*) FROM ie_stage').fetchone()[0]
    print('\n=== 驗證 ===')
    print(f'  ie_process 總數 前={before_total}  後={after_total}  '
          f'{"OK 一致" if before_total == after_total else "!!! 不一致 !!!"}')
    print(f'  stage_id 仍為 NULL 的工序: {null_stage}  {"OK" if null_stage == 0 else "!!! 有漏 !!!"}')
    print(f'  有工序的 header 數: {headers_with_proc}')
    print(f'  ie_stage 總數: {stages_total}')
    print(f'  一個 header 多 stage 的（本步驟後應為 0）: {len(multi)} {multi[:5]}')
    ok = (before_total == after_total) and (null_stage == 0)
    print('=== 結果:', 'PASS' if ok else 'FAIL', '===')
    return ok


def run():
    if not os.path.exists(DB):
        print('[step1] DB not found:', DB); sys.exit(1)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = time.strftime('%Y%m%d_%H%M%S')
    dest = os.path.join(BACKUP_DIR, f'pre_step1_{stamp}.db')
    shutil.copy2(DB, dest)
    print('[step1] 備份:', dest)

    conn = sqlite3.connect(DB)
    conn.execute('PRAGMA foreign_keys = OFF')
    before_total = conn.execute('SELECT COUNT(*) FROM ie_process').fetchone()[0]
    ensure_columns(conn)
    backfill_v1(conn)
    ok = verify(conn, before_total)
    conn.close()
    sys.exit(0 if ok else 2)


if __name__ == '__main__':
    run()
