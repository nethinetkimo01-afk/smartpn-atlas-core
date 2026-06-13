"""
SmartPN Atlas — 結果機晨間自動同步 (morning_sync.py)

每天早上 8:00 在「結果機 (D:\\smartpn-atlas-core)」自動：
  1. git pull origin main   （拉取 Code 機昨晚推送的程式碼）
  2. 重啟 Flask              （關閉舊 python.exe Flask，啟動新的）

DB (*.db) 為「手動同步」—— 本腳本不碰 DB。
Code 機跑完導入後，用隨身碟複製 flask_backend\\data\\*.db 到結果機同路徑。

用法：
  python morning_sync.py            一次性執行（pull + 重啟 Flask）
  python morning_sync.py --install  註冊 Windows 工作排程器（每天 08:00，需管理員）
  python morning_sync.py --startup  安裝到 啟動資料夾（登入後執行，免管理員）
  python morning_sync.py --remove   移除工作排程器任務
"""
import os
import sys
import subprocess

ROOT = r'D:\smartpn-atlas-core'
APP = os.path.join(ROOT, 'flask_backend', 'app.py')
LOG = os.path.join(ROOT, 'flask_backend', 'flask_boot.log')
TASK_NAME = 'Atlas_Morning_Sync'
SCRIPT_PATH = os.path.abspath(__file__)

# Windows process-creation flags (detached background Flask)
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200


def log(msg):
    print(f'[morning_sync] {msg}', flush=True)


def git_pull():
    log('git pull origin main ...')
    r = subprocess.run(['git', 'pull', 'origin', 'main'], cwd=ROOT,
                       capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
        log('WARNING: git pull 非 0 退出，仍續行重啟 Flask。')
    return r.returncode == 0


def kill_old_flask():
    """關閉舊 Flask，但**不殺自己**（本腳本也是 python.exe）。"""
    me = os.getpid()
    try:
        out = subprocess.run(
            ['tasklist', '/fi', 'imagename eq python.exe', '/fo', 'csv', '/nh'],
            capture_output=True, text=True).stdout
    except Exception as e:
        log(f'tasklist 失敗: {e}')
        return
    killed = 0
    for line in out.splitlines():
        line = line.strip()
        if not line or not line.startswith('"'):
            continue
        cols = [c.strip('"') for c in line.split('","')]
        if len(cols) < 2:
            continue
        try:
            pid = int(cols[1])
        except ValueError:
            continue
        if pid == me:
            continue  # 不殺自己
        subprocess.run(['taskkill', '/f', '/pid', str(pid)],
                       capture_output=True, text=True)
        killed += 1
    log(f'關閉舊 python.exe 程序：{killed} 個')


def start_flask():
    log('啟動 Flask（背景）...')
    logf = open(LOG, 'a', encoding='utf-8')
    subprocess.Popen(
        [sys.executable, APP], cwd=ROOT,
        stdout=logf, stderr=logf,
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        close_fds=True)
    log('Flask 已啟動 → http://localhost:5000/ie  /allocation')


def run_once():
    if not os.path.isdir(ROOT):
        log(f'找不到 {ROOT} — 本腳本只在結果機 (D:) 執行。')
        return 1
    git_pull()
    kill_old_flask()
    start_flask()
    log('完成。DB 記得手動用隨身碟同步 flask_backend\\data\\*.db')
    return 0


def install_scheduler():
    cmd = [
        'schtasks', '/create', '/tn', TASK_NAME,
        '/tr', f'"{sys.executable}" "{SCRIPT_PATH}"',
        '/sc', 'daily', '/st', '08:00',
        '/ru', os.environ.get('USERNAME', ''), '/rl', 'highest', '/f',
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout or r.stderr)
    if r.returncode == 0:
        log(f'已註冊每天 08:00 任務 "{TASK_NAME}"。手動測試： schtasks /run /tn {TASK_NAME}')
    else:
        log('註冊失敗 — 請用「以系統管理員身分執行」開 cmd 再跑 --install，'
            '或改用 --startup（免管理員）。')
    return r.returncode


def install_startup():
    """放一個 .bat 到 啟動資料夾（登入後自動跑一次）。"""
    startup = os.path.join(os.environ['APPDATA'],
                           r'Microsoft\Windows\Start Menu\Programs\Startup')
    bat = os.path.join(startup, 'atlas_morning_sync.bat')
    with open(bat, 'w', encoding='utf-8') as f:
        f.write('@echo off\r\n')
        f.write(f'"{sys.executable}" "{SCRIPT_PATH}"\r\n')
    log(f'已寫入啟動資料夾：{bat}（下次登入自動執行）')
    return 0


def remove_scheduler():
    r = subprocess.run(['schtasks', '/delete', '/tn', TASK_NAME, '/f'],
                       capture_output=True, text=True)
    print(r.stdout or r.stderr)
    return r.returncode


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else ''
    if arg == '--install':
        sys.exit(install_scheduler())
    elif arg == '--startup':
        sys.exit(install_startup())
    elif arg == '--remove':
        sys.exit(remove_scheduler())
    else:
        sys.exit(run_once())
