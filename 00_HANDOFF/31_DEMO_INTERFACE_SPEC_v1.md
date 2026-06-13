# SmartPN Atlas Demo — 界面規格 v1.0（Jim 確認版）
Version: v1.0 | 2026-06-12
Status: CONFIRMED by Jim 2026-06-12（8問答覆）。Demo 開發唯一依據。
取代：30_DEMO_INTERFACE_SPEC_DRAFT.md

---

# 1. 核心概念（Jim 原話精神）

Brand / Factory 看到的不是管理系統——是一個 **Apple 風格的購物網站**。
功能像購物網：購物車、我的帳戶、我的最愛、設定、公司主頁、產品主頁、評論。
材料卡片可標示「可提供 DPP / Compliance 資料」→ 品牌能搜到 DPP-ready 的 supplier。
這就是 supplier 由被動變主動：資料維護 = 商業曝光。

---

# 2. Brand / Factory 端（共用同一 view）

## 2.1 頂部導覽（購物網式）
- 搜尋欄（大）
- My Favorites（我的最愛）
- Cart（購物車概念 → 在 SmartPN 語境 = My Library 待確認名稱，先用 My Library）
- My Account（我的帳戶）
- Settings（設定）

## 2.2 頁面結構（三層主頁）
1. **公司主頁**（Company Profile）— supplier 公司介紹、認證、DPP/compliance 能力標示、該公司材料列表
2. **產品主頁**（SPU 頁）— 材料主體資訊、圖片、評論區
3. **產品+規格主頁**（SPU+SKU 頁）— SKU 選項列（Apple 選規格式）、單價、LT、Find Same Material

## 2.3 搜尋功能
- 單價（by SPU）和 LT 顯示在搜尋結果，**也是搜尋條件**（可按單價/LT篩選）
- 可搜尋「可提供 DPP / compliance 資料」的材料或 supplier
- Find Same Material：帶入 SPU+SKU 條件，Identical / Alternative 區分

## 2.4 評論功能
- 產品主頁有評論區（對應 S17 邏輯：private / shared 可見性）

## 2.5 Compare
- 排版參照 Apple 比較頁（apple.com 產品比較），數量上限依 Apple 慣例（3-4個）

---

# 3. Supplier 端 — 選單只有兩項（Jim 確認）

```
1. 公司建立
   ├─ 母公司
   ├─ 子公司
   └─ 各公司的：關務資訊 / 稅務資訊 / 材料訊息

2. SmartPN 建立
   ├─ 原物料
   ├─ 二次加工
   ├─ 權限管理
   └─ 單價管理
```

（原 Dashboard / Requests / My Profile 不是頂層選單，可作為頁內元素）

---

# 4. 權限設計（Jim 確認）

## 4.1 授權對象 = 公司 + 個人
- Brand 端身份：**公司 + 單位 + 名字**
- 授權到「某公司的某個人」

## 4.2 Supplier 內部角色分工
- **資料建立者** — 建資料的人
- **權限決定者** — 管理資料給誰看的人
（呼應 S09 的 editor / publisher 角色）

## 4.3 欄位資料夾（自定義群組）
- Supplier 建立資料夾並命名（例：關務資料夾 / 財務資料夾 / 原物料資料夾）
- 打勾決定哪些欄位屬於該資料夾
- 以資料夾為單位 → 開放給某公司的某人

## 4.4 預設狀態
- 新材料建立後：**全部 PRIVATE**，supplier 主動授權

---

# 5. 單價與報價（Jim 確認，分兩部分）

## 5.1 單價欄位（by SPU）
- 含 LT，顯示在 Brand 搜尋界面
- 是搜尋條件之一

## 5.2 報價單（Quotation）
- Supplier 建立報價單，自動帶入客戶訊息
- 報價層級三選：SPU / SPU+SKU / SPU+SKU+備註
- 透過 SmartPN 平台授權給特定帳號查看
- **本期範圍：只做報價記錄的交換**
- 最終成交單價：暫不記錄，未來依需求決定

---

# 6. Mock 資料
- 數量 Claude 決定（原則：If 10 is enough, do not use 100）
- 材料圖片：找網路系列圖，越像正式網站越好
- 建議：12筆材料、3家supplier、含 DPP-ready 標示差異

---

# 7. 視覺
- 100% Apple 風格（已確認規則不變）
- Brand 端 = Apple 商店購物體驗
- Supplier 端 = Apple 設定頁風格

---

# 8. 邊界（不變）
- 不存 BOM / 不做交易金流（報價記錄交換 ≠ 交易）/ 不做登入頁 / Scenario 不進選單 / 不發 unified code

---

## 補充確認（2026-06-13）

編碼規則：
- 每個材料有兩個號碼：GS1 code（可能有）+ SmartPN code（一定有）
- SmartPN 編碼排除字元：0（像O）/ 1（像I）/ I / O / E
- 純序號或亂碼，不帶任何資訊意義

單向可見性（核心設計）：
- Supplier 看不到 Brand/Factory 的資料
- Supplier 不能主動搜尋 Brand/Factory
- 只有 Brand/Factory 能發出好友邀請
- Supplier 接受邀請後才能互看、互聯絡
- 目的：保護 Brand/Factory 不被 Supplier 騷擾

My Library：
- 個人材料庫，每個帳號各自獨立
- 有分享給同公司其他帳號的功能

Requests：
- 即時對話功能（像購物網客服）
- Send Request 功能
- Supplier 在 Dashboard 收到通知

Find Same Material 搜尋範圍：
- OPEN 材料 + 已授權給這個帳號的材料
- 不是全平台搜尋
