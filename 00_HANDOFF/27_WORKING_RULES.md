# SmartPN Atlas — 工作規則與錯誤預防（2026-06-20更新）

---

## ★ 零、設計第一原則（Jim 定 2026-06-20，凌駕所有功能）

**假設使用者完全不懂、不看說明、會亂點。系統必須：**

1. **不用教就會用** — 功能一眼看懂在哪、做什麼，不需記網址/培訓
2. **不可能做錯** — 危險操作要確認、不該點的不顯示、填錯當場擋並給清楚提示
3. **符合直覺** — 存檔像Excel（直接存不跳框，只有另存才跳框）；有框=可填，無框=結果
4. **錯了能救** — 誤刪有提示、未存變更離開要攔截、重要操作可復原
5. **狀態看得見** — 存了沒/改了沒/輪到誰一眼可知

**每個界面任務先過這關（站笨蛋使用者立場想：會在哪卡、點錯什麼），再交 Code。**

---

## ★ 零之一、格子視覺規則（2026-06-20 定案，IE 細表＋廠務編制表通用）

| 格子類型 | 樣式 |
|---|---|
| **手工輸入格** | 白底 + 清楚灰色細邊框 `1px solid #C7C7CC`，常駐顯示成框（空值/有值框都清楚） |
| **自動計算格** | 無框、無底色、純黑數字 `#000000` |

