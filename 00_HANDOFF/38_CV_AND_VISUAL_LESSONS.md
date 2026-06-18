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

## 2026-06-17 CV 製作進度（六張圖內容全部定案）

### 視覺系統（全套統一）
- 白底 Apple 風格、Inter / SF Pro 字體、主色橘 #B5540D。
- 每頁底色框標籤：CURRENT（淺灰底深灰字）/ CONTRIBUTION（橘底白字），固定左上。
- 橘色只用在 Contribution 側。CURRENT 側中性黑灰。
- 每頁底部一句洞察金句（母語語感，不中翻英）。
- 設計鐵律：左右或上下結構必須一致，只有「變化的部分」不同。
- 標題一致性：標題由排版層統一加（靠左、同字體大小顏色），圖一律生成「不含標題純圖」再嵌入。

### CV 結構（順序）
1. 封面頁（極簡：應徵職位為主角、名字次要。兩版 A/B 待 Jim 選。職位：VF Product Owner, AI Products & Data）
2. 開場（VF CORPORATION — WHAT I CAN CONTRIBUTE + 合併段）
3. Performance and Potential Contribution to VF（What I Have Built 圖 + 句：Both systems were built with AI tools — but only clear AI communication logic makes AI work. Without direction, AI is just a word. Currently applied to internal department management.）※Jim 預計重做
4. System 01 區塊 P1–P6（六張滿版圖）
5. System 02：IE & Workforce Planning
6. What I'm Looking For（三圖示卡）
7. About Me（AI 心得 + Language + 聯絡）

### 六張圖定案
- P1（圖已生成）Reclaim your hidden margin from the manufacturing side. 雙欄同布同吊牌，吊牌兩行 Brand/Factory。左 Brand=Brand-MTL-Code $10、Factory $8 → With Hidden Margin；右 Brand 寫成 Factory-MTL-Code $8（橘不劃掉）→ No Hidden Margin。金句：Hidden margin exists when the same material carries different identities. Unify the identity, and the gap disappears.
- P2（Claude 排表格）Less manpower. More complete. Real-time. 上下比較，欄 MTL|Updated by|Updated|Price。Updated by 合併（上 Brand 跨2、下 Supplier 跨4）。上 CURRENT 2 筆 past 10；下 CONTRIBUTION 4 筆 MTL-2 today橘/8、MTL-3、MTL-4橘 today。標記 Less Manpower（Brand↔Supplier）、Real-time（兩箭頭指上下 MTL-2 價 10 與 8）、More Complete（指 MTL-3/4），Real-time 與 More Complete 右側對齊。金句：Accurate, real-time data is the supplier's responsibility — because they are the source.
- P3（Claude 排表格）Fast factory transfer. Consistent quality. Flexible FOB. 左右比較，身份合併格 Brand BOM/Factory BOM。左 Factory BOM 用 FTY-Code-01/02/03；右 Factory BOM 改 MTL-Code-1/2/3（橘）=Shared BOM。Brand BOM 不變。右側不要 callout 框。金句：A shared BOM makes sure every factory uses the same materials — easy to transfer, consistent in quality.
- P4（Claude 排表格）Reclaim your group purchasing power. 左 MTL|Volume|Supplier（10/20/30）；右多一欄 Supplier Group 合併格「Supplier-group」橘跨三列。不算總量。金句：Link suppliers to their parent company, and negotiate with the combined volume — not the scattered parts.
- P5（圖已生成）Supplier performance. Digitized. 左 Performance→mail→3人中2人收到；右 Performance→系統(隱私鎖)→3人全到。中性不貶低。金句：Performance, recorded in real time and kept private — for your purchasing and development teams to evaluate materials.
- P6（Claude 排表格）Fast fashion. Optimized. 欄 MTL|Product|Density|Supplier|LT。左 1 筆 MTL-1/Foam/30/Supplier-1/30；右 MTL-1 同料（MTL/Product/Density 合併跨三列），Supplier-1/2/3，LT 30/35/20，最短 20 橘。金句：The "Search Same Material" function finds the shortest LT to support fast-fashion design demand.
- IE（System 02 圖示型）IE & Workforce Planning。左 CURRENT—Fragmented：3 人各自電腦各連自己硬碟；右 CONTRIBUTION—Centralized：3 人位置與左相同，全連中央資料庫（橘）。金句：From fragmented local files to one centralized system — IE data, shared and consistent.

### 派工原則
- 表格型 P2/P3/P4/P6 → Claude 程式排版。
- 具象圖示型 P1/P5/IE → GPT 生成。
- 視覺/排版專業細節 Claude 主動判斷並建議，不反問 Jim。

