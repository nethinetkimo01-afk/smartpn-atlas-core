# SmartPN Atlas ??Master Entry Point
Version: v3.0 | 2026-06-01
Status: MANDATORY. Read ALL files before starting any work.

---

## Data Architecture

GitHub repo: https://github.com/nethinetkimo01-afk/smartpn-atlas-core
All files in: 00_HANDOFF/
This is the ONLY source of truth. All sessions read from here. All sessions write back here.

---

## File Index (Read in Order)

### Layer 1 ??Rules and Identity (Read First, Every Session)
01_CONSTITUTION.md ??product positioning, naming, four principles
07_RULES.md ??universal rules for all Claude sessions
18_WORKING_MODEL.md ??Claude role, Jim rule philosophy, execution standard
19_JIM_EXTERNAL_PERSONA.md ??external positioning boundaries, what we are NOT

### Layer 2 ??Current State (Read Second, Every Session)
21_CURRENT_STATUS.md ??where we stopped, next steps, pending items

### Layer 3 ??Project Files (Read Based on Today's Work)
11_DESIGN_SYSTEM.md ??visual system PPT Demo LinkedIn
12_AVATAR_AND_LINKEDIN.md ??avatar features, LinkedIn image system
13_LINKEDIN_CONTENT_SYSTEM.md ??CEO communication, article structure
14_S01_LINKEDIN_POST.md ??S01 confirmed post and workflow
16_S02_TO_S17_COMPLETE_SPECS.md ??all scenario specs
17_PPT_DESIGN_RULES.md ??universal PPT design rules
20_GTM_STRATEGY.md ??outreach intelligence, key people map
22_WRITING_RULES.md ??hooks, ALL CAPS, logic chain, CEO perspective
23_OUTREACH_AUTOMATION.md ??Make automation, keywords, Google Sheet
25_PARTNER_OUTREACH_STRATEGY.md — system partner positioning, target list, outreach logic, commercial model options
26_S01_DEMO_LOGIC.md — S01 demo logic, PPT animation, table structure
27_SMARTPN_LAYER_DEFINITION.md — SmartPN layer definition, MSDG positioning, industry stack (placeholder — Jim 尚未提供)
28_DEMO_MENU_STRUCTURE.md — Phase 1 Demo SaaS sidebar (18 items) + Formal Demo B sidebar (7 items), source file paths, version comparison
29_OUTREACH_WORK_PACKAGE.md — intelligence reports, Kate final, GTS note, GATE analysis, S02 LinkedIn draft
30_DEMO_INTERFACE_SPEC_DRAFT.md — demo interface spec draft, pending Jim review (A-H sections)
31_DEMO_INTERFACE_SPEC_v1.md — demo interface spec v1.0, CONFIRMED by Jim 2026-06-12 (replaces 30)
33_DEMO_SPEC_v1_2_ADDENDUM.md — v1.2 addendum: Boss BI 8 KPIs, "who viewed" privacy, role test items, CONFIRMED 2026-06-12
34_MASTER_WORK_ORDER.md — 總工單 2026-06-12 v1.0: Jim 授權 Claude 全權安排，Code 執行順序與任務清單
36_UX_TEST_AND_BOSS_DEMO_SCRIPT.md — 三角色測試腳本 + Boss 演示腳本 v1.0 (2026-06-13): Jim 走一遍 Demo 即可驗收
37_DEMO_MOCK_DATA.md — Demo 唯一數據世界 v1.0 (2026-06-13): 12材料/4供應商/Boss BI 數字，Brand端+Supplier端共用同一套
### Layer 4 — Demo Screens (Read When Working on Demo)
docs/preview/S01_DEMO.html through S17_DEMO.html — interactive demo screens for all 17 scenarios
### Layer 5 — New Projects (Add as Needed)
24_[PROJECT_NAME].md ??any new project gets its own file

---

## Mandatory Verification Test (All 5 Must Be Answered Before Work Begins)

Q1: Jim's rules ??difference between organization vs Jim himself?
Q2: Claude's role ??what is it? what is it NOT?
Q3: Top 3 pending tasks right now (from 21_CURRENT_STATUS.md)?
Q4: Jim's external persona boundary ??3 things SmartPN Atlas is NOT?
Q5: Writing rules ??how are key words handled? What is the logic chain order?

---

## Session Start Protocol

1. Read Layer 1 files (always)
2. Read Layer 2 file (always)
3. Read Layer 3 files relevant to today's work
4. Answer all 5 verification questions
5. Report: current status in 2-3 sentences
6. Begin work

---

## Session End Protocol

1. Update 21_CURRENT_STATUS.md with:
   - What was completed
   - Confirmed decisions
   - Next steps in priority order
2. Save any new project files
3. Push all changes to GitHub
4. Confirm push success
5. Session can close

---

## Save Protocol (Any Session, Any Time)

When Jim confirms any decision:
1. Write content to appropriate file in 00_HANDOFF/
2. Generate .ps1 script for Jim to execute
3. Jim runs: powershell -ExecutionPolicy Bypass -File [script]
4. Jim pushes: cd /d D:\smartpn-atlas-core && git add . && git commit -m "description" && git push [token]@github.com/nethinetkimo01-afk/smartpn-atlas-core.git main
5. Confirm success before moving on

NEVER write tokens or API keys in any GitHub file.
NEVER say "already saved" without a confirmed push.

---

## New Project Protocol

Any new project or topic:
1. Create new file: 00_HANDOFF/24_[PROJECT_NAME].md (or next number)
2. File must contain: goal, confirmed decisions, current status, next steps
3. Add file to this index under Layer 4
4. Push immediately

Any Claude session can pick up any project by reading its file.
No explanation from Jim needed.
