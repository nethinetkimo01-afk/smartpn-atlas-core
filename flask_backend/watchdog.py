#!/usr/bin/env python3
"""Watchdog: every 30s checks port 5000; restarts the server (serve.py) if down."""
import socket, subprocess, time, os, sys, datetime, atexit

# Launch via waitress (serve.py), not app.py — see test_output/ie_stress_waitress.md.
SERVE_PY  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'serve.py')
BOOT_LOG  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_boot.log')
LOCK_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'watchdog.lock')
PORT     = 5000
INTERVAL = 30
_proc    = None

PYTHON = sys.executable


def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {msg}', flush=True)


def port_alive():
    try:
        with socket.create_connection(('127.0.0.1', PORT), timeout=3):
            return True
    except OSError:
        return False


def start_flask():
    global _proc
    log('Starting server serve.py (waitress) ...')
    boot_fh = open(BOOT_LOG, 'a')
    _proc = subprocess.Popen(
        [PYTHON, SERVE_PY],
        cwd=os.path.dirname(SERVE_PY),
        stdout=boot_fh,
        stderr=boot_fh,
    )
    time.sleep(5)
    if port_alive():
        log(f'Server started (pid={_proc.pid})')
    else:
        log('WARNING: Server started but port 5000 still not responding')


# ── 防多開機制 (single-instance guard) ────────────────────────────────────────
# 啟動時：若已有 watchdog 正常運作(lock 內 PID 存活 且 port 5000 alive) → 本實例退出。
# 否則(lock 不存在 / PID 已死 / port 沒起來) → 取得控制權，寫入自己的 PID。
def pid_alive(pid):
    """Windows: 用 tasklist 判斷該 PID 進程是否存在；非 Windows fallback os.kill(pid,0)。"""
    if not pid or pid <= 0:
        return False
    try:
        out = subprocess.check_output(
            ['tasklist', '/FI', f'PID eq {pid}', '/NH', '/FO', 'CSV'],
            text=True, stderr=subprocess.DEVNULL,
        )
        return f'"{pid}"' in out   # CSV 欄位如 "python.exe","<pid>",... ；查無時為 INFO: No tasks
    except Exception:
        try:
            os.kill(pid, 0)        # POSIX fallback
            return True
        except Exception:
            return False


def read_lock():
    try:
        with open(LOCK_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return None


def write_lock():
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))


def clear_lock():
    """程式結束時清除自己持有的 lock（不誤刪別的實例寫的 lock）。"""
    try:
        if read_lock() == os.getpid():
            os.remove(LOCK_FILE)
    except Exception:
        pass


def acquire_or_exit():
    existing = read_lock()
    if existing and existing != os.getpid() and pid_alive(existing) and port_alive():
        log(f'已有 watchdog 運作中 (pid={existing}, port 5000 alive)，本實例退出')
        sys.exit(0)
    if existing and not pid_alive(existing):
        log(f'偵測到殘留 lock (pid={existing} 已不存在)，接管控制權')
    write_lock()
    atexit.register(clear_lock)
    log(f'取得 watchdog 控制權 (pid={os.getpid()})')


if __name__ == '__main__':
    acquire_or_exit()
    log('Watchdog started — monitoring port 5000 every 30s')
    while True:
        if port_alive():
            log('OK (port 5000 alive)')
        else:
            log('Port 5000 down — restarting Flask ...')
            if _proc:
                try:
                    _proc.terminate()
                except Exception:
                    pass
            start_flask()
        time.sleep(INTERVAL)
