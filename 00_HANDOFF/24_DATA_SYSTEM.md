# Data System - Internal Data Automation Project

Version: v1.5 | 2026-06-03
Status: DS-01 DS-02 confirmed, DS-03 complete, Flask backend built
Purpose: New Claude session reads this file to continue from last point.

---

## Background

Internal data automation system for Jim's company. NOT related to SmartPN Atlas.
Jim: defines data sources and reports.
Team: daily data maintenance (data entry, file uploads).

---

## System Architecture (CONFIRMED)

Deployment: Internal LAN server
Server: One always-on office PC
Tech stack: Python + Flask + SQLite
Team access: Browser via LAN URL, no software needed
Flow: Source -> Import UI -> Python server -> SQLite -> Jim report dashboard

---

## Core Mechanisms (CONFIRMED)

Dedup and change tracking:
- Each data source has its own primary key (Jim defines separately)
- New record: write to master table, no log
- Existing record changed: update master + log all changed fields (old, new, field name, timestamp)
- Exact duplicate: skip
- Field matching: always by NAME not position

Backup: Daily automatic full SQLite backup, retention days TBD

Reports:
- Fixed: Jim-approved tabs, auto-updated
- Exploratory pivot: Jim freely pivots, promotes to fixed when satisfied

---

## Save Protocol

24_DATA_SYSTEM.md update method (ONLY method):
1. Claude outputs full file content
2. Jim opens https://github.com/nethinetkimo01-afk/smartpn-atlas-core/blob/main/00_HANDOFF/24_DATA_SYSTEM.md
3. Click pencil icon to edit
4. Select all, delete, paste new content
5. Commit

Other files: cd /d D:\smartpn-atlas-core && git add . && git commit -m "desc" && git push https://[TOKEN]@github.com/nethinetkimo01-afk/smartpn-atlas-core.git main

---

## Data Source Registry

### DS-01: SP (Season Plan)

Sheet: {Season} SP{N}-EVM (e.g. FW26 SP7-EVM)
Type: System export, Excel, fixed format, ~6383 rows x 76 cols
Primary key (CONFIRMED): Article ID + Product Type DESC + Calendar Month
Quantity: Total (sum)
Field matching: by name, not position
Pending: Analysis requirements, import frequency

---

### DS-02: FOB Price List

Type: System export, Excel, fixed format, ~4193 rows x 30 cols
Fields: Model #, Model Name, Silhouette Number, Article #, Factory, Season,
  Category, O/S Tooling, EVA M/S Tooling, LC Total, LC CTB, Cutting,
  Stitching, Stockfitting, Assembly, (S) variants, Stage, Valid From,
  LC Treatments, Shoe Construction, Remark, Created By/Date, Modified By/Date
Primary key (CONFIRMED): Article # (ART) - also cross-table join key
Change tracking: ALL fields
Field matching: by name, not position
E-PPH source: LC Cutting / LC Stitching / LC Assembly / LC Stockfitting -> used in DS-03 SUM_C2B

---

### DS-03: IE/LC Operation Breakdown (OB)

Type: Manual input via web interface
Primary key (CONFIRMED): ART + EOLR + Run number (Lan 1, Lan 2...)
EOLR options: 60 / 120 / 150 pairs/H
Same ART + different EOLR = separate records
Parts, CT, layers do not change across EOLR
MP (operators) changes per EOLR
PPH = EOLR / MP (changes with MP, NOT a fixed value)

Interface file: ds03_ob_interface.html (v1.3 in repo)
Backend: flask_backend/ (app.py, database.py, schema.sql)
Start server: double-click flask_backend/start.bat

Navigation structure:
- L1: SUM_C2B (read-only) | SUM_Stock (read-only)
- L2 under SUM_C2B: Cutting, ATOM, 同材共裁, 电脑针车, Stitching 支流, Stitching 主流, Assembly 1, Assembly 2
- L2 under SUM_Stock: 打粗, 水洗, 贴大底, 照射, 成型面照射

SUM_C2B fields (all read-only):
- MP: aggregated from sub-sheets
- PPH: EOLR / MP
- E-PPH: from DS-02 FOB LC values
- Diff PPH: E-PPH - PPH (red=gap, green=ok)
- Eff%: PPH / E-PPH x 100%

Cutting sheet row structure:
- Row 1: Material category | Part name Viet (team input) | 部件名稱 中文 (auto lookup)
- Row 2: Layers, Qty/Pr, Knives/H, CT (manual), Allowance%, ST (formula), Actual Ops (manual)
- Additional process cols: Marking, Skiving, Attaching, Edge Paint, Heat Press

Stitching / Assembly: same as Cutting, no Material category column

Vietnamese-Chinese Part Name Lookup Table:
- Independent base table (not DS series)
- Team inputs Vietnamese -> system auto-fills Chinese
- 30+ pairs seeded in DB on first run
- Will grow from historical Excel files

Header import file: pending (Jim to provide format)

---

### DS-04 onward

Pending Jim input.

---

## Cross-table Relationships

DS-02 Article # = DS-01 Article ID (join key)
DS-03 ART = DS-02 Article # (join key)
DS-03 E-PPH sourced from DS-02 LC fields

---

## Flask Backend (BUILT - in flask_backend/)

Files:
- app.py: all API endpoints (DS-03 save/load, lookup CRUD, DS-02 E-PPH)
- database.py: SQLite helpers
- schema.sql: full schema (ob_header, ob_rows, ob_epph, lookup_viet_zh, change_log, ds01_sp, ds02_fob)
- requirements.txt: flask, flask-cors
- start.bat: one-click server start for LAN deployment

---

## Claude Code Operating Rules

- Always start with: claude --dangerously-skip-permissions
- Standard start: cd /d D:\smartpn-atlas-core && claude --dangerously-skip-permissions
- Auto mode in /config is NOT enough - still stops for bash/git commands
- First prompt: select "2. Yes, I accept"
- After this, all commands run without stopping
- If still stopping: exit and restart with --dangerously-skip-permissions

---

## Next Session Starting Point

1. Test ds03_ob_interface.html in browser (open file directly)
2. Test Flask backend: run start.bat, open http://localhost:5000
3. Define DS-04...N data sources
4. Define report requirements
5. Extract Viet-Chinese lookup from 300-400 historical OB Excel files
   (Jim to provide folder path)
6. Build batch import script for historical files

---

## Instructions for Claude

- Read this file every session
- Architecture confirmed, do not re-discuss
- Continue DATA SYSTEM: start from Next Session Starting Point
- New decision confirmed: output full file content, Jim updates via GitHub web editor
- After Jim updates GitHub: always verify by fetching the file and restart with --dangerously-skip-permissions
