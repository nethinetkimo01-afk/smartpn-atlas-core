# SmartPN Atlas Demo — 模擬數據世界 v1.0
Version: v1.0 | 2026-06-13
Status: Demo 唯一數據來源。Brand端 / Supplier端 / Boss BI 全部用同一套，數字互相對得上。
File: 37_DEMO_MOCK_DATA.md

---

# 原則

1. 一個一致的世界：Brand 搜到的材料 = Supplier 維護的材料 = Boss BI 的營收來源
2. 數字可互相驗證：BI 總營業額 = 各公司營收加總 = 各產品營收加總
3. 像真的：真實材料名、合理單價、合理 LT
4. If 12 is enough, do not use 100

---

# 1. 供應商集團（Demo 主角 = Formosa Materials Group）

## 母公司
**Formosa Materials Group**（台灣）— Boss view 的主體

## 子公司
| 公司 | 國家 | 主力產品線 |
|------|------|----------|
| Formosa Vietnam Co. | 越南 | 網布、合成皮 |
| Formosa Indonesia Co. | 印尼 | 薄膜、二次加工 |

## 其他供應商（Brand 搜尋時的競爭者）
| 公司 | 國家 | 特點 |
|------|------|------|
| Apex Textile Co. | 台灣 | 紡織專精，DPP-ready |
| Sunrise Synthetics | 越南 | 低價、LT 長 |

---

# 2. 材料庫（12 筆，SPU 層）

| # | SmartPN ID | 材料名 | 分類 | Supplier | 單價 | LT | 狀態 | DPP |
|---|-----------|--------|------|----------|------|----|----|-----|
| 1 | SPA-MAT-0001 | Recycled Polyester Mesh 220g | 紡織 | Formosa Vietnam | $2.00/m | 30d | OPEN | ✅ |
| 2 | SPA-MAT-0002 | TPU Laminating Film 0.15mm | 薄膜 | Formosa Indonesia | $1.45/m | 25d | OPEN | ✅ |
| 3 | SPA-MAT-0003 | PU Synthetic Leather 1.2mm | 人造皮 | Formosa Vietnam | $3.80/m | 35d | OPEN | — |
| 4 | SPA-MAT-0004 | Full Grain Cow Leather | 皮料 | Apex Textile | $8.50/sqft | 45d | OPEN | ✅ |
| 5 | SPA-MAT-0005 | Jacquard Knit Upper 380g | 紡織 | Apex Textile | $4.20/m | 28d | OPEN | ✅ |
| 6 | SPA-MAT-0006 | EVA Foam Sheet 4mm | 薄膜 | Sunrise Synthetics | $1.10/m | 40d | OPEN | — |
| 7 | SPA-MAT-0007 | Recycled Polyester Mesh 220g | 紡織 | Sunrise Synthetics | $1.85/m | 50d | OPEN | — |
| 8 | SPA-MAT-0008 | Microfiber Suede 0.8mm | 人造皮 | Apex Textile | $5.60/m | 32d | OPEN | ✅ |
| 9 | SPA-COMP-0101 | Laminated Black Mesh (2nd) | 二次加工 | Formosa Indonesia | $3.30/m | 38d | OPEN | ✅ |
| 10 | SPA-MAT-0010 | Ripstop Nylon 70D | 紡織 | Formosa Vietnam | $2.75/m | 30d | PRIVATE | — |
| 11 | SPA-MAT-0011 | Bio-based TPU Film | 薄膜 | Formosa Indonesia | $2.90/m | 42d | PRIVATE | ✅ |
| 12 | SPA-COMP-0102 | Bonded Knit + Foam (2nd) | 二次加工 | Formosa Vietnam | $4.85/m | 36d | PRIVATE | — |

關鍵設計：
- #1 和 #7 同名材料、不同 supplier（Find Same Material 的 Identical 案例：$2.00/30d vs $1.85/50d — 便宜但慢）
- #10-12 PRIVATE：External view 看不到
- #9、#12 二次加工：料號 SPA-COMP 順序編碼（無規則原則）

---

