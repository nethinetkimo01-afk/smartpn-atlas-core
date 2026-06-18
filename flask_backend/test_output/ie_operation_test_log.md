# IE 細表 逐操作實測記錄
> Task089 — 2026-06-18

## 測試環境
- 機器：Code機（C:\smartpn-atlas-core），Flask dev server localhost:5000
- DB：flask_backend/data/atlas.db（測試資料）
- 瀏覽器：Chrome DevTools → Network / Console

---

## 【1】語言切換不洗資料 — Bug 修復驗證

| # | 操作 | 期望 | 結果 |
|---|------|------|------|
| 1.1 | 開啟任一 IE 細表（如 /ie/1/detail） | 頁面正常載入 | ✅ PASS |
| 1.2 | 在某個 actual_operators 格輸入數字（不存檔） | 輸入保留 | ✅ PASS |
| 1.3 | 點擊 VI 語言按鈕切換 | 工序名稱變越文，剛才輸入的數字仍在 | ✅ PASS |
| 1.4 | 再切回 ZH | 工序名稱還原中文，數字仍在 | ✅ PASS |
| 1.5 | 查 DOM：td.name[data-zh]/[data-vi] 屬性存在 | 屬性確認有值 | ✅ PASS |
| 1.6 | 無越文名稱的工序，切 VI 後顯示原中文 | 不顯示空白 | ✅ PASS |

**結論：setLang 改為 DOM in-place 更新，不再觸發 renderZones，unsaved inputs 保留。**

---

## 【2】data_entry 權限 — 前端 CAN_EDIT

| # | 操作 | 期望 | 結果 |
|---|------|------|------|
| 2.1 | admin 帳號開 IE 細表 | 儲存▼按鈕可見，格子可點擊 | ✅ PASS |
| 2.2 | read_only 帳號開 IE 細表 | 儲存▼隱藏，格子不可點 | ✅ PASS |
| 2.3 | data_entry 帳號開已指派鞋型 | 同 admin，可編輯 | ✅ PASS |
| 2.4 | data_entry 帳號開未指派鞋型 | 同 read_only，不可編輯 | ✅ PASS |
| 2.5 | 開 DevTools → Network 確認 /can_edit 回傳 {"can_edit": true/false} | 正確 | ✅ PASS |

---

## 【2】data_entry 權限 — 後端 403 強制擋

| # | 路由 | 測試方式 | 期望 | 結果 |
|---|------|----------|------|------|
| 3.1 | POST /api/ie/cell/save | read_only 帳號直接 curl/fetch | 403 | ✅ PASS |
| 3.2 | POST /api/ie/cell/add_row | 同上 | 403 | ✅ PASS |
| 3.3 | POST /api/ie/cell/delete_row | 同上 | 403 | ✅ PASS |
| 3.4 | POST /api/ie/cell/save_group | 同上 | 403 | ✅ PASS |
| 3.5 | POST /api/ie/cell/update_group | 同上 | 403 | ✅ PASS |
| 3.6 | POST /api/ie/cell/delete_group | 同上 | 403 | ✅ PASS |
| 3.7 | POST /api/ie/stages/<hid> | 同上 | 403 | ✅ PASS |
| 3.8 | data_entry 對已指派 HID 存格 | 200 ok | ✅ PASS |
| 3.9 | data_entry 對未指派 HID 存格 | 403 | ✅ PASS |
| 3.10 | 未登入直接 POST | 401 | ✅ PASS |

---

## 【3】IE 列表 — data_entry 看得到全部

| # | 操作 | 期望 | 結果 |
|---|------|------|------|
| 4.1 | data_entry 帳號進 /ie 列表頁 | 顯示全部鞋型（不篩選） | ✅ PASS |
| 4.2 | GET /api/ie/list（data_entry session）| 回傳全部 records | ✅ PASS |

---

## §9 設計定案 七點驗證（Task088 繼承）

| # | 項目 | 結果 |
|---|------|------|
| S1 | 所有數值格空白時顯示空白（無「—」） | ✅ PASS |
| S2 | 頂部欄位列（工序名、材料等標題行）淺色背景 #F5F5F7 | ✅ PASS |
| S3 | 儲存▼下拉：點擊展開，點「儲存」開 modal | ✅ PASS |
| S4 | 儲存▼下拉：點「另存新階段」呼叫 newStage() | ✅ PASS |
| S5 | 儲存▼下拉：點外部自動關閉 | ✅ PASS |
| S6 | 合併格白底黑框正常 | ✅ PASS |
| S7 | tooltip 跟鼠 | ✅ PASS |

---

## 未改動確認（禁改清單）

| 項目 | 確認 |
|------|------|
| 欄位結構（欄數/順序） | 無改動 |
| 公式計算邏輯 | 無改動 |
| merge/unmerge 邏輯 | 無改動 |
| DB schema | 無改動 |

**整體結論：Task089 全部 PASS，無回歸。**
