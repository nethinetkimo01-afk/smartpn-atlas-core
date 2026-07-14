# Current Status

Last updated: 2026-07-13

## 線別狀態（2026-07-13）
- **IE 線：PAUSED**（第三批 Task F–O 全綠已 push，等 ME129 按更新＋Jim 於 /admin/recalc-cutting 派發重算）。
- **SmartPN Atlas SaaS 線：ACTIVE**（議會兩輪定案；**Demo v3 已落地**＝v1 全功能+議會八項+Boss視角+引導腳本，
  `docs/preview/SMARTPN_DEMO_V3.html` + `SMARTPN_DEMO_SUPPLIER_V3.html`，INDEX 主入口；v2 入口移除檔案留，v1 留對照。見 43 號檔）。
  **改版鐵則**（27_WORKING_RULES）：改版一律疊加不重寫，驗收必含功能迴歸（V1_PARITY 缺一即 FAIL）。

---

## 三線整合（2026-07-12）
三條線：IE表（已上線ME129）/ 編制表（本階段主線：自動化編制表）/ SmartPN Atlas Demo（獨立產品）。
三線共用同一套工作法：Playwright 真跑瀏覽器自測 + 隔離副本不污染正式DB + 對抗性測試（把用戶當會亂點的新人）+ 測過才push + 交出去必須能用。
Claude 是中樞不是打字機：自行思考、主動 web_search 查市面成熟做法、主動提建議、預想 Jim 的下一步。
→ 完整交接：41_THREE_TRACK_HANDOFF.md（2026-07-13 重寫，42 作廢併入）

## 2026-07-14 定案（Task X 交換機制 + Task BZ 編制表照 28 重建）
- **Task X** ✅：SmartPN 產品機制實作 + 死按鈕歸零。44 號規格檔 + `real_click_test.js`（jsdom 真點擊閘門）入庫；
  v3 兩檔疊加 44 資料模型（fieldGroups/accessRequests/grants/properties+units/exchanges/apiSpec+mappings）；
  全域點擊回饋層→**死按鈕歸零**（品牌0/供應商0）；引導改走 A申請→B交換→C對接。
  **`node real_click_test.js` 兩檔各 8/8 ALL GREEN**（死按鈕0/引導≥5步/機制五項全有）。
- **Task BZ** ✅：編制表照 `28_BIANCHE_SPEC.md` 重建（規格為唯一基準，`spec_gate_bianche.py` 逐欄對帳）。
  區塊B 補 **协理给 K 欄**（合計=裁斷+針車+成型+协理给）；每 LEAN 底部 **直工小計 N**（=SUM編制）+ **人力小計 P**（=SUM C2B），無框粗體上細線；
  區塊C 月度 11 項（既有）；手工格(白底灰框 `.manual-cell`)/公式格(無框純黑)視覺區分；DS-04 匯入 UI；防呆（非數字當場擋、離頁攔截、狀態可見）。
  **`python spec_gate_bianche.py` 7/7 + `hub_gate.py` 83/83 ALL GREEN**。
- **GATE-1 補丁** ✅：`/api/bianche` 合法月份不再 400（get_bianche_data 加 except→200 空集；`_valid_month` 非法格式→400）。

## 2026-07-14 定案（Task Y：編制表五步流程 + S-2 外框返工 + GATE-1 缺陷閘門）
- **Task Y** ✅：編制表由「四個孤島」變「流程」。bianche 頁頂常駐五步流程列（疊加不重寫）：
  ①匯入DS-04 ②EOLR確認 ③部件調度(勾選) ④計算編制 ⑤導出。後端 `/api/bianzhi/flow_state` 推導每步狀態
  （未開始/進行中/已鎖定/有誤四態）；①②③ iframe 內嵌不跳出頁簽、④原生內容、⑤導出動作；
  前一步完成才解鎖下一步（未匯入不能勾選…），卡關灰掉並說明原因；回退上游→下游標「需重算」；狀態隨月重推導。
  Playwright（隔離 5096）**7/7 PASS**：①→⑤ 真點擊走通、④原生+⑤真下載、回退需重算、空月不死路、切月、read_only 全灰迴歸。
- **Task S-2** ✅：整合外框生產級返工。iframe 逃逸修復（殼監聽導航，深入頁顯「←返回頁簽首頁」返回列+路徑，一鍵回、先 flush）；
  編制表頁頂 `#bz-status`「當前月份+N/M 單位有資料/未匯入列名」；API 失敗→errBlock 明確錯誤+重試不靜默空白。Playwright 8/8。
- **GATE-1** ✅：`hub_gate.py`（repo 根）6 類伺服器缺陷閘門 **69/69 全綠**：低權限不 500、寫入越權→403（13 端點補校驗）、
  重算並發→409（DB 原子鎖）、垃圾 month→4xx、不存在 id→404、缺參數/空資料→4xx（全域 /api 例外安全網）。
  規則入 25：每批 server 變更 push 前必跑 hub_gate 全綠、新端點必納入閘門。
- **Task X（品牌端交換機制）BLOCKED**：依賴 `00_HANDOFF/44_EXCHANGE_MECHANISM_SPEC.md`（中樞稱 commit 4fa3263），
  但該檔/commit 不在本地任何 ref/history/stash/reflog，且 Code 機 node 無 puppeteer/playwright → 無法跑 `node real_click_test.js`。
  **待 Jim push 44 號規格檔 + real_click_test.js**（勿臆造規格，見 Task R 返工教訓）。已入 47 帳本 G-12。

