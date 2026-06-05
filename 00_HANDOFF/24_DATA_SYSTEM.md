# Data System - Internal Data Automation Project

Version: v3.0 | 2026-06-05
Status: DS-01✅ DS-02✅ DS-03✅ DS-04✅ DS-05✅ 結果表v1✅ 比對完成✅
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

ob_epph MP (CONFIRMED 2026-06-04, 326/326 records filled after Jun\IE import):
- Extracted from SUM_C2B sheet "No.of Operators" header row
- cutting / stitching / assembly / stock all > 0
- Sheet selection: prefer shortest matching SUM_C2B sheet name

Batch import (CONFIRMED WORKING 2026-06-05):
- ob_header: 326 records (original 152 + Jun\IE 174)
- Source 1: C:\Users\user\OneDrive\Desktop\IE (155 xlsx, 3 skipped duplicates)
- Source 2: C:\Users\user\OneDrive\Desktop\Biên chế\Jun\IE (Jun batch, multi-ART)
- Jun\IE import: python flask_backend/import_jun_ie.py

---

### DS-04: Production Schedule (Monthly Progress)

Type: System export, Excel, fixed format, one file per month, multiple sheets (by department)
Primary key (CONFIRMED): Department + Group + ART + Month
Table range: max 35–37 rows per sheet
File path (Jun 2026): C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份正式进度表 5 30.xlsx

Order parsing logic (CONFIRMED, implemented in analyze_result_table.py):
- Order cell format: MF2604KJ8322-03--900(5/29)
- ART: first [A-Z]{2}\d{4,6} match in cell
- Quantity: number between '--' and '('
- Dual-ART cell: split qty evenly, remainder goes to first ART
- Scan all cells in all rows of the sheet
- Sum across all occurrences of same ART within sheet

DS-04 sheets in Jun 2026: 12 sheets (加1~加12), 331 unique ARTs (after dedup across sheets)

LEAN mapping status: **PENDING** — DS-04 sheets named "1部 " etc.; ref uses 1A/1B/1C etc.
Current approach: match ART to 廠務組織編制表 ref row to determine LEAN (partial coverage)
EOLR mapping: **PENDING** — Jim to provide Group → EOLR table

---

### DS-05: 大底課進度表 (Sole Department Progress Sheet)

Type: Manual Excel file, maintained by 大底課 team
Primary key: T-group + AD-code + Month
File path (Jun 2026): C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份正式贴底进度表进度表 5.16. (ĐẾ).xlsx

Parsing logic (CONFIRMED, implemented in analyze_ds05.py):
1. Scan column A for T-group markers — format: "T1\n5月:20人\n6月:22人"
   - Group name taken EXACTLY as written (T1 / T1+T2 / T1+T2+T3 — no splitting)
   - Headcount extracted per month from same cell
2. Within each T-group: find cells containing AD-xxxxx codes (5 digits) → model headers
   - Model name = text before AD- token in same cell
3. MF orders assigned to nearest AD-code above them (row-order within T-group)
4. Same AD-code within one T-group → merge, sum quantities
5. ADICHILL fix: when "ADICHILL" appears without AD-code, look 1–2 rows below in same column

Script: flask_backend/analyze_ds05.py
- CLI: python analyze_ds05.py <file.xlsx> [--group T1] [--dry-run]
- API: GET /api/ds05/analyze?file=<path>&group=<T1>

Result table design principle (CONFIRMED):
- Result tables are NEVER modified directly
- All changes must be made in the source table (來源表)

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

### 自檢流程（強制，每欄位都要執行）— Rule 15

1. 定義欄位邏輯
2. 立刻試算（用真實數據）
3. 與結果表比對
4. Jim 確認 ✅
5. 記錄到 GitHub
6. 才繼續下一欄

→ 結果不一致立刻說明原因，不能跳過
→ 未驗證的定義不算完成。未記錄到 GitHub 的定義不存在。

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

## 比對結果（2026-06-05）

### 比對來源 vs 廠務組織編制表 6.2026 sheet

DS-04 Jun 2026: 331 unique ARTs (12 sheets)
廠務組織編制表 ref: 209 rows

