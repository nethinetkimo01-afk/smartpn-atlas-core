# Data System - Internal Data Automation Project

Version: v1.3 | 2026-06-02
Status: DS-01 DS-02 confirmed, DS-03 field analysis complete
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
Sheets per file: SUM, Cutting, Stitching (main + sub flows), Assembly 1+2, SUM_Stock

Header info (comes from separate import file - TBD):
- Season, Model name, ART, Material, Category, EOLR

#### Cutting Sheet Fields

| Field | Source |
|-------|--------|
| STT (seq no) | Auto-generated |
| Material category | Manual input |
| Part name (部件名稱) | Manual input |
| No. of layers | Manual input |
| Qty of parts (prs) | Manual input |
| Standard knives/H | Manual input |
| Allowance (10%) | Preset = 10, manual override |
| Cycle time (D) | Manual input |
| Standard time (F) | Formula: D x 1.1 |
| Target output (G) | Formula: 3600 / F |
| Operators theory (H) | Formula: F / EOLR |
| Operators actual (I) | Manual input |
| Machine name (J) | Manual input |
| Remarks | Manual input |

Summary row (auto-calculated):
- Total TCT = SUM of all standard time
- Total operators = SUM machine operators + manual operators

#### Stitching Sheet Fields (same as Cutting, no Material category column)

| Field | Source |
|-------|--------|
| STT | Auto-generated |
| Part name | Manual input |
| Cycle time (D) | Manual input |
| Allowance (E) | Preset = 10 |
| Standard time (F) | Formula: D x 1.1 |
| Target output (G) | Formula: 3600 / F |
| Operators theory (H) | Formula: F / EOLR |
| Operators actual (I) | Manual input |
| Machine name (J) | Manual input |
| Machine qty (K) | Manual input |
| Remarks | Manual input |

#### Assembly Sheet Fields (same as Stitching)

| Field | Source |
|-------|--------|
| STT | Auto-generated |
| Part name | Manual input |
| Cycle time (D) | Manual input |
| Allowance (E) | Preset = 10 |
| Standard time (F) | Formula: D x 1.1 |
| Target output (G) | Formula: 3600 / F |
| Operators theory (H) | Formula: F / EOLR |
| Operators actual (I) | Manual input |
| Machine name (J) | Manual input |
| Machine qty (K) | Manual input |
| Remarks (L) | Formula: capacity calculation |

#### SUM Sheet (auto-calculated from all sheets)

| Field | Source |
|-------|--------|
| Season | From header import |
| Model name | From header import |
| ART | From header import (join key) |
| Material | From header import |
| Category | From header import |
| EOLR | From header import |
| Cutting operators | From Cutting sheet summary |
| Stitching operators | From Stitching sheet summary |
| Assembly operators | From Assembly sheet summary |
| Stockfitting operators | From SUM_Stock sheet |
| TCT per section | Manual input |
| PPH | Formula: EOLR / operators |
| Remarks | Manual input |

#### UI Requirement
Web interface must visually match existing Excel layout exactly.
Same position, font style, structure. Team fills data in corresponding cells.
System auto-calculates formula fields.

#### Primary Key (CONFIRMED)
ART + Season + Run number (Lan 1, Lan 2...)

#### Header Import File
Pending: Jim will provide format later.

---

### DS-04 onward

Pending Jim input.

---

## Cross-table Relationships

DS-02 Article # = DS-01 Article ID (join key)
DS-03 ART = DS-02 Article # (join key)
Other relationships TBD

---

## Next Session Starting Point

1. Design DS-03 web input interface (visual match to Excel)
2. Jim to provide header import file format
3. Process historical Excel files -> import to standard format
4. Continue DS-04...N definition

---

## Instructions for Claude

- Read this file every session
- Architecture confirmed, do not re-discuss
- Continue DATA SYSTEM: start from Next session starting point
- New decision confirmed: output full file content, Jim updates via GitHub web editor
