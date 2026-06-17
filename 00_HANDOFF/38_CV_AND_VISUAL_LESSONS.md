# CV 製作與視覺系統教訓記錄
Version: v1.0 | 2026-06-15
Status: CONFIRMED — 從今天的錯誤中整理，新視窗必讀

---

## 今天犯的錯誤，不能再犯

### 錯誤 1：沒有先定義目標就開始做
Claude 直接開始做圖，沒有先問「CV 的目標是什麼」「輸出物是什麼」「結構是什麼」。
**正確做法：** 定義目標 → 確認輸出 → 拆解步驟 → 派工。永遠不跳步驟。

### 錯誤 2：讀文件只看有沒有，不看內容
Claude 讀了 S01 Demo Logic，但做圖時完全沒有用 S01 的表格邏輯、顏色規則、before/after 結構。
**正確做法：** 讀完立刻用。讀而不用 = 沒讀。

### 錯誤 3：自己設計視覺風格
Claude 自己畫了 before/after 方塊圖，沒有照 Jim 已有的三張參考圖。
**正確做法：** 做任何 CV 或簡報圖片前，必須先看參考圖。參考圖在這個 repo：
- Transparency.png
- What_is_the_problem.png
- Root_cause_and_solution.png

### 錯誤 4：把 SmartPN Atlas 放進 CV 圖片
CV 是賣 Jim 這個人，不是賣 SmartPN Atlas。品牌高層要看到的是「這個人解決過我的問題」，不是「這個產品有多厲害」。
**正確做法：** 圖片邏輯 = 品牌的痛（左）→ 解決後的結果（右）。不提工具名稱。

### 錯誤 5：不知道 CV 視覺系統就開始做
黑底金字 = LinkedIn 圖片 / PPT 視覺系統。
白底 Apple 風格 = Demo 軟件 / CV 視覺系統。
**正確做法：** 先確認用哪套視覺系統，再做圖。

### 錯誤 6：派工錯誤
圖片生成是 ChatGPT 的工作，不是 Claude 的工作。Claude 的工作是給正確的 image prompt。
**正確做法：** Claude 寫 prompt → Jim 用 ChatGPT 生成 → Jim 確認 → 繼續下一張。

### 錯誤 7：讓 Jim 重傳已傳過的圖
Jim 在這個對話傳過三張參考圖，Claude 沒有用，逼 Jim 重傳。
**正確做法：** 收到圖的那一刻，立刻確認視覺系統，然後才開始做。

---

## CV 結構（已確認）

**格式：** 橫式，白底，Apple 風格，1分鐘讀完

**Section 1 — What I Can Contribute**
- 總結一句話：整合製造端供應鏈，讓品牌拿回利潤、減少人員、擴大材料庫、為 downstream 做準備
- 六張圖（P1–P6），每張圖下一句說明

**Section 2 — Who I Am**
- PDM / ERP / 標準化經驗
- 懂 Brand / Factory / Supplier 三方關係
- 英文非母語，面試前請考慮

**Section 3 — What I'm Looking For**
- 重視數據管理的公司
- 尊重無形資產的公司
- 提供高於市場標準薪資的公司

---

## CV 格式與結構（已確認 2026-06-16）

**格式：** 橫式，多頁 PDF

**頁面順序：**
- 第 1 頁：Section 1 — 針對該公司的貢獻（六個點）
- 第 2-7 頁：P1-P6 六張圖，每張一頁，圖多字少
- 第 8 頁：Section 3 — What I'm Looking For
- 第 9 頁：Section 2 — Who I Am（含聯絡資訊）

**設計邏輯：**
高層第一頁看貢獻，六張圖看痛點，最後才看人是誰。
記住的是問題，不是背景。

---

## 六個 Contribution Title（已確認）

P1 — Reclaim your hidden margin from the manufacturing side.
P2 — Less manpower. More accuracy. In your material library.
P3 — Fast factory transfer. Consistent quality. Flexible FOB.
P4 — Reclaim your group purchasing power.
P5 — Supplier performance. Digitized.
P6 — Fast fashion. Optimized.

---

## 視覺系統對照

| 用途 | 視覺系統 |
|------|---------|
| LinkedIn 圖片 / PPT | 黑底、白字主標題、金色關鍵字、左右對比、問題紅色、解法藍色 |
| Demo 軟件 / CV | 白底、Apple 風格、乾淨卡片、無裝飾 |

---

## 圖片派工規則

1. Claude 確認每張圖的邏輯（對應哪個 Scenario，左邊是什麼問題，右邊是什麼結果）
2. Claude 寫 ChatGPT image prompt
3. Jim 生成圖片
4. Jim 確認後繼續下一張
5. 六張全部確認後，Claude 整合成完整 CV 文件

---

## Jim 的做事邏輯（永遠遵守）

定義目標 → 確認輸出 → 拆解步驟 → 派工 → 永遠不跳步驟

Claude 的角色：Central brain — 分析、討論、拆解、派工、抓錯誤。
不是執行者。不是圖片生成工具。不是自動決策者。

