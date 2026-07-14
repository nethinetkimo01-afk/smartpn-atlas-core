# 43 — Council SaaS Review（多AI議會審查記錄）
Version: v1.0 FINAL | 2026-07-13
Status: 兩輪攻防完成，全數定案，零懸案。本檔為 SaaS 設計正式依據。

## 架構定案（三層存放與交換）
1. 欄位結構由 SmartPN 統一定義（mapping 前提）。
2. 資料放哪由供應商選：
   - API mapping 模式：資料留自家系統，SmartPN 不存，授權交換時經雙方 API 流動。
   - SmartPN 維護模式（弱系統供應商）：資料存 SmartPN，權限自控。
3. 公開欄位存入 SmartPN 建搜尋索引；私有欄位零索引。
- 對外話術：「私有資料零存放」，不講絕對零存放。
- 導入三軌：自接標準 API / SmartPN 代接 / SmartPN 作主系統。

## 搜尋與比對原則
- 搜尋與 Find Same Material 以「物性」比對，不以料號。
- identical = 供應商已公開的可搜尋物性全符合。
- 只透過自己公開的欄位被找到／被比對。曝光是授予的，不是被拿走的。
- 私密/僅授權材料不出現在任何人的 FSM 結果（即 D1：不需另設共同開發保護）。
- 選擇性開放是品牌側賣點：品牌搜到的材料，競品可能看不到也不知道存在。

## 價格原則
- 價格永遠不是統一 ID 的屬性，只存在報價單：一單、一客戶、一授權。
- 差別定價（以量制價）是正常商業。平台不提供比價視圖。
- D6：不寫「永不比價」條款——permission control 全權治理：
  私密＝平台無從洩露（場外洩露是人的行為，平台不負責）；
  公開是擁有者同等正當的選擇，若供應商自願公開價格，全平台帳號有知的權利。

## 責任模型
- SmartPN 負責交換；資料提供者對正確性負全部法律責任（食品成分表原則），
  寫入使用條款。
- 「SmartPN Verified」不得存在。認證顯示第三方發證機構＋效期。
- DPP-ready ＝ 欄位齊全度（對應憲法 Readiness Governance），不代表內容為真。
- D4 mapping 責任：私密資料 SmartPN 看不到內容、無從驗證，
  驗收簽署為啟用前強制步驟——未驗收批次不上線不交換；簽署後責任歸提供方。
- Mapping 方法論：分批（財務→關務→物性…），一次全量錯誤率高。

## 版本與存證（D3）
- 公開資料：SmartPN 內建版本記錄。
- 私密資料：零存放；雙方可各自在自家 API 端留版本。
- 交換存證＝選配：只留交易記錄不留內容，或 supplier API 只推送
  修改記錄+交易記錄作存證。存證永不進可搜尋資料庫。

## 計費（D5）
1. 永不按營業額/交易量抽成——結構上不可能：賣帳號，交易進銷存不經平台。
2. 席次不封頂，以量制價；定價不錨定現階段範圍（未來交換每月財務、報關等）。
3. Pilot 不免費；風險控制＝帳號隨用隨增。
4. 創始供應商無免費/折價。GTM：品牌先行，供應商跟隨，先機即紅利。

## 功能裁決
- 「誰看過我的材料」暫緩。商場模式：瀏覽方決定供應商能否聯絡他。
- D2 需求雷達（供應商匿名聚合搜尋訊號）：保留空間、本期不做、
  未來依雙方需求新增。原則：買方同意權優先。
- 影子 BOM 定調：非漏洞，是 S05 設計本意——品牌定義 Shared BOM 同步各廠，
  工廠用搜尋找當地品牌核可供應商申請替代，品牌因此看到各廠實際 BOM
  與價差，此即產品販售的透明度。
- 退出權：帳號失效＝資料存取全失效；可匯出自有資料；
  SmartPN 統一料號為 SmartPN 財產，不交付。

## 貫穿性規則
所有定案必須設計進 SaaS 介面，不得只存在條款或白皮書。

## SaaS 介面設計需求
1. 欄位級來源標示（Source / Authority / Sync Time / Cached）
2. 搜尋結果「N results visible to you」＋ permission-filtered 提示
3. 權限三態貫穿：公開/私密/授權指定對象（公司·單位·帳號）
4. Mapping 分批驗收頁（未簽不流通）
5. 交換存證選配開關
6. 公開資料版本歷史視圖
7. 帳號隨用隨增購買流程
8. Export my data（統一料號不隨匯出）

## 三方最終立場
品牌：有條件加入、支持試點。供應商：有條件分階段第一批上。
工廠：有條件小規模 pilot。

## 未來事項（非議會範圍）
API 可行性驗證（Jim 自留）、~~品牌端 KPI dashboard mock~~（**已落地 2026-07-14 Task W**，V3 品牌端 Dashboard，KPI 全由 MOCK_WORLD 推導、不含毛利率、遵隱私、EN/ZH、8/8 PASS）、工廠視角 demo（未起）。

## Demo 已知違規（第二步修正）
SmartPN Verified 字樣、Boss BI 毛利率卡、「誰看過我的材料」頁。

