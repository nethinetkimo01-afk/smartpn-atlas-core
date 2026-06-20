#!/usr/bin/env python3
"""
Demo launcher — serves the app via waitress using atlas_demo.db (anonymized).

啟動前先建 demo DB：
    python flask_backend/make_demo_db.py

啟動 demo server（port 5001，不影響正式 ME129:5000）：
    python flask_backend/serve_demo.py
"""
import os, sys

_demo_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'atlas_demo.db')
if not os.path.isfile(_demo_db):
    print(f'ERROR: Demo DB not found: {_demo_db}')
    print('Run first:  python flask_backend/make_demo_db.py')
    sys.exit(1)

# 必須在 import database / app 之前設定，database.py 模組載入時讀取此值
os.environ['ATLAS_DB'] = _demo_db

import database as db
from app import app

PORT    = int(os.environ.get('ATLAS_PORT', '5001'))
THREADS = int(os.environ.get('ATLAS_THREADS', '8'))

if __name__ == '__main__':
    db.init_db()
    print(f'[DEMO] IE Management — demo mode  http://0.0.0.0:{PORT}')
    print(f'[DEMO] DB: {_demo_db}')
    from waitress import serve
    serve(app, host='0.0.0.0', port=PORT, threads=THREADS)
