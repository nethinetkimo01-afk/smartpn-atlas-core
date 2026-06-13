# SmartPN Atlas — 總工單 2026-06-12
Version: v1.0 | 2026-06-12
Status: Jim 授權 Claude 全權安排。Code 依序執行，每任務完成即 push，中斷可續。

---

## 工具分工

| 工具 | 負責 |
|------|------|
| Claude chat (Fable) | 規格整理、派工、QC 審查、下一批設計 |
| Claude Code | 全部檔案操作、Demo 開發、GitHub push |
| Jim | 看結果、做決定（Kate郵件/GTS note/GRANT定案） |

---

## Code 執行順序（依序，每步 push）

### Step 1 — 規格入庫
- Downloads\33_DEMO_SPEC_v1_2_ADDENDUM.md → 00_HANDOFF\
- （若 32 號尚未入庫，一併處理）
- 更新 00_ENTRY_POINT.md 索引（32、33）
- push

### Step 2 — 確認上批任務狀態
- 檢查 git log：32 號規格的 Demo 升級（首頁廣告/最新上架/分類樹/新視窗find-same/評論/排序/星等/unsplash圖、supplier母子公司/編碼規則/Boss BI v1）是否完成
- 未完成的先補完
- push

### Step 3 — Boss BI 升級為 8 指標（SMARTPN_DEMO_SUPPLIER.html）
1. 總營業額（同比/環比箭頭）
2. 產品銷售佔比（橫條圖）
3. 各公司營收佔比
4. 利潤比
5. 現金流明細表（含入帳預計日期）
6. 應收帳齡（30/60/90分桶）
7. 客戶集中度（前三大客戶）
8. 報價成交率
mock 數據、CSS 圖表、Apple 風格。push。

### Step 4 — 「誰看過我的材料」隱私分級版（Supplier 端）
- 預設：公司名+次數（Brand-A 查看 12 次）
- 切換：行業/地區模糊層級
- 註明永不顯示個人
- 另加：報價有效期提醒、資料完整度分數條
push。

### Step 5 — Brand 端補漏
- 確認卡片星等、LT/單價排序存在，缺就補
push。

### Step 6 — QC 全面檢查
- S01-S17 PPT 對照 16 號規格，產出 docs\preview\PPT_QC_REPORT.md
- S01-S17 Demo HTML 同樣檢查，結果併入報告
- 發現差異直接修正
push。

### Step 7 — 倉庫健康
- flask_backend/data/*.db 加入 .gitignore（atlas.db 64MB 接近上限）
- git rm --cached flask_backend/data/atlas.db（保留本地檔案）
push。

### Step 8 — 收尾
- 更新 21_CURRENT_STATUS.md：今日全部進展 + 待 Jim 決定清單
- push 並回報完成摘要

---

## 待 Jim 決定（不擋工，有空處理）

1. Kate Nishimura 郵件發送（29號文件 Part 2，READY）
2. GTS note 填聯絡人名（Part 3）
3. S02 LinkedIn post 確認（Part 5）
4. GRANT 層名稱正式定案（目前暫定）

---

## Claude chat 下一批（Code 跑完後）

1. 審查 QC 報告，列修正清單
2. 模擬三角色完整走一次 Demo，產出體驗測試報告
3. 設計 Demo 給第一個供應商 Boss 看的演示腳本
