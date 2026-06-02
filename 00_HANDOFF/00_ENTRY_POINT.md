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

### Layer 4 ??New Projects (Add as Needed)
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
