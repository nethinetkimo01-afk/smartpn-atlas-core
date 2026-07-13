# 41｜三線整合交接（2026-07-13 版）
Status: ACTIVE。本檔取代原計畫中的 41/42 兩檔；42_CODE_BATCH_STATUS 作廢，
其內容（2026-07-11 批次）已全數執行完畢，結果見 驗收報告_20260711.md 與本檔。

## 一、三條線
1. IE表（生產系統）：已上線 ME129（172.16.1.29:5000）。第三批 Task F–L 全綠已 push：
   cutting ×1.0（連刀欄，公式 3600÷刀÷層×件×1.0÷連刀）、裁斷手工區、ATOM/EMMA 精簡5欄、
   flushPendingEdits 防丟值、read_only/無權editor 前端全灰、STF 八欄向 Assembly 標準化
   （舊資料 fallback 不重算）、STF 實際人數→「EOLR=190 實際人數」、36欄導出（值 BLOCKED 等真實資料）、
   設備種類管理頁（manager/admin，已引用鎖名）。
2. 編制表（本階段主線）：E2E Step1/2/3/4/7 PASS；Step5 勾選表、Step6 MP 手算 BLOCKED——
   Code 機無 IE 來源資料。解鎖條件：在 ME129 執行，或 IE 來源 xlsx（約623MB）進 Code 機。
3. SmartPN Atlas SaaS：議會審查兩輪完成，D1–D6 全定案＋退出權＋責任原則，
   見 43_COUNCIL_SAAS_REVIEW.md。D2（需求雷達）＝保留不做，未來按雙方實際需求再加。
   基礎版面＝docs/preview/SMARTPN_DEMO.html＋SMARTPN_DEMO_SUPPLIER.html（內嵌 mock data）。

## 二、三線共用工作法
Playwright 真跑瀏覽器自測＋隔離副本不污染正式DB＋對抗性測試（把用戶當會亂點的新人）＋
測過才 push＋交出去必須能用。第一性原則：不能執行的操作不該顯示。

## 三、中樞守則
Claude 是中樞不是打字機：自行思考、主動 web_search 查成熟做法、主動提建議、預想 Jim 下一步；
Jim 說「交給你」時中樞代決並記錄理由，Jim 可推翻。

## 四、未結待辦（依序）
1. ME129 按更新（ie5/Thanh 可按）→ 抽查：標時39600、連刀欄在層數左、STF八欄舊值不變、tongcai全灰。
2. ME129 跑 recalc_cutting_x10.py --dry-run → 筆數回報中樞判讀 → --apply（自動備份，rollback 可還原）。
3. 設備種類選項：ie5 自行上 /admin/equipment-types 維護，不經 Code。
4. 編制表 Step5/6：待條件解鎖後在有 IE 資料環境重跑。
5. 已代決待追認：manager 對 IE 工序維持唯讀（編審分離）；Thanh 需編輯時另開 editor 帳號。
6. SaaS 下一步：43 號檔「SaaS 介面設計需求 8 項」逐項落到 demo 版面改版任務。
