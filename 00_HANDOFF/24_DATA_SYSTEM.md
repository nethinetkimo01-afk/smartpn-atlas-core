# Data System - Internal Data Automation Project

Version: v2.1 | 2026-06-04
Status: DS-01✅ DS-02✅ DS-03✅ DS-04 defined DS-05 script built, Flask backend v1.4, analyze_gongcai built
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

Batch import (CONFIRMED WORKING 2026-06-04):
- ob_header: 152 records (eolr=120: 127, eolr=60: 25)
- Seasons: FW25(20), SS25(28), FW26(50), SS26(46), SS24(4), SS23(2), FW24(2)
- Source: C:\Users\user\OneDrive\Desktop\IE (155 xlsx files, 3 skipped duplicates)
- ART/EOLR source: filename-first (fixes template copy-paste artifact in content)
  - fn_art(): first [A-Z]{2}\d{4,6} from filename
  - fn_eolr(): 120双→120, 60双→60
- CLI options: --xlsx-only --fresh (for full re-import)

ob_epph MP (CONFIRMED 2026-06-04, 152/152 records filled):
- Extracted from SUM_C2B sheet "No.of Operators" header row
- cutting / stitching / assembly / stock all > 0 for all 152 records
- Sheet selection: prefer shortest matching SUM_C2B sheet name
  (avoids "SUM.C2B 67-68" variant sheets being selected over canonical "SUM.C2B")

---

### DS-04: Production Schedule (Monthly Progress)

Type: System export, Excel, fixed format, one file per month, multiple sheets (by department)
Primary key (CONFIRMED): Department + Group + ART + Month
Table range: max 35–37 rows per sheet
Import CLI: TBD (pending Excel path and frequency)
Pending: Group vs EOLR mapping table, import frequency

File format:
- Order number format: MF2604KJ8322-03--900(5/29)
- ART: alphanumeric code extracted from order number after the "-" prefix (e.g. KJ8322)
- Order quantity: number between "--" and "("; dual-ART format → sum both quantities
- Grey cell = holiday (excluded from work-hour calculation)
- Yellow cell = model-change loss quantity

