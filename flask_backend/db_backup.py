# -*- coding: utf-8 -*-
"""
db_backup.py — atlas.db 自動備份 / 驗證 / 還原（Task BACKUP，防資料全損）。

★為什麼用 SQLite online backup API 而不是 shutil.copy2：
  ME129 上 atlas.db 是「線上資料庫」——Flask server 隨時可能正在寫入，且 journal_mode=wal。
  對線上 DB 直接 shutil.copy2 會複製到「撕裂(torn)」的檔案：主檔複製到一半時另一端已寫入新頁，
  且 -wal 裡未 checkpoint 的交易不會被一起複製 → 備份看似成功、實際打不開或缺最新資料。
  sqlite3 的 backup API 走 SQLite 自己的讀鎖，保證取到一致性快照（含 WAL 內容），
  這正是 hub_ci.clone_prod_db() 已在用的方式（實測：來源/copy2/backup API 三方資料完全一致）。
  → 備份一律用 backup API；copy2 只在「已確認無人寫入」的離線情境才安全。

用法：
  python db_backup.py backup              建立一份備份（含驗證＋輪替）
  python db_backup.py list                列出現有備份
  python db_backup.py verify <path>       驗證某份備份
  python db_backup.py restore <path>      還原（還原前自動先備份當前）
"""
import os
import sys
import io
import glob
import shutil
import sqlite3
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get('ATLAS_DB', os.path.join(HERE, 'data', 'atlas.db'))
BACKUP_DIR = os.environ.get('ATLAS_BACKUP_DIR', os.path.join(HERE, 'data', 'auto_backup'))
# 異地備份點：優先讀「管理頁設定」(app_settings)，其次環境變數。未設＝只做本機備份。
OFFSITE_DIR = os.environ.get('ATLAS_BACKUP_OFFSITE', '')
KEEP_DAYS = int(os.environ.get('ATLAS_BACKUP_KEEP_DAYS', '30'))

# 設定鍵（管理頁「備份設定」寫入 app_settings；全程畫面操作，不碰命令列）
K_OFFSITE = 'backup.offsite_dir'
K_FREQ = 'backup.frequency'      # 'daily' | 'every12h'
K_KEEP = 'backup.keep_days'
FREQ_HOURS = {'daily': 24, 'every12h': 12}


def settings():
    """讀管理頁設定，讀不到就退回環境變數/預設值。
    DB 讀不到不能讓備份整條掛掉 → 一律有可用預設。"""
    off, freq, keep = OFFSITE_DIR, 'daily', KEEP_DAYS
    try:
        import database as _db
        off = _db.get_setting(K_OFFSITE, OFFSITE_DIR) or ''
        freq = _db.get_setting(K_FREQ, 'daily') or 'daily'
        keep = int(_db.get_setting(K_KEEP, KEEP_DAYS) or KEEP_DAYS)
    except Exception:
        pass
    if freq not in FREQ_HOURS:
        freq = 'daily'
    return {'offsite_dir': off, 'frequency': freq, 'keep_days': keep,
            'stale_hours': FREQ_HOURS[freq] + 2}   # 寬限 2h 才告警，避免排程剛好慢幾分鐘就紅

# 驗證用：這些表的列數必須與來源完全相同，任一不符即判定壞備份
VERIFY_TABLES = ['ie_process', 'ob_header', 'ie_sheet_data', 'ie_stage',
                 'allocation_item', 'ds04_orders', 'ob_articles']


def _counts(path):
    """開啟 DB（唯讀）回傳各表列數；順帶跑 integrity_check。"""
    uri = 'file:' + path.replace('\\', '/').replace('?', '%3f').replace('#', '%23') + '?mode=ro'
    conn = sqlite3.connect(uri, uri=True)
    try:
        out = {}
        have = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        for t in VERIFY_TABLES:
            out[t] = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] if t in have else None
        integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
        return out, integrity
    finally:
        conn.close()