## Demo v2 已落地（2026-07-13, Task P）
議會定案落地版：`docs/preview/SMARTPN_DEMO_V2.html`（品牌端）＋`SMARTPN_DEMO_SUPPLIER_V2.html`（供應商端），
舊 v1 檔保留對照，INDEX.html 加 v2 入口（標「議會定案版」）。兩檔共用同一份 `MOCK_WORLD`（24 材料，deterministic）。
- 八項介面需求全落地：①欄位級來源標示（Source/Authority/Sync/Cached，點擊展開）②FSM「N results visible to you」+
  帳號 A/B 切換（A 見 5 / B 見 3，選擇性開放）③供應商端每欄位權限三態（公開/私密/授權·公司單位帳號）
  ④Mapping 分批驗收（財務已簽/關務待驗/物性未送；未簽=不流通鎖；簽署頁明示 D4 責任移轉）
  ⑤交換存證選配開關+清單（只交易記錄、無內容）⑥公開欄位版本歷史 ⑦帳號隨用隨增（席次/量價/無上限/無免費試用）
  ⑧Export my data（統一料號不匯出）。
- 三違規拆除（全域 0 命中）：SmartPN Verified→第三方發證機構+效期；Boss BI 毛利率卡移除；誰看過→商場模式聯絡許可開關。
- 測試鉤子：`window.MOCK_WORLD / setAccount(id) / getVisibleMaterials() / setLang(lg)`（純測試，不影響 UI）。
- Playwright 驗收全 PASS：兩檔 0 JS 錯誤；MOCK_WORLD 兩視角一致（同 24 材料、抽 3 筆名稱相符、A/B=5/3）；
  私密材料(SPA-FV-1003)在 B 帳號 FSM/搜尋/下拉完全不出現；EN/ZH 全頁切換；三違規全文 0 命中。
  證據：`test_screenshots/taskP_demo_v2/`（P1–P8 逐項截圖 + task_P_result.json）。

## Demo v3 已落地（2026-07-13, Task R 返工）
**根因**：v2 為全新重寫，丟失 v1 大量函式/畫面 → 返工。**改版鐵則**寫入 27_WORKING_RULES：
「改版一律在現有版本疊加，禁止全新重寫；驗收必含功能迴歸，舊版全部函式缺一即 FAIL。」
- `SMARTPN_DEMO_V3.html` + `SMARTPN_DEMO_SUPPLIER_V3.html` = **v1 全功能 + 議會八項疊加 + Boss 視角 + 引導腳本**。
  以 v1 兩檔為基底複製、在其上「加」council overlay（不動 v1 既有函式）。
- **功能迴歸 PASS**：v1 函式全集逐一存在（`window.V1_PARITY`）——品牌 **54/54**、供應商 **19/19**，0 missing。
  新建料號/二次加工編碼/母子公司樹/權限/FSM/評論/詢問…原樣保留。
- 議會八項疊加：欄位級來源鏈、N results visible + 帳號 A/B(5/3)、供應商欄位權限三態、Mapping 分批驗收、
  存證選配、版本歷史、席次加購、Export（統一料號不匯出）。
- **Boss 視角**（INDEX 第三入口，只讀）：`SMARTPN_DEMO_SUPPLIER_V3.html#boss` → BI 8 KPI（毛利率卡除外）、只讀 dim 導覽。
- **引導腳本**（右下「▶ 演示流程/Guided」，可跳過，EN/ZH）：供應商建料號→交給 SmartPN→Mapping 簽署→授權品牌A→
  品牌搜到→報價→交換存證，五步逐句說明。
- 三違規全域 0 命中；測試鉤子 `window.MOCK_WORLD/setAccount/getVisibleMaterials/setLang/V1_PARITY`。
- INDEX：v3 標「議會定案完整版」為主入口 + Boss 第三入口；**v2 入口移除（檔案保留）**；v1 留對照。
- Playwright 全 PASS（`test_screenshots/taskR_demo_v3/` R1–R6 + task_R_result.json）：兩檔 0 錯、V1_PARITY 0 missing、
  MOCK_WORLD 兩視角一致、私密材料在 B 完全不出現、引導 5 步走通、Boss 無錯無毛利率。

### Demo v3 修補 · R-1（FSM 空脈絡例外）
- **根因**：`openFsmInNewWindow`/`renderFsmBody` 在 `fsmContext=null` 時 `const{fromId}=fsmContext` → TypeError。
- **修法（第一性原則 + 防禦層）**：FSM 操作鈕本就在 FSM modal 內（無脈絡＝modal 隱藏不顯示）；各依賴脈絡函式入口加
  null guard 安靜 return。
- **全檔同型掃描結果**（空脈絡逐一觸發）：已修 `openFsmInNewWindow`（fsmContext）、`renderFsmBody`（fsmContext）、
  `selectOpt`（currentMat）、`sendMsg`（activeThread→t）、`renderSpuPage`（m）、`showFieldHistory`（m，原用 `m?:''` 不崩、
  仍加 guard 不開空視窗）。`openSpu`（原已 `if(!currentMat)return`）、`openThread`（原已 `if(!t)return`）本就安全。
- **Playwright（隔離 v3）全 PASS**：7 個依賴脈絡函式空脈絡呼叫 0 例外；全頁亂點兩遍 **0 pageerror**；
  正常 FSM 動線（開材料→FSM modal→比對→新視窗）迴歸。證據：`test_screenshots/taskR1_fsm/task_R1_result.json`。
