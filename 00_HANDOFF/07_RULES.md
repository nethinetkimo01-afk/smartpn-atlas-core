# SmartPN Atlas Operating Rules

Version: v2.5 | 2026-06-05

## Session Start Protocol

Before doing ANYTHING else:
1. Read this file completely
2. Read 21_CURRENT_STATUS.md
3. Answer the 5 verification questions from 00_ENTRY_POINT.md
4. Only then begin work
5. After every confirmed decision - save to GitHub immediately

---

## Rule 1: GitHub is the Only Memory

Claude has no memory between sessions. GitHub is the only persistent memory.
If it is not in GitHub, it does not exist.

## Rule 2: Save Protocol (One Method Only)

When Jim confirms any decision:
1. Write content to appropriate file in 00_HANDOFF/
2. Output full file content for Jim to paste into GitHub web editor
3. Jim opens GitHub, clicks pencil icon, selects all, pastes, commits
4. Jim confirms version number directly to Claude
5. Claude accepts Jim's confirmation - never says "confirmed" without it

Never say "already recorded" without Jim's direct confirmation.
Never wait until end of session to save.
One decision = one push.

## Rule 3: Update 21_CURRENT_STATUS.md at Session End

Before Jim closes any session:
1. Update 21_CURRENT_STATUS.md with what was completed, confirmed decisions, next steps
2. Push to GitHub
3. Jim confirms

## Rule 4: Never Write Secrets in GitHub Files

Never write API keys, tokens, or passwords in any GitHub file.
If a key is needed, write: "stored separately, do not write in any file"

## Rule 5: New Project = New File in GitHub

Every new project gets its own file: 00_HANDOFF/[number]_[PROJECT_NAME].md
File must contain: goal, confirmed decisions, current status, next steps.
Add new file to 00_ENTRY_POINT.md index.

## Rule 6: Any Claude Session Can Operate Independently

Any Claude that reads these rules can continue Jim's work without asking Jim to re-explain.
No explanation from Jim needed. Read the files. Begin work.

## Rule 7: Execute, Test, Confirm, Then Report

Claude executes -> tests -> confirms success -> reports to Jim.
Never wait for Jim to verify.
Never report before confirming success.
Never apologize after failure - fix and report the result.

## Rule 8: Session Start Protocol

1. Read ALL files in 00_ENTRY_POINT.md
2. Answer all 5 verification questions
3. Report current status from 21_CURRENT_STATUS.md
4. Begin work

## Rule 9: Tool Assignment

Claude chat = central brain (analyze, discuss, break down, assign)
ChatGPT = image generation
Claude Code = code, file operations, batch processing, backend
Make = automation execution
GitHub = single source of truth
Never centralize all work in one session.

## Rule 10: Jim's Rule Philosophy

For organization and tools: rules are to be followed strictly.
For Jim: rules are made to be broken when he sees further.
When Jim moves in a new direction - follow him, do not remind him of old rules.
Track Jim's thinking direction, not his exact words.

## Rule 11: Goal First, Then Tool Assignment

Every task follows this sequence:
1. Define goal clearly
2. Break down into steps
3. Assign each step to the right tool
4. Execute in order

Claude chat does not start executing before goal is confirmed.
Claude chat assigns to the right tool - not everything to itself.

## Rule 12: GitHub File Reading - Reliable Method

Claude chat web_fetch reads cached pages - NOT live content. Do not use to verify.
raw.githubusercontent.com also has CDN cache - not reliable for immediate verification.

ONLY reliable method:
Claude Code reads local file: type "D:\smartpn-atlas-core\00_HANDOFF\{filename}"

Session start procedure:
1. Claude Code runs: type "D:\smartpn-atlas-core\00_HANDOFF\24_DATA_SYSTEM.md"
2. Claude Code confirms version number
3. Claude chat receives confirmation and begins work

Jim verification: Jim states version number directly. Claude accepts this as final confirmation.

## Rule 13: Claude Code Operating Rules

Always start with: claude --dangerously-skip-permissions
Standard start: cd /d D:\smartpn-atlas-core && claude --dangerously-skip-permissions
Auto mode in /config is NOT enough - still stops for bash/git commands
First prompt: select "2. Yes, I accept"
If still stopping: exit and restart with --dangerously-skip-permissions

<!-- updated: 2026-06-03 -->
## Rule 14: Every Session Must Show Progress

When Jim opens a new session, he expects progress — not error-fixing, not re-explaining, not re-teaching.

Claude's responsibility before Jim arrives:
- GitHub is up to date
- All decisions are recorded
- Claude Code has completed its assigned tasks
- Next steps are clear and ready to execute

When Jim types the first message, Claude must already know:
- What was done
- What is pending
- What Jim needs to decide

Jim's time is for thinking and deciding — not for managing AI.

## Rule 15: Verify Before Record

Every logic definition follows this sequence:
1. Define the logic
2. Run a trial calculation immediately to produce output
3. Jim confirms the output is correct
4. Record to GitHub
5. Only then proceed to the next definition

An unverified definition is not complete.
A definition not recorded to GitHub does not exist.

<!-- updated: 2026-06-05 -->
