# 版本控制設計 + 系統藍圖 + MP公式 + 編制表資料流 + 測試/思維規則

> 建立：2026-07-09（Jim 定案，Claude 記錄）
> 本檔補記今天定案的關鍵設計與規則，避免下個 session 漏掉。
> 相關檔：`28_BIANCHE_SPEC.md`（編制表規格）、`27_WORKING_RULES.md`（工作規則）、`29_UX_RULES.md`（UX鐵則）

---

## A. 版本控制設計（定案）

### 版本兩種
| 類型 | 數量 | 可編輯 | 「儲存」 | 「另存新檔」 | 說明 |
|---|---|---|---|---|---|
| **一般版本** | 可多個 | ✅ | ✅ 有效 | ✅ 有效 | 名稱自訂 |
| **鎖定版本** | 全系統/每鞋型**只一個** | ✅ | ❌ **失效** | ✅ 有效 | 對外基準（trusted source），「儲存」不能覆蓋對外基準 |

### 核心規則
- **另存新檔** = 基於「當前正在看的版本」複製一份（含該版所有工序資料）
- **鎖定單位 = 鞋型（header）**，該鞋型底下的 ART 一併鎖定
- **經理設鎖定版**：同鞋型只能一個；設新的自動解除舊的；可解鎖
- **鎖定版變更歷史**：每次設鎖定版記一筆（生效時間 / 版本 / 設定者 / 備註選填），供追溯「哪天的編制表取的是哪一版 IE」
- **刪除版本**：
  - 只有 經理 / admin 可刪
  - 鎖定版**不能刪**（要先解鎖）
  - 刪除要確認
  - 每個鞋型**至少保留一個**版本
- **唯讀帳號**：只能看鎖定版
- **沒鎖定 IE 的通知**：編制表結果對應格顯示「空 + 紅底」（+ tooltip 提示原因＝該鞋型尚未設鎖定 IE）
- **現有資料**：可清空重導（Jim 授權），但先備份、能不清就不清

---

## B. 總體藍圖（系統終極目標）

```
IE（標準工時）
  → 版本控制（鎖定基準 = trusted source）
    → 編制表（按 ART 抓鎖定 IE 的「實際人數」 + offline 撥人 + MP 公式）
      → 滿載率（單位/機台） + IE 達成率（標準 vs 實際產出）
        → 管理決策
```

**關鍵**：沒有版本控制，對外 IE 不可信，就無法創造 trusted source，整個系統就沒有意義。版本控制是把 IE 從「一堆會變的數字」變成「可信基準」的那一步。

---

## C. MP 人力公式（定案）

```
部件人力 = (標準秒數 × 總件數) ÷ (工作天 × 每日工時 × 3600)
```

- **件數與天數對應同週期**（月總件數 → 對應月工作天）
- **工作天、每日工時 = 手工輸入**
- 編制表 MP 抓 IE 的**「實際人數」**（不是理論人數）
- 承接的部件人力相加 = 該 offline 單位總人力 → 算滿載率 → 對比實際產出 = IE 達成率

---

## D. 編制表資料流（現況 + 目標）

1. 手工匯入排程表 → 拆成 ART + 數量
2. 按 ART 抓對應鞋型「**鎖定 IE**」的 裁斷/針車/成型/STF 人力 + offline 製程（ATOM / 電腦針車 / 折邊組 / Laser）
3. offline 做成明細 → offline 單位勾選承接/不承接（現有 `allocation_item`）
4. 承接 → 撥人：
   - **外移 P** = 同材共裁 / 自動裁斷 / 折邊
   - **外移 Q** = 電腦針車
   - **外移 R** = 大底課
5. **C2B = 主線人力 + 外移 = 最終編制**

**現況**：allocation 半成品已有大半邏輯，但抓的是**即時 `ie_process`**，要改成抓**「鎖定版」**。
**規格見**：`28_BIANCHE_SPEC.md`

---

## E. Playwright 自動測試產線（重要工具）

- 中樞已裝 **playwright + chromium**（Windows 能跑），補「前端實際操作測試」的洞
- **Antigravity 評估過**：瀏覽器 subagent 僅支援 Linux，Windows 用不了，故改用 Playwright
- **用途**：每個功能改完，寫 Playwright 腳本自動測（開瀏覽器 / 登入 jim/admin123 / 操作 / 截圖），不讓 Jim 當測試員
- **教訓**：光讀碼 + 靜態渲染不夠，要驗「實際操作的資料流」
  - 今天 cutting 合併 bug 真因 = **前端只存 `EDITS` 沒送後端**，靜態看不出，只有實際操作才會抓到

---

## F. 中樞思維（Jim 對 Claude 的核心要求）