## 2026-07-14 定案（Task W：SmartPN 品牌端 V3 KPI Dashboard）
- **Task W** ✅：V3 品牌端（`docs/preview/SMARTPN_DEMO_V3.html`）加 Dashboard 頁（43 號遺留、中樞代決執行）。
  頂欄新增 Dashboard 入口 + `#page-dashboard` 5 KPI 卡，**全由 MOCK_WORLD 推導**：
  可見材料數（visibleTo）、授權中請求（granted 欄位數）、Mapping 驗收進度（signed/total）、交換存證量（evidenceRecords）、DPP 就緒度（欄位完備率均值）。
  - **不含毛利率**（KPI 卡零 margin 指標）；**遵守隱私定案**：只出彙總數，不列他方私密欄位值/交易對手名。
  - EN/ZH 雙語（Object.assign STRINGS）；引導腳本 +1 步（⑥ Dashboard，共 6 步）；測試鉤子 +`window.getDashboardKPIs`。
  - **疊加不重寫**（改版鐵則）：以 overlay 包 showPage/toggleLang/setAccount，**不動 v1 函式** → 功能迴歸 v3 全函式 V1_PARITY **0 缺**。
  - Playwright（file://）**8/8 PASS**：KPI==獨立期望（Brand-A visible5/grants3/mapping33%/evidence3/dpp79%）、帳號切換 A5→B3、EN/ZH、無毛利率/無他方私密、引導 6 步、V1_PARITY 0 缺、0 pageerror。

## 2026-07-14 定案（Task V：編制表 Step5/6 合成資料邏輯層全驗證）
- **Task V** ✅：不等真檔，用 deterministic 合成 IE 世界（隔離 E2E 庫 atlas_v_e2e.db）驗證編制表計算邏輯層。
  合成：20 型體全段標時（EOLR 60/120 各半、裁斷連刀≠1、手工/公式列混合）+ 3 缺 IE 型體；期望值由腳本**獨立公式另算**再與 db 函式比對。
  - **Step6 MP 0 差異**：`get_bianzhi_detail` 20 型體逐欄（裁斷理論 Σstd×EOLR/3600、針車/成型實際人數、K、C2B）== 獨立期望。
  - **連刀÷N**：獨立 `3600/刀/層×件/連刀` == `db._recalc_new_std`；連刀4=180 < 連刀1=720（÷連刀生效）。
  - **offline 撥人**：勾選承接(is_checked)後 C2B=K+moved_q，路徑通。
  - **缺 IE 紅底不擋單（決策③）**：3 型體 has_locked=False、MP=None，但訂單/數量保留、不被丟棄。
  - **STF 式**：訂單÷(3600÷TCT)÷222 獨立值成立（對照 get_allocation_parts 打粗水洗）。
  - **36欄導出**：`export_ie_capacity` 已實作填「已知人數欄」（裁断/针车/成型/CSA 标准人数，逐欄==獨立期望），未知欄(CT/產能/PPH，出自已丟失規格)仍留空**不臆造**。
  - 一條龍 E2E（Playwright 走 /bianche 界面）：合成 lean 渲染 + 缺IE未鎖定紅底 + 導出可下載。**7/7 PASS**。
  - **G-03 降級**：BLOCKED 之「邏輯層」已解，僅剩真資料層（真 IE xlsx 對映覆蓋+廠務檔逐欄比對+未知欄公式）待 Jim 供檔。

## 2026-07-14 定案（Task U：目標總帳 47_GOAL_LEDGER）
- **Task U** ✅：新建 `47_GOAL_LEDGER.md` 目標總帳（全部未結事項單一真相表，ID|事項|狀態|Owner|卡點|來源）。
  收 11 條 G-01~G-11：ME129更新(G-01)、裁斷重算預覽(G-02)、IE xlsx拷Code機解鎖Step5/6+36欄真值(G-03)、
  manager唯讀待追認(G-04)、Pages開通(G-05)、GRANT名稱待定(G-06)、設備種類自助(G-07)、SaaS八項(G-08)、
  SmartPN下一步候選(G-09)、求職線DORMANT(G-10)、MP勾選舊案待清檔(G-11)。
  掃 00_HANDOFF 全檔：無「可由 Code 立即實作卻漏做」的孤兒定案（開放項皆 Jim-blocked／待拍板／休眠／待清）。
  規則入 `00_ENTRY_POINT`＋`27_WORKING_RULES §零之四`：定案即入帳編 ID、開場先對帳、**僅 Jim 可關帳**。

## 2026-07-14 定案（Task T：功能權限矩陣，中樞代決規格，Jim 可推翻）
- **Task T** ✅：帳號×單元功能權限矩陣落地。單元＝`ie_edit/select_parts/allocate/import/export/audit/base_data`（7）。
  - 儲存：`sys_users.permissions`（JSON array）；`NULL`＝舊帳號依角色預設（**遷移零變化**），非 NULL＝admin 明確設定的權威矩陣。
  - 角色預設映射：admin→全部（**不受矩陣限**）、manager→{審核,基礎資料}、data_entry(editor)→{IE編輯}、read_only→全空。
  - 雙層 403 防線：有角色閘門端點＝`既有角色 OR 矩陣授權`（`_unit_allowed`）；開放端點（allocation）＝`_matrix_block`（只擋「有明確矩陣但未含該單元」帳號，舊帳號 fall-through→零迴歸）。
  - 帳號管理頁（manager+admin）新增「功能權限」欄＋矩陣勾選 modal；admin 列顯「全部（不受限）」；`/api/me/units` 供前端隱藏入口；`PUT /api/users/<id>/permissions`。
  - Playwright（隔離 5099）**8/8 PASS**：造「只勾撥人」read_only 帳號→`/api/me/units=={allocate}`、硬打其他 6 單元 API 全 403、撥人 200；admin 全過、manager(審核/基礎/導出過+IE編輯擋)、editor(指派可編)、tongcai(閘門全擋+撥人非擋) 逐一零變化；矩陣 UI 勾選存取一致。
  - 前端入口隱藏：現有頁面本已依角色隱藏（read_only 帳號本就看不到 IE編輯/導出/審核/設備種類入口）→ 零迴歸；`/api/me/units` 已備供逐頁細分隱藏後續接入。