### 待辦（下次開機接續）
1. 封面頁：Jim 選 A 或 B。
2. 第1頁：On the supply chain → On the manufacturing-side supply chain。
3. 第4頁 P2：補上 CURRENT/CONTRIBUTION 底色框（前版漏）。
4. 標題全頁統一。
5. IE 頁重做到 P5 品質。
6. 圖改「不含標題純圖」，標題由排版層加。
7. 第2頁 Jim 預計重做。

### 新教訓
- 錯誤 12：漏掉既定元素（P2 忘放 CURRENT/CONTRIBUTION 底色框）。預防：每頁產出前對照「全套共通元素清單」逐項核對。
- 錯誤 13：prompt 沒寫「左右位置完全相同」，致 IE 圖左右人物排列不一致。預防：凡對比圖，prompt 必含「兩側結構/位置完全相同，只有變化部分不同」。

## 2026-06-17（續）CV 統一版面框架 + 四張表格完成

### 統一版面框架（所有對比頁共用，已對齊）
- 每頁固定位置：系統名稱 eyebrow（橘色小標，主標上方）→ 主題大標 → CURRENT/CONTRIBUTION 底色框 → 內容區 → 底部金句。
- CURRENT / CONTRIBUTION 底色框：**等寬 150px、同樣式、同位置**（CURRENT 淺灰底深灰字、CONTRIBUTION 橘底白字）。
- P1–P6 系統 eyebrow 一律 MATERIAL IDENTITY MANAGEMENT；IE 頁不要主題大標，只放系統名稱 IE & WORKFORCE PLANNING（當標題大小）。
- 排版抄 Apple keynote 做法（eyebrow + 大標）。Jim 對排版細節不出意見，Claude 主動判斷。

### 封面頁（已定）
- 極簡，應徵職位為主角、名字次要。版式：APPLICATION FOR（橘 eyebrow）→ Product Owner / AI Products & Data（大標兩行）→ VF Corporation → 橘色短線 → Jim Kao → 聯絡資訊。
- 聯絡資訊（jim.kao@smartpn.com.tw · linkedin.com/in/jim-k-969579339）已從 About Me 移到封面。About Me 不再放聯絡。

### 派工與目前狀態
- Claude 排（表格型，已完成並填入統一框架）：P2、P3、P4、P6。
- GPT 生（圖示型，待 Jim 重生「不含標題純圖」後由 Claude 嵌入框架）：P1、P5、IE。
  原因：標題要全頁統一，圖內不可自帶標題；標題由排版層統一加。
- P2 細節定案：下區「Supplier」橘色（Brand 黑）；today/MTL-3/MTL-4 橘；Real-time 兩箭頭指上 MTL-2 價(10) 與下 MTL-2 價(8)；Real-time 與 More Complete 標記框左緣對齊、箭頭轉折對齊成一條竖線（x=940）。
- 第2頁 Performance：圖區留白待重做；底部句已定：Both systems were built with AI tools — but only clear AI communication logic makes AI work. Without direction, AI is just a word. Currently applied to internal department management.

### 技術環境（接手須知）
- CV 是用 Python + playwright(chromium) + Inter 字體（@fontsource/inter, npm 安裝）渲染成多頁 PDF，非 GitHub 程式碼。
- 主色橘 #B5540D、白底、Inter/SF Pro、16:9（1280x720）。
- Jim 上傳的圖：CV_P1_hidden_margin（含標題版）、P5（含標題版）、What I Have Built（第2頁）。純圖版待 Jim 重生。
- 最新檔：Jim_Kao_CV_VF_v3.pdf（12 頁：封面/開場/Performance/P1留白/P2/P3/P4/P5留白/P6/IE留白/What I'm Looking For/About Me）。

### 待辦（下次接手）
1. 給 Jim P1、P5、IE 的「不含標題純圖」prompt（圖內不放標題、頂部留白；其餘內容照各頁定案）。
2. Jim 重生純圖後，Claude 嵌入統一框架（標題由框架統一加）。
3. 第2頁 Performance 重做。
4. 全部到齊後輸出完整 CV PDF。

### 新教訓
- 錯誤 14：CURRENT/CONTRIBUTION 底色框各頁大小不一（寬度跟著文字跑）。預防：底色框固定等寬同樣式同位置，全 CV 一致。
- 錯誤 15：標記框與箭頭未對齊（Real-time/More Complete 歪）。預防：右側標記框左緣對齊、箭頭轉折統一在同一 x。
- 錯誤 16：圖內自帶標題導致與排版頁字體不一致。預防：圖一律生成「不含標題純圖」，標題由排版層統一加。

## 2026-06-18 CV 接近完成（v6，12 頁）

### 結構（最終，12 頁）
封面 → 前言 → 轉場(Performance and Potential Contribution to VF) → System 01: IE & Workforce Planning → System 02 六貢獻(Identity→Governance→Decision 順序) → About Me。What I'm Looking For 已移除。

