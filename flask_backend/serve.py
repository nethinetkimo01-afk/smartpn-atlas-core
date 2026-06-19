#!/usr/bin/env python3
"""
Production launcher — serves the Flask app via waitress (multi-threaded WSGI).

Why: 壓測 (test_output/ie_stress_test_real.md) 證明 app.run()（Werkzeug 開發
伺服器）在 20 並發下把重型細表讀取排隊序列化，p95 達 ~10.7 秒。waitress 多線程
同時服務多個請求，p95 可降回接近單線程量級。SQLite 本身無問題（無 locked）。

不改 app.py：直接 import 既有 app 物件。app.py 的 if __name__=='__main__' 仍保留
app.run() 當開發後備。

啟動方式（取代 python app.py）：
    python flask_backend/serve.py
"""
import os
import database as db
from app import app

PORT    = int(os.environ.get('ATLAS_PORT', '5000'))
THREADS = int(os.environ.get('ATLAS_THREADS', '8'))

if __name__ == '__main__':
    db.init_db()  # 與 app.py __main__ 一致：啟動前確保 schema/migration/seed
    print(f'Atlas Data System (waitress, threads={THREADS}) starting on http://0.0.0.0:{PORT}')
    from waitress import serve
    serve(app, host='0.0.0.0', port=PORT, threads=THREADS)