## 2026-07-14 定案（Task S：IE表/編制表 最外層主頁簽整合）
- **Task S** ✅：最外層主頁簽【IE表｜編制表】統一外框落地（21 號既有定案「看編制的人也要查 IE 流程」執行）。
  實作＝**共用外框 `/app`（`app_shell.html`）各載一頁 iframe**，`ie_interface.html`／`bianche.html` **零改動**（git diff 空）→ 兩頁全部函式/按鈕逐一保留、零迴歸。
  - 登入後預設進 IE表（login.html 導 `/app#ie`；外聯單位 tongcai/dianno/dacu 仍導 `/allocation` 不變）。
  - 切頁簽前接 `flushPendingEdits` 同款防護：離開前對當前 iframe flush；iframe 保活不卸載 → 即使 flush 失敗（鎖定版）值仍留，不靜默丟。
  - 網址可分辨 `#ie` / `#bianche`，F5 停留在當前頁簽。
  - 工具列各歸各頁簽脈絡（矩陣/帳號/設備種類/審核/導出/更新燈號屬 IE；匯入/匯出/EOLR/勾選屬編制表）—各在自己 iframe 內，不混排。
  - 權限沿用各自現有規則：read_only（tongcai）兩頁全灰、editor 指派可編+編制表唯讀、bianche 角色可見性照 28 號不變。
  - Playwright（隔離 5099）**10/10 PASS**：互切 10 次抽測、細表未存值切頁 flush 保住、tongcai 兩頁全灰、editor 迴歸、三語(IE)、F5 停留、舊入口 `/ie`·`/bianche` 獨立可開。
  - 註：`bianche.html` 本無三語切換鈕（現況即中文），Task S 未新增（屬另案）；「三語兩頁正常」＝IE 三語有效 + 編制表照渲染不破。

## 2026-07-13 定案（第三批 Task F / G / H）
- **Task F**：裁斷 standard_time DB 重算 ×1.0（方案a）。只碰公式型裁斷機列，手工/其他區不動；
  bianche 維持讀 DB 值（鎖定版＝快照）。ME129 派發腳本 `recalc_cutting_x10.py`＋`rollback_cutting_x10.py`
  已交（隔離 E2E 全 PASS）；**正式庫等 Jim 看報告後在 ME129 執行**。見 `Task_F_執行說明_20260713.md`。
- **Task G**：IE 產能彙總表**定案 36 全欄**（與 廠務編製自動計算.xlsx「數據源-IE标准」逐欄一致；
  **29 欄出自已丟失規格檔，作廢**）。取值來源＝IE 鎖定版＋offline 撥人。產能/人數欄值維持
  **BLOCKED**，解鎖條件：在 ME129 執行、或 IE 來源 xlsx 進 Code 機。UI 導出入口已補（admin/manager 限定）。
- **Task H** ✅：IE 裁斷段界面改版（ATOM/EMMA 精簡 5 欄、裁斷機加「連刀」欄 `interlock_cut` DEFAULT 1 +公式÷連刀、
  新增「裁斷手工」區 type M）。規格見 27_WORKING_RULES §二「①-H」；Playwright 4 情境全 PASS + read_only 403 迴歸。
- **Task H-2** ✅：連刀下拉加選項 6（1/2/4/6/8/16，默認1）。匯入無值白名單→無需改。Playwright：選6→標時÷6(39600→6600)、理論連動、flush/read_only 迴歸全 PASS。
- **Task H-1** ✅：連刀欄移到「層數」左邊（只動顯示順序，公式/DB/36欄不變）；匯入按 DB 欄名（不受欄序影響）並補帶 interlock_cut。Playwright 3 情境全 PASS。
- **Task J** ✅：STF 段所有區塊「實際人數」→「EOLR=190 實際人數」（三語），改在 STF 共用表頭定義層（`SEG_COL_LABELS.stf`），新增 STF 區自動繼承；只改顯示名稱，其他段不動。Playwright 4 情境全 PASS。
- **Task O-1** ✅：移除 ART 選單缺漏修復（群組聯集）——列表列＝model 群組(60/120合併)，選單改列群組全 header 的 ART 聯集，
  逐 ART 帶實際所屬 header_id 逐 header 移除；某 header 清空級聯刪、另一 EOLR 不受影響。Playwright 4 情境全 PASS。
- **Task O** ✅：移除 ART 靜默失敗修復——後端比對放寬(TRIM+不分大小寫)+檢查 rowcount(刪0列→ok:false)；
  前端 prompt 改選擇視窗(列 ART 點選)；同類掃描僅 remove_art 有此 bug。Playwright 5 情境全 PASS。
- **Task N** ✅：裁斷重算改為 admin 管理頁 `/admin/recalc-cutting`（預覽→確認→自動備份→可還原，執行中鎖擋並發），
  取代 cmd 腳本派發（腳本保留備援）。原則寫入 27_WORKING_RULES §七。Playwright 5 情境全 PASS（含 lock 409、非 admin 全 403）。
- **Task L** ✅：STF 段欄位標準化——所有區塊欄位組/公式與 Assembly 完全一致（正常時間×(1+寬放/100)，寬放默認10；
  移除舊 STF 特例）。舊資料相容(缺 normal→顯示存值，補填後轉公式)；不回填不重算；Task J 表頭不被蓋回；
  36欄/編制表 TCT 來源 standard_time 取值不變。Playwright 3 情境全 PASS。
- **Task K** ✅：設備種類管理頁 `/admin/equipment-types`（**權限 manager＋admin**，Jim 定案；editor/read_only→403、入口不顯示）。
  新增/改名/排序/停用啟用/刪除；**已被引用＝名稱鎖定不可改不可刪只能停用**（前端反灰+引用數，API 409）。
  入口在 ie_interface 頭部（不受 Task I 全灰影響，manager 可點）；manager 的 IE 工序仍全灰唯讀不變。Playwright 6 情境全 PASS。