### 重大變更（全部完成）
- 系統順序對調：IE = System 01（先）、Material Identity Management = System 02（後）。
- 轉場頁卡片：左 IE / 右 Material，移除 SYSTEM 01/02 字樣，用程式重排取代舊圖。底部句：Both systems were built with AI tools — but only clear AI communication logic makes AI work. Without direction, AI is just a word. Currently applied to internal department management.
- 六貢獻按主軸重排：NP1=Less manpower(IDENTITY) / NP2=Fast factory transfer(GOVERNANCE) / NP2b=Shared BOM vs Actual BOM vs Trusted Source(GOVERNANCE,新增S05多廠版) / NP3=Reclaim hidden margin(DECISION) / NP4=Group purchasing(DECISION) / NP5=Supplier performance(DECISION) / NP6=Fast fashion(DECISION)。eyebrow 格式：MATERIAL IDENTITY MANAGEMENT · IDENTITY/GOVERNANCE/DECISION（不放 System 02 字樣）。
- 標題統一：全頁「橘色系統名稱 eyebrow 在上 + 黑色主標在下」上下排。IE 也給主標：One centralized system for the whole factory.
- 三張純圖已嵌入（Jim 重生「不含標題純圖」，標題由排版層加）：P1 hidden margin、P5 performance、IE。檔案：/tmp/p1_pure.png、p5_pure.png、ie_pure.png（皆 1672x941，頂部留白）。
- CURRENT/CONTRIBUTION 底色框全頁等寬 150px、同樣式同位置。
- 封面已含聯絡資訊；About Me 移除聯絡。
- 第1頁：On the manufacturing-side supply chain。

### S05 新增頁（NP2b, Governance）
標題 Shared BOM vs Actual BOM vs Trusted Source.（原 Actual DPP 改 Trusted Source）。
表格：行=部位(Toe cap/Quarter/Shoelace/Outsole)；欄=Shared BOM(Brand) + Actual BOM 三廠(China/Vietnam/Indonesia)，子標題 MTL Code，料號 -Code。
Brand 與三廠之間有垂直區隔線（兩區）。Alternative 用橘色：China·Quarter=Factory-China-Alternative、Vietnam·Outsole=Factory-Vietnam-Alternative。
金句：Material alternatives stay under brand control — and expand easily to a new factory when needed.
另有 S05 內容 Excel 已交付：/mnt/user-data/outputs/S05_content.xlsx（Jim 要自己做示意圖用）。

### P2 箭頭（最終，已驗證乾淨）
- Real-time / More Complete 完全對稱：同起點 x=800、同轉折竖線 x=920、標記框 x=965。Real-time 從上 MTL-2 價(10)+下 MTL-2 價(8)匯聚；More Complete 從 MTL-3 價(10)+MTL-4 價(10)匯聚。
- Less Manpower：拿掉穿表格箭頭（箭頭穿表格會壓字卡線，是設計坑，禁用）。標記置中對齊到「Updated by」欄中心、垂直在兩表之間，靠位置說明 Brand→Supplier 轉變。
- 下區「Supplier」橘色（Brand 黑）。

### 技術
- builder: /tmp/build_cv_v4.py 輸出 /mnt/user-data/outputs/Jim_Kao_CV_VF_v6.pdf。Python+playwright(chromium)+Inter 字體。主色橘 #B5540D。
- 圖示型派 GPT/Jim 生純圖；表格型 Claude 程式排。

### 待辦（下次接手）
1. hidden margin(NP3) 左右兩塊布看起來不一樣（GPT 無法複製同一塊布）。可靠解法：Jim 重生「單塊布+空白吊牌」單圖，Claude 程式複製成左右兩份保證一致再填吊牌字。Jim 未決定做或維持現狀。
2. 依各家 JD 分品牌改版：VF 為基礎版；Nike 新加坡(SAP,製造端供應鏈治理角度)、ON Running(Lead TPM Supply Chain AI)。Jim 會給各家 JD，依 JD 決定改封面職位+公司名+強調重點，非只換名。
3. Jim 可能換掉某些不重要的 slide（剛新增 S05/NP2b，未指定移除哪張）。

### 新教訓
- 錯誤 17：箭頭穿越表格會壓字、卡線、難對齊——禁止用「箭頭穿進表格指向欄位」的做法；改用置中標記+對齊基準，或從表格邊緣外引線到右側標記。
- 錯誤 18：元素位置不可隨意擺放，必須有明確對齊基準（如 Less Manpower 對齊到 Updated by 欄中心）。
- 錯誤 19：細節（壓字、未對齊）Claude 必須自己放大檢查到乾淨再交付，不可讓 Jim 一一糾錯。
