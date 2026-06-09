# SmartPN Atlas Operating Rules

Version: v3.2 | 2026-06-09

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

**General start:**
1. Read ALL files in 00_ENTRY_POINT.md
2. Answer all 5 verification questions
3. Report current status from 21_CURRENT_STATUS.md
4. Begin work

**Fixed handoff — trigger: Jim says "繼續 DATA SYSTEM"**

When Jim types "繼續 DATA SYSTEM", Claude immediately executes these 4 steps without asking anything:

1. Read memory index (Claude Code: `C:\Users\user\.claude\projects\D--smartpn-atlas-core\memory\MEMORY.md`)
2. Claude Code reads local files and brings full content into the claude.ai window:
   - `D:\smartpn-atlas-core\00_HANDOFF\24_DATA_SYSTEM.md`
   - `D:\smartpn-atlas-core\00_HANDOFF\07_RULES.md`
3. Report in this exact format:
   ```
   版本：24_DATA_SYSTEM.md vX.X | 07_RULES.md vX.X
   當前狀態：[一句話]
   已完成：[清單]
   待 Jim 確認：[清單]
   下一步：[Claude 立刻開始執行的事]
   ```
4. Begin work immediately. Do NOT ask Jim any questions.

<!-- updated: 2026-06-05 -->

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

## Rule 11: Goal First, Then Tool Assignment (派工執行)

Every task follows this sequence:
1. Define goal clearly
2. Break down into steps
3. Assign each step to the right tool
4. Execute in order

Claude chat does not start executing before goal is confirmed.
Claude chat assigns to the right tool - not everything to itself.

**派工執行補充：**
- 每個邏輯定義後，立刻試算，不等 Jim 說
- 試算結果直接呈現，不問 Jim 要不要看
- Jim 只需要說 OK 或不對

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

**新視窗補充：**
- 新視窗開始，直接讀 24_DATA_SYSTEM.md 的最新執行結果
- 報告差異，不問 Jim 要怎麼做
- 自己決定下一步，執行，報告結果

## Rule 15: Verify Before Record

Every logic definition follows this sequence:
1. Define the logic
2. Run a trial calculation immediately to produce output
3. Jim confirms the output is correct
4. Record to GitHub
5. Only then proceed to the next definition

An unverified definition is not complete.
A definition not recorded to GitHub does not exist.

<!-- Rule 15 updated: 2026-06-05 -->

## Rule 16: Test Before Recording

Before writing any new behaviour, script, or automation into GitHub rules or handoff files:
1. Implement the code or change
2. Run it once end-to-end with real data (`--force --no-push` for nightly tasks)
3. Confirm the output is correct
4. Only then commit to GitHub

If the test fails: fix the code, re-run, confirm again — then commit.
Do not write "confirmed working" until you have seen the output yourself.

<!-- Rule 16 added: 2026-06-06 -->

## Rule 17: Data Validation Method

Every table or field logic must be verified with this method:
1. Pick a concrete number (e.g., KJ7844 = 1850)
2. Trace where that number comes from (what is the raw source value)
3. Confirm the aggregation logic is correct
4. Jim confirms — only then is it complete

DS-04 Schedule rules (CONFIRMED 2026-06-06):
- Each sheet is independent — no cross-sheet aggregation
- Same ART in different sheets = independent orders in different departments
- Same ART in different LEAN groups within one sheet = separate rows in result table

<!-- Rule 17 added: 2026-06-06 -->

## Rule 18: Dynamic Workflow

- 目標清晰後，不回頭確認，直接執行
- 每個步驟完成，立刻進行下一步
- 遇到不確定的，先用最合理的假設執行，執行完報告，Jim 再修正
- 不問 Jim 應該由 Claude 決定的事

<!-- Rule 18 added: 2026-06-08 -->

## Rule 19: DS-04 進度表取值規則（已確認）

- 製令號碼唯一，全廠不重複
- 每個 sheet 獨立，不跨 sheet 加總
- LEAN 組分多段時，只取「成型进度」段，外包鞋面 / 针车进度跳過
- 合併行邏輯：同 LEAN + 同 Model Name + 同 LC → 合併顯示，訂單加總；合併行總量不等於個別 ART 量，比對時須用原始 DS-04 個別 ART 量
- 雙製令格式 `MF2606KH8402-01-02--56-36`：`--` 後兩個數字相加（56+36=92）
- 非標準製令號碼 → 記錄到 non_standard.txt，不處理

這些規則適用於所有月份，未來新月份直接套用，不重新問 Jim。

<!-- Rule 19 added: 2026-06-08 -->

## Rule 20: 新數據源開始前的設計步驟

接到新 Excel 數據源任務時，必須先執行：

1. 讀取說明表，理解格式和拆分邏輯
2. 設計製令明細表（每張製令一行）
3. 製令明細對應結果表，差異標示
4. Jim 確認明細正確後，才開始取值

不得跳過步驟直接取值，否則等於白工

**教訓來源（2026-06-08）**：
DS-04 HP4218 8B：廠務登 172，DS-04 有 12 張製令合計 7,247。
若先讀明細表，可立刻看到 MF2604HP4218-31 一張就 4,450，早發現廠務漏登。
直接比對總量只會看到差異，看不到原因。

<!-- Rule 20 added: 2026-06-08 -->

## Rule 21: 交接 SOP（適用所有專案）

當 Jim 說「交接」時，立刻執行以下步驟，不需要 Jim 提醒或操作：

**Step 1：儲存所有變更**
- git add .
- git commit -m "交接：[日期] [今日主要工作摘要]"
- git push origin main

**Step 2：更新該專案的主要 handoff 文件（如 24_DATA_SYSTEM.md / 21_CURRENT_STATUS.md）**：
- 今日完成事項
- 進行中任務（未完成）
- 待 Jim 確認事項
- 今晚自動化任務
- 明天開機第一件事

**Step 3：git push origin main**

**Step 4：輸出交接摘要給 Jim 確認（格式固定）**：
```
---
交接摘要 [日期]
已完成：
進行中：
待確認：
今晚自動化：
明天第一件事：
---
```

**Step 5：確認 Claude Project Files 已同步最新版本**

規則：
- Jim 只說「交接」，其餘全由 Claude Code 完成
- 不問 Jim 任何問題
- 不需要 Jim 執行任何指令
- 每次交接必須完整執行全部 5 步驟

### Rule 21 補充：交接常見問題 SOP

**問題 1：Project Files 版本過舊**
原因：GitHub connector 不自動同步，需手動刷新或重新上傳
解決：交接 Step 3 完成後，立刻提醒 Jim：
「請到 DATA SYSTEM Project → Files → 刪除舊的 24_DATA_SYSTEM.md → 重新上傳最新版本」
預防：每次 git push 後，nightly log 自動提示 `[ACTION REQUIRED] Project Files 需要更新`

**問題 2：新視窗讀到舊版，報告狀態不正確**
原因：Project Files 沒有同步最新版本
解決：新視窗開始時，先確認 24_DATA_SYSTEM.md 版本號，若版本不是最新，告知 Jim 需要更新 Project Files

**問題 3：新視窗問 Jim 應該由 Claude 決定的事**
原因：Instructions 不夠強
解決：Claude 遇到兩個技術任務時，同時執行，不問 Jim 選哪個

**問題 4：交接摘要狀態與 GitHub 不一致**
原因：交接時 GitHub 已有最新版，但摘要說「尚未寫入」
解決：交接前先確認 git push 成功，再生成交接摘要

<!-- Rule 21 added: 2026-06-09 -->