# 3. SKU 範例（SPA-MAT-0001 之下）

| SKU | 顏色 | 幅寬 | 單價 | LT |
|-----|------|------|------|----|
| sku-001-BLK-58 | Black | 58" | $2.00/m | 30d |
| sku-001-WHT-58 | White | 58" | $2.05/m | 30d |
| sku-001-BLK-44 | Black | 44" | $1.90/m | 28d |

Find Same Material 帶入條件：SPU=SPA-MAT-0001 + SKU=sku-001-BLK-58
→ Identical：Sunrise 的同款（SPU相同+SKU規格相同）
→ Alternative：sku-001-BLK-44（同SPU不同SKU）

---

# 4. 評論（S17 邏輯）

| 材料 | 留言者 | 星等 | 內容 | 可見性 |
|------|--------|------|------|--------|
| SPA-MAT-0001 | Brand-A 開發部 | ★★★★★ | 品質穩定，交期準 | 同公司 |
| SPA-MAT-0007 | Brand-A 採購部 | ★★ | 兩次延誤交期 | 同公司 |
| SPA-MAT-0004 | Brand-B 材料部 | ★★★★ | 認證齊全 | 公開 |
| Apex Textile（公司頁） | Brand-C | ★★★★★ | DPP 資料配合度高 | 公開 |

---

# 5. Boss BI 數據（Formosa Group，數字互相對得上）

## 總營業額：$4.08M（YTD），同比 +12%，環比 +3%

## 各公司佔比（加總 = 總額）
| 公司 | 營收 | 佔比 |
|------|------|------|
| Formosa Vietnam | $2.45M | 60% |
| Formosa Indonesia | $1.63M | 40% |

## 產品銷售佔比（前4 + 其他 = 100%）
| 產品 | 佔比 |
|------|------|
| Recycled Mesh (0001) | 31% |
| PU Leather (0003) | 22% |
| TPU Film (0002) | 18% |
| Laminated Mesh (0101) | 14% |
| 其他 | 15% |

## 利潤比
| 產品 | 利潤率 |
|------|--------|
| Laminated Mesh (二次加工) | 28% |
| PU Leather | 19% |
| Recycled Mesh | 15% |
| TPU Film | 11% |
（洞察：二次加工最賺 — Boss 一眼看到該推什麼）

## 現金流明細（含入帳預計日）
| 客戶 | 金額 | 條件 | 預計入帳 |
|------|------|------|---------|
| Factory Group A (VN) | $380K | Net 60 | 2026-07-15 |
| Factory Group B (ID) | $215K | Net 45 | 2026-06-28 |
| Factory Group C (VN) | $142K | Net 90 | 2026-08-20 |

## 應收帳齡
| 桶 | 金額 |
|----|------|
| 0-30d | $310K |
| 31-60d | $260K |
| 61-90d | $125K |
| >90d | $42K（紅色警示） |

## 客戶集中度
前三大客戶 = 68%（Factory A 35% / B 21% / C 12%）→ 黃色提醒

## 報價成交率
本季報價 24 張，成交 9 張 = 37.5%

## 誰看過我的材料
| 公司 | 次數 |
|------|------|
| Brand-A | 12 |
| Brand-B | 7 |
| Factory Group D | 3 |
（模糊模式：歐洲運動品牌 ×2、亞洲代工集團 ×1）

## 報價有效期提醒
| 報價單 | 客戶 | 到期 | 狀態 |
|--------|------|------|------|
| Q-2026-018 | Brand-A | 6/20 | 🔴 7天內 |
| Q-2026-021 | Factory B | 7/05 | 🟡 30天內 |
| Q-2026-023 | Brand-C | 8/12 | 🟢 |

---

# 6. PPT 數據邊界

S01-S17 PPT 的數據依 16 號規格 LOCKED（Data 1/2/3/4、spu-01 等通用標籤），**不套用本檔真實名稱** — PPT 是教育工具，通用標籤是刻意設計（噪音最小化原則）。
本檔只管 SMARTPN_DEMO.html / SMARTPN_DEMO_SUPPLIER.html 兩個系統 Demo。
