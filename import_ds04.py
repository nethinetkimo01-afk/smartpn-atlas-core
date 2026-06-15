"""
Run once to import DS-04 parsed data into atlas.db.
Usage: python import_ds04.py  (from repo root)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'flask_backend'))
import database as db

# Re-run the parser to get fresh records
exec(open('parse_ds04.py', encoding='utf-8').read())  # sets all_records

db.init_db()
result = db.ds04_import(all_records)
if result['ok']:
    print(f"Imported {result['count']} rows into ds04_orders.")
else:
    print(f"Error: {result['error']}")