- **Task I** ✅：前端角色感知渲染（read_only/無權 editor 全灰、input/select→灰底文字、操作鈕不顯示、
  連刀→文字；eolr/allocation 同規則；後端 403 保留=雙層防線）。規格見 27_WORKING_RULES §十「角色感知渲染」。
  Playwright 5 情境全 PASS（含 read_only API 寫入 403）。**注意**：manager 因後端 `_can_edit_ie` 現為 IE 唯讀→亦全灰（既有設計，Task I 未改後端）。

## 2026-07-12 定案
- cutting 公式 ×1.1 → ×1.0（見 27_WORKING_RULES §二①）
- 裁斷合併 bug 修法＝A 強化版 flushPendingEdits（本批 Task D 執行）
- IE 導出＝規格回源，讀實際來源 xlsx header（本批 Task E 執行；Task G 定案 **36 欄**，「29欄」作廢）
- 編制表併列不比對 FOB（見 28_BIANCHE_SPEC 決策④）

---

## 當前狀態（2026-07-10）— ME129 部署穩定 + 本階段目標

### ME129 部署與多開根治（2026-07-10）
- **多開根因**：ME129 的 `py` / 開機 bat 會抓到 WindowsApps 的 `python3.exe`（Microsoft Store 殼），它的 `sys.executable` 異常。watchdog.py 用 `PYTHON=sys.executable` 啟 serve 時多繞一層，造成「兩個 watchdog 疊跑」（父進程鏈 python3→python314→serve）。防多開的 tasklist 判斷認不出跨 python 版本，擋不住。
- **解法（治標，已做）**：啟動 watchdog 一律用明確路徑 `C:\Users\ie5\AppData\Local\Programs\Python\Python314\python.exe`，不用 `py`。smartpn.bat 已改成明確路徑。autopull.bat / update.bat 已停用（改 `.disabled`），只留 smartpn.bat 單一開機啟動點。
- **治本（待做）**：watchdog.py 的 `PYTHON=sys.executable` 應改成明確 python 路徑或加跨版本防多開，回中樞改+測再 pull。（見 27_WORKING_RULES §八 / 任務板待做）
- **更新鍵斷線根因** = 多開打架；多開根治後更新鍵才穩。
- **ME129 現況**：碼 d13f74b 最新、系統 200 活著、乾淨一 watchdog 一 serve（都 Python314）、IE 功能已上線。（取代 2026-06-20「ME129 跑舊版 v1.4」與休眠斷線待辦）

### cutting 公式確認（2026-07-10）
- 裁斷機標準時間 = **3600÷刀數÷層數×件數×1.1** 是「**正確的**」（一度被誤判為錯，實際對，不要改）。
- 理論人數 = 標時 ÷ (3600÷eolr)。
- 例：層1件11刀1 → 標時 43560、eolr120 理論 1452，是正確業務值。
- 詳見 27_WORKING_RULES §二① 補註。

### 本階段目標：自動化編制表
- 流程：排程 → 拆 ART → 抓鎖定 IE 實際人數 → offline 撥人 → C2B → 導出 Excel。
- IE 表是地基，自動化編制表是**最終結果**。
- 嵌入 vs 獨立：看編制的人也要查 IE 流程，所以**編制表跟 IE 用最外層兩個主頁簽切換（IE表 / 編制表）**。
- Jim 方法論已寫入 27_WORKING_RULES §十一（中樞須內化）。
- 承接上一階段主線（版本控制，見下）：自動化編制表要「抓鎖定 IE 實際人數」，依賴版本控制的鎖定版語意。

---

## ★ 下一階段主線：版本控制（2026-07-09 定案）
- 設計/藍圖/MP公式/編制表資料流/測試規則/中樞思維 → **見 `39_VERSION_CONTROL_DESIGN.md`**
- 現況調查結論：目前「版本」只有標籤、**沒有資料隔離**（所有版本共用同一份 `ie_process`）。詳見 39 檔 G 節
- 待補核心：資料分版 + 鎖定版語意（升級 is_approved）+ 刪除版本 + 編制表改抓鎖定版

---

## 當前狀態（2026-06-20）

### ★ 最高設計原則（2026-06-20 Jim 定案，凌駕所有功能）
假設使用者完全不懂、不看說明、會亂點。系統必須：不用教就會用 / 不可能做錯 / 符合直覺 / 錯了能救 / 狀態看得見。詳見 **27_WORKING_RULES.md 第一節** 及 **29_UX_RULES.md**。

### ME129 部署狀態（已上線）
- waitress 版(serve.py, threads=8)、強制登入、watchdog 守護
- 啟動鏈：開機 bat(smartpn.bat, `py`) → watchdog.py(sys.executable) → waitress
- 電源：standby/hibernate 設永不(powercfg=0)，已解10分鐘休眠斷線
- 員工連 **http://172.16.1.29:5000**（必 http、必 :5000）
- 帳號：jim/admin123(admin)、manager01、editor01、ie5/Thanh(manager)、tongcai/dianno/dacu(read_only)

#### ME129 未完成待辦
1. **開機免登入**：netplwiz/regedit 被 GPO 擋，改用工作排程器未設完
2. **重開機驗證**：開機自動跑尚未實測（挑沒人用時做）
3. ME129 跑舊版 v1.4，需按更新鍵 pull 最新(含登入/權限/格子/UX修正)
4. 帳號頁「編輯」按鈕無反應（待修）
5. jim 密碼 admin123 太弱，穩定後改強

### IE 系統（2026-06-20 做扎實）
- 功能模擬 31/31、資料正確 5/5 PASS
- 壓測：waitress 真實尺寸細表 438ms 達標、DB locked 0
- 強制登入(b150aba)：未登入→/login，API→401
- 一鍵更新燈號：admin/manager 限定，灰=最新/橘=有新版
- 帳號權限修正(49b3dcf)：/api/users 加 _require_manager + 提權防護
- UX 修正(a5aeb23)：存檔靜默/beforeunload攔截/帳號管理入口/手工格統一白框/配色/危險操作確認

