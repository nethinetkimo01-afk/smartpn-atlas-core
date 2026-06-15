# SmartPN Atlas ???Ｗ??脫?
Version: v1.0 | 2026-05-28

## 1. Naming Rules
- Formal name: SmartPN Atlas
- NEVER use SmartPN alone
- Allowed: SmartPN Atlas ID, After SmartPN Atlas

## 2. Product Positioning
SmartPN Atlas is a manufacturing-side material identity governance layer.
NOT: ERP, PLM, PDM, BOM storage, marketplace, purchasing platform, transaction platform, complete DPP generator.
Core question: How do we make one material mean the same thing across supplier, OEM/factory, and brand?

## 3. Locked Language
Primary slogan: More time for what matters.
Core principle: Let the right people do the right thing.
Key sentence: Trusted outputs require trusted data at the source.
Always say: manufacturing-side supply chain

## 4. Four Principles
1. Atomic Authorization: Authorization must reach SPU level. SKU is child attribute only.
2. ID Mapping: Never force suppliers to change ERP. SmartPN Atlas = Mapping Layer.
3. Readiness Governance: Only Ready to Publish or Missing Metadata. Never hide missing items.
4. Visual Minimalism: Lime green #deff9a ONLY for Unified ID.

## 5. Jim Founder Positioning
IS: manufacturing-side operator, standardization practitioner serving SE Asia OEMs and suppliers
IS NOT: SaaS salesman, DPP expert, ESG consultant, compliance vendor, policy commentator
Strongest claim: I understand how the manufacturing side actually works.

## 6. BOM Boundary
Brand keeps BOM in its own system.
Factory keeps BOM in its own system.
SmartPN Atlas provides material identity reference and permission governance ONLY.

## 7. 層定義（Layer Definitions）

SmartPN Atlas 運作在三個層之間：

| 層 | 英文 | 說明 |
|----|------|------|
| 身份層 | Identity Layer | 每個材料的唯一 SmartPN Atlas ID + 基礎屬性 |
| 治理層 | Governance Layer | 誰可以看、誰可以改、誰可以發布（OPEN / PRIVATE / PENDING） |
| 語言層 | Language Layer | 跨供應商、品牌、工廠的共同命名標準（Shared Language） |

這三層不與任何一方 ERP 綁定。各方保留自己的 ERP，SmartPN Atlas 只做映射和治理。

## 8. SGL 候選名詞

SGL = Shared Governed Language（共同治理語言）

候選用法（待 Jim 確認方向）：

| 候選名稱 | 用途情境 |
|---------|---------|
| Shared Governed Language | 正式文件、品牌定義 |
| SGL | 技術文件、API 文件縮寫 |
| Governed Shared Language | 現行 slogan 中的用法（已鎖定） |
| Standard Zero Zone | 場域定語，搭配 slogan 使用 |

注意：Governed Shared Language 已作為 primary slogan 鎖定，SGL 作為縮寫時指向同一概念。

## 9. GRANT Layer Definition (暫定 2026-06-10)

Layer name: GRANT（暫定，非縮寫，用字義本身）

**Definition:**
GRANT is a manufacturing-side system layer that governs the authorization of source data — what data is released, to whom, in what precision, by the data owner's decision.

GRANT 是製造端的系統層，治理 source data 的授權——什麼資料、釋放給誰、釋放到什麼精度，由資料擁有者決定。

**Layer comparison:**

| Layer | Manages |
|-------|---------|
| ERP | Enterprise resources |
| PLM | Product lifecycle |
| WMS | Warehouses |
| GRANT | Data authorization |

**Core sentences:**
- 製造端缺一個 GRANT 層
- 沒有 GRANT 層，supplier 不敢開放資料，Shared Language 無法 scale
- SmartPN Atlas is the first GRANT system for footwear and apparel manufacturing
- Access is not taken. It is granted.

**Data qualities in GRANT:** timely（及時）、trusted（可信）、precise（精準）

**GRANT 操作機制（2026-06-13 確認）：**
- Supplier 自建資料夾（自行命名）→ 打勾選欄位屬於該資料夾 → 授權給指定公司+單位+帳號
- 同一欄位可屬於多個資料夾
- 新材料預設全 PRIVATE
- Access is not taken. It is granted.

**Status:** 暫定。取代先前 MSDG / SGL / GATE 候選。正式定案前所有對外文件先不使用。

## 10. 視覺系統（唯一標準）（2026-06-13 確認）

- 所有輸出：Demo 軟件 / Scenario PPT / 官網 — 100% Apple 風格
- 參考：Apple.com 產品頁（iPad 規格選單）
- 純白背景 / SF Pro 字體 / 0.5px #D2D2D7 細線 / 無邊框無陰影 / 大量留白
- 黑底版本：REJECTED，永不使用
- LinkedIn 圖片：獨立系統（白底+Jim頭像+行銷版面）

## 11. 系統名詞（正式）（2026-06-13 確認）

- SPU → **Product**
- SKU → **Option**
- 所有界面統一使用 Product / Option，不使用 SPU / SKU

## 12. 單向可見性（核心設計原則）（2026-06-13 確認）

- Supplier 看不到 Brand/Factory 的資料
- Supplier 不能主動搜尋 Brand/Factory
- 只有 Brand/Factory 能發出好友邀請
- Supplier 接受後才能互看互聯絡
- 目的：保護 Brand/Factory 不被騷擾

## 13. SmartPN 編碼規則（2026-06-13 確認）

- 每個材料有兩個號碼：GS1 Code（可能有）+ SmartPN Code（一定有）
- SmartPN 編碼排除字元：0（像O）/ 1（像I）/ I / O / E
- 純序號或亂碼，不帶任何資訊意義
- 料號編定後不可更改
- SPU 物性改變 = 新材料新料號

## 14. My Library（2026-06-13 確認）

- 個人材料庫，每個帳號各自獨立
- 有分享給同公司其他帳號的功能

## 15. Requests / 即時對話（2026-06-13 確認）

- Brand/Factory 可向 Supplier 發出 Request
- 即時對話功能（像購物網客服）
- Supplier 在 Dashboard 收到通知後才能回應

## 16. 評論（2026-06-13 確認）

- 私密：只有同公司帳號可見
- 公開：所有人可見（包含 Supplier）
- Supplier 完全看不到 Brand 的私密評論

## 17. Find Same Material 搜尋範圍（2026-06-13 確認）

- OPEN 材料 + 已授權給這個帳號的材料
- 不是全平台搜尋

## 18. Supplier 財務資料（2026-06-13 確認）

- 收款方資訊：銀行名稱 / 帳號 / Swift Code / 收款幣別 / 發票抬頭
- 不是付款條件（那是買方）

## 待確認

- CV 是什麼？Jim 尚未說明，等待確認後補入
