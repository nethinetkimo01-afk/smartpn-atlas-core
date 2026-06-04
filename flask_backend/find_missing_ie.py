#!/usr/bin/env python3
"""
Find IE files in Biên chế/Jun/IE folder for missing ARTs.
Extracts ALL ART codes from each filename (not just the first).
"""
import os, re, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_ART_RE = re.compile(r'[A-Z]{2}\d{4,6}')

IE_FOLDER = r"C:\Users\user\OneDrive\Desktop\Biên chế\Jun\IE"
MISSING_TXT = r"D:\smartpn-atlas-core\flask_backend\test_output\missing_ie_files.txt"

# Parse missing ARTs from txt
missing_arts = set()
with open(MISSING_TXT, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('ART') or line.startswith('-'):
            continue
        parts = line.split()
        if parts:
            missing_arts.add(parts[0])

print(f"Missing ARTs: {len(missing_arts)}")

# Scan Jun\IE folder for ALL xlsx files and extract ALL ART codes
file_to_arts = {}   # filepath -> list of ARTs
art_to_files = {}   # ART -> list of (filepath, is_first)

for root, dirs, files in os.walk(IE_FOLDER):
    for fn in files:
        if fn.startswith('~$') or not fn.lower().endswith('.xlsx'):
            continue
        fpath = os.path.join(root, fn)
        arts_in_file = _ART_RE.findall(fn)
        if arts_in_file:
            file_to_arts[fpath] = arts_in_file
            for i, art in enumerate(arts_in_file):
                if art not in art_to_files:
                    art_to_files[art] = []
                art_to_files[art].append((fpath, i == 0))

print(f"Total xlsx files scanned: {len(file_to_arts)}")
print(f"Total unique ARTs in filenames: {len(art_to_files)}")

# Find which missing ARTs have files
found = {}
not_found = []
for art in sorted(missing_arts):
    if art in art_to_files:
        found[art] = art_to_files[art]
    else:
        not_found.append(art)

print(f"\nMissing ARTs found in Jun/IE files: {len(found)}")
print(f"Missing ARTs NOT found in Jun/IE files: {len(not_found)}")

print("\n--- Found ARTs and their files ---")
for art, file_list in sorted(found.items()):
    for fpath, is_first in file_list:
        rel = fpath.replace(IE_FOLDER + '\\', '')
        tag = '[FIRST]' if is_first else '[SECONDARY]'
        print(f"  {art}  {tag}  {rel}")

print("\n--- NOT found in Jun/IE ---")
for art in not_found:
    print(f"  {art}")
