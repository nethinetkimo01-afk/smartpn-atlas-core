# Current Status

Last updated: 2026-06-15

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