---

## 當前狀態（2026-06-15）

- CV 結構：確認
- Section 1 文字：確認
- 六個 title：確認
- 圖片：待 ChatGPT 生成（P1–P6 prompt 待 Claude 輸出）
- Section 2 / Section 3 文字：待細化
- CV 文件整合：待圖片確認後進行

---

## CV 完整結構（最終確認 2026-06-16）

頁面順序：
第1頁：Section 1 — VF 開頭 + 六個貢獻點
第2頁：What I Have Built（System 01 + System 02）
第3-8頁：P1-P6 六張圖
第9頁：Section 3 — What I'm Looking For
第10頁：Section 2 — Who I Am

## What I Have Built（第2頁確認）

System 01 — Material Identity Management
三主軸：Identity / Governance / Decision
底部：Demo available in a confidential setting

System 02 — IE & Workforce Planning
數字：290 shoe models / 20,434 IE process records / 4 departments / 20+ factory users
技術：Python · Flask · SQLite · AI

底部句子：Both systems were designed and built using AI. Both are available for confidential demonstration.
圖片：已由 ChatGPT 生成確認 ✅

## P1-P6 六張圖核心邏輯（已確認）

P1：料號統一 → 價差透明 → 拿回隱藏利潤
視覺：Brand-MTL-Code vs Unified-code（紅）
圖片：已由 ChatGPT 生成確認 ✅

P2：Supplier 自維護 → Brand 少做反而得到更大更新更完整的材料庫
視覺：紙標籤人工收集 vs 數位化乾淨
圖片：已由 ChatGPT 生成（待修改，精髓未完整表達）

P3：Shared BOM → 品牌拿回對材料的掌控權 → 品質透明可控
視覺：同款鞋 不同布+不同 code vs 同款鞋 相同布+Shared BOM
圖片：已由 ChatGPT 生成確認 ✅

P4：料號統一 + Supplier 母子公司對應 → 第一次有真實採購量 → 議價從被動變主動
視覺：三廠分散採購 vs 合併總量一個數字議價
圖片：待生成

P5：線上收集 Supplier performance → 取代 audit → 機密設置只供品牌內部
視覺：待生成

P6：Find Same Material → 最短 LT → 加快上市時間
視覺：待生成

## Section 2 最終確認版

Experience: 20 years on the manufacturing side of footwear and apparel.
Specialization: PDM / ERP / material standardization across 4 factories in 3 countries in Southeast Asia.
Current Work: Designed and deployed an internal manufacturing AI system: 290 shoe models, 20,434 IE process records, automated monthly workforce planning across 4 departments, serving 20+ factory users via LAN. Built with Python / Flask / SQLite using AI throughout the design and development process.
Perspective: I understand how Brand, Factory, and Supplier actually work together — and where the gaps are.
On working with AI: The first mile, you must build yourself — the goal, the strategy, the structure, the first visible result. Once that foundation exists, AI can help you build the next 99. If you expect AI to build all 100 miles from nothing, it never will. Without direction, AI is just a word. With it, AI becomes the most powerful tool you have ever used.
Language: English is not my first language. Please consider this before interview.

## Demo 策略（已確認）

面試時攜帶兩個 Demo：

System 1 — Material Identity Management
說法："I've been designing a material identity governance system for footwear and apparel manufacturing. I can share more in a confidential setting if you're interested."

System 2 — IE 分析系統
說法："I also built an internal workforce planning system using Python and AI, currently used by 20+ factory staff across 4 departments."

兩個都帶 laptop，現場 demo。

## 各品牌職位分析（已確認）

共同要求：
1. 供應鏈 domain 知識（製造/採購/品質/計劃）
2. 把業務痛點轉成產品需求
3. 和工程師/數據科學家有效溝通
4. 有真實產品交付經驗

各品牌差異：
VF：AI 數據產品 + 供應鏈 domain，翻譯官角色
Nike：數據產品生命週期，工具經驗
Adidas：SCM 流程和系統 Product Owner
ON Running：高速成長，供應鏈 AI 轉型

現階段符合的職缺：
優先：VF Corporation 新加坡（立刻投）
追蹤：Nike 新加坡 / ON Running 亞洲區

Jim 核心差異點：
20年製造端經驗 + PDM/ERP 標準化（4廠3國）+ 兩個真實 AI 系統 = 市場上沒有其他人能說這句話

---

## CV 最終結構修正（2026-06-17）

第1頁：VF 開頭 + 兩個 AI 系統開場（簡短，讓高層想繼續翻）
第2頁：What I Have Built（System 01 + System 02 詳細展開）
第3-8頁：P1-P6 六張圖
第9頁：Section 3 — What I'm Looking For
第10頁：Section 2 — Who I Am

第1頁 vs 第2頁差別：
- 第1頁：兩個系統標題 + 一句話，吸引高層翻下去
- 第2頁：兩個系統完整細節（Identity/Governance/Decision + 數字）