差異分類（共 384 筆）：
- Type 1 ART/鞋型/訂單不一致: 68 筆
  - A. DB有MP但編制表完全找不到此ART: 2個 (IG9016 OZWEEGO J, JH6149 SAMBA GOLF)
  - B. ART在編制表有LEAN但裁/針欄位空白(DB有值): 30筆
    - 10C: 13個ART (HANDBALL SPEZIAL, SPEZIAL GOLF)
    - 5C: 12個ART (SL 72 RS 系列)
    - 12A: 1個ART (1609ER RS)
  - C. 編制表與DB均無裁/針值，差異來自成型欄位: 36筆
    - 12A: 10個ART, 5C: 19個ART, 10C: 4個ART
- Type 2 有MP但數值不一致: 132 筆 (MP邏輯未定義，暫不處理)
- Type 3 DB無MP: 184 筆 (MP邏輯未定義，暫不處理)

重要發現 (Type 1 重複比對): 7個ART+LEAN組合被比對演算法重複匹配
→ 比對腳本 compare_csa() 需優化匹配邏輯

### 非MP欄位差異 (ART層級)

進度表有/編制表無: TBD (見 result_table_v1.xlsx 非MP差異 sheet)
編制表有/進度表無: TBD (同上)

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

Scripts (all confirmed working 2026-06-05):
- app.py v1.4
- database.py
- schema.sql
- requirements.txt: flask, flask-cors, openpyxl
- start.bat
- import_ds01.py
- import_ds02.py
- import_ds03_batch.py
- import_jun_ie.py: import Jun\IE folder (multi-ART IE files)
- analyze_ds04.py: per-group analysis → /api/ds04/analyze
- analyze_ds05.py: T-group parsing → /api/ds05/analyze
- analyze_gongcai.py: 同材共裁 report → /api/gongcai/analyze
- analyze_result_table.py: CSA+OCS full result table + compare vs 廠務編制表
- build_result_table.py: build result_table_v1.xlsx (CSA+OCS+Ref+Diff sheets)
- classify_diffs.py: categorize diff_report_jim.txt into Type 1/2/3
- backup.py
- generate_comparison_table.py: ob_epph vs 廠務編制表 comparison_table.xlsx

Output files (flask_backend/test_output/):
- result_full.txt: full CSA + diff report (384 diffs)
- diff_report_jim.txt: diff section only
- result_table_v1.xlsx: Jim review Excel
- comparison_table.xlsx: 309-row MISMATCH/MISSING_IE table

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
3. DS-03 ✅ 326 records (ob_header), all MP filled
   → Source 1: C:\Users\user\OneDrive\Desktop\IE
   → Source 2: C:\Users\user\OneDrive\Desktop\Biên chế\Jun\IE
4. DS-04: Production Schedule ✅
   → 進度表路徑: C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份正式进度表 5 30.xlsx
   → 12 sheets, 331 unique ARTs
   → PENDING: EOLR mapping (Group → EOLR)
5. DS-05: 大底課進度表 ✅
   → Script built + API endpoint confirmed
   → 大底課進度表路徑: C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份正式贴底进度表进度表 5.16. (ĐẾ).xlsx
6. 廠務組織編制表路徑: C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份廠務组织編制 20260524.xlsx
7. 結果表 v1 ✅ — flask_backend/test_output/result_table_v1.xlsx
   → 4 sheets: CSA / OCS大底課 / 廠務編制表_Ref / 非MP差異
8. 已完成比對：
   → Type 1 (結構不一致): 68筆，2個ART完全找不到 (IG9016, JH6149)
   → Type 2/3 (MP差異/無MP): 316筆，等Jim確認MP分配規則後處理
9. PENDING (等Jim確認):
   → MP分配規則：DB ob_epph 是整條產線MP，廠務編制表是分配後MP，差距約2~3倍
   → LEAN對應規則：DS-04 "1部" 對應 廠務編制表哪些LEAN？
   → EOLR mapping：每個組別對應哪個EOLR？
10. Rule 15 ✅ 已加入 07_RULES.md：定義→試算→Jim確認→記錄GitHub→才繼續

---

## Instructions for Claude

- Read this file every session
- Architecture confirmed, do not re-discuss
- Continue DATA SYSTEM: start from Next Session Starting Point
- 24_DATA_SYSTEM.md: Claude outputs full content, Jim pastes via GitHub web editor
- After Jim updates GitHub: fetch raw URL to verify, then continue
