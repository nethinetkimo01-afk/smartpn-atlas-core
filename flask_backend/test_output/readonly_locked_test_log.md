# 版本控制「唯讀帳號只看鎖定版」測試報告

日期：2026-07-09
測試腳本：`flask_backend/test_output/test_readonly_locked.py`（Playwright + chromium）
隔離方式：複製正式 DB → setup 建 read_only 帳號 + 版本狀態 → 隔離 server(5099) → 兩個瀏覽器 context(唯讀 / admin) → 每步截圖 → 測完刪副本（**不污染正式 DB**）

## 用哪個唯讀帳號測
- 現有唯讀單位帳號 `tongcai/dianno/dacu`（sys_users role=read_only）**password_hash 為空、無法用 /api/login 登入**（它們走 allocation 身分登入）。
- 故測試在副本 DB **新建一個 read_only 帳號 `viewer1`/`view123`**（`db.create_user(...,'read_only',...)`）代表唯讀帳號。限制邏輯對「任何 role=read_only 帳號」皆生效。

## 結果：6/6 PASS ✅

| 步驟 | 內容 | 結果 | 實測 |
|---|---|---|---|
| server | 隔離 server 啟動 | PASS | http://127.0.0.1:5099 |
| 0 | 唯讀帳號 viewer1 登入 | PASS | |
| 1 | 唯讀進鎖定版鞋型：下拉只鎖定版 + 內容可見 + 唯讀 | PASS | stages=1(locked)、下拉=1、格 disabled、儲存/設鎖定/刪除鈕皆 hidden |
| 2 | 唯讀寫入 API 全被後端擋(403) | PASS | save=403、另存=403、鎖定=403 |
| 3 | 唯讀進無鎖定版鞋型：顯示提示、看不到一般版 | PASS | stages=0、「尚無鎖定版」提示、工序格數=0 |
| 4 | admin 對照：看所有版本(2) + 可編輯（不受唯讀限制） | PASS | stages=2、下拉=2、格可編輯、儲存可見 |

截圖：`readonly_shots/01_ro_locked_view.png`、`02_ro_no_locked.png`、`03_admin_all_versions.png`

## 做法摘要
### 沿用現有 role 機制（沒新造一套）
- 新增 `app.py::_ie_locked_only()`：`_auth_user()` role == 'read_only' → True（admin/manager/data_entry → False）。
- 版本清單 `GET /api/ie/stages/<hid>` → `db.get_ie_stages(hid, locked_only=_ie_locked_only())`：locked_only 時 WHERE `is_approved=1`（只回鎖定版）。
- 讀工序 `GET /api/ie/cell/<hid>` → `db.get_ie_cell_data(..., locked_only=_ie_locked_only())`：
  - 有鎖定版 → 強制讀鎖定版（忽略前端傳的 stage_id，唯讀不能挑別版）。
  - 沒鎖定版 → 回 `{no_locked: True, zones: []}`，不給看一般版。
- **寫入本來就已擋**（未新增）：save/add/insert/delete/group 走 `_can_edit_ie`（read_only→403）；approve/unlock/delete-stage 走 `_require_manager`（read_only→403）。

### 前端
- `loadSegment`：`DATA.no_locked` → mainContent 顯示「🔒 此鞋型尚無鎖定版」提示，不 render 工序表。
- `init`：`!CAN_EDIT` → 直接隱藏「儲存▼」入口（不靠 renderZones，沒鎖定版時也不殘留）。
- 版本下拉自動只剩鎖定版（來源 API 已過濾）。
- 編輯格 disabled、設鎖定版/解鎖/刪除鈕由既有 `isManager()` gate（read_only 非 manager→隱藏）、儲存/另存由既有 `applyReadOnlyDOM`（CAN_EDIT false）隱藏。

### admin/manager/data_entry 不受影響
- `_ie_locked_only` 只在 role=='read_only' 為真 → 其餘角色 locked_only=False，版本清單/讀工序照舊（看所有版本）。步驟4 驗證 admin 看 2 版本、可編輯。

## 正式 DB 驗證（測後）
- ie_process 20434、approved=0（測試在副本，未污染）；正式 DB **無 viewer1**（read_only 帳號仍只有 tongcai/dianno/dacu）；無殘留副本。

## 範圍聲明
- 只做唯讀帳號的檢視限制，未動已完成的版本控制邏輯（分版/鎖定/刪除/編制表）。
- 既有 `/api/ie/review/list` 500 與本步無關，待收尾。
