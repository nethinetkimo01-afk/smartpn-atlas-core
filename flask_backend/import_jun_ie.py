#!/usr/bin/env python3
"""
Import IE files from Biên chế/Jun/IE folder.
Handles multi-ART filenames: creates ob_header+ob_epph records for ALL ART codes
found in each filename, not just the first.

For secondary ARTs (2nd, 3rd, ... in filename), copies MP values from the primary
ART's import rather than re-parsing the file.

Usage:
    python import_jun_ie.py [--dry-run] [--verbose]
"""
import sys, os, re, glob

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db
from import_ds03_batch import process_file, fn_eolr

IE_FOLDER = r"C:\Users\user\OneDrive\Desktop\Biên chế\Jun\IE"
_ART_RE = re.compile(r'[A-Z]{2}\d{4,6}')

_SKIP_FILENAMES = {
    '120双_FW26_GHOST SPRINT W_HQ3330..xlsx',
}


def all_arts_from_filename(path):
    """Return all ART codes found in filename (preserving order)."""
    return _ART_RE.findall(os.path.basename(path))


def art_already_in_db(conn, art, eolr):
    row = conn.execute(
        '''SELECT a.id FROM ob_articles a
           JOIN ob_header h ON h.id = a.header_id
           WHERE a.art=? AND h.eolr=?''',
        (art, eolr)
    ).fetchone()
    return row is not None


def save_secondary_art(art, eolr, season, model, mp_vals, dry_run=False):
    """Create an ob_header + ob_epph record for a secondary ART copying MP from primary."""
    if dry_run:
        return {'ok': True, 'new': True, 'dry_run': True}
    ob_data = {
        'header': {
            'art': art, 'season': season,
            'model': model, 'material': '', 'category': '', 'eolr': eolr, 'run': 1
        },
        'epph': {
            'cutting':   mp_vals.get('cutting')   or 0,
            'stitching': mp_vals.get('stitching') or 0,
            'assembly':  mp_vals.get('assembly')  or 0,
            'stock':     mp_vals.get('stock')     or 0,
        },
        'sheets': {}
    }
    return db.save_ob_record(ob_data)


def main():
    dry_run = '--dry-run' in sys.argv
    verbose = '--verbose' in sys.argv

    db.init_db()

    files = glob.glob(os.path.join(IE_FOLDER, '**', '*.xlsx'), recursive=True)
    files = [
        f for f in files
        if not os.path.basename(f).startswith('~$')
        and os.path.basename(f) not in _SKIP_FILENAMES
    ]
    files.sort()

    print(f"IE folder: {IE_FOLDER}")
    print(f"Files found: {len(files)}  dry_run={dry_run}\n")

    total_new = 0
    total_skip = 0
    total_secondary_new = 0
    total_secondary_skip = 0
    errors = []

    for path in files:
        rel = os.path.relpath(path, IE_FOLDER)
        arts_in_fn = all_arts_from_filename(path)
        if not arts_in_fn:
            if verbose:
                print(f"  SKIP (no ART in filename): {rel}")
            continue

        eolr = fn_eolr(path) or 120
        primary_art = arts_in_fn[0]
        secondary_arts = arts_in_fn[1:]

        # Check if primary ART already in DB
        conn = db.get_conn()
        primary_exists = art_already_in_db(conn, primary_art, eolr)
        conn.close()

        if primary_exists:
            # Primary already imported — just handle secondary ARTs using DB values
            conn = db.get_conn()
            row = conn.execute(
                '''SELECT h.season, h.model, e.cutting, e.stitching, e.assembly, e.stock
                   FROM ob_header h JOIN ob_epph e ON e.header_id=h.id
                   WHERE h.art=? AND h.eolr=? ORDER BY h.id DESC LIMIT 1''',
                (primary_art, eolr)
            ).fetchone()
            conn.close()

            if not row:
                errors.append(f"  No epph for existing {primary_art}/{eolr}: {rel}")
                continue

            season, model = row[0], row[1]
            mp_vals = {'cutting': row[2], 'stitching': row[3], 'assembly': row[4], 'stock': row[5]}

            if verbose:
                print(f"  PRIMARY exists {primary_art}/{eolr} | {rel}")

            for art in secondary_arts:
                conn = db.get_conn()
                exists = art_already_in_db(conn, art, eolr)
                conn.close()
                if exists:
                    total_secondary_skip += 1
                    if verbose:
                        print(f"    SECONDARY skip {art}/{eolr} (exists)")
                    continue
                r = save_secondary_art(art, eolr, season, model, mp_vals, dry_run)
                if r.get('ok'):
                    total_secondary_new += 1
                    print(f"    SECONDARY new  {art}/{eolr}  C={mp_vals.get('cutting')} S={mp_vals.get('stitching')} A={mp_vals.get('assembly')}  from {primary_art}")
                else:
                    errors.append(f"    SECONDARY error {art}: {r.get('error')}")

        else:
            # Import file fresh
            r = process_file(path, dry_run=dry_run)
            if not r.get('ok'):
                errors.append(f"  ERROR {rel}: {r.get('error')}")
                continue

            mp_vals = r.get('mp', {})
            hdr = r.get('header', {})
            season = hdr.get('season', '')
            model = hdr.get('model', '')
            ob = r.get('ob_save', {})

            if ob and ob.get('new'):
                total_new += 1
                print(f"  PRIMARY new  {primary_art}/{eolr}  C={mp_vals.get('cutting')} S={mp_vals.get('stitching')} A={mp_vals.get('assembly')}  | {rel}")
            elif ob and not ob.get('new'):
                total_skip += 1
                if verbose:
                    print(f"  PRIMARY upd  {primary_art}/{eolr}  | {rel}")
            else:
                total_skip += 1
                if verbose:
                    print(f"  PRIMARY skip {primary_art}/{eolr} | {rel}")

            # Now handle secondary ARTs with same MP values
            for art in secondary_arts:
                conn = db.get_conn()
                exists = art_already_in_db(conn, art, eolr)
                conn.close()
                if exists:
                    total_secondary_skip += 1
                    if verbose:
                        print(f"    SECONDARY skip {art}/{eolr} (exists)")
                    continue
                r2 = save_secondary_art(art, eolr, season, model, mp_vals, dry_run)
                if r2.get('ok'):
                    total_secondary_new += 1
                    print(f"    SECONDARY new  {art}/{eolr}  C={mp_vals.get('cutting')} S={mp_vals.get('stitching')} A={mp_vals.get('assembly')}  from {primary_art}")
                else:
                    errors.append(f"    SECONDARY error {art}: {r2.get('error')}")

    print(f"\n{'='*60}")
    print(f"Primary ART new: {total_new}  skip/update: {total_skip}")
    print(f"Secondary ART new: {total_secondary_new}  skip: {total_secondary_skip}")
    print(f"Errors: {len(errors)}")
    for e in errors:
        print(f"  {e}")
    if dry_run:
        print("(DRY RUN — nothing written)")


if __name__ == '__main__':
    main()
