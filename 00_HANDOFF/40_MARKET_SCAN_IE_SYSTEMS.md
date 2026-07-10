# 市場掃描：市售 IE / 工時系統對比（2026-07）

> 建立：2026-07-10（中樞市場研究記錄）
> 目的：釐清 SmartPN 相對市售「IE／標準工時」系統的定位與差異化，供 GTM / 產品方向參考。
> 相關檔：`39_VERSION_CONTROL_DESIGN.md`（版本控制＝我們護城河的核心）、
> `10_GTM_STRATEGY.md` / `20_GTM_STRATEGY.md`（GTM）、`27_SMARTPN_LAYER_DEFINITION.md`（分層定義）。

---

## 一、市面主流產品

| 產品 | 供應商 / 背景 | 型態 | 核心方法 | 定位 / 賣點 | 價位 |
|---|---|---|---|---|---|
| **GSDCost** | Coats Digital | SaaS | GSD / PMTS 預定動作時間 → SMV | **業界 de-facto 標準**；品牌＋vendor 共同語言；提升生產力 ~10% | 約 5,000 美金級 |
| **SewEasy GSD** | 斯里蘭卡（25 年） | Web-based / 免安裝 | 影片分析 + GSD | 200+ 語言、變異追蹤、免 MTM2 license 可稽核、競爭價格 | 競爭價 |
| **Pro-SMV** | — | PMTS | MTM / MODAPTS based | 預定時間標準 | — |
| **Engineered TruCost (ETC)** | — | PMTS | MTM / MODAPTS based | 工時 + 成本 | — |
| **MODSEW** | — | PMTS | MODAPTS based | 縫製動作標準 | — |

**共通點**：全部都是「**怎麼得到標準工時**」——用 TMU／動作分析（GSD/MTM/MODAPTS）推導 SAM/SMV。

---

## 二、他們的核心 vs 我們的定位

- **他們的核心 = 算標準工時**：用 TMU / 動作分析得 SAM / SMV。賣的是「**怎麼得到標準時間**」。
- **我們不做算工時**（直接輸入標準時間）。我們做「**標準時間之後**」：
  版本控制 / 鎖定基準（trusted source）/ 編制表 / offline 撥人 / 滿載率 / IE 達成率。
- **結論：定位不同，不是競品。**
  - 他們 = **工時來源**（upstream，把動作變成秒數）。
  - 我們 = **工時之後的產線管理與成本治理**（downstream governance）。
  - 這是 SmartPN 的差異化：**STANDARD ZERO ZONE — governed shared language**。

```
動作分析(GSDCost/SewEasy…) → 標準工時(SMV/SAM)
                                   │  ← 他們到這裡為止
                                   ▼
        SmartPN：版本控制(鎖定基準=trusted source)
                 → 編制表(ART→鎖定IE實際人數→offline撥人→C2B)
                 → 滿載率 / IE 達成率 → 管理決策
```

---

## 三、值得學的（中樞建議）

1. **共同語言、跨品牌/工廠對齊**：GSDCost 最強賣點，與 SmartPN shared language 方向一致 → **可強化**。
2. **Allowances 標準化**：SAM = 基本時間 + bundle(10%) + machine/personal(20%)；基本時間全球統一、寬放各廠在範圍內校準。
   我們已有「寬放 %」，可學其「**標準化 + 可校準**」的做法。
3. **變異追蹤**：盯「標準 vs 實際」差異 = 我們的 **IE 達成率**，方向對 → **可深化**。
4. **影片化工序分析**：未來可考慮（動作/工序錄影對照）。
5. **多語系**：SewEasy 200+ 語言；我們已有 中/英/越，方向對。
6. **web-based 免安裝免升級**：我們架構已是，方向對。

---

## 四、我們相對他們的優勢（護城河）

- **版本控制 + 鎖定基準（trusted source）**：他們沒有「對外基準版 + 變更歷史可追溯」的治理層。
  （對應 `39_VERSION_CONTROL_DESIGN.md`：鎖定版 = 對外基準、鎖定版變更歷史、送審審核 workflow。）
- **編制表**（排程 → ART → 抓鎖定 IE 的「實際人數」→ offline 撥人 P/Q/R → C2B 最終編制）：
  他們算工時，不做這種**產線人力治理**。
- **護城河一句話**：**SmartPN 不是「算工時」，是「工時之後的 governance」。**

---

## 五、一句話定位（對外可用）

> 市售系統把「動作」變成「標準工時」；**SmartPN 把「標準工時」變成「可信基準 + 產線人力/成本治理」**——
> 從一堆會變的數字，變成跨品牌/工廠對齊的 trusted shared language。
