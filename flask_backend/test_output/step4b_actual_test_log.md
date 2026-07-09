# 版本控制 Step 4b「編制表 MP 改抓實際人數(actual_operators)」測試報告

日期：2026-07-09
測試腳本：`flask_backend/test_output/test_step4b_actual.py`（Playwright + chromium）
隔離方式：複製正式 DB → 隔離 server(5099，啟動前 init_db) → 登入 jim/admin123 → 每步截圖 → 測完刪副本（**不污染正式 DB**）

## 結果：6/6 PASS ✅

| 步驟 | 內容 | 結果 | 實測 |
|---|---|---|---|
| server | 隔離 server 啟動 | PASS | http://127.0.0.1:5099 |
| 0 | 登入 + 鎖定 header | PASS | header=1 (OZWEEGO J) |
| 1 | 針車 MP = 實際人數加總(5)，非理論換算 | PASS | stitching=5.0（理論≈6.1，兩者不同），has_actual=True |
| 2 | 改實際人數(4+4) → 編制表針車=8 | PASS | stitching=8.0 |
| 3 | 實際人數留空(NULL)→當0加，不NaN/報錯 | PASS | stitching=4.0（float，非NaN） |
| 4 | 數字是實際人數加總，非 standard_time 理論換算 | PASS | 理論≈6.1 vs 實際 5→8→4 |

截圖：`step4b_shots/01_actual_5.png` ~ `03_null_zero.png`

## 做法摘要
### 改哪
`get_bianzhi_detail`（bianche.html 用）+ `get_bianche_data`（/api/bianche，legacy）：
- IE 讀取 SQL 一併抓 `actual_operators`（原本只抓 `standard_time`），WHERE 放寬為 `standard_time>0 OR actual_operators>0`（避免只填實際人數、沒 std 的列被濾掉）。
- 資料結構 `ie_data[art][zone]` 從 `[std]` 改為 `[(std, act)]`。
- 分製程聚合：
  - **針車(STITCH_ZONES=電腦針車/折边)**：`sum(actual_operators)`，NULL 當 0。
  - **成型(ASSEMBLY_ZONES=成型主區/成型UV/水蜘蛛)**：`sum(actual_operators)`，NULL 當 0。
  - **STF(打粗/照射)**（get_bianche_data）：`sum(actual_operators)`（原本是 `qty×tct/3600/222` 產能式，一併改實際人數）。
- 加 `has_actual` 旗標：該鎖定版主線(針車/成型)有沒有填實際人數（供前端淡色提示；本步先不做紅底）。

### 裁斷(cutting)怎麼處理 → **維持理論**
- 裁斷 = `sum(standard_time)×eolr/3600`（理論），**不改 actual**。
- 原因：裁斷機是**公式列（standard_time 由三欄即時算，多半 NULL）**，`actual_operators` 欄常為空；沿用系統既有 `get_ie_sum`（SUM C2B）的定案規則——「裁斷用理論、針車/成型/STF 用實際」。task 也預期此處理。

### 外移(P/Q/R)現況 → **仍為理論基礎（未改，回報如下）**
- 外移 P/Q/R 來自 `allocation_item.theory_mp`（prefill 當下由 `standard_time/(3600/eolr)` 種進去的**快照**），是 offline 單位勾選承接的另一套算法，**不走 4b 的主線即時聚合**。
- 因此目前 **C2B = 主線實際人數 + 外移(理論快照)**，兩者基礎不完全一致。
- 要讓外移也用實際人數，需改 `prefill_allocation` 的 `theory_mp` 種法或改成即時 join `ie_process.actual_operators`——屬 allocation「快照 vs 即時」的決策（Jim 先前已標記），**本步(4b)未動**，留待後續一步處理。

## 正式 DB 驗證（測後）
- ie_process 20434、approved=0（測試在副本，未污染）；無殘留副本。

## 範圍聲明（本步只做 4b）
- 只改「主線 MP theory→actual」；未動鎖定版/紅底(4a)、分版/鎖定/刪除(1-3)。
- 外移基礎、cutting 是否改 actual、allocation 快照/即時 → 皆未動，見上「外移現況」。
- 既有 `/api/ie/review/list` 500 與本步無關，待收尾。
