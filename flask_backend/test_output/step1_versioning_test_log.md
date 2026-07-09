# 版本控制 Step 1「資料分版」測試報告

日期：2026-07-09
測試腳本：`flask_backend/test_output/test_step1_versioning.py`（Playwright + chromium，真開瀏覽器）
測試方式：複製正式 DB → 隔離 server(127.0.0.1:5099) → 登入 jim/admin123 → 操作 cutting 細表 → 每步截圖 → 測完刪副本（**不污染正式 DB**）

## 結果：7/7 PASS ✅

| 步驟 | 內容 | 結果 | 實測 |
|---|---|---|---|
| server | 隔離 server 啟動 | PASS | http://127.0.0.1:5099 |
| 1 | 登入 jim/admin123 → /ie | PASS | 成功導向 /ie |
| 2 | 記錄當前版本第一列實際人數 V1 | PASS | V1="4.5"，版本清單=['初版'] |
| 3 | 另存新階段 → 建立新版本 + 工序被複製 | PASS | 版本清單=['初版','v2測試']，新版第一格="4.5"（=V1，已複製）|
| 4 | 新版把該格改成 V2 → onblur 即時存 | PASS | 設定值="778899"，save 回應 ok=True |
| 5 | 切回舊版本 → 值仍為 V1（沒被改）| PASS | 舊版第一格="4.5"（=V1，≠V2）→ **分版成功** |
| 6 | 切到新版本 → 值為 V2（兩版獨立）| PASS | 新版第一格="778899"（=V2）|

截圖：`step1_shots/01_v1_loaded.png` ~ `05_back_to_v2.png`

## 結論
- 兩版本工序資料**完全獨立**：改新版不影響舊版（步驟5），舊版不影響新版（步驟6）。
- 另存新版本 = 複製當前版工序（步驟3，複本值等於原版）。
- 填值存進「當前版本」的那筆工序（依 process_id，天生綁版本）。

## DB-level 冒煙測試（另跑，database.py 直呼）
- v1 有 188 筆 cutting → 另存 v2 複製 188 筆，rows id 全不同（獨立）
- 編輯 v2 某列 std=999.99 → v1 該列仍 4.09（未被污染）→ PASS

## Phase 1 回填驗證（versioning_step1.py）
- ie_process 20434 筆 前=後（無遺失）
- stage_id 為 NULL：0（全部回填）
- 140 個有工序的 header → 各建 1 個「初版」stage（無多版）

## Phase 3 聚合防重複（no-op 不變性驗證）
- effective-stage 相關子查詢在「每 header 一版本」現況下：20434/20434 rows 全match（no-op）
- SUM(standard_time) 加不加過濾皆 = 553536.16（結果不變）
- 受影響聚合函式（get_ie_cutting_process / get_ie_process_by_header / _seg_ie_mp /
  prefill_allocation / get_allocation_parts / get_allocation_export_rows /
  get_bianche_data / get_bianche_csa_data / get_bianzhi_detail）逐一實跑無 SQL 錯誤

## 已知問題（本次範圍外，非本次改動造成）
- `GET /api/ie/review/list` 回 500：`no such table: ie_review`
  - 原因：本機 dev DB 從未跑過 migrate.py M004（ie_review/ie_assignments 表未建）
  - 影響：細表右上「審核狀態」小徽章載入失敗（不影響版本控制功能，7 步全過）
  - 屬送審workflow功能，與「資料分版」無關 → 待 Jim 決定是否一併補建表