### UX 修正完成項目（2026-06-20，commit a5aeb23）
1. 「儲存」直接靜默存、已儲存✓淡出、另存才跳框
2. 有未存變更離頁/切版本前攔截警告
3. admin/manager 頂部見「帳號管理」按鈕；帳號頁有「← 返回 IE 清單」
4. /admin/users 加 _require_manager 守衛；manager 無法選 admin 角色
5. 所有手工格 1px solid #C7C7CC 統一白框
6. 刪除工序/帳號有「無法復原」確認框

### 廠務編制表規格（2026-06-20 完成，待 Jim 拍板）
規格見 **28_BIANCHE_SPEC.md**。三塊結構完整分析（區塊A彙總+區塊B明細+區塊C月度）。
**唯一待決策：MP/直工數 = 系統自動從IE標時算 vs 主管手工填（同範本）？**
決策一定，即可出 code 完整重建廠務編制表。

### 其他
- demo 脫敏版：make_demo_db.py / serve_demo.py 已建
- API 金鑰外洩：Jim 已知，選暫不處理
- 首頁(/)仍是舊 DS-03 深藍界面，可改 redirect→/ie

---

## 當前狀態（2026-06-18）

### 系統架構
- 三台電腦：中樞電腦（白天開）/ ME129（主DB，172.16.1.29:5000）/ 不關機Code機
- ME129 已部署，開機自動 git pull + 啟動 Flask
- DB 在中樞電腦 D:\smartpn-atlas-core\flask_backend\data\atlas.db（81MB）
- 待做：把中樞電腦 atlas.db 複製到 ME129

### IE 表系統現狀
- 20,434 筆工序資料已導入（290份鞋型）
- 帳號系統已建（admin/manager/editor/viewer + tongcai/dianno/dacu）
- 細表四段（Cutting/Stitching/Assembly/STF）功能完成
- 合併/解除合併實際人數功能完成

### 待修正（新視窗接手）
界面設計全面修正（照 09 節定案規格）：
1. 格線統一（顏色粗細一致）
2. 輸入格/顯示格統一（白底，無「—」）
3. 表頭 Apple 風格（#F5F5F7底，#1D1D1F字）
4. 頂部列重設計（左：返回+鞋型+ART；右：語言+EOLR+儲存▼）
5. 語言切換只切換欄位標題
6. 分區更明顯
7. 同一ART各階段對比頁面（待決定後實作）

### 廠務編制系統現狀
- /ds04 三層折疊（部門/LEAN/鞋型）完成
- /eolr-settings 年度橫向表格完成
- /allocation 勾選表框架完成（邏輯待修正）
- /bianche CSA/OCS/RB/QC 完成

### 下一步優先順序
1. IE細表界面全面修正（最高優先）
2. allocation 勾選表邏輯修正（按IE表分區展開）
3. 把中樞電腦 atlas.db 複製到 ME129
4. Excel 導出/導入功能
5. 同一ART階段對比頁面

---

---

## 今日確認決定（2026-06-13）

### SmartPN Atlas — 設計決定鎖定

- [x] 視覺系統：100% Apple 風格（純白/SF Pro/0.5px細線/大量留白）；黑底版 REJECTED
- [x] 系統名詞：SPU→Product / SKU→Option，全界面統一
- [x] GRANT 操作機制：Supplier 自建資料夾→打勾欄位→授權公司·單位·帳號；同欄位可多資料夾；新材料預設 PRIVATE
- [x] 單向可見性：只有 Brand/Factory 能發邀請；Supplier 無法主動搜尋 Brand/Factory
- [x] SmartPN 編碼：排除 0/1/I/O/E；料號定後不可改；物性變=新料號
- [x] My Library：個人庫+同公司分享功能
- [x] Requests：Brand/Factory 發 Request；即時對話（像客服）；Supplier 收通知後才可回
- [x] 評論：私密（同公司）/ 公開（含 Supplier）；Supplier 看不到私密評論
- [x] Find Same Material：範圍=OPEN+已授權給此帳號，非全平台
- [x] Supplier 財務資料：收款方（銀行/帳號/Swift Code/幣別/發票抬頭）≠ 付款條件（買方）

### 待確認

- [ ] CV 是什麼？Jim 尚未說明，等待確認後補入 01_CONSTITUTION.md

---

## 今日完成（2026-06-08 evening）

### DATA SYSTEM — 已完成
- [x] ds04_pipeline.py 修正：Rule 19 成型进度段落過濾 + 廠務合批跳過 → 數量差異從 256→32 筆
- [x] generate_bianche.py 製令明細加入「外包鞋面」欄位（J欄），小計行含外包鞋面小計
- [x] IE 匯入：C:\Users\user\OneDrive\Desktop\IE 新增掃描（含縮寫ART還原）
- [x] 1609 IE 文件導入（KI9854/55/56/57/61）
- [x] nightly/tasks/data_system.py Task 6（IE全面掃描）+ Task 7（gb.run() + bianche_diff 更新 24_DATA_SYSTEM.md）
- [x] missing_ie_list.txt：134 筆 ART 缺 IE 記錄
- [x] 07_RULES.md v2.9：Rule 11 + Rule 14 + Rule 18 更新
- [x] 24_DATA_SYSTEM.md v3.2：DS-03/04/05 月度流程確認

