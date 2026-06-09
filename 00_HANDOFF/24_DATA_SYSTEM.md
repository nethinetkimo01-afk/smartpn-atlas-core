# Data System - Internal Data Automation Project

Version: v3.3 | 2026-06-08
Status: DS-01✅ DS-02✅ DS-03✅ DS-04✅ DS-05✅ 結果表v2✅ 比對完成✅ RB✅ QC✅
Purpose: New Claude session reads this file to continue from last point.

---

## Background

Internal data automation system for Jim's company. NOT related to SmartPN Atlas.
Jim: defines data sources and reports.
Team: daily data maintenance (data entry, file uploads).

---

## System Architecture (CONFIRMED)

Deployment: Internal LAN server
Server: One always-on office PC（24 小時運行）
Tech stack: Python + Flask + SQLite
Team size: 10人內操作，無需安裝任何軟體
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

Type: Manual input via web interface（標準化網頁界面）
**輸入方式（CONFIRMED 2026-06-08）**：歷史文件批量導入已完成，未來只用標準化網頁界面輸入，不再上傳 Excel。
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
**月度更新流程（CONFIRMED 2026-06-08）**：每月上傳 Excel → 系統自動解析 → 重複跳過 → 新增/變更才更新
Primary key (CONFIRMED): Department + Group + ART + Month
Table range: max 35–37 rows per sheet
File path (Jun 2026): C:\Users\user\OneDrive\Desktop\Biên chế\Jun\2026年6月份正式进度表 5 30.xlsx

Order parsing logic (CONFIRMED, updated 2026-06-06 in build_result_table.py _parse_order_cell + load_schedule):
- Order cell format: MF2604KJ8322-03--900(5/29) or MF2606KH8402-01-02--56-36(6/13)
- ART: all [A-Z]{2}\d{4,6} matches in cell, excluding MF-prefix codes (manufacturing order numbers)
- Quantity: sum ALL numbers between '--' and '(' (multi-lot support: 56-36 → 56+36=92)
- Multi-ART cell: split qty evenly among non-MF ARTs, remainder goes to first ART
- MF-prefix fix (2026-06-06): MF2606, MF2604 etc. are order numbers embedded in cells, NOT real ARTs

Sub-section filtering (CONFIRMED 2026-06-06):
- Some LEAN groups have sub-sections: 成型进度 / 外包鞋面 / 针车进度
- Rule: only take orders from 成型进度 section when it exists for that LEAN group
- 外包鞋面 and 针车进度 sections are always skipped
- If no section headers exist → take all orders (normal case for most LEAN groups)
- Affected in Jun 2026: 7B (成型进度 at R54) and 9C (成型进度 at R64)
- MF order number deduplication: (lean, MFyyyyARTCODE-lot) prevents double-counting
  from repeated column sets within the same sheet
- Verification: JQ0597 LEAN=7B = 5,268 ✓ (was 10,536 before fix)

DS-04 sheets in Jun 2026: 12 sheets (加1~加12), 331 unique ARTs (after dedup across sheets)

LEAN mapping status: **CONFIRMED 2026-06-05** — 從 DS-04 組別標題行直接解析
- 格式：加一A组 → 1A、加十一A1组 → 11A1、加十二D组 → 12D
- 邏輯：去掉「加」和「组」→ 中文數字轉阿拉伯數字（一=1...十二=12）→ 保留英文字母和尾端數字
- 實作：build_result_table.py `_parse_lean_title()` + `load_schedule()` 中 `art_lean` 欄位
- 跨部門共用 ART：同一 ART 可出現在多個 DS-04 部門（正常業務），各部門各自顯示各自 LEAN
- 114 筆 LEAN 不符廠務表 = 跨部門共用 ART / 廠務表 LEAN 指派不同 → 已確認不處理
EOLR mapping: **PENDING** — Jim to provide Group → EOLR table

---

### DS-05: 大底課進度表 (Sole Department Progress Sheet)

Type: Manual Excel file, maintained by 大底課 team
**月度更新流程（CONFIRMED 2026-06-08）**：每月上傳 Excel → 系統自動解析 → 重複跳過 → 新增/變更才更新
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

## 比對結果（2026-06-06 UPDATED v2，_parse_order_cell 修正後）

### 非MP欄位比對 — result_table_v2.xlsx / auto_bianche.xlsx vs 廠務組織編制表 6.2026

DS-04 Jun 2026: 15 sheets, 432 ARTs（MF-prefix codes 已排除）
auto_bianche CSA 行數: 435（(sheet, lean, art) 各自獨立）
廠務組織編制表 ref: 313 ART

