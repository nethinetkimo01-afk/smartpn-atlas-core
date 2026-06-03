# Current Status

Last updated: 2026-06-02

---

## DATA SYSTEM Project

File: 00_HANDOFF/24_DATA_SYSTEM.md (v1.4)

### Completed Today
- System architecture confirmed: LAN Server + Python Flask + SQLite
- DS-01 SP: primary key confirmed
- DS-02 FOB Price List: primary key confirmed
- DS-03 OB interface: design complete, Claude Code building
- ds03_ob_interface.html v1.2: SUM_C2B + SUM_Stock auto-aggregation done
- Rule 11 added to 07_RULES.md v2.2
- Claude Code installed and active

### Claude Code In Progress
- Task: push ds03_ob_interface.html to GitHub
- Task: extract Viet-Chinese part name lookup from historical Excel files
- Task: batch import script for 300-400 historical OB Excel files
- Location: D:\smartpn-atlas-core

### Next Session Starting Point
1. Confirm Claude Code completed tasks above
2. Define DS-04...N data sources
3. Define report requirements
4. Define Flask backend + SQLite structure
5. Historical OB files folder path: TBD (Jim to provide)

---

## SmartPN Atlas Project

Make Automation: ACTIVE
Google Sheet: https://docs.google.com/spreadsheets/d/1i9WgKNj5-ueNrP5ZCit9Cghug0BL2bJ_hbOSoSQchXU

Next Steps:
1. Jim reviews Google Sheet daily results
2. Send Kate Nishimura draft
3. S02 PPT final confirmation
4. Continue S03-S17 PPT

---

## Tool Assignment

| Tool | Responsibility |
|------|---------------|
| Claude (chat) | Design, analysis, DS definition, report requirements |
| Claude Code | Code, file operations, batch processing, backend |
| GitHub | Single source of truth |
| Make | Automation execution |not write in any filey, do not write in any file

## Claude Code Operating Rules

- All git and bash commands: auto-execute, never stop to ask confirmation
- Use: Yes, and don't ask again for this session (shift+tab) on first prompt
- Run all tasks to completion without stopping
- If Claude Code stops waiting for input, Jim types: 從現在開始所有指令自動執行，不要停下來問我確認，跑到所有任務完成
- Never ask Jim to verify intermediate steps