### SmartPN Atlas — 已完成
- [x] docs/preview/S01_DEMO.html（已提交）
- [x] docs/preview/S02_DEMO.html 至 S17_DEMO.html 全部建立（16 個互動式 Demo 畫面）
- [x] S01-S17 全部 Demo HTML：DONE（docs/preview/S01_DEMO.html ~ S17_DEMO.html）
- [x] S01 PPT：已建立為互動式 Widget，尚未經 Jim 確認最終版本
- [x] 26_S01_DEMO_LOGIC.md 建立並推送 GitHub
- [x] 27_SMARTPN_LAYER_DEFINITION.md 建立（placeholder，等 Jim 提供內容）
- [x] 28_DEMO_MENU_STRUCTURE.md 建立（Phase 1 Demo SaaS + Formal Demo B 側欄結構）
- [x] 00_ENTRY_POINT.md Layer 3 加入 26/27/28 號文件索引 + demo screens 路徑

### 待確認（需 Jim 決定）
- [ ] Jim 確認 EOLR mapping（每個 LEAN 組別對應哪個 EOLR）
- [ ] Jim 確認 MP 分配規則（DB ob_epph 整條產線 vs 廠務分配後，差距 2~3 倍）
- [ ] DS-04 有/廠務無 17 筆 ART — Jim 決定是否補登廠務編制表
- [ ] 廠務有/DS04 無 1 筆（JS1068, LEAN=7A）— Jim 決定廠務表是否刪除
- [ ] DS-06 定義 — 等 Jim 輸入
- [ ] 27_SMARTPN_LAYER_DEFINITION.md — Jim 尚未提供內容

### 進行中
- [ ] Partner outreach 目標資料庫建立（8 個版本外聯信）
- [ ] GTS 透明說明信草稿
- [ ] Kate Nishimura 草稿送出
- [ ] S02 PPT 最終確認

---

## DATA SYSTEM Project

File: 00_HANDOFF/24_DATA_SYSTEM.md (v1.5)

### Completed 2026-06-03 (Session A — Flask backend + DS-03 v1.3)
- ds03_ob_interface.html v1.3: Lookup Manager bug fixed (📚 Lookup button added)
- ds03_ob_interface.html v1.3: Save now POSTs to Flask backend (/api/ds03/save)
- Flask backend built: flask_backend/app.py + database.py + schema.sql
- SQLite schema complete: ob_header, ob_rows, ob_epph, lookup_viet_zh, change_log, ds01_sp (placeholder), ds02_fob (placeholder)
- API endpoints: POST /api/ds03/save, GET /api/ds03/load, GET /api/ds03/list, DELETE /api/ds03/delete
- API endpoints: GET /api/lookup/all, POST /api/lookup/add, GET /api/ds02/epph
- Default 30+ Viet-Chinese pairs seeded into DB on first run
- flask_backend/start.bat: double-click to start server (pip install + python app.py)

### Completed 2026-06-03 (Session B — Import scripts + Admin UI)
- flask_backend/import_ds02.py: CLI script to import DS-02 FOB Price List Excel
- flask_backend/import_ds01.py: CLI script to import DS-01 Season Plan Excel
- flask_backend/import_ds03_batch.py: Batch processor for historical OB Excel files (extracts Viet-Chinese pairs + imports OB headers)
- flask_backend/backup.py: SQLite daily backup utility (keeps 30 days by default)
- import_admin.html: Admin import page served at http://localhost:5000/admin
- Flask v1.1 backend: POST /api/ds02/upload, POST /api/ds01/upload, GET /api/ds02/list, GET /api/ds01/list, GET /api/stats
- database.py: import_ds02_records, import_ds01_records, list_ds02_records, list_ds01_records, get_db_stats (all with change tracking)
- requirements.txt: added openpyxl>=3.1.0

### Completed 2026-06-03 (Session C — DS-03 UI v1.4)
- ds03_ob_interface.html v1.4: 📂 Open button → Record Browser Modal (search/filter, click to load any saved OB record from server)
- ds03_ob_interface.html v1.4: DS-02 → button next to ART field (auto-fills E-PPH bar from DS-02 FOB LC values)

### Completed 2026-06-03 (Session D — Server test + start.bat fix)
- Python 安裝確認：系統有 Python（透過 Windows PATH）
- flask_backend/start.bat 修正：pip install → python -m pip install（相容所有 Python 安裝方式）
- Flask server 啟動測試成功：http://localhost:5000/api/health → {"ok":true,"version":"1.1"}
- http://localhost:5000 (OB Interface) 可訪問
- http://localhost:5000/admin (Import Admin) 可訪問

### Completed 2026-06-03 (Session E — DS-02 & DS-01 首次導入)
- import_ds01.py 修正：改為掃描所有工作表找 header（原 wb.active 指向 pivot 表）
- DS-02 FOB Price List 導入：New 1903 | Updated 2288 | Unchanged 1 | Errors 0
  來源：C:\Users\user\OneDrive\Desktop\FOB Price List.xlsx
- DS-01 Season Plan 導入：New 2044 | Updated 4929 | Unchanged 126 | Errors 0
  來源：C:\Users\user\OneDrive\Desktop\SS27 SP1 & FW26 SP7.xlsx（讀取 SS27 SP1-EVM 工作表）

### Completed 2026-06-03 (Session F — DS-03 批量導入 + DS-04 定義)
- import_ds03_batch.py 修正：加入 stdout UTF-8 encoding（解決 cp950 編碼錯誤）
- DS-03 批量導入：128 個 xlsx 處理 OK / 27 個舊 .xls 格式跳過 / 538 個 Viet-Chinese pairs 寫入 lookup_viet_zh
  來源：C:\Users\user\OneDrive\Desktop\IE（155 個文件）
- DS-04 定義：生產進度表（部門/組別/ART/月份），分析邏輯確認，待 Jim 提供 EOLR 對應表 + Excel 路徑
- 24_DATA_SYSTEM.md 更新至 v1.7

### Completed 2026-06-04 (Session G — DS-03 修正 + DS-05 建立)