Analysis logic (CONFIRMED):
1. From schedule: extract ART + order quantity for all columns per department/group
2. ART → DS-02 FOB (Article #) → get Model Name + Cutting / Stitching / Assembly LC
3. Same group, same Model Name AND all LC values identical → merge rows, sum orders
4. LC values differ (even same Model Name) → display separately
5. ART → DS-03 OB → get MP for corresponding EOLR (Cutting / Stitching / Forming)
6. No DS-03 match → flag in red, allow manual input as final value
7. Output per group: Model Name + ART | Orders | Cutting MP | Stitching MP | Forming MP

EOLR mapping:
- Defined per department/group (Jim to provide)
- Pending: full group → EOLR table

Validation:
- 加一A group total: 15,096 PRS (confirmed correct)

---

### DS-05: 大底課進度表 (Sole Department Progress Sheet)

Type: Manual Excel file, maintained by 大底課 team
Primary key: T-group + AD-code + Month
File format:
- Column A: T-group headers (format: "T1\n5月:20人\n6月:22人")
  - Group name taken EXACTLY as written in source: T1 / T1+T2 / T1+T2+T3 etc.
- Within each T-group: rows with shoe model titles containing AD-xxxxx codes (5 digits)
- MF order cells: same format as DS-04 (MFyymmART-seq--qty(date))

Analysis logic (CONFIRMED):
1. Scan column A for T-group markers (starts with T + digit or "+")
2. Extract headcount from T-group header cell (5月:xx人, 6月:xx人)
3. Within each T-group, find all cells containing AD-xxxxx codes → model headers
4. Assign MF orders to the nearest AD-code above them (row-order)
5. Same AD-code within a T-group → merge display, sum quantities
6. ADICHILL fix: when "ADICHILL" appears without AD-code on same line,
   search 1–2 rows below for the AD-code (handles multiline/split-row format)

Result table design principle: Result tables are NEVER modified directly.
All changes must be made in the source table (來源表).

Analysis script:
- flask_backend/analyze_ds05.py
  - CLI: python analyze_ds05.py <file.xlsx> [--group T1] [--dry-run]
  - API: GET /api/ds05/analyze?file=<path>&group=<T1>
- Returns: {groups: [{group_name, headcount, models: [{ad_code, model_name, orders, total_qty}]}]}

Status: Script built ✅ | Pending: real file test + result table definition (H-L columns)

---

### DS-06 onward

Pending Jim input.

---

## 結果表設計規則（廠務組織編制表）

### 核心原則（CONFIRMED）

- **結果表不變更任何東西** — 所有變更全部在來源表作業
- T 群組名稱完全照來源表（T1+T2+T3 就顯示 T1+T2+T3，不拆開、不重命名）
- AD 代碼相同 → 合併顯示，訂單加總
- DS-03 無對應資料 → 紅字標示，手工填入為最終值（不計算）

### 四大類別架構（CONFIRMED 2026-06-04）

#### 1. CSA — 加1~加12（C2B 生產部門）

- 每個加幾（加一、加二…加十二）= 一個區塊
- 每個組別（1A / 1B / 1C…）各自顯示明細
- 每個加幾底部有總匯總（1A + 1B + 1C 合計）
- 欄位：

| 欄位 | 說明 |
|------|------|
| LEAN | 組別代號（1A / 1B…） |
| 鞋型 | Model Name + ART |
| 訂單 | 本月訂單量（來自 DS-04） |
| 裁斷 MP | DS-03 Cutting No.of Operators（依 EOLR） |
| 針車 MP | DS-03 Stitching No.of Operators（依 EOLR） |
| 成型 MP | DS-03 Assembly No.of Operators（依 EOLR） |
| 協理給 | 手工填入（預設空白） |
| 合計 | 裁斷 + 針車 + 成型 + 協理給 |
| 編制 | 取整後實際編制人數 |

#### 2. OCS — 大底課 + 固定單位

- 多個 Tab，Tab 名稱 = 單位名稱
- Tab 清單：大底課 / 組底配套 / 自動化 / 電腦針車 / 印刷 / 設備工程
- 各 Tab 內為該單位明細

**大底課 Tab：**
- 來自 DS-05（T 群組 + AD 代碼 + 訂單 + 人頭）
- 欄位：LEAN | 鞋型 | ART | 訂單 | T群組 | 人數

**固定單位欄位（直接讀廠務組織編制表）：**

| 組別 | 包含單位 |
|------|---------|
| 組底配套 | 組底倉庫、整理組、外包組、打粗組、UV/水洗組、Tổ phối liệu PXD |
| 自動化 | 同材共裁 1,2 組、自動裁斷 1,2 組、鞋墊手工組、自動化保全技術組、自動化倉庫 |
| 電腦針車 | 折邊/TGB、電腦針車/MVT、電腦針車倉庫、電腦針車保全技術組 |
| 印刷 | 高周波、印刷組、配套組、網板組、印刷房、印刷開發、加工組 |
| 設備工程 | 保全/Bảo trì、西工/bảo trì RB |

#### 3. RB

| 欄位 | 說明 |
|------|------|
| 單位 | 預備組、RB生管、RB倉庫、出半成品、模具、密練組A/B、混A/B/C組、熱A/B/C組、整理A/B/C組、技術組、硫化組 |
| 上月人數 | 唯讀，自動從上月結果帶入 |
| 本月人數 | 可修改，預設 = 上月人數 |

- 本月鎖定後自動變成下月的「上月人數」
- 上月人數不可手動修改

#### 4. QC

| 欄位 | 說明 |
|------|------|
| 單位 | OCPT、實驗室、樣品室、檢驗真皮組、檢驗副料組、收料組、底料檢驗、EVC檢驗、T2中底、T3外包、印刷高周波QC、外包QC部件、QCRB、外包RB QC、自動化中心QC、電腦針車QC、QC貼底課、外包QC貼底、QC 1-12、QC YH、品包1-3組、掃描組、貼外箱標組、QC入庫 |
| 上月人數 | 唯讀（同 RB 設計） |
| 本月人數 | 可修改，預設 = 上月 |

---

### 自檢流程（強制，每欄位都要執行）

1. 定義欄位邏輯
2. 立刻試算（用真實數據）
3. 與結果表比對
4. Jim 確認 ✅
5. 才繼續下一欄

→ 結果不一致立刻說明原因，不能跳過

---

### 工作節奏（CONFIRMED）

| 時段 | 負責 |
|------|------|
| 08:00–16:00 Vietnam time | Jim 在線：討論、決策、確認 |
| 16:00 以後 | Claude Code 後台：技術執行、批次處理 |

---

### 資料流向

```
來源表（DS-04 / DS-05 / 廠務編制表）
        ↓  讀取、計算（不回寫）
結果表（每月報告）— 四大類別：CSA / OCS / RB / QC
        ↓  唯讀，不可直接修改
```

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
- app.py v1.4: all API endpoints
- database.py: SQLite helpers + import functions (change tracking)
- schema.sql: full schema
- requirements.txt: flask, flask-cors, openpyxl
- start.bat: python -m pip install -r requirements.txt -q && python app.py
- import_ds02.py: CLI → python import_ds02.py <path> [--dry-run]
- import_ds01.py: CLI → python import_ds01.py <path> [--dry-run]
- import_ds03_batch.py: CLI → python import_ds03_batch.py <folder> [--dry-run] [--lookup-only] [--xlsx-only] [--fresh]
- analyze_ds04.py: CLI → python analyze_ds04.py <file> --dept <d> --group <g> [--eolr 120]
- analyze_ds05.py: CLI → python analyze_ds05.py <file> [--group T1] [--dry-run]
- analyze_gongcai.py: CLI → python analyze_gongcai.py <ds04.xlsx> --group 加一A組 [--eolr 120] [--dry-run]
- backup.py: CLI → python backup.py [--keep-days=30]

API endpoints:
- POST /api/ds03/save       GET /api/ds03/load    GET /api/ds03/list    DELETE /api/ds03/delete
- POST /api/ds02/upload     POST /api/ds01/upload
- GET  /api/ds02/list       GET  /api/ds01/list
- GET  /api/lookup/all      POST /api/lookup/add
- GET  /api/ds02/epph?art=  GET  /api/stats        GET /api/health
- GET  /api/ds04/analyze?file=&dept=&group=&eolr=
- GET  /api/ds05/analyze?file=&group=
- GET  /api/gongcai/analyze?file=&group=&eolr=&ie_folder=

---

## Claude Code Operating Rules

- Always start with: claude --dangerously-skip-permissions
- Standard start: cd /d D:\smartpn-atlas-core && claude --dangerously-skip-permissions
- All git/bash commands: auto-execute, never stop to ask confirmation
- Run all tasks to completion without stopping
- If Claude Code stops: Jim types 從現在開始所有指令自動執行，不要停下來問我確認，跑到所有任務完成

---

## Next Session Starting Point

1. DS-01 ✅ imported — C:\Users\user\OneDrive\Desktop\SS27 SP1 & FW26 SP7.xlsx
2. DS-02 ✅ imported — C:\Users\user\OneDrive\Desktop\FOB Price List.xlsx
3. DS-03 ✅ 152 records, ob_epph 152/152 MP filled (C/S/A/Stock)
   → Source: C:\Users\user\OneDrive\Desktop\IE
4. DS-04: Production Schedule
   → 進度表路徑: C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份正式进度表 5 30.xlsx
   → analyze_gongcai.py ✅ built — GET /api/gongcai/analyze
   → Pending: EOLR mapping table (Group → EOLR)
5. DS-05: 大底課進度表
   → Script built ✅ (analyze_ds05.py + /api/ds05/analyze)
   → 大底課進度表路徑: C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份正式贴底进度表进度表 5.16. (ĐẾ).xlsx
6. 廠務組織編制表路徑: C:\Users\user\OneDrive\Desktop\Biên chế\2026年6月份廠務组织編制_20260524.xlsx
7. 結果表設計（CONFIRMED）：
   → 四大類別：CSA（加1~加12）/ OCS（大底課+固定單位）/ RB / QC
   → 自檢流程：定義→試算→比對→Jim確認→才繼續
   → 工作時間：08:00-16:00 VN = Jim在線；16:00+ = Claude Code後台
8. 下一步：
   → 建立 analyze_result_table.py（CSA全組 + OCS大底課）
   → CSA 欄位：LEAN | 鞋型 | 訂單 | 裁斷MP | 針車MP | 成型MP | 協理給 | 合計
   → 與廠務組織編制表 6.2026 sheet 逐行比對
9. DS-06...N: Pending Jim input

---

## Instructions for Claude

- Read this file every session
- Architecture confirmed, do not re-discuss
- Continue DATA SYSTEM: start from Next Session Starting Point
- 24_DATA_SYSTEM.md: Claude outputs full content, Jim pastes via GitHub web editor
- After Jim updates GitHub: fetch raw URL to verify, then continue