1. **目標優先**：缺能力先找 solution 不是認命。自己做不到的先主動找工具/方法、主動提；真需要 Jim 操作的才說，並講清楚為什麼
2. **預想下一步**：Jim 給目標，要推導出「未說出口的下一步」、主動預留接口（不只做當下）
3. **不讓 Jim 當搬運工/測試員**：Jim 的腦袋留給決策邏輯；執行層（搬 code / 測試 / 除錯 / 驗證）是 Claude 的事
4. **交出去必須能用**：不能用 = 這段時間白費 = 做了廢物。**驗到能用才交**
5. **重要規定/經驗/教訓要進 handoff**，不當聊天，讓新 session 不用重教（這條就是這次的教訓）
6. **分步做 + 每步測 + 每步確認**，風險鎖單步

---

## G. 版本控制現況調查（2026-07-09，只查不改）

> 結論：**目前的「版本」是只有標籤、沒有資料隔離的骨架**。不能直接當版本控制用，要在此基礎上補「資料分版」與「鎖定版」兩大核心。

### G1. `ie_stage` 實際欄位
- schema 檔（`ie_import_la_trainer.py`）：`id / header_id / stage_name / created_at`
- migrate.py `003`：`ALTER TABLE ie_stage ADD COLUMN is_approved INTEGER DEFAULT 0`
- **實測 `data/atlas.db`（本機 demo）：只有 `id / header_id / stage_name / created_at`，`is_approved` 尚未 migrate、且 `ie_stage` 0 筆資料**（從沒建過版本）
- ⚠️ ME129 production DB 需另外確認 is_approved 是否已 migrate

### G2. `ie_process` 如何關聯版本 → **沒有真正關聯**
- `ie_process` **沒有 `stage_id` 欄位**，只有一個 `stage INTEGER DEFAULT 1`（實測 20434 筆全部 = 1）
- `stage_id` 只被寫進 **`ie_edit_log`**（誰在哪版改了什麼的稽核紀錄），**不影響工序資料本體**
- `get_ie_cell_data()`：只用 `header_id + segment` 撈 `ie_process`，**不依 stage 過濾**；另外撈「最新一筆 stage」只當標籤顯示
- **換版本時工序資料怎麼分？→ 完全不分。所有版本共用同一份 `ie_process`。** 換版本畫面資料不變

### G3. create / get / set_stage_approved 前端誰在用
| 後端函式 | 路由 | 前端 UI（`ie_cell_detail.html`） |
|---|---|---|
| `get_ie_stages` | `GET /api/ie/stages/<hid>` | `init()` 載入右上「— 版本 —」下拉 |
| `create_ie_stage` | `POST /api/ie/stages/<hid>` | 儲存▼ →「另存新階段」`newStage()` |
| `set_stage_approved` | `POST /api/ie/stages/<hid>/<sid>/approve` | 「✓ 設為合格版」`approveCurrentStage()`（限 admin/manager 顯示） |

### G4. `is_approved` 行為 → **接近「鎖定版」概念**
- `set_stage_approved()`：先 `UPDATE ie_stage SET is_approved=0 WHERE header_id=?`，再把選定 stage 設 1
- ⇒ **同鞋型只會有一個 approved**，設新的自動把舊的歸零。這正是「鎖定版（每鞋型只一個）」的雛形
- 但目前**缺**：解鎖、變更歷史紀錄、「鎖定版儲存失效」、唯讀只看鎖定版、編制表抓鎖定版

### G5. 現在填工序資料存進哪個 stage → **不存 stage，直接寫 `ie_process` 本體**
- `saveSilent()` 前端雖帶 `stage_id`，但 `save_ie_edit()` 是 `UPDATE ie_process SET <field>=? WHERE id=?`（依 process_id）
- stage_id 只寫進 `ie_edit_log` 稽核。⇒ 不管選哪版，改的都是同一份工序資料

### G6. 前端右上三個控件現況
| 控件 | 函式 | 接後端 | 實際行為 |
|---|---|---|---|
| 「— 版本 —」下拉 | `switchStage()` | 無（純前端） | **只改 `STAGE` 變數，不重載資料**（因資料沒分版，重載也一樣）；有未存修改會先攔截確認 |
| 「儲存 ▼ / 儲存」 | `saveSilent()` | `POST /api/ie/cell/save` | 逐格靜默存進 `ie_process` 本體 |
| 「儲存 ▼ / 另存新階段」 | `newStage()` | `POST /api/ie/stages/<hid>` | **只新增一筆空的 stage 標籤，不複製任何工序資料** |
| 「✓ 設為合格版」 | `approveCurrentStage()` | `POST /api/ie/stages/<hid>/<sid>/approve` | 設 is_approved（同鞋型互斥），但目前無任何下游消費此旗標 |

