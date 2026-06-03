# Data System - Internal Data Automation Project

Version: v1.7 | 2026-06-03
Status: DS-01✅ DS-02✅ DS-03✅ DS-04 defined (pending EOLR map + file path), Flask backend built + tested
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

Backup: python flask_backend/backup.py (keeps 30 days)

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
Import CLI: python flask_backend/import_ds01.py "<path.xlsx>"
Import UI:  http://localhost:5000/admin → DS-01 section
Pending: actual Excel file path, analysis requirements, import frequency

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
Import CLI: python flask_backend/import_ds02.py "<path.xlsx>"
Import UI:  http://localhost:5000/admin → DS-02 section
Pending: actual Excel file path, analysis requirements, import frequency

---

### DS-03: IE/LC Operation Breakdown (OB)

Type: Manual input via web interface
Primary key (CONFIRMED): ART + EOLR + Run number (Lan 1, Lan 2...)
EOLR options: 60 / 120 / 150 pairs/H
Same ART + different EOLR = separate records
Parts, CT, layers do not change across EOLR
MP (operators) changes per EOLR
PPH = EOLR / MP (changes with MP, NOT a fixed value)

Interface: ds03_ob_interface.html v1.4
Backend: flask_backend/ (app.py v1.1, database.py, schema.sql)
Start server: double-click flask_backend/start.bat → http://localhost:5000
TESTED: Flask server confirmed working 2026-06-03

Interface features (v1.4):
- 📂 Open: Record browser modal (search/filter, load any saved OB record)
- 💾 Save: POSTs to /api/ds03/save
- DS-02 →: Auto-fills E-PPH bar from DS-02 FOB LC values by ART (requires DS-02 imported)
- 📚 Lookup: Viet-Chinese part name lookup manager
- ＋ New: Clear form and start new record

Navigation:
- L1: SUM_C2B (read-only) | SUM_Stock (read-only)
- L2 under SUM_C2B: Cutting, ATOM/自动化, 同材共裁, 电脑针车, Stitching 支流, Stitching 主流, Assembly 1, Assembly 2
- L2 under SUM_Stock: 打粗, 水洗, 贴大底, 照射, 成型面照射

SUM_C2B fields (all read-only):
- MP: aggregated from sub-sheets
- PPH: EOLR / MP
- E-PPH: from DS-02 FOB LC values (auto-fill via DS-02 → button)
- Diff PPH: E-PPH - PPH
- Eff%: PPH / E-PPH x 100%

Cutting sheet: Material category | Part Viet | 部件名稱中文 | Layers | Qty/Pr | Knives/H | CT | Allowance% | ST | Actual Ops | Marking | Skiving | Attaching | Edge Paint | Heat Press
Stitching / Assembly: same, no Material category column
Stock sheets: Part Viet | 部件名稱中文 | CT | Allowance% | ST | Actual Ops

Vietnamese-Chinese Part Name Lookup:
- Independent base table
- 30+ pairs seeded on first run
- Batch extract from historical files: python flask_backend/import_ds03_batch.py "<folder>"

---

### DS-04: Production Schedule (Monthly Progress)

Type: System export, Excel, fixed format, one file per month, multiple sheets (by department)
Primary key (CONFIRMED): Department + Group + ART + Month
Import CLI: TBD (pending Excel path and frequency)
Pending: Group vs EOLR mapping table, actual Excel file path, import frequency

File format:
- Order number format: MF2604KJ8322-03--900(5/29)
- ART: extracted from order number after "--"
- Order quantity: extracted between "--" and "("
- Deadline: date inside parentheses
- Grey cell = holiday, excluded from work-hour calculation
- Yellow cell = model-change loss quantity
- Cumulative scheduled hours: formula-based, used to determine order completion date

Analysis logic (CONFIRMED):
1. From schedule: extract ART + order quantity per department/group
2. ART → DS-02 FOB col J → get col G (Model Name) + Cutting/Stitching/Assembly LC
3. Same group, same Model Name + same LC → merge display, sum orders
4. ART → DS-03 OB → get MP for EOLR (Cutting / Stitching / Forming)
5. Output: Model Name + ART | Orders | Cutting MP | Stitching MP | Forming MP

EOLR mapping:
- Defined per department/group (Jim to provide)
- Example: Group 加一A → EOLR TBD

---

### DS-05 onward

Pending Jim input.

---

## Cross-table Relationships

DS-02 Article # = DS-01 Article ID (join key)
DS-03 ART = DS-02 Article # (join key)
DS-03 E-PPH sourced from DS-02 LC Cutting/Stitching/Assembly/Stockfitting

---

## Flask Backend (flask_backend/)

Start: double-click start.bat  OR  cd flask_backend && python app.py
URLs:
  http://localhost:5000        ← OB Interface (ds03_ob_interface.html)
  http://localhost:5000/admin  ← Import Admin (DS-01/DS-02 upload, DB stats)

Files:
- app.py v1.1: all API endpoints
- database.py: SQLite helpers + import functions (change tracking)
- schema.sql: full schema
- requirements.txt: flask, flask-cors, openpyxl
- start.bat: python -m pip install -r requirements.txt -q && python app.py
- import_ds02.py: CLI → python import_ds02.py <path> [--dry-run]
- import_ds01.py: CLI → python import_ds01.py <path> [--dry-run]
- import_ds03_batch.py: CLI → python import_ds03_batch.py <folder> [--dry-run] [--lookup-only]
- backup.py: CLI → python backup.py [--keep-days=30]

API endpoints:
- POST /api/ds03/save       PUT /api/ds03/load    GET /api/ds03/list    DELETE /api/ds03/delete
- POST /api/ds02/upload     POST /api/ds01/upload
- GET  /api/ds02/list       GET  /api/ds01/list
- GET  /api/lookup/all      POST /api/lookup/add
- GET  /api/ds02/epph?art=  GET  /api/stats        GET /api/health

---

## Claude Code Operating Rules

- Always start with: claude --dangerously-skip-permissions
- Standard start: cd /d D:\smartpn-atlas-core && claude --dangerously-skip-permissions
- All git/bash commands: auto-execute, never stop to ask confirmation
- Run all tasks to completion without stopping
- If Claude Code stops: Jim types 從現在開始所有指令自動執行，不要停下來問我確認，跑到所有任務完成

---

## Next Session Starting Point

1. DS-02 ✅ imported (1903 new, 2288 updated) from: C:\Users\user\OneDrive\Desktop\FOB Price List.xlsx
2. DS-01 ✅ imported (2044 new, 4929 updated) from: C:\Users\user\OneDrive\Desktop\SS27 SP1 & FW26 SP7.xlsx
3. DS-03 batch ✅ imported from: C:\Users\user\OneDrive\Desktop\IE (128 xlsx files, 538 Viet-Chinese pairs)
4. DS-04: Production Schedule
   → Pending: EOLR mapping table (Group → EOLR), actual Excel file path
   → Pending: import frequency
5. DS-05...N: Pending Jim input
6. Define report requirements / dashboard tabs

---

## Instructions for Claude

- Read this file every session
- Architecture confirmed, do not re-discuss
- Continue DATA SYSTEM: start from Next Session Starting Point
- 24_DATA_SYSTEM.md: Claude outputs full content, Jim pastes via GitHub web editor
- After Jim updates GitHub: fetch raw URL to verify, then continue
