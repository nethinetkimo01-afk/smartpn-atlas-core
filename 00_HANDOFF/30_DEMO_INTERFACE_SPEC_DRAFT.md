# SmartPN Atlas Demo — 完整界面規格（Claude 理解版，待 Jim 修改確認）
Version: v0.1 | 2026-06-11
Status: DRAFT — Jim 逐項確認：✅ 對 / ✏️ 改（直接改字）/ ❌ 刪
確認完成後此文件升級為 30_DEMO_INTERFACE_SPEC.md v1.0，成為 Demo 開發唯一依據

---

# A. 系統角色（3種視角）

| # | 角色 | 看到什麼 | 確認 |
|---|------|---------|------|
| A1 | Brand / Factory view | 自己 Library + 被授權的材料 + 所有 OPEN 材料 | ☐ |
| A2 | Supplier view | 自己全部材料 + 維護功能 + 權限管理 | ☐ |
| A3 | External view（未授權者） | 只看到 OPEN 材料 | ☐ |

切換方式：右上角 role toggle（Demo 用，正式版由登入帳號決定）

---

# B. Brand / Factory 端 — 功能選單

```
B1. Material Search        材料搜尋（Apple 商店式，預設首頁）
B2. My Library             我的材料庫（已 Add 的材料）
B3. Compare                材料比較（最多?個並排）        ← ?數量未確認
B4. Requests               向 supplier 請求資料（缺欄位時）
B5. BOM Reference          BOM 參照（只是參照，不存 BOM）
```

| 確認點 | 我的理解 | 確認 |
|--------|---------|------|
| B-1 | 選單就這5項，不多不少 | ☐ |
| B-2 | Compare 並排數量上限 = ___ 個（Jim 填） | ☐ |
| B-3 | Requests 是獨立選單，還是只在 Detail 頁出現按鈕？ | ☐ |

---

# C. Brand 端 — 核心流程（購物網邏輯）

```
C1 搜尋
   Material Search 首頁
   ├─ 頂部搜尋欄（關鍵字）
   ├─ Filter chips：All / Raw material / Secondary / OPEN only
   └─ 材料卡片網格（含圖片）

C2 卡片 → 點擊 → Material Detail（SPU + SKU 頁）
   ├─ 材料圖片（大圖）
   ├─ SPU 主體資訊：SmartPN ID / Name / Category / Composition
   ├─ SKU 選項列（像 Apple 選容量）：Color / Spec / Width...
   ├─ Supplier 名稱 ──點擊──→ C4 Company Profile
   ├─ [Find Same Material] 按鈕 ──→ C5
   ├─ [Add to My Library] 主按鈕
   ├─ [Compare] 次按鈕
   └─ [Request Missing Data] （欄位不全時出現）

C3 權限對照（同一頁，不同人看到不同欄位）
   Brand 已授權 → 看到授權欄位
   未授權     → 只看到 OPEN 欄位

C4 Company Profile（公司介紹頁）
   ├─ 公司名 / 簡介 / 認證
   └─ 該公司的材料列表（依我的權限過濾）

C5 Find Same Material（帶條件搜尋）
   ├─ 自動帶入當前 SPU + SKU 為條件
   ├─ 結果分兩區：
   │   Identical    = same SPU + same SKU（不同 supplier，比 LT/價格）
   │   Alternative  = same SPU + different SKU
   └─ 客戶可修改條件（如改 SKU）重新搜尋
```

| 確認點 | 我的理解 | 確認 |
|--------|---------|------|
| C-1 | SKU 在 Detail 頁是「選項列」呈現（像 Apple 選 128GB/256GB） | ☐ |
| C-2 | 切換 SKU 時，頁面資訊跟著變（LT、價格、規格） | ☐ |
| C-3 | 價格欄位 Brand 看得到嗎？還是要 supplier 授權才看到？ | ☐ |
| C-4 | Company Profile 包含哪些欄位？我列的對嗎（名/簡介/認證/材料列表）？ | ☐ |
| C-5 | Find Same Material 結果排序依據 = ___（LT短優先？價格？） | ☐ |

