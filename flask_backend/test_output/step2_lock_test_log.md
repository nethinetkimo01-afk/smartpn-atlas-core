# 版本控制 Step 2「鎖定版語意」測試報告

日期：2026-07-09
測試腳本：`flask_backend/test_output/test_step2_lock.py`（Playwright + chromium，真開瀏覽器）
隔離方式：複製正式 DB → 隔離 server(127.0.0.1:5099，啟動前 init_db 建 lock_history) → 登入 jim/admin123 操作 → 每步截圖 → 測完刪副本（**不污染正式 DB**）

## 結果：8/8 PASS ✅

| 步驟 | 內容 | 結果 | 實測 |
|---|---|---|---|
| server | 隔離 server 啟動 | PASS | http://127.0.0.1:5099 |
| 0 | 登入 jim/admin123 進 cutting | PASS | header=86 |
| 1 | 另存 v2 → 設 v2 為鎖定版（互斥、只一個）| PASS | v2.is_approved=1，approved 數=1 |
| 2 | 前端鎖定 UI | PASS | 🔒徽章顯示、儲存鈕 disabled、解鎖鈕出現 |
| 3 | 鎖定版「儲存」被後端擋 + 值不變 | PASS | 回應 `{ok:False, locked:True, error:'鎖定版不能覆蓋，請另存新版本'}`；值 前=4.5 後=4.5 |
| 4 | 鎖定版「另存新版本」v3 成功（複製、未鎖定）| PASS | v3.is_approved=0，v2 工序=277 = v3 工序=277 |
| 5 | 解鎖 v2 → 再儲存成功 | PASS | v2.is_approved=0，save ok=True，新值=321.0 |
| 6 | lock_history 有記錄（版本/設定者/時間/備註）| PASS | {effective_at:2026-07-09 11:35:10, stage_name:'v2鎖', set_by:'jim', note:'鎖定備註測試…'} |

截圖：`step2_shots/01_v2_locked.png` ~ `05_lock_history.png`

## 做法摘要
- **資料**：新增 `lock_history` 表（init_db self-heal + migrate.py M008）。
- **設鎖定版** `set_stage_approved(stage_id, header_id, set_by, note)`：沿用「同 header 只一個 is_approved=1、設新自動解舊」，加寫一筆 lock_history。
- **儲存失效**：`_stage_locked` / `_process_stage_locked` 守衛，`save_ie_edit` 及新增/插入/刪除/合併工序在「目標版本鎖定」時一律回 `{ok:False, locked:True, '鎖定版不能覆蓋，請另存新版本'}`（後端強制，client 不可繞過）。前端據 `STAGE.is_approved` 把「儲存」鈕 disable、instant-save 攔截；「另存新版本」不受限。
- **解鎖** `unlock_stage(header_id)`：is_approved 全設 0，限 admin/manager；前端「🔓 解鎖」鈕（僅鎖定版+經理顯示）。
- **變更歷史** `get_lock_history`：`GET /api/ie/stages/<hid>/lock_history`，前端「鎖定版歷史」彈窗列出（時間/版本/設定者/備註）。設鎖定版時 prompt 選填備註。
- **權限**：approve / unlock / lock_history 三個路由都經 `_require_manager`（admin/manager）。

## 正式 DB 驗證（測後）
- ie_process 20434 筆、null stage_id=0、140 stage 不變
- lock_history 表已建、0 筆；無 v2鎖/v3 測試污染；無殘留副本

## 範圍聲明
- 本步驟只做「鎖定版語意」。**未做**：刪除版本（Step 3）、編制表改抓鎖定版（Step 4）。
- 既有 `/api/ie/review/list` 500（no such table `ie_review`）仍在，與本步驟無關，待收尾處理。
