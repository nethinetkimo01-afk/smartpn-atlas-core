#!/usr/bin/env python3
"""Watchdog: every 30s checks port 5000; restarts the server (serve.py) if down."""
import socket, subprocess, time, os, sys, datetime

# Launch via waitress (serve.py), not app.py — see test_output/ie_stress_waitress.md.
SERVE_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'serve.py')
BOOT_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_boot.log')
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


if __name__ == '__main__':
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
