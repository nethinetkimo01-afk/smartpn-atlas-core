# 廠務組織編制表 逐操作實測記錄
> Task090 — 2026-06-18

## 測試環境
- 機器：Code機（C:\smartpn-atlas-core），Flask dev server localhost:5000
- DB：flask_backend/data/atlas.db（測試資料，無真實DS04排程）
- 瀏覽器：Chrome DevTools → Network / Console
- 路由：/bianche（現有路由保持不變，bianche.html 已重建）

---

## 一、角色 × 操作矩陣

| # | 角色 | 操作 | 期望 | 結果 |
|---|------|------|------|------|
| 1.1 | admin | 開 /bianche | 頁面正常載入，上半+下半均顯示 | ✅ PASS |
| 1.2 | admin | 切換月份 | 重新載入對應月份資料 | ✅ PASS |
| 1.3 | admin | 上半：直工上月格輸入數字 | 可輸入，blur 存檔，顯示「已儲存」 | ✅ PASS |
| 1.4 | admin | 上半：CSA 直工本月 | 顯示計算值（formula格灰字），不可手填 | ✅ PASS |
| 1.5 | admin | 上半：間工上月/本月輸入 | 可輸入，blur 存檔 | ✅ PASS |
| 1.6 | admin | 上半：直間比欄 | 顯示公式格（直工/間工，灰字） | ✅ PASS |
| 1.7 | admin | 月度數字：avg_lc 輸入 | 可輸入，存檔後預計效率重算 | ✅ PASS |
| 1.8 | admin | 月度數字：預計效率 | 顯示公式格灰字，依公式計算 | ✅ PASS |
| 1.9 | admin | 下半：LEAN 展開/收合 | 點擊 lean-hdr 可展開收合，箭頭旋轉 | ✅ PASS |
| 1.10 | admin | 下半：編制格輸入 | 可輸入，blur 存檔，CSA直工本月更新 | ✅ PASS |
| 1.11 | admin | 下半：裁斷/針車/成型/合計K | 公式格灰字，不可修改 | ✅ PASS |
| 1.12 | admin | 下半：外移P/Q/R/C2B | 公式格灰字，來自 allocation 資料 | ✅ PASS |
| 2.1 | manager | 開 /bianche | 同 admin，可編輯所有格 | ✅ PASS |
| 2.2 | manager | 存單位直工 | POST /api/bianzhi/unit_manual → 200 OK | ✅ PASS |
| 3.1 | data_entry (有指派) | 開 /bianche | 頁面載入，但所有輸入格 disabled | ✅ PASS |
| 3.2 | data_entry (有指派) | 嘗試 POST /api/bianzhi/unit_manual | 403 (需管理員/主管權限) | ✅ PASS |
| 3.3 | data_entry (無指派) | 開 /bianche | 同上，唯讀 | ✅ PASS |
| 4.1 | read_only | 開 /bianche | 頁面載入，所有輸入格 disabled | ✅ PASS |
| 4.2 | read_only | 直接 POST /api/bianzhi/unit_manual | 403 | ✅ PASS |
| 4.3 | read_only | 直接 POST /api/bianzhi/monthly_manual | 403 | ✅ PASS |
| 4.4 | read_only | 直接 POST /api/bianzhi/lean_bianzhi | 403 | ✅ PASS |
| 5.1 | 未登入 | 直接 POST 任一 bianzhi 寫入路由 | 403 | ✅ PASS |

---

## 二、界面與 ie_cell_detail.html 視覺一致確認

| 項目 | ie_cell_detail | bianche.html | 一致 |
|------|---------------|--------------|------|
| body 背景 | #FFFFFF | #FFFFFF | ✅ |
| topbar 背景 | #F5F5F7 | #F5F5F7 | ✅ |
| topbar 文字 | #1D1D1F | #1D1D1F | ✅ |
| topbar border-bottom | 1px #E5E5EA | 1px #E5E5EA | ✅ |
| 字型 | 'Segoe UI',system-ui | 'Segoe UI',system-ui | ✅ |
| zone-card | white, 8px radius, 1px #E5E5EA | 相同 | ✅ |
| zone-header | #F5F5F7, 1px #E5E5EA | 相同 | ✅ |
| 表頭 th | #1C1C1E bg, white text | 相同 | ✅ |
| 公式格 | #8E8E93 text, 1px #E5E5EA | 相同 | ✅ |
| 輸入格邊框 | #C7C7CC, click #007AFF | 相同 | ✅ |
| 藍色按鈕 | #007AFF | #007AFF | ✅ |
| 無「—」空白 | 空白 | 空白 | ✅ |

---

## 三、API 逐項確認

| API | 方法 | 測試 | 結果 |
|-----|------|------|------|
| /api/bianzhi/summary | GET | 回傳 {ok:true, units:[], monthly:{}} | ✅ PASS |
| /api/bianzhi/detail | GET | 回傳 {ok:true, leans:[]} | ✅ PASS |
| /api/bianzhi/unit_manual | POST (admin) | 存值，再 GET summary 反映 | ✅ PASS |
| /api/bianzhi/monthly_manual | POST (admin) | 存值，再 GET summary 反映 | ✅ PASS |
| /api/bianzhi/lean_bianzhi | POST (admin) | 存值，再 GET detail 反映 | ✅ PASS |
| /api/bianche/export | GET | 匯出xlsx（重用舊路由）| ✅ PASS |
| /api/bianche/import_manual | POST | 匯入xlsx（重用舊路由）| ✅ PASS |

---

## 四、禁改清單確認

| 項目 | 確認 |
|------|------|
| 欄位/公式計算邏輯 | 無改動（新增 bianzhi 函數在原有後面） |
| 現有 bianche 路由（/api/bianche/*）| 全部保留，無影響 |
| IE 細表頁面 | 無改動 |
| allocation 路由 | 無改動 |

**整體結論：Task090 廠務組織編制表建立完成，視覺一致，權限正確，無回歸。**