**_parse_order_cell 修正（2026-06-06）**：
- 多製令格式 `--56-36(6/13)` 現在正確加總 → 92（舊邏輯只取 56）
- MF-prefix 碼排除於 ART 清單（舊邏輯錯誤地將 MF2606 等當成獨立 ART）
- 修正後 KH8402 LEAN=1A 訂單量 = 756 ✓（修正前 = 109）

**LEAN 比對（auto_bianche vs 廠務，雙方都有的 ART）**

| 項目 | 筆數 |
|------|------|
| LEAN 一致 ✓ | 303 |
| LEAN-跨部門 | 112 | (同ART出現多個DS-04部門，廠務只記一個LEAN) |
| LEAN-指派差異 | 6 | (ART僅在一個DS-04部門，但廠務LEAN不同) |
| ART auto有/廠務無 | 13 |
| ART 廠務有/auto無 | 1（JS1068，LEAN=7A） |

**結論：118 筆 LEAN 不符 = 業務差異，不處理**
- 廠務表 LEAN 是計畫分配，DS-04 是實際排程，可以不同
- 跨部門共用 ART 是正常安排（例如 KZ9155 同時在 8 個部門排產）

**OCS 5 Tab（CONFIRMED 2026-06-05）**

| Tab | 單位數 | 狀態 |
|-----|--------|------|
| OCS_組底配套 | 6 | ✓ 100% 一致 |
| OCS_自動化 | 5 | ✓ 100% 一致 |
| OCS_電腦針車 | 4 | ✓ 100% 一致 |
| OCS_印刷 | 7 | ✓ 100% 一致 |
| OCS_設備工程 | 2 | ✓ 100% 一致 |

**RB / QC Tab（CONFIRMED 2026-06-05）**

| Tab | 單位數 | 資料來源 |
|-----|--------|---------|
| RB | 15 | 廠務組織編制表 RB section（R398-R415） |
| QC | ~47 | 廠務組織編制表 QC section（R417-R464） |

欄位：單位 / 上月人數（col13，灰底唯讀）/ 本月人數（col15，白底可修改）

**當前版本：result_table_v2.xlsx**
- 路徑：flask_backend/test_output/result_table_v2.xlsx
- Sheets：CSA / OCS大底課 / OCS_組底配套 / OCS_自動化 / OCS_電腦針車 / OCS_印刷 / OCS_設備工程 / RB / QC / 廠務編制表_Ref / 非MP差異
- 比對報告：flask_backend/test_output/full_compare_report.txt

---

## 設計教訓（2026-06-08）

### Rule 20 教訓：先看製令明細，再比對總量

**事件**：HP4218 8B — DS-04 有 12 張製令合計 7,247，廠務只登 172，差異 +7,075（42x）。

**根本原因**：廠務表漏登了 11 張製令，只登了最小一張（MF2605HP4218-04 = 135 或 MF2605HP4218-07 = 26 附近的值）。最大一張 MF2604HP4218-31 = 4,450 完全沒登。

**教訓**：
- 若先設計製令明細表（每張製令一行），第一眼就能看到哪張製令漏登
- 直接比對總量只顯示差異數字，看不到哪張製令造成的差異
- Rule 20：新數據源 → 先讀說明表 → 設計明細表 → Jim 確認 → 才開始取值

**製令明細表現狀**：
- 位置：auto_bianche.xlsx Sheet 2「製令明細」
- 欄位：LEAN | 製令號碼 | ART | 鞋型 | 段落 | DS-04訂單量 | 交期 | 廠務訂單 | 差異
- 差異標示：>20% 或 >50 對 → 紅色（FFCCCC）；任何差異 → 黃色（FFF2CC）
- 總計 1,367 筆個別製令記錄（含成型进度 + 外包鞋面，不含针车进度）

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
- build_result_table.py: build result_table_v2.xlsx (CSA+OCS+RB+QC+Ref+Diff sheets)
  - load_schedule(): DS-04 → LEAN from group titles (加一A组→1A)
  - load_bianche_structure(): 廠務編制表 CSA ref rows
  - load_ocs_fixed_units(): 廠務編制表 OCS 5 fixed sections
  - load_rb_qc_units(): 廠務編制表 RB/QC sections (col13=上月, col15=本月)
  - build_csa(): CSA tab with DS-04 LEAN assignment
  - build_ocs_fixed_tab(): one tab per OCS section
  - build_rb_qc_tab(): RB and QC tabs (上月人數唯讀, 本月人數可修改)