**DS-03 批量導入修正（ob_header 74→152 筆）**
- 根本原因：content ART 提取抓到模板複製殘留 ART（如 5 個不同 LA TRAINER 檔案全部提取到 IH1651），導致大量檔案互相覆蓋
- 修正：fn_art() 從檔名提取第一個 ART 作為主要來源（override content）
- 修正：fn_eolr() 從 120双/60双 前綴推斷 EOLR
- 新增：_SKIP_FILENAMES（跳過 3 個已知重複 xlsx：HQ3330..、KH9682 Recovered、KI5323 Copy）
- 新增 CLI 選項：--xlsx-only（跳過 .xls，所有 .xls 都有對應 .xlsx）
- 新增 CLI 選項：--fresh（清空 ob_header 後重新導入）
- 最終結果：ob_header 152 筆（eolr=120: 127筆，eolr=60: 25筆；FW25~FW26、SS24~SS26）

**DS-05 定義確認**
- 名稱：大底課進度表（Sole Department Progress Sheet）
- 結構：A 欄 T 群組（T1 / T1+T2 / T1+T2+T3 等，完全照來源表）
- T 群組標頭格式："T1\n5月:20人\n6月:22人"
- 鞋型標題：含 AD-xxxxx 代碼（5位數）
- 合併邏輯：同一 T 群組內相同 AD 代碼 → 合併顯示，訂單加總
- MF 訂單：格式同 DS-04（MFyymmART-seq--qty(date)）
- 結果表設計原則：結果表不變更，所有變更在來源表作業

**DS-05 分析腳本建立**
- flask_backend/analyze_ds05.py：parse_sheet() + analyze() 完整實作
  - A 欄 T 群組邊界掃描
  - AD-xxxxx 代碼偵測（含 ADICHILL 修正）
  - ADICHILL bug 修正：當 ADICHILL 出現在儲存格但 AD 代碼在下方 1-2 列時，自動向下查找
  - MF 訂單與最近 AD 代碼關聯（row-order 最近上方原則）
  - AD 代碼合併 + 訂單加總
  - CLI：python analyze_ds05.py <file> [--group T1] [--dry-run]
- flask_backend/app.py v1.3：GET /api/ds05/analyze?file=<path>&group=<T1>

**工作時間確認**
- 08:00-16:00 Vietnam time = Jim 在線討論決策
- 16:00+ = Claude Code 後台執行

### Next Session Starting Point
1. DS-05 analyze_ds05.py 測試（Jim 提供實際大底課進度表 Excel 路徑）
2. 定義結果表 H-L 欄位邏輯（Jim 說明）
3. 定義 DS-06...N 數據源
4. 報表 dashboard 需求（固定 report tabs）
5. DS-04 生產進度表：
   → 仍待 Jim 提供 EOLR 對應表 + Excel 路徑

---

## SmartPN Atlas Project

Last updated: 2026-06-12

### 完成（2026-06-10）
- [x] S01–S17 PPT HTML：DONE（docs/preview/S01_PPT.html ~ S17_PPT.html，共 17 個靜態投影片）
- [x] Outreach work package: DONE（29_OUTREACH_WORK_PACKAGE.md）
- [x] 00_ENTRY_POINT.md Layer 3：加入 29 號文件索引

### 完成（2026-06-13）
- [x] 任務板機制建立：35_TASK_BOARD.md，永久任務追蹤（排隊中/進行中/✅完成/❌失敗）
- [x] DATA SYSTEM Cutting/裁斷機區 IE Process 導入完成
  - ie_import_cutting.py：建立 ie_process table，172 ARTs 全部導入，8081 行流程資料
  - flask_backend/test_output/cutting裁斷區_缺口清單.xlsx：完全缺=0 / 可疑=0 / 待分區=1476
  - formula 比例 67.7% / manual 32.3%
- [x] /ie/cutting 界面：Cutting 段流程檢視頁（stats bar / ART選擇 / 全部/待分區/Formula/Manual 篩選）
- [x] 34_MASTER_WORK_ORDER.md 入庫 + 00_ENTRY_POINT.md 索引更新
- [x] SMARTPN_DEMO.html 補漏：
  - Find Same Material：新增「⬡ 開新視窗」按鈕（openFsmInNewWindow），在新分頁開結果
  - 評論區：改為同公司(SHARED)/公開(OPEN) 兩段式顯示，附彩色 section header
- [x] SMARTPN_DEMO_SUPPLIER.html 補漏確認：母子公司樹/關務稅務分頁/GS1-SmartPN/SPU物性鎖定/二次加工編碼規則 全部已存在

### 完成（2026-06-13 晚）— Demo 全面重建 v3
- [x] 31_DEMO_INTERFACE_SPEC_v1.md：加入「補充確認（2026-06-13）」— 編碼規則(GS1+SmartPN,排除0/1/I/O/E)、單向可見性(只有Brand/Factory能發邀請,保護不被Supplier騷擾)、My Library個人庫+同公司分享、Requests即時對話、Find Same範圍(OPEN+已授權)
- [x] 兩個 Demo 全部材料圖改 **inline SVG 紋理**（8種 pattern，零外部 URL；先前 unsplash 全部移除）
- [x] SMARTPN_DEMO.html（Brand）完整重建：
  - 首頁(分類縮圖×5/Latest/Most Popular) → 搜尋(側欄分類+filter bar+External View) → 產品主頁(SmartPN ID+GS1+Options切換+成分/認證+Add/Compare/Find Same/Request) → 公司主頁(認證含到期日+DPP標示+產品列表+公開評論)
  - **Find Same Material 新視窗**：條件帶入(Product+Option)、範圍=OPEN+已授權、Identical/Alternative 分區、條件可改重搜
  - **My Library**：個人庫 + 分享給同公司按鈕
  - **Requests**：即時對話列表(像客服)+訊息+附件
  - 評論區：公開(Supplier可見)/私密(同公司) 標示 + 留言框含公開/私密切換
