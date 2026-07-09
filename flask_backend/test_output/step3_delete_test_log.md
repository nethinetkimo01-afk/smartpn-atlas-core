# 版本控制 Step 3「刪除版本」測試報告

日期：2026-07-09
測試腳本：`flask_backend/test_output/test_step3_delete.py`（Playwright + chromium，真開瀏覽器）
隔離方式：複製正式 DB → 隔離 server(127.0.0.1:5099，啟動前 init_db) → 登入 jim/admin123 操作 → 每步截圖 → 測完刪副本（**不污染正式 DB**）

## 結果：6/6 PASS ✅

| 步驟 | 內容 | 結果 | 實測 |
|---|---|---|---|
| server | 隔離 server 啟動 | PASS | http://127.0.0.1:5099 |
| 1 | 建立 3 個版本 v1(初版)/v2/v3 | PASS | 版本數=3，工序 v1=277 v2=277 v3=277 |
| 2 | 刪 v3(一般版) 成功，別版工序不受影響 | PASS | 剩 ['初版','v2']；v3 工序=0；v1=277、v2=277 未動 |
| 3 | 鎖定版 v2 不能刪(鈕 disable + 後端擋) | PASS | 刪除鈕 disabled=True；API `{ok:False, locked:True, '這是鎖定版，請先解鎖再刪除'}` |
| 4 | 解鎖 v2 後刪除成功 | PASS | 剩 ['初版']；v2 工序=0；v1 工序=277 完整 |
| 5 | 最後一個版本不能刪(至少留一個) | PASS | API `{ok:False, last_one:True, '至少需保留一個版本，不能刪除'}`；v1 工序=277 完整 |

截圖：`step3_shots/01_three_versions.png` ~ `05_last_one_blocked.png`

## 做法摘要
- **後端** `delete_ie_stage(stage_id, header_id, user)`：
  1. 版本存在且屬於此 header
  2. `is_approved=1` → 拒絕 `{locked:True, '這是鎖定版，請先解鎖再刪除'}`
  3. 該 header 版本數 ≤ 1 → 拒絕 `{last_one:True, '至少需保留一個版本，不能刪除'}`
  4. 通過 → **乾淨刪**：`DELETE ie_process WHERE stage_id AND header_id` + `DELETE ie_process_group WHERE stage_id AND header_id` + `DELETE ie_stage`，只刪被指定那一版，不動別版
- **路由** `POST /api/ie/stages/<hid>/<sid>/delete`，經 `_require_manager`（admin/manager）
- **前端**：頂列「🗑 刪除此版本」鈕（僅 admin/manager 顯示）；鎖定版時 disable+提示「請先解鎖」；點擊跳確認框「確定刪除版本 XXX？此動作不可復原」；刪除後自動切到剩餘最新版並重載

## 正式 DB 驗證（測後）
- ie_process 20434 筆、null stage_id=0、140 stage 不變；無 v2/v3 測試污染；每個 header 仍恰一版本；無殘留副本

## 範圍聲明
- 本步驟只做「刪除版本」。**未動**編制表（Step 4）。
- 既有 `/api/ie/review/list` 500（no such table `ie_review`）仍在，與本步驟無關，待收尾處理。