- 嚴禁「點了才出現輸入框」
- 當欄位由手工改公式時，格子樣式須同步由白框改無框純數字
- 配色：表頭/分區列可有顏色；**其餘所有儲存格白底、純黑字(#000000)、圖示純黑**

---

## ★ 零之二、全系統 UX 鐵則（2026-06-20 定案，永久標準）

1. **存檔行為比照 Excel**：直接「儲存」= 靜默存檔不跳框，存完顯示「已儲存✓」2秒淡出；只有「另存新階段」才跳確認框
2. **功能必須有看得到的入口**：嚴禁要使用者手打網址才能進功能
3. **有未存變更離頁前攔截**：`beforeunload` + 切換操作前 confirm
4. **危險操作必須確認**：刪除行/帳號等不可逆操作，點擊要跳「確定刪除？此操作無法復原」
5. **表單防呆**：空白/格式錯誤/重複當場擋並顯示清楚錯誤訊息，不讓使用者建出壞資料

詳細規格見 **29_UX_RULES.md**

---

## ★ 零之三、三台電腦角色（2026-06-20 最終定案）

| 電腦 | 角色 | 操作 |
|---|---|---|
| **Code 機**（另一台） | 跑 Claude Code 改程式 | 改完 push GitHub |
| **中樞** | Jim 下指令/決策/demo | 指揮 Code、看結果 |
| **ME129** | 純資料儲存+跑系統(production) | **只按更新鍵**，不敲指令 |

中樞關機不影響 ME129（ME129 獨立 24h 跑）。所有更新時機由 Jim 指揮。
ME129 啟動鏈：`smartpn.bat`(`py`) → `watchdog.py`(`sys.executable`) → `serve.py`(waitress)

---

## ★ 零之四、目標總帳對帳（2026-07-14 定案，永久標準）

`47_GOAL_LEDGER.md` ＝全部未結事項的單一真相表。中樞鐵則：
1. **定案即入帳**：任何定案/需求一產生，立即在 47 表新增一列並編 ID（G-NN），不得只留在對話或散落各檔。
2. **開場先對帳**：每個新視窗開場、每批任務派發前，中樞先讀 47 對帳，回報未結項與卡點。
3. **僅 Jim 可關帳**：狀態改 ✅CLOSED 只有 Jim 可為之；中樞只能更新進度/卡點，不得自行關帳。

---

## 一、錯誤檢討

### 根本錯誤
給了標準界面 xlsx，沒有第一天就用 Python 逐格讀完每個 sheet，
靠記憶和猜測給 Code，導致整個禮拜在糾錯。

### 為何掃描標準界面還是會漏
1. 只讀了部分 sheet，沒有讀全部
2. 讀了但沒有確認每個區的欄位差異（YINGHUI 跟裁斷機不同，Laser 只有裁斷欄）
3. 讀了數據但沒有產出預覽給 Jim 確認，直接給 Code
4. 每次只修 Jim 指出的問題，沒有整體對照標準界面

### 預防方法
1. 任何涉及界面/欄位/格式/公式的任務：
   必須先用 Python 讀取來源 xlsx 每個 sheet 的每個格子
   產出預覽給 Jim 確認
   Jim 說 OK 才給 Code

2. Jim 說的每句話立刻記錄進 GitHub，不是對話結束才整理

3. 在 Jim 確認前：禁止給 Code 任何執行指令

4. 不懂就說，不猜

## 二、IE 表完整規格（2026-06-16定案）

### Cutting 段（9項）

① 裁斷機區：
材料类别|序号|部件名称|层数|件数|刀数/H|
裁断標時(公式=3600/G/E*F)|裁断理人(公式=標時÷eolrDiv)|裁机要求人数(手工)|
印線/畫線標時(手工)|印線理人(公式)|
削皮標時(手工)|削皮理人(公式)|
貼補強標時(手工)|貼補強理人(公式)|
涂邊/烘毛邊標時(手工)|涂邊理人(公式)|
热压標時(手工)|热压理人(公式)

② ATOM區（無刀数/H，標時手工）：
材料类别|序号|部件名称|层数|件数|
標時(手工)|理人(公式)|裁机要求人数(手工)|
印線標時(手工)|印線理人(公式)|
削皮標時(手工)|削皮理人(公式)|
貼補強標時(手工)|貼補強理人(公式)|
涂邊標時(手工)|涂邊理人(公式)|
热压標時(手工)|热压理人(公式)

③ EMMA區：同ATOM區

④ Laser區：
材料类别|序号|部件名称|层数|件数|標時(手工)|理人(公式)|裁机要求人数(手工)

⑤ YINGHUI區：
材料类别|序号|部件名称|层数|件数|
裁断標時(手工)|裁断理人(公式)|裁机要求人数(手工)|
烘鞋垫標時(手工)|烘鞋垫理人(公式)|
轉印鞋垫標時(手工)|轉印鞋垫理人(公式)

⑥ 移印區：
材料类别|序号|部件名称|標時(手工)|理人(公式)

⑦ 轉印區：同移印區

⑧ 水蜘蛛：固定2人，只有實際人數(手工)

⑨ 手工總人數：公式=Σ②③④⑤⑥⑦理論人數

共用規則：
- 公式格灰底(#F2F2F2)不可編輯
- 手工格白底可編輯
- eolrDiv：EOLR=120→30，EOLR=60→60
- 段標題背景#FCE4D6，表頭白底黑字
- × 最左欄，+ 每區最後一行最左
- 七個區固定顯示，沒資料顯示空白表頭+號行

### ① 裁斷機標準時間公式 — 定案（2026-07-12 Jim 定案：×1.1 → ×1.0）
**2026-07-12 Jim 定案：裁斷機標準時間公式改為 `3600 ÷ 刀數 ÷ 層數 × 件數 × 1.0`（取消 ×1.1 係數）。**
- 例：層1 件11 刀1 → 標時 = 3600÷1÷1×11×**1.0** = **39600**；eolr120 理論人數 = 39600÷30 = **1320**。
- 理論人數 = 標時 ÷ (3600 ÷ eolr)（等同 標時 ÷ eolrDiv：eolr120→30、eolr60→60）。
- **取代 2026-07-10「×1.1 正確、不要改」的記錄**（該記錄作廢）。
- 施工：全庫 1.1 係數出現點（前端 recalcCutting* / 後端標時 / 導入腳本）一律改 ×1.0（見 Task 1）。

### ①-H 裁斷段界面改版 — 定案（2026-07-12 Jim 定案，Task H 施工）
四項定案，改寫本節裁斷段規格：

1. **ATOM 區精簡**：只保留裁斷 5 欄（層數／件數／標準時間／理論人數／裁機要求人數）＋材料類別／部件名稱。
   `印线/画线`、`削皮`、`贴补强`、`涂边/烘毛边`、`热压` 五組後製欄**從 UI 移除、總計排除**；
   **DB 欄位（post_marking_*…post_heat_*）與既有資料保留不刪**（僅不渲染、不計入）。前端由 type B → **type C**。
2. **EMMA 區**：同 ATOM（type B → type C）。
3. **裁斷機區新增「連刀」欄**：下拉 1／2／4／6／8／16（遞增，H-2 加 6），**默認 1**。
   位置（Task H-1 2026-07-13 調整）：**在「層數」左邊** → 順序＝材料類別｜部件名稱｜**連刀**｜層數｜件數｜刀數/H｜標時…（三語表頭同步）。
   匯入：`/api/ie/import/apply` 係**按 DB 欄名**做 source→target 列複製（非按顯示位置），故欄序調整不影響匯入；
   另已補：複製時一併帶 `interlock_cut`（原先漏帶→預設 1）。
   - DB：`ie_process` 加 `interlock_cut INTEGER DEFAULT 1`，既有資料全補 1。
   - **公式改**：`標準時間 = 3600 ÷ 刀數 ÷ 層數 × 件數 × 1.0 ÷ 連刀`；理論人數 = 標時 ÷ (3600÷eolr) 連動。
     例：層1件11刀1 連刀1 → 標時 **39600**；連刀改 **4** → 標時 **9900**、理論同步除 4。
   - **手工標時列不套此公式**（維持手工）。連刀切換即時重算＋存值，**不觸發 loadSegment**（迴歸 Task D flush）。
   - **匯入/導出**：標時取「除完連刀後」的值（recalc 腳本公式亦 ÷連刀，連刀默認1→向下相容）；**36 欄結構不變**。
4. **新增區塊「裁斷手工」**：位置在 **①裁斷機 之後、ATOM 之前**，區塊編號順延
   （①裁斷機 ②裁斷手工 ③ATOM ④EMMA ⑤Laser ⑥YINGHUI ⑦移印 ⑧轉印）。前端 type = **M**。
   - 欄位：`流程名稱`(手工)／`標準時間`(手工)／`理論人數`(公式＝標時÷(3600÷eolr)，灰底)／`要求人數`(手工)。
   - 行為與 ATOM/EMMA 一致：插／刪／＋／匯入、總計行；**計入 cutting 段總計**（後端 hand_total 與
     bianche CUTTING_ZONES 均已納入）。

### Stitching 段

① 主流區
② 支流區
③ 電腦針車AC區
④ 折边區
⑤ 鞋舌組區
⑧ 水蜘蛛（只有實際人數）

①②④⑤欄位：序號|流程名稱(越/中雙行)|正常時間(手工)|寬放率%(手工)|標時(公式=正常×1.1)|生産目標(公式=3600÷標時)|理論人數(公式=標時÷eolrDiv)|實際人數(手工)|機台(手工)|機器數量(手工)|備注

③ 電腦針車AC欄位：序號|流程名稱|雙/1次|換線時間|手工時間|換夾板|機器時間|總共時間(公式)|機器效率(公式)|正常時間(公式)|寬放率%|標時(公式)|生産目標(公式)|理論人數(公式)|實際人數(手工)

### Assembly 段

① 成型主區（Assembly.1 + Assembly.2 合併）
② 成型UV區（成型面照射）
⑧ 水蜘蛛（只有實際人數）

欄位：序號|流程名稱(越/中雙行)|正常時間(手工)|寬放率%(手工)|標時(公式=正常×1.1)|生産目標(公式=3600÷標時)|理論人數(公式=標時÷eolrDiv)|實際人數(手工)|機台(手工)|機器數量(手工)|備注

### STF 段

① 打粗區
② 水洗區（固定人力，不走TCT公式）
③ 貼底區
④ 照射區
⑧ 水蜘蛛（只有實際人數）

①②③④欄位：序號|流程名稱(越/中雙行)|正常時間(手工)|寬放率%(手工)|標時(公式=正常×1.1)|生産目標(公式=3600÷標時)|理論人數(公式=標時÷eolrDiv)|實際人數(手工)|機台(手工)|機器數量(手工)|備注

#### STF 段欄位標準化 — 向 Assembly 看齊（Task L 定案 2026-07-13）
**STF 段所有區塊（打粗/照射/水洗/貼底，及未來新增每一個區）欄位組與成型 Assembly 完全一致**：
`工序名稱｜設備種類｜正常時間(手工)｜寬放%(手工,默認10)｜標準時間(公式)｜生産目標(公式)｜理論人數(公式)｜實際人數(手工)`。
- **公式、默認值、行為全部沿用成型段定義，不另立 STF 版本**：`標準時間 = 正常時間×(1+寬放/100)`（寬放默認10）；
  生産目標＝`3600÷標時`；理論人數＝`標時÷(3600÷eolr)`。實作在共用定義層（getZoneCols / renderCell / _rowStd
  的 `stitching||assembly` 分支併入 `stf`；移除舊 STF 特例：打粗/照射手工標時、貼底×1.1、水洗僅實際人數）。
- **舊資料相容**（照 stitching/assembly 既有 fallback）：既有 STF 列只有 standard_time、無 normal_time →
  標準時間**顯示存值**、維持可用；使用者補填正常時間後**轉為公式值**（公式勝過存值）。**不回填、不重算既有資料。**
- **與 Task J 疊加**：STF 實際人數表頭仍是「EOLR=190 實際人數」三語版（SEG_COL_LABELS.stf，不被本任務蓋回）。
- **36欄導出/編制表 STF MP**（`訂單×TCT÷3600÷222`）**取值不變**：TCT 來源 = `ie_process.standard_time`
  （`get_bianche_dept` 讀 `ip.standard_time AS tct`），僅前端顯示改動，DB 欄位與後端讀取邏輯未改。

#### STF 段「實際人數」欄改名（Task J 定案 2026-07-13）
- STF 段**所有區塊**（打粗/照射/水洗/貼底/水蜘蛛，及未來新增的每一個區）「實際人數」欄標題一律顯示
  **「EOLR=190 實際人數」**。三語：中「EOLR=190 實際人數」/英「EOLR=190 Actual operators」/越「EOLR=190 Số người thực tế」。
- 施工在**STF 段共用表頭定義層**（`SEG_COL_LABELS.stf.actual_operators`，前端 renderZoneCard 讀取）——不逐區硬寫，
  新增 STF 區自動繼承。**只改顯示名稱**：欄位 key（actual_operators）、DB、公式、36欄導出、合併鈕行為全部不動。
  **裁斷/針車/成型段的「實際人數」不改**（只 seg==='stf' 生效）。

### SUM.C2B 公式

裁斷人員 = Cutting段所有理論人數加總
針車人員 = Stitching段所有理論人數加總
成型人員 = Assembly段所有理論人數加總
貼底人員 = STF段所有理論人數加總
各段PPH = 目標產量(120) ÷ 人員
總體效率PPH = 3600÷((3600/裁斷PPH)+(3600/針車PPH)+(3600/成型PPH)+(3600/貼底PPH))
Offline Labor（電腦針車）= 獨立列出，不計入段加總

## 三、導入策略（定案）

批量掃描所有IE xlsx
→ 遇到不確定sheet名稱 → 列出來問Jim一次
→ Jim確認後記錄進sheet對照表
→ 相同名稱自動對應，不再問
→ 導完產出對比表

### Sheet 名稱對照表（已確認）
Cutting/Cutting(da thật)/Cutting_XXX → 裁斷機區
ATOM → ATOM區
Cutting_EMMA → EMMA區
自动裁/自动化 → 依L欄機台名判定(ATOM/LASER/YINGHUI)
AC → 機台歸屬對照表（跳過，只讀取）
Stitching/Stitching（主流）→ 主流區
Sub.Stitching/Sub.Stitching(支流) → 支流區
电脑针车/CS → 電腦針車AC區
折边 → 折边區
Assembly.1/Assembly 1 → 成型主區前半
Assembly.2/Assembly 2 → 成型主區後半
成型面照射 → 成型UV區
打粗 → 打粗區
水洗 → 水洗區
贴大底 → 貼底區
组底面照射/SUM_Stock → 照射區
跳過：SUM.C2B/Chi tiết/Sheet1/Sheet2/同材共裁/AC_XXX

### 導入驗證對比表格式
鞋型|ART|SUM裁斷原始|導入後裁斷|差異|SUM針車原始|導入後針車|差異|SUM成型原始|導入後成型|差異|SUM貼底原始|導入後貼底|差異

差異=0 ✅，差異≠0 ❌標紅

## 四、帳號體系（定案）

三個角色：
1. 管理員：建帳號、指派任務、核准修改、鎖定合格版、決定主表顯示版本
2. 資料建立：填寫IE資料、送審
3. 只讀：看資料不能改

外移單位帳號（三個）：
tongcai=同材共裁自動化
dianno=電腦針車折邊
dacu=打粗水洗照射

## 五、Excel 導出導入（定案）

鞋型+階段+EOLR 先在系統建好才能下載範本
鞋型+階段+EOLR = 唯一值（同鞋型多ART共用一份IE表）
一次上傳一份
可在網頁補，也可在Excel補，兩種都支援

## 六、功能開發完整流程（從目標到完成）

### 正確流程（定案）

Step 1：收到目標
→ 不急著寫 prompt
→ 先問：這個功能涉及哪些角色？每個角色會做什麼操作？

Step 2：模擬所有角色的作業流程
→ 列出每個角色（Admin/管理者/編輯者/外移單位/只讀）
→ 列出每個角色會做的所有操作（正向+反向）
→ 找出設計缺口（沒想到的功能、邊界情況）
→ 有合併就要有解除合併
→ 有新增就要有刪除
→ 有送審就要有核准和退回

Step 3：確認完整規格
→ 把所有場景列給 Jim 確認
→ Jim 說 OK 才開始寫 prompt

Step 4：給 Code 執行
→ prompt 必須包含所有場景的自測步驟
→ Code 必須模擬每個場景，發現問題立刻修正
→ 全部通過才 commit

Step 5：驗收
→ Code 產出每個場景的測試結果
→ 有失敗繼續修，不通過不 commit

### 這次做錯的地方

1. 沒有在開始前模擬所有角色的作業流程
   → 導致 + 和 × 放在主表每行（Jim 才指出問題）

2. 說「功能完成」但沒有完整驗收
   → Code 自測只讀 HTML，看不到視覺問題
   → 導致 Jim 一直截圖糾錯

3. 有合併功能但沒有想到解除合併
   → Jim 說「有功能就要有反向功能」

4. 沒有模擬角色，導致帳號管理/送審/指派/Excel導出等核心功能缺失
   → Jim 說「功能沒完成就不算完成」

### 預防方法

任何新功能開發前：
必須先完成角色模擬清單，Jim 確認後才給 Code
不允許跳過這個步驟

## ★ 改版鐵則（Task R 返工根因 2026-07-13，永久標準）
**demo／系統改版一律在現有版本上「疊加修改」，禁止全新重寫。**
- 驗收**必含功能迴歸**：舊版全部函式／畫面必須存在於新版，**缺一即 FAIL**。
- 做法：以現有檔為基底複製出新版，在其上「加」功能；不得為了加新功能而重寫掉既有功能。
- 提取基準：改版前先 `grep -oE "function [A-Za-z0-9_]+"` 舊版全集，逐一在新版核對存在（Playwright typeof===function）。
- 反例（Task P v2）：全新重寫 demo，丟失 v1 大量函式/畫面（FSM/評論/詢問/公司樹/二次加工編碼…）→ 返工為 v3。

## ★ 禁詞鐵則（Task W-1 定案 2026-07-14，永久標準）
**議會定案的敏感/違規詞（如「毛利率 / gross margin」），連同「否定句」都不准出現在使用者可見文案。**
- 錯例：「不含毛利率」「gross-margin card removed」——雖是否定/移除語氣，但禁詞仍出現在畫面 → FAIL。
- 對做法：改正面表述（例：「僅呈彙總／非敏感經營指標」「aggregate only / non-sensitive metrics」），EN/ZH 同步。
- 涵蓋範圍：使用者可見文案為主；註解/程式碼一併清除以免日後複製擴散。
- 驗收：改版後 `grep -niE "毛利|gross[ -]?margin"`（排除 CSS `margin:`）**全檔歸零**才可 commit。
- 現行禁詞集：毛利率 / gross margin（議會既有三違規：SmartPN Verified、毛利率卡、誰看過我的材料——見 43 號）。

## ★ 分組標題規則（Task Z，Jim 2026-07-14 定案，永久標準）
**區塊內製程分組標題，依「分組工序類型」判斷（非依分組數量）：**
- 分組工序＝**該段本身主工序**（裁斷段的機台分區：裁斷機/裁斷手工/ATOM/EMMA/Laser/YINGHUI 等）
  → **不渲染該段名標題**（頁簽與區塊名已表明，重複＝噪音）。
- 分組工序＝**非本段主工序**（印線畫線/削皮/貼補強/塗邊烘毛邊/熱壓/磨皮/烘鞋墊/轉印鞋墊…）
  → **標題必須保留**，讓使用者看得出這幾欄屬於哪個工序。
- **實作在共用表頭定義層**（`SEG_OWN_GROUP_TITLES` + `segGroupTitle(seg,title)`，`ie_cell_detail.html`），
  針車/成型/STF 段同規則、未來新區塊/新段自動適用。跨欄 colspan 不變 → 欄位對齊/總計列/三語表頭全不受影響。

## ★ 品牌識別分離鐵則（Task UI-1 定案 2026-07-14）
**工廠內部生產系統（IE表/編制表/帳號/勾選表…）不得掛「SmartPN / Atlas」品牌字樣。**
- 原因：SmartPN Atlas 是**對外產品品牌**；工廠內部生產系統是另一套東西，混用會內外混淆。
- 範圍：所有工廠系統頁（`app_shell.html`/`ie_interface.html`/`bianche.html`/`login.html`/`allocation.html`/`admin_users.html`…）
  的標題列、`<title>`、頁尾、favicon alt 一律不得出現 SmartPN/Atlas。外框只留【IE表｜編制表】兩頁簽（最簡，無品牌字）。
- **例外**：`docs/preview/` 下的 SmartPN demo 檔（SMARTPN_DEMO_*）——那才是真正的 SmartPN 產品，不受此限。

## 七、數據庫保護規則（2026-06-17定案）

### 正式庫維運操作＝管理頁按鈕（Task N 定案 2026-07-13）
**正式庫維運操作（重算／還原類）一律做成 admin 管理頁按鈕，預覽→確認→自動備份→可還原；
不派發 cmd 腳本到生產機。ME129 現場只使用，不操作維運。**
- 實作範式（見 `/admin/recalc-cutting`）：① 預覽(dry-run，只算不寫，顯示筆數+前10筆新舊值+排除數)
  → ② 執行(二次確認→先自動整庫備份→重算，顯示實改筆數+備份檔名) → ③ 還原(列備份，一鍵還原，二次確認)。
- **執行中鎖**：重算/還原進行時擋並發（第二人按→409 busy 提示），完成/失敗狀態明確顯示、不靜默。
- 後端函式 `database.recalc_cutting_preview/apply/backups/rollback`（admin 限定）；
  對應 cmd 腳本 `recalc_cutting_x10.py / rollback_cutting_x10.py` **保留為備援/離線**，主要路徑＝管理頁。

### DB 位置與操作原則
- 數據庫（atlas.db）存放在 **ME129** 機器
- 所有用戶連接 ME129 作業，不在本機建立 DB
- 開發只在 Code 機（Claude Code），不在 ME129 改 DB
- git pull 只更新程式碼（.py/.html 等），DB 不受影響

### Schema 變更規則
- 所有 schema 變更必須通過 `python flask_backend/migrate.py`
- migrate.py 只允許：ADD COLUMN / CREATE TABLE / CREATE INDEX
- **嚴禁** 直接執行 DROP TABLE / DROP COLUMN
- migrate.py 執行前自動備份 DB

### 軟刪除規則
- ds04_orders 刪除 = UPDATE SET is_deleted=1，不執行 DELETE
- 已刪除記錄保留在 DB 中，可通過 admin 工具查詢
- 只有 role='admin' 的帳號才可執行不可逆操作

### Edit Log 覆蓋範圍
| 資料表 | Log 表 | 狀態 |
|------|------|------|
| ie_process | ie_edit_log | ✅ 已有 |
| ds04_orders | ds04_edit_log | ✅ 已有 |
| allocation_item | alloc_edit_log | ✅ 2026-06-17 建立 |
| bianche 系列 | bianche_edit_log | ✅ 2026-06-17 建立 |

### 備份機制
- **每日凌晨2點**：`flask_backend/daily_backup.py` 自動備份，保留30天
  - 排程指令：`schtasks /create /tn "AtlasBackup" /tr "python D:\smartpn-atlas-core\flask_backend\daily_backup.py" /sc DAILY /st 02:00 /f`
- **git pull 前**：執行 `flask_backend/pre_update.bat`（取代直接 git pull）
  - 自動備份 → 備份成功 → git pull
- **還原**：`python flask_backend/restore.py --date 20260616`
- 備份位置：`flask_backend/backup/atlas_YYYYMMDD.db`

## 八、三台電腦角色定案（2026-06-17）

### 中樞電腦（討論機，白天開，定期關）
- 與 Jim 討論、看結果、下決策
- 連 http://ME129:5000 看結果
- 不存本地 DB，不跑本地 Flask
- 每次開機：git pull origin main

### ME129（主資料庫，盡量不關）
- 唯一的 Flask server（http://ME129:5000）
- 唯一的 atlas.db（員工所有輸入資料存這裡）
- 員工連 ME129:5000 作業
- 開機自啟：watchdog + Flask
- 每天自動 git pull 更新程式碼（不影響 DB）
- 定時備份：每天把 atlas.db 推送到不關機電腦

### 不關機電腦（Code機，24小時）
- 跑 Claude Code 開發任務
- 完成後立刻 git push
- 接收 ME129 的 atlas.db 備份
- ME129 關機時可切換成備用 server

### 軟體更新流程
Code機完成任務 → git push → ME129 git pull → watchdog重啟Flask → 所有人看到新版本

### DB 備份流程（待實作）
ME129 開機 → 自動把 atlas.db 推送到不關機電腦
每天定時同步一次
實作方式：robocopy 內網同步

### 待實作
- ME129 自動 git pull 排程
- ME129 → 不關機電腦 DB 同步排程
- 不關機電腦設定共享資料夾

### ME129 多開根治（2026-07-10）
**多開根因**：ME129 的 `py` / 開機 bat 抓到 WindowsApps 的 `python3.exe`（Microsoft Store 殼），其 `sys.executable` 異常。watchdog.py 用 `PYTHON=sys.executable` 啟 serve 時多繞一層，造成「兩個 watchdog 疊跑」（父進程鏈 python3→python314→serve）；防多開的 tasklist 判斷認不出跨 python 版本，擋不住。**更新鍵斷線根因 = 多開打架，根治後更新鍵才穩。**

**治標（已做）**：
- 啟動 watchdog 一律用明確路徑 `C:\Users\ie5\AppData\Local\Programs\Python\Python314\python.exe`，不用 `py`
- smartpn.bat 改成明確路徑
- autopull.bat / update.bat 停用（改 `.disabled`），只留 smartpn.bat 單一開機啟動點

**治本（待做）**：watchdog.py 的 `PYTHON=sys.executable` 改成明確 python 路徑，或加跨版本防多開判斷。回中樞改+測再 pull。

**ME129 現況**：碼 d13f74b 最新、系統 200 活著、乾淨一 watchdog 一 serve（都 Python314）、IE 功能已上線。

## 九、IE細表界面設計定案（2026-06-18）

### 格線規則
所有格線統一：顏色、粗細一致，沒有例外

### 格子規則（只有兩種）
輸入格（手工）：顯示輸入框，白底黑框
顯示格（公式）：直接顯示值，白底灰字
沒有值：空白，不顯示「—」
底色全白

### 表頭設計
參照 Apple 風格（apple.com 越南官網）
不用純黑表頭
字色、格式、字型全部一致化
淺灰底 #F5F5F7，文字 #1D1D1F，按鈕 #0066CC

### 頂部列（定案）
左側：← 返回列表 | 鞋型名稱 | ART（多個考慮第二行）
右側：語言切換（中/越）| EOLR 60 | EOLR 120 | 儲存▼（下拉：儲存/另存新階段）
移除：新建版本獨立按鈕、多餘顏色按鈕

### 語言切換規則
中越切換只切換欄位標題語言
不切換輸入格內容
新增行時，輸入格填什麼就是什麼，不受語言環境影響

### 分區清晰
各段子區（主流/支流/ATOM/EMMA等）分區要明顯
用明顯的區塊標題和分隔線區分

### 同一ART各階段查詢（待決定）
選項A：版本下拉切換（已有）
選項B：階段對比頁面（並排顯示，直接對比差異）
選項C：導出Excel查
Jim 傾向 B，待確認後實作

## 十、IE細表權限設計定案（2026-06-18）

### 角色與權限

| 角色 | 看 IE 列表 | 開細表 | 編輯格子 |
|------|-----------|--------|---------|
| admin | 全部 | 全部 | 全部 |
| manager | 全部 | 全部 | 全部 |
| data_entry | 全部（可見） | 全部 | 只限指派的鞋型 |
| read_only | 全部（可見） | 全部 | 不可編輯 |
| 未登入 | — | — | 401 |

### 後端強制擋（重點）
所有寫入 IE 的路由進來先呼叫 `_can_edit_ie(header_id)`：
- admin/manager：直接通過
- data_entry：查 `ie_assignments` 表，只有在指派清單內才通過
- 其他角色/未登入：直接回 403/401
不可只鎖前端，後端必須強制。

受保護路由（共7條）：
- `POST /api/ie/stages/<header_id>`（另存新版本）
- `POST /api/ie/cell/save`（存格）
- `POST /api/ie/cell/add_row`（新增行）
- `POST /api/ie/cell/delete_row`（刪除行）
- `POST /api/ie/cell/save_group`（建立合併格）
- `POST /api/ie/cell/update_group`（更新合併格）
- `POST /api/ie/cell/delete_group`（刪除合併格）

### 前端 CAN_EDIT 機制
`init()` 平行 fetch `/api/ie/<HID>/can_edit`，設 `CAN_EDIT` 全域變數。
`renderZones()` 結尾：`if (!CAN_EDIT) applyReadOnlyDOM()`
- 停用所有 input/textarea
- 隱藏 儲存▼ 按鈕
- 移除可點格子的 onclick
- 停用刪除/合併按鈕

### 角色感知渲染（Task I 定案 2026-07-12：不能執行的操作不該顯示）
**規則**：`read_only` 角色前端**全灰** — 手工格以**灰底純文字**呈現（同公式格），**不渲染輸入框**；
`插 / × / ＋ / 合 / 匯入 / 另存 / 送審` 等操作鈕**一律不顯示**；**連刀顯示為文字非下拉**。
`editor`(data_entry) **依 `can_edit` 範圍**：無權的鞋型同樣全灰。**後端 403 防線保留不動（雙層防護）**。
- 施工：`applyReadOnlyDOM()` 強化為「input/select→灰底文字、操作鈕 display:none、連刀 select→文字、
  送審/取消審核/設為鎖定版一併隱藏」；`isEditor`(送審顯示) 加 `CAN_EDIT` 條件。
- **注意（manager）**：後端 `_can_edit_ie` 現行邏輯 manager 對 IE 工序=唯讀（can_edit=false），故 manager
  亦渲染全灰。此為既有後端設計；Task I「保留後端不動」→ 不改。若要 manager 可編輯 IE，屬另案後端變更。
- **同規則套用其他頁**：`eolr_settings.html`（read_only：EOLR 下拉→純文字）；
  `allocation.html`（非撥人編輯者 admin/unit_user → 勾選框禁用 + toggle 防線）；
  `ie_cutting.html` 為純檢視頁（只有搜尋/篩選，無資料編輯元素）→ 無需改。
- **Playwright 驗收**：read_only 細表 input/select/操作鈕=0 且數值可讀 + API 寫入 403；
  editor 無權鞋型全灰、有權鞋型正常；admin 不受影響；eolr read_only 純文字/admin 下拉；
  allocation read_only 勾選框全禁用。

### 設備種類管理（Task K 定案 2026-07-13；權限＝manager/admin）
- 設備種類選項**由 manager/admin 在 `/admin/equipment-types` 自行維護，不經 Code**。
  （2026-07-13 Jim 定案：由 admin-only 改為 **manager＋admin**；editor/read_only → 403、入口不顯示。）
- **引用鎖定**：已被 `ie_process` 任何列引用的設備種類＝**名稱鎖定不可改、不可刪除，只能停用**；
  未被引用的可改名、可刪除。**停用＝下拉不再出現，既有資料照常顯示。**
- 前端：已引用列的「改名／刪除」鈕**反灰不可點 + 顯示引用筆數**（例「已被 37 道工序使用」）；
  未引用可改名/刪除（刪除二次確認）。停用/啟用、排序**不受引用限制**。
- 後端 API `/api/equipment_types`：GET（下拉來源，任何登入者，只回 active=1）；
  POST/PUT/DELETE + `/api/equipment_types/admin`（含停用項+引用數）一律 **`_require_manager()`**（manager/admin）。
  改名/刪除被引用 → **409**（`referenced=true, ref_count`）。
- **與 Task I 的關係**：manager 在 **IE 工序資料**仍是全灰唯讀（不變）；此處只開「設備種類選項維護」
  這一個管理功能給 manager，**不是**開 IE 編輯權。入口鈕在 `ie_interface.html`（非細表），
  不受 `applyReadOnlyDOM` 影響 → 對 manager 顯示且可點。
- 下拉快取：`ie_cell_detail` init 從 `/api/equipment_types` 快取一次；**停用後重新載入細表即生效**（每次載入重取）。

### 語言切換不洗資料（定案修法）
`setLang()` 改為 DOM in-place 更新：
遍歷 `td.name[data-zh]`，直接替換 innerHTML/textContent。
禁止在 `setLang` 中呼叫 `renderZones()`（會清空 unsaved inputs）。
name cell 必須帶 `data-pid`、`data-zh`、`data-vi` 三個屬性。

### 實測標準
每次 IE 相關修改，必須產出 `flask_backend/test_output/ie_operation_test_log.md`，
包含語言切換、CAN_EDIT、後端 403 全部逐項確認。

## 十一、Jim 方法論（中樞須內化）（2026-07-10）

### 結果導向（Jim 先給結果，Claude 回推地基）
- Jim 先給結果 / 答案，Claude 回推地基（做出支撐那個結果的底層）。
- IE 表是地基之一；**自動化編制表是最終結果**。
- 不要只做 Jim「當下說的那一格」，要回推它服務的最終結果，補齊中間地基。

### 嵌入 vs 獨立（依用戶方便性決定）
- 一個應用要放在既有系統內（分頁）還是做成獨立頁，**依「看的人方便性」決定**，不是依技術方便性。
- 判準：同一批人會不會在同一情境下同時用到？會 → 放一起。
- 例：看編制的人也要查 IE 流程 → **編制表跟 IE 用最外層兩個主頁簽切換（IE表 / 編制表）**，不是各自獨立網址。

### 本階段目標：自動化編制表
排程 → 拆 ART → 抓鎖定 IE 實際人數 → offline 撥人 → C2B → 導出 Excel。
（地基＝IE 表已上線；最終結果＝這條自動化鏈路。）

## 十二、多方驗證鐵則（MPV，2026-07-15 入規）

> 全文見 [45_MULTIPARTY_VERIFICATION.md](45_MULTIPARTY_VERIFICATION.md)；
> 每次交付填 [46_DELIVERY_CHECKLIST.md](46_DELIVERY_CHECKLIST.md)。

1. **驗的人 ≠ 做的人**：Code 的自證（hub_ci 全綠）只是**入場券**，
   必經破壞者 / 對規者 / 使用者三方獨立驗證。
2. **全票制**：任一方紅即不上線，**非多數決**。沒有「小問題先上」。
3. **證據制**：每方交「我試了什麼 + 可重現證據」，不接受「我覺得」「應該沒問題」。
4. **閘門判定不得由被驗收方修改**：改判定＝作弊，該次交付直接作廢。
   `hub_ci.py` 的 `GATE_FILES` hash 每次列印自證。
5. **上 ME129 前必過本機制**：中樞用 Jim 真庫複核全綠才放行。
6. **破壞者閘門常駐**：`breaker_gate.py` 為 hub_ci **閘門13**，每次 push 必跑；
   **新端點必須同步納入攻擊面**（並發/壞資料/權限繞過/邊界/狀態殘留）。

### ★ 7. 綠燈必須自證「測的是哪個庫」（2026-07-15 血的教訓）

**閘門全綠，是在你餵的那份資料上綠的。**

- hub_ci 每次啟動列印「來源身分」橫幅（ie_process 列數 / ob_header / 有 actual 的 header 數），
  報告**必須連橫幅一起貼**，不得只貼「ALL GREEN」。
- 「複製忠實」≠「來源是真庫」。`clone_prod_db()` 逐表斷言只證明前者。
- `flask_backend/data/` 在 `.gitignore` 內 → **ME129 真庫不經 git 同步**。
  開發機上的 atlas.db 是舊副本（8295 列 / 3 個有 actual 的 header），
  **不是** Jim 真庫（≈20434 列 / ≈140 個有 actual 的 header）。
- 因此：**任何依賴真實資料的結論（IE-VER / BZ-VER 對帳、遷移歸屬、零丟值證明），
  在開發機上一律不成立**，必須在真庫所在環境跑，或由中樞用真庫複跑。
- 診斷「資料少了」時，**先量來源本身**，再懷疑複製。
  否則會把不存在的 bug「修」成真的 bug（如：對線上 WAL 庫改用 copy2 → 取到撕裂檔）。

### 8. 反饋迴路：每輪重大交付四方各交一份 .json

```
Code 做完 → verification/round_NN/builder.json（自證 + hub_ci + ★data_source）
   ↓
破壞者/對規者/使用者各跑 → breaker.json / auditor.json / user.json
（自動閘門、獨立 AI 視窗、Jim 的 GPT —— 都寫進同一個 round_NN/）
   ↓
python mpv_feedback.py → 交叉比對 → round_NN/arbiter.md
   ↓
全綠 → 放行（中樞用真庫複核，才對 Jim 說「可以看」）
任一紅 → arbiter.md 內含自動退回令 → 貼給 Code → 下一輪
```

- `verification/` ＝**與外部 AI 對接的資料交換點，JSON 格式即介面**。
  誰驗的不重要，交出來的 .json 長得一樣就能裁決。格式見 `verification/README.md`。
- **四方各自獨立填，互不通氣，不看彼此結論。**
  建造者**不得代填**他方（代填＝驗的人＝做的人，該輪作廢）。
- `mpv_feedback.py` 為裁決程式，屬判定檔：**被驗收方不得修改**。

### 9. 裁決一律 fail-closed（沒驗 ≠ 沒問題）

- 範本預設 `verdict: red`，填完才改綠。
- **缺席即紅**、壞檔即紅、未申報 `data_source` 即紅。
- `verdict: "green"` 但 `findings` 非空 → **判紅**（說綠不算數，證據算數）。
- finding 缺 `repro` → 標「證據不足」但**仍算紅**，中樞人工判定
  （不允許因為「說不清楚」就當沒發生）。

---

## 十三、發佈防呆鐵則（R1–R4，Jim 定案 2026-07-15，永久標準）

> 起因：Jim 人工發現「更新鈕地雷」——`/api/system/update` 直接 `git pull origin main` 後重啟。
> 開發者一把半成品 push 上 main，現場（ME129）誤按更新就拉到半成品：程式新、DB 舊 → 白畫面，
> 且現場沒有回頭路。當時 **13 支閘門全綠**，沒有一支擋得住。
> 根因：破壞者只攻「功能」，沒攻「營運/發佈路徑」。**功能全對、發佈錯，現場一樣停產。**

### R1 破壞者攻擊面永久擴充「營運/發佈路徑」

每批 push 前必模擬（詳見 45_MULTIPARTY_VERIFICATION §破壞者第 7 項）：
按更新鈕（開發中／push 後／核可前／核可後）、還原備份、半新程式+舊 schema、
舊程式+新 schema、更新中斷電重啟。
**任何一項讓現場掛死或白畫面＝紅，擋 push。**

### R2 hub_ci 常設閘門14 `deploy_gate`

自動化模擬上列情境（全程隔離副本）。與其他閘門同等地位，**缺跑＝整批不過**。

### R3 分支凍結 ＋ 發佈閘（本批 G1/G2 即第一批受測對象，先紅後綠）

- **開發一律走分支，不得直接動 main。** main 只保留「已全綠的安全版」，
  現場任何時候誤按更新，拉到的都是能跑的版本。
- **ME129 的更新目標＝`release` 分支**，且必須等於 `00_HANDOFF/RELEASE_GATE.json`
  的 `approved_commit` 才准更新；不符 → 拒絕 + 顯示「等待中樞核可」+ **服務照跑不中斷**。
- 發佈閘 **fail-closed**：閘門設定檔壞掉/讀不到 → 一律不准更新
  （不更新永遠比更新到半成品安全，現場服務本來就還在跑）。
- **分支合回 main 只能在中樞回覆「核可合併」之後，不得自行合併——這條是鐵律。**
- 晉升流程：中樞核可 → `git push origin <sha>:release` → RELEASE_GATE.json 填同一個 sha。
  **開發者不得自行改 RELEASE_GATE.json 晉升版本。**

### R4 開機 schema 守門（絕不讓現場拿到白畫面）

- app 啟動先比對「DB 實際 schema」vs「現行程式期望 schema」，不符 → **拒絕啟動**
  + 印明確原因（缺哪張表/哪個欄）+ 一鍵回滾指令 `python flask_backend/rollback_release.py`。
- 期望 schema 的**唯一真相來源** ＝ `schema.sql` ＋ `migrate.py` 的 MIGRATIONS。
  → 改 schema 一律走這兩處；用 `_migrate_xxx.py` 臨時腳本繞過管理器改欄位，
  正是 2026-07-15 查出「兩條血脈 schema 雙向分歧」的成因（基準庫缺 lean、
  卻獨有 group_info/theory_operators），**永久禁止**。
- 守門只驗「該有的有沒有」，**不管多出來的**——多一欄不該擋現場開機。
- 回滾只回滾**程式碼，不碰 DB**：DB 是現場的真實輸入，程式碼可逆、DB 不可逆。
  schema 不符時正確方向是「把程式退回配得上這份 DB 的版本」。
