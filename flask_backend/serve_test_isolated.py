#!/usr/bin/env python3
"""
Isolated test launcher — serves the app via waitress using an ISOLATED copy of the
DB (data/test_isolated/atlas_test.db) on port 5099, so verification tests never
touch the real atlas.db / production data.

Start:
    python flask_backend/serve_test_isolated.py
"""
import os, sys

_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'test_isolated', 'atlas_test.db')
if not os.path.isfile(_db):
    print(f'ERROR: isolated test DB not found: {_db}')
    sys.exit(1)

# Must be set before importing database/app (database.py reads ATLAS_DB at import).
os.environ['ATLAS_DB'] = _db

import database as db
from app import app

PORT    = int(os.environ.get('ATLAS_PORT', '5099'))
THREADS = int(os.environ.get('ATLAS_THREADS', '8'))

if __name__ == '__main__':
    db.init_db()
    print(f'[TEST-ISOLATED] IE Management  http://127.0.0.1:{PORT}')
    print(f'[TEST-ISOLATED] DB: {_db}')
    from waitress import serve
    serve(app, host='127.0.0.1', port=PORT, threads=THREADS)
