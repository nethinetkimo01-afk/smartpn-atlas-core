from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import database as db
import os

app = Flask(__name__, static_folder='..', static_url_path='')
CORS(app)

# ── Frontend ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('..', 'ds03_ob_interface.html')

# ── DS-03 OB ─────────────────────────────────────────────────────────────────

@app.route('/api/ds03/save', methods=['POST'])
def save_ob():
    data = request.get_json(force=True)
    return jsonify(db.save_ob_record(data))

@app.route('/api/ds03/load', methods=['GET'])
def load_ob():
    art  = request.args.get('art', '')
    eolr = request.args.get('eolr', 60)
    run  = request.args.get('run', 1)
    if not art:
        return jsonify({'ok': False, 'error': 'art is required'}), 400
    return jsonify(db.load_ob_record(art, eolr, run))

@app.route('/api/ds03/list', methods=['GET'])
def list_ob():
    return jsonify(db.list_ob_records())

@app.route('/api/ds03/delete', methods=['DELETE'])
def delete_ob():
    art  = request.args.get('art', '')
    eolr = request.args.get('eolr', 60)
    run  = request.args.get('run', 1)
    return jsonify(db.delete_ob_record(art, eolr, run))

# ── Lookup ────────────────────────────────────────────────────────────────────

@app.route('/api/lookup/all', methods=['GET'])
def get_lookup():
    return jsonify(db.get_all_lookup())

@app.route('/api/lookup/add', methods=['POST'])
def add_lookup():
    data = request.get_json(force=True)
    return jsonify(db.add_lookup_entry(data.get('viet',''), data.get('zh','')))

# ── DS-02 cross-table helper ─────────────────────────────────────────────────

@app.route('/api/ds02/epph', methods=['GET'])
def get_epph():
    art = request.args.get('art', '')
    if not art:
        return jsonify({'ok': False, 'error': 'art is required'}), 400
    return jsonify(db.get_epph_by_art(art))

# ── Health check ─────────────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'ok': True, 'version': '1.0'})

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    db.init_db()
    print('Atlas Data System starting on http://0.0.0.0:5000')
    app.run(host='0.0.0.0', port=5000, debug=False)