- [x] SMARTPN_DEMO_SUPPLIER.html 完整重建：
  - 選單兩項：公司建立(5 tab：基本/認證含上傳/財務資料夾🔒/關務資料夾🔒/子公司樹) + SmartPN建立(原物料/二次加工/權限/單價/誰看過)
  - 原物料：GS1選填 + SmartPN自動碼(排除0/1/I/O/E,可重產) + SPU物性鎖定黃警示 + Options可新增(顏色/幅寬/重量/單價/LT/SVG圖)
  - 二次加工：Input選現有Product+加工方式+比例+Output新碼(順序編碼)
  - 權限管理：4預設資料夾(財務/關務/DPP/材料)+勾選欄位+授權(公司·單位·帳號)+新材料預設PRIVATE
  - 單價管理：報價三層級+授權帳號+有效期紅黃綠
  - Boss BI 8 指標 + 誰看過(公司名+次數↔模糊,永不個資) + Requests(收到的對話可回覆)
- [x] 數據全部對齊 37_DEMO_MOCK_DATA.md（12材料/4供應商/BI $4.08M 互相對得上）

### 完成（2026-06-12）
- [x] 31_DEMO_INTERFACE_SPEC_v1.md：Jim 確認版（8問答覆）入庫，取代 30 號草稿。唯一 Demo 開發依據。
- [x] 33_DEMO_SPEC_v1_2_ADDENDUM.md：v1.2 增補確認版入庫。Boss BI 8 KPIs、誰看過我的材料隱私分級、角色測試項目全部採納。
- [x] SMARTPN_DEMO.html v2：完整重建 Brand/Factory 端購物網 UI
  - 頂部導覽（購物網式）：搜尋 / My Favorites / My Library / My Account / Settings
  - 三層頁面：搜尋網格 → SPU 主頁（含評論區）→ SKU 頁（規格選擇、Find Same Material）
  - 搜尋條件含：單價 / LT / DPP-ready 篩選
  - 材料卡片含 DPP-ready 標示
  - Compare：Apple 比較頁排版（3 欄、最優值高亮）
  - 12 筆 mock 材料 / 3 家 supplier
- [x] SMARTPN_DEMO.html v2.1（Brand）— 新增：
  - 材料卡片顯示供應商星等摘要（★ 平均分 from reviews）
  - 搜尋結果 LT ↑↓ / Price ↑↓ 排序切換按鈕
- [x] SMARTPN_DEMO_SUPPLIER.html v3：完整重建 Supplier 端（含 v1.2 增補全功能）
  - 選單三組：公司建立 / SmartPN 建立 / Boss BI
  - 公司建立：母/子公司 + 關務/稅務/材料訊息
  - 原物料建立：4 步驟精靈（SPU → SKU → 權限 → 確認）
  - 二次加工：Input/Output/Ratio 表單
  - 權限管理：欄位資料夾 + 打勾 + 授權給「公司 · 單位 · 姓名」
  - 單價管理：報價層級三選 + 有效期提醒（紅/黃/綠分級）
  - 誰看過我的材料：公司名+次數 ↔ 行業/地區模糊切換，永不顯示個人資料
  - 資料完整度：各材料進度條 + 缺漏欄位標籤 + DPP-ready 標示
  - Boss BI 經營儀表板：8 KPI 全部 CSS 圖表（Apple 風格，mock 數據）
    1. 總營業額（YoY/MoM 箭頭）2. 產品銷售佔比（橫條圖）3. 各公司營收佔比（母/子）
    4. 利潤比（毛利率橫條）5. 現金流明細表（含入帳預計日期）6. 應收帳款帳齡 30/60/90天
    7. 客戶集中度前三大 8. 報價成交率（環狀 CSS 圖）
  - 新材料預設全 PRIVATE

### 待確認（需 Jim 決定）
- [ ] Kate Nishimura email: READY TO SEND — 等 Jim 核准後送出
- [ ] GTS transparent note: DRAFT — 待確認 contact name
- [x] GRANT layer 暫定 (2026-06-10)，寫入 01_CONSTITUTION.md 第 9 章，取代 MSDG / SGL / GATE 候選
- [ ] S02 LinkedIn post: DRAFT — 待 Jim review + 核准
- [ ] 29_OUTREACH_WORK_PACKAGE.md: placeholder — 待 Jim 從 claude.ai 對話 2026-06-10 貼入完整內容

---

## Partner Outreach Strategy
File: 00_HANDOFF/25_PARTNER_OUTREACH_STRATEGY.md (v1.0)
Status: Confirmed 2026-06-06

Priority targets:
1. GTS — already connected, handle with care
2. TextileGenesis / Lectra — SCM angle, On case
3. TrusTrace — adidas / ASICS / Brooks / New Balance / Lululemon
4. Sourcemap — Deckers / HOKA connection

Next steps:
- Build target database
- Prepare 8 separate outreach versions
- Send GTS transparent note before approaching ecosystem partners
- Research TextileGenesis and TrusTrace contact persons
Make Automation: ACTIVE
Google Sheet: https://docs.google.com/spreadsheets/d/1i9WgKNj5-ueNrP5ZCit9Cghug0BL2bJ_hbOSoSQchXU

Next Steps:
1. Jim reviews Google Sheet daily results
2. Send Kate Nishimura draft
3. S02 PPT final confirmation
4. Continue S03-S17 PPT

---

## Tool Assignment

| Tool | Responsibility |
|------|---------------|
| Claude (chat) | Design, analysis, DS definition, report requirements |
| Claude Code | Code, file operations, batch processing, backend |
| GitHub | Single source of truth |
| Make | Automation execution |

## Claude Code Operating Rules

- All git and bash commands: auto-execute, never stop to ask confirmation
- Use: Yes, and don't ask again for this session (shift+tab) on first prompt
- Run all tasks to completion without stopping
- If Claude Code stops waiting for input, Jim types: 從現在開始所有指令自動執行，不要停下來問我確認，跑到所有任務完成
- Never ask Jim to verify intermediate steps