- build_v2.py: standalone rebuild script (handles locked file via temp copy)
- auto_compare.py: post-build comparison, outputs compare_result.txt
- full_compare_report.py: row-by-row comparison with reason classification
- column_compare_report.py: 鞋型/ART/訂單 欄位比對，分類邏輯差異 vs 人為差異
- generate_bianche.py: 從DS-04自動產生廠務組織編制表 (auto_bianche.xlsx)
  - Sheet 1: MONTH_SH — 主表（LEAN/鞋型/ART/訂單，MP留空）
  - Sheet 2: 製令明細 — 每張製令一行（製令號碼/ART/鞋型/段落/DS-04訂單量/交期/廠務訂單/差異），差異>20%標紅
- bianche_diff.py: auto_bianche.xlsx vs 廠務表逐欄比對，輸出 bianche_diff.txt
- classify_diffs.py: categorize diff_report_jim.txt into Type 1/2/3
- backup.py
- generate_comparison_table.py: ob_epph vs 廠務編制表 comparison_table.xlsx

Output files (flask_backend/test_output/):
- result_table_v2.xlsx: current result Excel (11 sheets)
- auto_bianche.xlsx: DS-04自動產生廠務組織編制表（LEAN/ART/訂單填入，MP留空）
- compare_result.txt: auto_compare summary
- full_compare_report.txt: detailed row-by-row comparison with reason classification
- column_compare_report.txt: 鞋型/ART/訂單 欄位比對報告（分類邏輯差異 vs 人為差異）
- bianche_diff.txt: auto_bianche vs 廠務表差異分析
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
7. 結果表 v2 ✅ — flask_backend/test_output/result_table_v2.xlsx
   → 11 sheets: CSA / OCS大底課 / OCS_組底配套 / OCS_自動化 / OCS_電腦針車 / OCS_印刷 / OCS_設備工程 / RB / QC / 廠務編制表_Ref / 非MP差異
   → LEAN 來自 DS-04 組別標題（加一A组→1A），已確認
   → OCS 5 Tab 100% 一致，已確認
   → RB 15單位 / QC ~47單位，已建立（上月/本月人數欄位）
8. 比對報告 ✅ — flask_backend/test_output/full_compare_report.txt
   → LEAN一致 301筆 / 不符 114筆（正常業務差異，不處理）
   → ART DS04有廠務無 17筆，廠務有DS04無 1筆（JS1068）
9. PENDING (等Jim確認):
   → MP分配規則：DB ob_epph 是整條產線MP，廠務編制表是分配後MP，差距約2~3倍
   → EOLR mapping：每個組別對應哪個EOLR？
10. Rule 15 ✅ 已加入 07_RULES.md：定義→試算→Jim確認→記錄GitHub→才繼續

---

## Instructions for Claude

- Read this file every session
- Architecture confirmed, do not re-discuss
- Continue DATA SYSTEM: start from Next Session Starting Point
- 24_DATA_SYSTEM.md: Claude outputs full content, Jim pastes via GitHub web editor
- After Jim updates GitHub: fetch raw URL to verify, then continue

## 最新執行結果

**執行時間**：2026-06-09 08:39

### 各任務狀態

| 任務 | 狀態 |
|------|------|
| T0 檔案版本檢查 | ✅ ok |
| T1 IE 全面掃描 | ❌ error: no such column: h.model |
| T2 comparison_table.xlsx | ❌ error |
| T3 MP 分配分析 | ✅ ok |
| T4 LEAN/OCS 比對 | ✅ ok (差異: LEAN不符=134 缺=14) |
| T6 IE 補充掃描 | ❌ error: no such column: h.model |
| T7 自動表+diff+MD更新 | ✅ ok (人為差異=32) |

### LEAN / OCS 比對摘要

| 項目 | 數值 |
|------|------|
| LEAN 一致 | 282 筆 |
| LEAN 不符 | 134 筆（跨部門業務差異，不處理） |
| ART DS04有/廠務無 | 14 筆 |
| ART 廠務有/DS04無 | 14 筆 |
| OCS 固定單位 | ✓ 5 Tab 100% 一致 |

### bianche_diff — auto_bianche.xlsx vs 廠務組織編制表

| 項目 | 數值 |
|------|------|
| 訂單 一致 | 39 筆 |
| 訂單 邏輯差異(廠務合批) | 211 筆（非錯誤） |
| **訂單 人為差異** | **32 筆** ← 需 Jim 確認 |
| auto有/廠務無 ART | 10 筆 |
| 廠務有/auto無 ART | 14 筆 |

### 需要 Jim 確認的事項

- EOLR mapping：每個組別對應哪個 EOLR？（PENDING）
- MP 分配規則：DB ob_epph 整條產線 MP vs 廠務編制表分配後 MP，差距約 2~3 倍（PENDING）
- DS04 有/廠務無 ART **14** 筆 — 是否需補登廠務編制表？
- 廠務有/DS04 無 ART **14** 筆（JS1068, LEAN=7A）— 廠務表是否刪除？
