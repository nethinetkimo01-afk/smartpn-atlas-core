#!/usr/bin/env python3
"""
make_demo_db.py — 從 atlas.db 建立脫敏 demo 資料庫 atlas_demo.db

執行：python flask_backend/make_demo_db.py
每次執行都完整重建 atlas_demo.db（不累積舊資料）。
原始 atlas.db 絕不修改。
"""
import os, sys, shutil, sqlite3, random, hashlib

random.seed(42)  # 固定 seed，重複執行結果一致

BASE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(BASE, 'data', 'atlas.db')
DST  = os.path.join(BASE, 'data', 'atlas_demo.db')

FAKE_MODELS = [
    'Falcon Runner', 'Apex Trainer', 'Velocity Pro', 'Storm Court',
    'Swift Edge', 'Peak Flex', 'Stride Elite', 'Quantum Boost',
    'Aero Sprint', 'Nova Step', 'Titan Force', 'Echo Trail',
    'Zenith Run', 'Blaze Pace', 'Ridge Sport', 'Arc Glide',
    'Solace Walk', 'Crest Speed', 'Orbit Fit', 'Pulse React',
    'Flash Dash', 'Core Drive', 'Spin Loop', 'Bravo Kick',
]

FAKE_MATERIALS = ['Synthetic', 'Mesh', 'Leather', 'Suede', 'Knit', 'Canvas', 'Nylon', 'Foam Composite']


def perturb(v):
    if v is None:
        return v
    try:
        f = float(v)
        if f == 0:
            return f
        pct = random.uniform(0.05, 0.15) * random.choice([-1, 1])
        return round(f * (1 + pct), 4)
    except (TypeError, ValueError):
        return v


def stable_idx(val, n):
    h = int(hashlib.md5(str(val).encode()).hexdigest(), 16)
    return h % n


if __name__ == '__main__':
    if not os.path.isfile(SRC):
        print(f'ERROR: {SRC} not found')
        sys.exit(1)

    shutil.copy2(SRC, DST)
    print(f'Copied {SRC} → {DST}')

    conn = sqlite3.connect(DST)
    conn.row_factory = sqlite3.Row

    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    # ── 1. model_name ─────────────────────────────────────────────────────────
    models = [r[0] for r in conn.execute(
        'SELECT DISTINCT model_name FROM ob_header WHERE model_name IS NOT NULL AND model_name != ""'
    ).fetchall()]
    model_map = {}
    used = []
    for m in sorted(models):
        idx = stable_idx(m, len(FAKE_MODELS))
        name = FAKE_MODELS[idx]
        tries = 0
        while name in used and tries < len(FAKE_MODELS):
            idx = (idx + 1) % len(FAKE_MODELS)
            name = FAKE_MODELS[idx]
            tries += 1
        if name in used:
            name = f'Demo Model {len(used)+1:03d}'
        model_map[m] = name
        used.append(name)

    for orig, fake in model_map.items():
        conn.execute('UPDATE ob_header SET model_name=? WHERE model_name=?', (fake, orig))
        if 'ds02_fob' in tables:
            conn.execute('UPDATE ds02_fob SET model_name=? WHERE model_name=?', (fake, orig))
    print(f'Anonymized {len(model_map)} model names')

    # ── 2. ART codes ──────────────────────────────────────────────────────────
    arts = [r[0] for r in conn.execute(
        'SELECT DISTINCT art FROM ob_articles ORDER BY id'
    ).fetchall()]
    art_map = {art: f'DM{i+1:04d}' for i, art in enumerate(arts)}

    for orig, fake in art_map.items():
        conn.execute('UPDATE ob_articles SET art=? WHERE art=?', (fake, orig))
        if 'ie_process' in tables:
            conn.execute('UPDATE ie_process SET art=? WHERE art=?', (fake, orig))
        if 'ds02_fob' in tables:
            conn.execute('UPDATE ds02_fob SET art=? WHERE art=?', (fake, orig))
        if 'ds01_sp' in tables:
            conn.execute('UPDATE ds01_sp SET article_id=? WHERE article_id=?', (fake, orig))
    print(f'Anonymized {len(art_map)} ART codes → DM0001~DM{len(art_map):04d}')

    # ── 3. material ───────────────────────────────────────────────────────────
    mat_rows = conn.execute(
        'SELECT id, material FROM ob_header WHERE material IS NOT NULL AND material != ""'
    ).fetchall()
    for r in mat_rows:
        idx = stable_idx(r['material'], len(FAKE_MATERIALS))
        conn.execute('UPDATE ob_header SET material=? WHERE id=?', (FAKE_MATERIALS[idx], r['id']))
    print(f'Anonymized {len(mat_rows)} material values')

    # ── 4. ob_epph numeric perturbation ──────────────────────────────────────
    ep_rows = conn.execute(
        'SELECT id, cutting, stitching, assembly, stock FROM ob_epph'
    ).fetchall()
    for r in ep_rows:
        conn.execute(
            'UPDATE ob_epph SET cutting=?, stitching=?, assembly=?, stock=? WHERE id=?',
            (perturb(r['cutting']), perturb(r['stitching']),
             perturb(r['assembly']), perturb(r['stock']), r['id'])
        )
    print(f'Perturbed {len(ep_rows)} ob_epph rows')

    # ── 5. ie_process numeric perturbation ───────────────────────────────────
    if 'ie_process' in tables:
        proc_rows = conn.execute(
            'SELECT id, tct, normal_time, standard_time, actual_operators, cut_per_hour FROM ie_process'
        ).fetchall()
        for r in proc_rows:
            conn.execute(
                'UPDATE ie_process SET tct=?, normal_time=?, standard_time=?, actual_operators=?, cut_per_hour=? WHERE id=?',
                (perturb(r['tct']), perturb(r['normal_time']), perturb(r['standard_time']),
                 perturb(r['actual_operators']), perturb(r['cut_per_hour']), r['id'])
            )
        print(f'Perturbed {len(proc_rows)} ie_process rows')

    # ── 6. ie_sheet_data numeric values ──────────────────────────────────────
    if 'ie_sheet_data' in tables:
        sd_rows = conn.execute('SELECT id, value FROM ie_sheet_data').fetchall()
        updated = 0
        for r in sd_rows:
            pv = perturb(r['value'])
            if pv is not None and str(pv) != str(r['value']):
                conn.execute('UPDATE ie_sheet_data SET value=? WHERE id=?', (str(pv), r['id']))
                updated += 1
        print(f'Perturbed {updated} ie_sheet_data numeric values')

    conn.commit()
    conn.close()
    print(f'\nDone. Demo DB ready: {DST}')
    print('Start demo server: python flask_backend/serve_demo.py')