### G7. 由現況到目標的關鍵缺口（給下一步）
1. **資料分版**：`ie_process` 需真正綁 stage（加 `stage_id` 或複製列），`newStage`/另存要**複製當前版工序**；讀取要依版過濾 → ✅ Step 1 完成
2. **鎖定版語意**：把 `is_approved` 升級為「鎖定版」——鎖定版「儲存」失效、只能「另存」；加解鎖；加變更歷史表 → ✅ Step 2 完成
3. **刪除版本**：新增刪除（經理/admin、鎖定版擋刪、至少留一個、確認框）→ ✅ Step 3 完成
4. **唯讀只看鎖定版**、**編制表改抓鎖定版**（取代即時 `ie_process`）→ Step 4
5. 沒鎖定 IE → 編制表對應格 空+紅底+tooltip → Step 4a

---

## G8. Step 4「編制表抓鎖定版」前置調查（2026-07-09，只查不改）

> 結論：allocation/編制表**已用 `_eff_stage_clause` 讀單一版本**，但它靜默取「鎖定版或最新版」，
> **不檢查有沒有鎖定版** → 沒鎖定時 fallback 最新版。Step 4a 要改成「必須有鎖定版才給數字，
> 沒鎖定→空+紅底」。另外 MP 現抓 theory（standard_time）不是 actual，是 4b 的事。

### G8-1. allocation 怎麼抓 ie_process
- `prefill_allocation`(db.py:2176)：`ie_process WHERE header_id AND flag!=deleted AND {eff_stage} AND zone IN(TARGET_ZONES)`，
  已有 eff 過濾；算 `theory_mp = standard_time/(3600/eolr)` 寫進 **`allocation_item`（快照，INSERT OR IGNORE，不覆蓋既有列＝勾選被保留）**。
- `_seg_ie_mp`(2326)/`get_csa_mp`(2338)：`SUM(standard_time)` 帶 eff 過濾。

### G8-2. 編制表 MP 抓哪個欄位 → **theory（待改 actual）**
- `get_bianche_data`(2830) / `get_bianzhi_detail`(3376)：`zone_mp = sum(standard_time)×eolr/3600` = **理論人力**，來源 `standard_time`，**不是 actual_operators**。
- 唯一用 `actual_operators` 的是 SUM C2B / `ie_sum.html`（db.py:1997），非編制表。
- ⚠️ 與 handoff C「編制表抓實際人數」不符 → **Step 4b** 再處理，4a 先不動。

### G8-3. 按 ART 還是 header
- IE 存 **header** 級；編制表**按 ART 索引**，經 `ob_articles(header_id, art)` 對應。同 header 多 ART 共用同一份 IE。
- 訂單 `ds04_orders`(GROUP BY lean/model/art) 用 art 對回 `ie_data[art]`；bianzhi 用 `first_art`。
- 鎖定版是 header 級（Step 2）→ 一 header 鎖定即其所有 ART 一起鎖定，與 by-ART 相容。

### G8-4. 有沒有「鎖定版」概念 → **沒有**
- eff 子查詢只是靜默取「鎖定版或最新版」，從不判斷「到底有沒有鎖定版」，無 `has_locked` 旗標。

### G8-5. `_eff_stage_clause` 用在哪 9 處
`prefill_allocation`、`_seg_ie_mp`、`get_bianche_data`、`get_bianche_csa_data`、`get_bianzhi_detail`、
`get_allocation_parts`、`get_allocation_export_rows`、`get_ie_cutting_process`、`get_ie_process_by_header`。
- allocation + 兩個編制表都已用（讀單一版本、不重複計）；缺的是「必須是鎖定版否則空」。
- ⚠️ 後兩者（cutting import stats / process-by-header）是 IE 編輯輔助視圖，**不是編制表**
  → Step 4a **不可**把 `_eff_stage_clause` 全域改鎖定版（會讓那兩個在沒鎖定時全空）；
  應**新增 `_locked_stage_clause` 只用在編制表/allocation**。

### G8-6. 前端編制表結果表
- 檔案 **`bianche.html`**（路由 `/bianche`），資料來自 `GET /api/bianzhi/detail`（→ `get_bianzhi_detail`）。
- 渲染在 **bianche.html ~300–337 行** `for (const r of rows)`：欄位 裁斷/針車/成型/合計K/編制/外移PQR/C2B。
- 現成模式：第 319 行 `noIe = !r.has_ie` → `<span class="badge-noie">無IE</span>`。「沒鎖定空紅底」照此加 `has_locked`。
- （`get_bianche_data` 走 `/api/bianche`，現無前端消費，屬 legacy/export。）

### G8-7. Step 4 工作切分
- **4a（本次）**：加 `has_locked`；編制表 IE 改「只讀鎖定版」（無鎖定→空、不 fallback）；bianche.html 沒鎖定→空+紅底+tooltip。保留 offline 勾選（`allocation_item.is_checked` 不洗）。MP 仍 theory。
- **4b（下次）**：MP 由 theory 改 actual_operators（對齊 handoff C）。
- **其他**：唯讀只看鎖定版；allocation 快照 vs 即時的決策。
