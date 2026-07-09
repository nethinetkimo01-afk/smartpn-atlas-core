# 版本控制 Step 4c「外移(P/Q/R)改實際人數 + 統一 C2B 基礎」測試報告

日期：2026-07-09
測試腳本：`flask_backend/test_output/test_step4c_offline_actual.py`（Playwright + chromium）
隔離方式：複製正式 DB → 隔離 server(5099，啟動前 init_db) → 登入 jim/admin123 → 每步截圖 → 測完刪副本（**不污染正式 DB**）

## 結果：6/6 PASS ✅

| 步驟 | 內容 | 結果 | 實測 |
|---|---|---|---|
| server | 隔離 server 啟動 | PASS | http://127.0.0.1:5099 |
| 0 | 登入 + 鎖定 + prefill | PASS | header=1 (OZWEEGO J) |
| 1 | 承接 → 外移Q = 實際人數(5)，非理論 | PASS | q_ext=5.0（理論≈6.1，不同） |
| 2 | 改實際人數(4+4) → 外移Q=8（實際基礎） | PASS | q_ext=8.0 |
| 3 | 不承接(uncheck) → 不算進外移（勾選邏輯保留） | PASS | q_ext=0 |
| 4 | 承接勾選改實際人數重讀後保留 | PASS | 仍勾選=True，q_ext=6.0 |
| 5 | C2B = 主線實際 + 外移實際（兩者相加） | PASS | c2b=54.6 == k(48.6)+外移(6.0) |

截圖：`step4c_shots/01_moved_actual_5.png` ~ `05_c2b_consistent.png`

## 做法摘要
### 外移原本怎麼算
- `get_bianzhi_detail`/`get_bianche_data` 的 moved：`SELECT art, zone, SUM(theory_mp) FROM allocation_item WHERE is_checked=1` → 再依 zone 分 P/Q/R。
- `theory_mp` 是 **prefill 當下**由 `standard_time/(3600/eolr)` 種進 `allocation_item` 的**理論快照**。
- 因此 4b 後 C2B = 主線實際 + 外移理論，基礎不一致。

### 改成什麼
- 新增 `_moved_actual_by_art_zone(conn, month)`：對 `is_checked=1` 的 `allocation_item`，即時 `LEFT JOIN ie_process`（on header_id+zone+seq+process_name，且 `_locked_stage_clause` 只取鎖定版），`SUM(COALESCE(ip.actual_operators,0))` → 得「實際人數基礎」的外移。
- `get_bianzhi_detail` 的 moved_p/q/r、`get_bianche_data` 的 moved_data 都改用這個 helper。
- 只抓**鎖定版**（沒鎖定 → LEFT JOIN 無配對 → 0，與主線一致）；NULL 當 0。

### 勾選有沒有保留 → **有**
- helper 仍以 `WHERE ai.is_checked=1` 篩選——**只有承接的才撥**，勾選邏輯完全不變。
- 只換「撥的人力數字來源」：`theory_mp` 舊快照 → 即時 `actual_operators`。
- 不動 `allocation_item.is_checked`、不動 prefill 的勾選機制（步驟3/4 驗證：uncheck 不算、re-check 後改實際人數重讀勾選仍在）。

### C2B 基礎統一
- 主線 k = 裁斷(理論*) + 針車(實際) + 成型(實際)；外移 P/Q/R = 實際人數。
- C2B = k + p_ext + q_ext + r_ext（步驟5 驗證 54.6 = 48.6 + 6.0）。
- (*) 裁斷仍理論：裁斷機是公式列、actual 常空，沿用 get_ie_sum 定案（4b 已說明），非本步範圍。

## 正式 DB 驗證（測後）
- ie_process 20434、approved=0（測試在副本，未污染）；allocation_item 48268 不變；無殘留副本。

## 範圍聲明（本步只做 4c）
- 只改外移「人力基礎 theory→actual」+ 保留勾選；未動主線(4b)、鎖定/紅底(4a)、分版/鎖定/刪除(1-3)、勾選機制本身。
- 既有 `/api/ie/review/list` 500 與本步無關，待收尾。
