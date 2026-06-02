# Data System - Internal Data Automation Project
Version: v1.2 | 2026-06-02
Status: Architecture confirmed, defining data sources
Purpose: New Claude session reads this file to continue from last point.
---
## Background
This is Jim's company internal data automation system. NOT related to SmartPN Atlas.
Jim: defines data sources and report requirements.
Team: daily data maintenance.
---
## System Architecture (CONFIRMED)
Deployment: Internal LAN server
Server: One always-on office PC
Tech stack: Python + Flask + SQLite
Team access: Browser via LAN URL, no software needed
---
## Core Mechanisms (CONFIRMED)
Dedup and change tracking:
- Each data source has its own primary key (Jim defines separately)
- New record: write to master table, no log
- Existing record with changes: update master + log all changed fields (old value, new value, field name, timestamp)
- Exact duplicate: skip
Field matching: Always use field NAME not position.
Backup: Daily automatic backup of full SQLite database, stored in separate folder, retention days TBD
Report mechanism:
- Fixed reports: Jim-approved, shown as tabs, auto-updated
- Exploratory pivot: Jim freely pivots data, promotes to fixed report when satisfied
- UI: multi-tab, pivot (field/dimension/aggregation), one-click promote
---
## Data Source Registry
### DS-01: SP (Season Plan)
Sheet: {Season} SP{N}-EVM (e.g. FW26 SP7-EVM)
Type: System export, Excel (.xlsx), fixed format
Size: ~6,383 rows x 76 columns
Fields:
- Product ID: RecordID, Article ID, Article DESC, Model
- Supply chain: GT1 FSC/Code, RT1 FSC/Code, GT1 LO, GT1 Group, GT1 COO
- Product attributes: Division, Product Type DESC, Gender, Construction type, Technology Concept
- Market: Market Group, Market (level 1~3), Forecast Customer Description, Forecast Customer No
- Time: Marketing Season, Production Season, Calendar Month, CRD Month
- Quantity: Metric, Total, Offered Capacity
Primary key (CONFIRMED): Article ID + Product Type DESC + Calendar Month
Quantity field: Total (sum)
Field matching: by name, not position
Pending: Analysis requirements, import frequency
---
### DS-02: FOB Price List
Type: System export, Excel (.xlsx), fixed format
Size: ~4,193 rows x 30 columns
Fields:
- Product ID: Model #, Model Name, Silhouette Number(Upper ID), Article #
- Factory, Season, Category
- Tooling: O/S Tooling, EVA M/S Tooling
- Cost: LC Total, LC CTB, Cutting, Stitching, Stockfitting, Assembly
- Cost(S): LC Total(S), LC CTB(S), Cutting(S), Stitching(S), Stockfitting(S), Assembly(S)
- Other: Stage, Valid From, LC Treatments, Shoe Construction, Remark
- Audit: Created By, Created Date, Modified By, Modified Date
Primary key (CONFIRMED): Article # (ART) - also cross-table join key
Change tracking: ALL fields
Change detected: update master + log all changed fields (old, new, field name, timestamp)
Field matching: by name, not position
Pending: Analysis requirements, import frequency
---
### DS-03 onward
Pending Jim input
---
## Cross-table relationships
DS-02 Article # = DS-01 Article ID (join key)
Other relationships TBD
---
## Next session starting point
1. Continue collecting DS-03...N
2. Jim defines analysis needs / fixed reports per data source
3. After all sources defined: design import UI and server architecture
---
## Instructions for Claude
- Must read this file at start of every session
- Architecture confirmed, do not re-discuss
- Jim says "continue DATA SYSTEM": start from Next session starting point
- New decision confirmed: write out full file content, Jim updates via GitHub web editor