def backup(src=DB, dst_dir=BACKUP_DIR, offsite=None, keep_days=None):
    """建立一致性快照 → 驗證 → 異地複製 → 輪替。回傳 dict 供管理頁顯示。
    offsite/keep_days 預設讀管理頁設定（None＝去讀設定，不是「不做異地」）。"""
    cfg = settings()
    if offsite is None:
        offsite = cfg['offsite_dir']
    if keep_days is None:
        keep_days = cfg['keep_days']
    if not os.path.isfile(src):
        raise FileNotFoundError(f'找不到來源資料庫：{src}')
    os.makedirs(dst_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(dst_dir, f'atlas_{ts}.db')

    # 一致性快照（backup API；來源全程唯讀，不寫正式庫）
    uri = 'file:' + src.replace('\\', '/').replace('?', '%3f').replace('#', '%23') + '?mode=ro'
    s = sqlite3.connect(uri, uri=True)
    d = sqlite3.connect(dst)
    try:
        with d:
            s.backup(d)
    finally:
        s.close()
        d.close()

    ok, detail = verify(src, dst)
    if not ok:
        bad = dst + '.BAD'
        os.replace(dst, bad)
        raise RuntimeError(f'❌ 備份驗證失敗，已標記為 {os.path.basename(bad)}：{detail}')

    off_status = _copy_offsite(dst, offsite)
    pruned = prune(dst_dir, keep_days)
    return {'ok': True, 'path': dst, 'size': os.path.getsize(dst),
            'at': ts, 'detail': detail, 'offsite': off_status, 'pruned': pruned}


def verify(src, dst):
    """斷言副本各表列數 == 來源，且副本 integrity_check=ok。不符即壞備份。"""
    if not os.path.isfile(dst):
        return False, '副本不存在'
    try:
        sc, _ = _counts(src)
        dc, integrity = _counts(dst)
    except sqlite3.DatabaseError as e:
        return False, f'副本無法開啟（可能是撕裂的複製）：{e}'
    if integrity != 'ok':
        return False, f'副本 integrity_check={integrity}'
    diffs = [f'{t}: 來源{sc[t]} != 副本{dc[t]}' for t in sc if sc[t] != dc[t]]
    if diffs:
        return False, '列數不符 → ' + '; '.join(diffs)
    return True, ' '.join(f'{t}={sc[t]}' for t in sc if sc[t] is not None)


def _copy_offsite(path, offsite):
    """異地副本：單機壞了還有一份。未設 OFFSITE_DIR 就明講沒做，不假裝有。"""
    if not offsite:
        return '未設定（ATLAS_BACKUP_OFFSITE 未給 → 目前只有本機備份，單機壞掉仍會全損）'
    try:
        os.makedirs(offsite, exist_ok=True)
        far = os.path.join(offsite, os.path.basename(path))
        shutil.copy2(path, far)   # 此時來源是已驗證的靜態備份檔，非線上DB → copy2 安全
        ok, detail = verify(path, far)
        return f'成功：{far}' if ok else f'❌ 異地副本驗證失敗：{detail}'
    except OSError as e:
        return f'❌ 異地複製失敗：{e}'


def prune(dst_dir=BACKUP_DIR, keep_days=KEEP_DAYS):
    """保留最近 keep_days 天，刪更舊的，避免塞爆磁碟。至少永遠留最新一份。"""
    files = sorted(glob.glob(os.path.join(dst_dir, 'atlas_*.db')), key=os.path.getmtime)
    cutoff = datetime.datetime.now().timestamp() - keep_days * 86400
    removed = []
    for f in files[:-1]:            # 最新一份永不刪
        if os.path.getmtime(f) < cutoff:
            os.remove(f)
            removed.append(os.path.basename(f))
    return removed


def status(dst_dir=BACKUP_DIR, offsite=None):
    """管理頁監控用：最近備份時間/大小/成功否/異地副本狀態/共幾份 + 告警。"""
    cfg = settings()
    if offsite is None:
        offsite = cfg['offsite_dir']
    stale_h = cfg['stale_hours']
    alerts = []
    # 異地未設定＝單機壞掉就全損 → 管理頁必須紅字，不能靜靜地過。
    if not offsite:
        alerts.append('異地備份未設定，資料有全損風險')

    files = sorted(glob.glob(os.path.join(dst_dir, 'atlas_*.db')), key=os.path.getmtime)
    bad = glob.glob(os.path.join(dst_dir, 'atlas_*.db.BAD'))
    if bad:
        alerts.append(f'有 {len(bad)} 份備份驗證失敗（.BAD）')
    if not files:
        alerts.append('從未備份過')
        return {'ok': False, 'last_at': None, 'count': 0, 'alerts': alerts,
                'settings': cfg, 'offsite_configured': bool(offsite),
                'msg': '❌ 從未備份過'}
    last = files[-1]
    mt = datetime.datetime.fromtimestamp(os.path.getmtime(last))
    age_h = (datetime.datetime.now() - mt).total_seconds() / 3600
    fresh = age_h < stale_h
    if not fresh:
        alerts.append(f'最近備份已是 {round(age_h)} 小時前（設定每 {FREQ_HOURS[cfg["frequency"]]}h 應備份一次）')
    try:
        counts, integrity = _counts(last)
        rows, last_ok = counts.get('ie_process'), (integrity == 'ok')
    except sqlite3.DatabaseError as e:
        rows, last_ok = None, False
        alerts.append(f'最近一份備份打不開：{e}')
    if not last_ok:
        alerts.append('最近一份備份 integrity_check 未過')
    far = os.path.join(offsite, os.path.basename(last)) if offsite else ''
    offsite_ok = bool(offsite) and os.path.isfile(far)
    if offsite and not offsite_ok:
        alerts.append('最近一份備份沒有異地副本')
    return {'ok': fresh and last_ok and not alerts,
            'last_at': mt.strftime('%Y-%m-%d %H:%M:%S'),
            'age_hours': round(age_h, 1), 'count': len(files),
            'last_path': last, 'last_size': os.path.getsize(last),
            'last_ok': last_ok, 'ie_process_rows': rows,
            'offsite_configured': bool(offsite), 'offsite_dir': offsite,
            'offsite_ok': offsite_ok, 'bad_count': len(bad),
            'settings': cfg, 'alerts': alerts,
            'msg': '正常' if not alerts else '；'.join(alerts)}


def list_backups(dst_dir=BACKUP_DIR, offsite=None):
    """還原頁用：列出所有備份（帶日期/大小/異地副本有無）。"""
    cfg = settings()
    if offsite is None:
        offsite = cfg['offsite_dir']
    out = []
    for f in sorted(glob.glob(os.path.join(dst_dir, 'atlas_*.db')),
                    key=os.path.getmtime, reverse=True):
        mt = datetime.datetime.fromtimestamp(os.path.getmtime(f))
        out.append({'name': os.path.basename(f), 'path': f,
                    'at': mt.strftime('%Y-%m-%d %H:%M:%S'),
                    'size': os.path.getsize(f),
                    'offsite': bool(offsite) and os.path.isfile(
                        os.path.join(offsite, os.path.basename(f)))})
    return out


def restore(backup_path, target=DB):
    """還原：先備份當前(防還原本身變成災難) → 驗證來源備份 → 覆蓋。"""
    if not os.path.isfile(backup_path):
        raise FileNotFoundError(f'找不到備份：{backup_path}')
    ok, detail = verify(backup_path, backup_path)   # 自檢：能開、integrity ok
    if not ok:
        raise RuntimeError(f'❌ 這份備份本身是壞的，拒絕還原：{detail}')
    pre = None
    if os.path.isfile(target):
        pre = backup(target, BACKUP_DIR)['path']    # 還原前先保住現況
    shutil.copy2(backup_path, target)
    # 舊 WAL 會在下次開啟時重播、蓋掉還原結果，必須清掉。
    # Windows 上只要還有任何連線（含 Flask server）開著這個 DB，就刪不掉 → 明確擋下，
    # 不能讓「還原看似成功、其實被舊 WAL 蓋回去」。還原前務必先停 server。
    for side in ('-wal', '-shm'):
        p = target + side
        if not os.path.isfile(p):
            continue
        try:
            os.remove(p)
        except PermissionError as e:
            raise RuntimeError(
                f'❌ 還原中止：{os.path.basename(p)} 仍被其他程序佔用（server 還開著？）。'
                f'請先停止 ME129 上的 Flask server 再還原，否則舊 WAL 會蓋掉還原結果。'
                f'目前現況已備份於 {pre}。原始錯誤：{e}') from e
    ok2, detail2 = verify(backup_path, target)
    if not ok2:
        raise RuntimeError(f'❌ 還原後驗證失敗：{detail2}')
    return {'ok': True, 'restored_from': backup_path, 'pre_restore_backup': pre, 'detail': detail2}


def _main():
    # 只在 CLI 進入點接管 stdout；模組被 import 時不可動 sys.stdout（會弄壞匯入方的輸出）
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'backup'
    if cmd == 'backup':
        r = backup()
        print(f"✅ 備份完成：{r['path']}")
        print(f"   大小：{r['size']:,} bytes")
        print(f"   驗證：{r['detail']}")
        print(f"   異地：{r['offsite']}")
        if r['pruned']:
            print(f"   輪替刪除：{len(r['pruned'])} 份")
    elif cmd == 'list':
        s = status()
        print(f"最近備份：{s['last_at']}（{s.get('age_hours')} 小時前）  共 {s['count']} 份  狀態：{s['msg']}")
        for f in sorted(glob.glob(os.path.join(BACKUP_DIR, 'atlas_*.db'))):
            print(f'   {os.path.getsize(f):>12,}  {os.path.basename(f)}')
    elif cmd == 'verify':
        ok, detail = verify(DB, sys.argv[2])
        print(('✅ ' if ok else '❌ ') + detail)
        sys.exit(0 if ok else 1)
    elif cmd == 'restore':
        r = restore(sys.argv[2])
        print(f"✅ 還原完成，來源：{r['restored_from']}")
        print(f"   還原前現況已備份至：{r['pre_restore_backup']}")
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == '__main__':
    _main()
