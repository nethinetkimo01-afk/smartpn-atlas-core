# SmartPN Atlas ??Universal Rules for All Claude Sessions
Version: v2.0 | 2026-06-01
Status: MANDATORY. Any Claude in any session must follow these rules independently.
Purpose: Every Claude session can operate without going back to the original session.

---

## Rule 1: GitHub is the Only Memory

Claude has no memory between sessions.
GitHub is the only persistent memory.
If it is not in GitHub, it does not exist.

---

## Rule 2: Save Immediately After Every Confirmed Decision

When Jim confirms anything:
1. Write a .ps1 file immediately
2. Give Jim the download link
3. Jim executes the .ps1
4. Push with this command:
   cd /d D:\smartpn-atlas-core && git add . && git commit -m "description" && git push https://github.com/nethinetkimo01-afk/smartpn-atlas-core.git main
5. Confirm push success before moving on

Never say "already recorded" without a successful GitHub push.
Never wait until end of session to save.
One decision = one push.

---

## Rule 3: Update 21_CURRENT_STATUS.md at Session End

Before Jim closes any session:
1. Update 21_CURRENT_STATUS.md with:
   - What was completed this session
   - Confirmed decisions made
   - Next steps in priority order
   - Any pending items
2. Push to GitHub
3. Confirm success

This file is what the next Claude reads first.

---

## Rule 4: Never Write Secrets in GitHub Files

Never write in any GitHub file:
- GitHub Personal Access Token
- Claude API keys
- Any passwords or credentials

If a key is needed, write: "stored separately, do not write in any file"

---

## Rule 5: New Project = New File in GitHub

Every new project or topic gets its own file in 00_HANDOFF/.
File naming: sequential number + project name
Example: 24_NEW_PROJECT.md

File must contain:
- Project goal
- Confirmed decisions
- Current status
- Next steps

---

## Rule 6: Any Claude Session Can Operate Independently

Any Claude in any session that reads these rules can:
- Continue Jim's work without asking Jim to re-explain
- Save confirmed decisions to GitHub independently
- Update current status at session end
- Hand off to the next session cleanly

If a Claude session cannot do this after reading all files ??it has not read the files properly.

---

## Rule 7: Execute, Test, Confirm, Then Report

Claude executes ??tests ??confirms success ??reports to Jim.
Never wait for Jim to verify.
Never report before confirming success.
Never apologize after failure ??fix and report the result.

---

## Rule 8: Session Start Protocol

1. Read ALL files listed in 00_ENTRY_POINT.md
2. Answer all 5 verification questions
3. Report current status from 21_CURRENT_STATUS.md
4. Begin work

If unable to answer verification questions ??re-read files.
Do not begin work until all 5 questions are answered correctly.

---

## Rule 9: Tool Assignment

Claude = central brain (analyze, discuss, break down, assign)
ChatGPT = image generation
Codex = code, PPT refinement
Make = automation execution
GitHub = single source of truth

Never do in Claude what another tool does better.
Never centralize all work in one session.

---

## Rule 10: Jim's Rule Philosophy

For organization and tools: rules are to be followed strictly.
For Jim: rules are made to be broken when he sees further.
When Jim moves in a new direction ??follow him, do not remind him of old rules.
Track Jim's thinking direction, not his exact words.

---

## GitHub Repo Information

Repo: https://github.com/nethinetkimo01-afk/smartpn-atlas-core
Files location: D:\smartpn-atlas-core\00_HANDOFF\
Push command template:
cd /d D:\smartpn-atlas-core && git add . && git commit -m "MESSAGE" && git push [use your GitHub token] main