---

# D. Supplier 端 — 功能選單

```
D1. Dashboard              待辦概覽（pending requests 數）
D2. Company                公司建立 / 總部子公司管理
D3. SmartPN
    ├─ 原物料建立          SPU + SKU 結構
    ├─ 二次加工建立        Input + Output + Ratio
    └─ Permission          權限管理
D4. Requests               收到的資料請求（Approve / Decline）
D5. My Profile             公司資料完整度
```

| 確認點 | 我的理解 | 確認 |
|--------|---------|------|
| D-1 | 選單就這5項？ | ☐ |
| D-2 | 28號文件的 Quotation / Reports 要不要進這版 Demo？ | ☐ |

---

# E. Supplier 端 — Permission 設計（昨天確認，最重要）

```
E1 產品權限：By SPU
   每個 SPU 一個權限設定，SKU 繼承，不能單獨設

E2 欄位群組（Supplier 自定義）
   步驟1：建立群組，自己命名（例：關務欄位 / 財務欄位）
   步驟2：打勾 ✓ 哪些欄位屬於這個群組
          例：關務欄位 ✓Composition ✓HS Code ✓Origin
   步驟3：以群組為單位，授權給指定帳號
          例：關務欄位 → 授權給 brand-A-customs@xxx

E3 權限矩陣（界面呈現）
   行 = SPU / 欄位群組
   列 = 帳號（或公司）
   格子 = 授權狀態
```

| 確認點 | 我的理解 | 確認 |
|--------|---------|------|
| E-1 | 授權對象是「帳號」？還是「公司」？還是兩層都有？ | ☐ |
| E-2 | 一個欄位可以同時屬於多個群組嗎？ | ☐ |
| E-3 | 預設狀態：新材料建立後全部 PRIVATE，要主動授權？ | ☐ |
| E-4 | OPEN 的意思 = 對所有人公開該 SPU 的基本欄位？基本欄位是哪些？ | ☐ |

---

# F. 視覺規則（已確認，列出供檢查）

| 項目 | 規則 | 確認 |
|------|------|------|
| F-1 | 100% Apple 風格：純白 / #1D1D1F / 0.5px #D2D2D7 細線 / 無框無陰影 | ☐ |
| F-2 | Material Search = Apple 商店產品列表 | ☐ |
| F-3 | Material Detail = Apple 產品購買頁（規格選單式） | ☐ |
| F-4 | 名詞：Add to My Library / Compare / Maintained by | ☐ |
| F-5 | 狀態純文字色：OPEN 綠 / SHARED 藍 / PRIVATE 灰 | ☐ |

---

# G. 邊界（不做的，防止 Demo 長歪）

| 項目 | 不做 | 確認 |
|------|------|------|
| G-1 | 不存 BOM（Brand/Factory BOM 留在自己 ERP） | ☐ |
| G-2 | 不做交易 / 下單 / 金流 | ☐ |
| G-3 | 不做登入頁（這版 Demo） | ☐ |
| G-4 | Scenario S01-S17 不進系統選單（那是 PPT） | ☐ |
| G-5 | 不發 unified code（mapping only） | ☐ |

---

# H. 我不確定、需要 Jim 補充的

| # | 問題 |
|---|------|
| H-1 | Factory 和 Brand 的界面有差異嗎？還是這版 Demo 共用同一個 view？ |
| H-2 | 二次加工材料在 Search 結果怎麼標示？（卡片上有 Secondary 標籤？） |
| H-3 | Request Missing Data 送出後，Brand 端在哪裡追蹤狀態？ |
| H-4 | Demo 用的 mock 材料數量：幾筆夠？（規則說 If 10 is enough, do not use 100） |

---

# Jim 操作方式

1. 下載這份文件
2. 直接在上面改：✅ / 改字 / 刪掉 / 在 H 區回答
3. 丟回來給我
4. 我整理成 v1.0 → Code 一次做對，不再來回
