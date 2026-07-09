# 版本控制 Step 4a「編制表抓鎖定版 + 沒鎖定空紅底」測試報告

日期：2026-07-09
測試腳本：`flask_backend/test_output/test_step4a_locked_source.py`（Playwright + chromium）
隔離方式：複製正式 DB → 隔離 server(127.0.0.1:5099，啟動前 init_db) → 登入 jim/admin123 → 每步截圖 → 測完刪副本（**不污染正式 DB**）

## 結果：7/7 PASS ✅

| 步驟 | 內容 | 結果 | 實測 |
|---|---|---|---|
| server | 隔離 server 啟動 | PASS | http://127.0.0.1:5099 |
| 0 | 登入 jim/admin123 | PASS | |
| 0b | 基線(無任何鎖定版)→ 編制表 MP 空 | PASS | header_A has_locked=False, cutting=None |
| 1 | 鎖 header_A → A 有數字、B 空紅底 | PASS | A(has_locked=True, cutting=9.2)；B(has_locked=False, cutting=None)；未鎖定 badge=136 |
| 2 | 解鎖 A → A 變空紅底 | PASS | A has_locked=False, cutting=None |
| 3 | 重新鎖 A → A 又有數字 | PASS | A has_locked=True, cutting=9.2 |
| 4 | offline 勾選重跑 prefill 後保留 | PASS | item=48269，勾選後=True，重跑 prefill 後仍勾=True |

測試資料：header_A=1(OZWEEGO J, art IG9016)、header_B=3(OZMILLEN, art JP7827)
截圖：`step4a_shots/01_baseline_all_red.png` ~ `05_offline_check_preserved.png`

## 做法摘要
- **新增 `_locked_stage_clause(a)`**：相關子查詢只取該 header 的鎖定版(`is_approved=1`)；沒鎖定版→子查詢 NULL→`stage_id=NULL` 無列匹配→該 header 沒 IE 數據（**不 fallback 最新版**）。**只用在編制表，不動 `_eff_stage_clause`**（那個給 IE 編輯輔助視圖 cutting-stats / process-by-header 用，全域改會讓它們沒鎖定時全空）。
- **新增 `_locked_arts(conn)`**：有鎖定版的 art 集合（`ob_articles ⋈ ie_stage(is_approved=1)`）。
- **`get_bianzhi_detail` / `get_bianche_data`**：
  - IE 讀取改 `_locked_stage_clause`（即時讀鎖定版，不靠 allocation 舊快照）
  - 每列加 `has_locked` 旗標
  - `has_locked=false` → 該列 MP 全空（cut/stch/asm/合計K/外移P/Q/R/C2B = None）；manual 編制欄不動
- **前端 `bianche.html`（~318 行）**：`has_locked===false` → MP 格 `background:#FDECEA` 空 + `title` tooltip「此鞋型 IE 尚未設定鎖定版，請先鎖定」；鞋型名加「未鎖定」紅 badge。合計會自動排除（`Number(None)||0`）。
- **offline 勾選保留**：`prefill_allocation` 維持 `INSERT OR IGNORE`（不覆蓋既有 `is_checked`）→ 重跑 prefill 不洗掉單位已填勾選（步驟4 驗證）。

## 正式 DB 驗證（測後）
- ie_process 20434、ie_stage 140、approved=0（測試在副本，未污染）；allocation_item 48268 不變；無殘留副本
- ⚠️ 因正式 DB 目前 0 個鎖定版 → 套用後編制表**全部顯示未鎖定(紅)**，屬正確行為（Jim 逐一鎖定後才會出現數字）。

## 範圍聲明（本步只做 4a）
- MP 仍維持 **theory（standard_time）** 抓法；改 actual_operators 是 **Step 4b**，本步未動。
- 未動 Step 1-3 已完成的分版/鎖定/刪除。
- `_eff_stage_clause` 保持原樣（IE 編輯輔助視圖不受影響）。
- 既有 `/api/ie/review/list` 500（no such table `ie_review`）與本步無關，待收尾。
