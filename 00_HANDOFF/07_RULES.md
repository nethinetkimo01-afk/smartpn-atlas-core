# SmartPN Atlas — Universal Rules for All Claude Sessions
Version: v2.0 | 2026-06-01
Status: MANDATORY. Any Claude in any session must follow these rules independently.

## FIRST ACTION IN EVERY NEW SESSION
Before doing ANYTHING else:
1. Read this file completely
2. Read 21_CURRENT_STATUS.md
3. Answer the 5 verification questions from 00_ENTRY_POINT.md
4. Only then begin work
5. After every confirmed decision — save to GitHub immediately

## Rule 1: GitHub is the Only Memory
Claude has no memory between sessions.
GitHub is the only persistent memory.
If it is not in GitHub, it does not exist.

## Rule 2: Save Immediately After Every Confirmed Decision
When Jim confirms anything:
1. Write content to appropriate file in 00_HANDOFF/
2. Generate .ps1 script for Jim to execute
3. Jim executes the .ps1
4. Jim pushes to GitHub
5. Confirm push success before moving on

Never say "already recorded" without a confirmed GitHub push.
Never wait until end of session to save.
One decision = one push.

## Rule 3: Update 21_CURRENT_STATUS.md at Session End
Before Jim closes any session:
1. Update 21_CURRENT_STATUS.md with what was completed, confirmed decisions, next steps
2. Push to GitHub
3. Confirm success

## Rule 4: Never Write Secrets in GitHub Files
Never write API keys, tokens, or passwords in any GitHub file.
If a key is needed, write: "stored separately, do not write in any file"

## Rule 5: New Project = New File in GitHub
Every new project gets its own file: 00_HANDOFF/[number]_[PROJECT_NAME].md
File must contain: goal, confirmed decisions, current status, next steps.

## Rule 6: Any Claude Session Can Operate Independently
Any Claude that reads these rules can continue Jim's work without asking Jim to re-explain.

## Rule 7: Execute, Test, Confirm, Then Report
Claude executes → tests → confirms success → reports to Jim.
Never wait for Jim to verify. Never report before confirming success.

## Rule 8: Session Start Protocol
1. Read ALL files in 00_ENTRY_POINT.md
2. Answer all 5 verification questions
3. Report current status from 21_CURRENT_STATUS.md
4. Begin work

## Rule 9: Tool Assignment
Claude = central brain
ChatGPT = image generation
Codex = code, PPT refinement
Make = automation execution
GitHub = single source of truth

## Rule 10: Jim's Rule Philosophy
For organization and tools: rules are to be followed strictly.
For Jim: rules are made to be broken when he sees further.
When Jim moves in a new direction — follow him, do not remind him of old rules.
