"""
Launch the REAL Flask app via app.run() — exactly as production does
(flask_backend/app.py line ~1657: app.run(host=..., port=..., debug=False)) —
but pointed at tests/atlas_stress.db instead of data/atlas.db.

DB redirection is done by monkeypatching database.DB_PATH BEFORE app is imported,
so every db.get_conn() call resolves to the stress DB. data/atlas.db is never opened.
"""
import os, sys

TESTS_DIR   = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(TESTS_DIR)
STRESS_DB   = os.path.join(TESTS_DIR, 'atlas_stress.db')

sys.path.insert(0, BACKEND_DIR)

import database
database.DB_PATH = STRESS_DB          # redirect EVERY connection to the stress DB
assert database.DB_PATH == STRESS_DB

import app as flask_app

PORT    = int(os.environ.get('STRESS_PORT', '5099'))
MODE    = os.environ.get('STRESS_SERVER', 'apprun')   # 'apprun' | 'waitress'
THREADS = int(os.environ.get('STRESS_THREADS', '8'))

if __name__ == '__main__':
    if MODE == 'waitress':
        # Same as production serve.py: waitress multi-threaded WSGI.
        from waitress import serve
        serve(flask_app.app, host='127.0.0.1', port=PORT, threads=THREADS)
    else:
        # Match old production: app.run() Werkzeug dev server.
        flask_app.app.run(host='127.0.0.1', port=PORT, debug=False)
