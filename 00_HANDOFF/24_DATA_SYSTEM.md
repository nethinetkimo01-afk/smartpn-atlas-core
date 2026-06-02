# Data System - Internal Data Automation Project

Version: v1.4 | 2026-06-02
Status: DS-01 DS-02 confirmed, DS-03 design complete
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
Pending: Analysis requirements, import frequency

---

### DS-03: IE/LC Operation Breakdown (OB)

Type: Manual input via web interface (replaces Excel entry)
File format: One Excel file per style per production run
Primary key (CONFIRMED): ART + EOLR + Run number (Lan 1, Lan 2...)

Note: Same ART with different EOLR (60/120/150) = separate records.
Parts, CT, layers do not change across EOLR.
MP (operators) changes per EOLR. PPH = EOLR / MP (changes with MP).

#### Navigation Structure (CONFIRMED)

Layer 1 (main tabs - READ ONLY):
- SUM_C2B: auto-aggregated from all C2B sub-sheets
- SUM_Stock: auto-aggregated from all Stock sub-sheets

Layer 2 - under SUM_C2B:
- Cutting, ATOM/自动化, 同材共裁, 电脑针车, Stitching 支流, Stitching 主流, Assembly 1, Assembly 2

Layer 2 - under SUM_Stock:
- 打粗, 水洗, 贴大底, 照射, 成型面照射

Rule: To change any number -> go to sub-sheet -> edit -> SUM auto-updates.

#### SUM_C2B Fields (ALL READ ONLY)

| Field | Source |
|-------|--------|
| 部門 | Fixed |
| MP (operators) | Aggregated from sub-sheets |
| PPH | Formula: EOLR / MP |
| E-PPH | From DS-02 FOB: LC Cutting/Stitching/Assembly/Stockfitting -> converted to E-PPH |
| Diff PPH | Formula: E-PPH - PPH |
| Eff% | Formula: PPH / E-PPH x 100% |

Cross-table: DS-03 ART -> DS-02 Article # -> get LC values -> calculate E-PPH

#### Cutting Sheet Fields

Row 1 (full width): Material category | Part name Việt (team input) | 部件名稱 中文 (auto lookup)
Row 2 (data): Layers | Qty/Pr | Std Knives/H | CT (manual) | Allowance% | Std Time (formula) | Actual Ops (manual)
Additional process columns: Marking | Skiving | Attaching | Edge Paint | Heat Press

| Field | Source |
|-------|--------|
| STT | Auto-generated |
| Material category (材料類別) | Manual input |
| Part name Việt (Tên phối kiện) | Manual input by team |
| Part name 中文 | Auto from Viet-Chinese lookup table |
| Layers (层数) | Manual input |
| Qty/Pr (片数) | Manual input |
| Std Knives/H (刀数) | Manual input |
| Cycle Time CT (正常時間) | Manual input |
| Allowance% (寬放率) | Preset 10%, manual override |
| Standard Time ST (標准時間) | Formula: CT x 1.1 |
| Actual Operators (裁机人数) | Manual input |

Summary row (auto):
- Total CT, Total ST = SUM of all rows
- Total Ops = SUM of actual operators

#### Stitching Sheet Fields (same as Cutting, NO Material category column)
#### Assembly Sheet Fields (same as Stitching)

#### Vietnamese-Chinese Part Name Lookup Table (INDEPENDENT BASE TABLE)

- NOT part of DS series
- Team inputs Vietnamese -> system auto-fills Chinese
- Used across all sub-sheets (Cutting, Stitching, Assembly, etc.)
- Initial data: extracted from historical Excel files uploaded by Jim
- Will grow as more files are processed

#### Header Import File

Fields: Season, Model name, ART, Material, Category, EOLR
Source: Separate import file (Jim will provide format later)

---

### DS-04 onward

Pending Jim input.

---

## Cross-table Relationships

DS-02 Article # = DS-01 Article ID (join key)
DS-03 ART = DS-02 Article # (join key)
DS-03 E-PPH sourced from DS-02 LC Cutting/Stitching/Assembly/Stockfitting fields
Other relationships TBD

---

## Next Session Starting Point

1. Complete DS-03 web interface: Stitching, Assembly tabs
2. Build SUM_C2B auto-aggregation logic
3. Extract Viet-Chinese part name lookup from historical Excel files
4. Process all uploaded historical Excel files -> import to standard format
5. Continue DS-04...N definition

---

## Instructions for Claude

- Read this file every session
- Architecture confirmed, do not re-discuss
- Continue DATA SYSTEM: start from Next session starting point
- New decision confirmed: output full file content, Jim updates via GitHub web editorontent, Jim updates via GitHub web editor
