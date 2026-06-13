# SmartPN Atlas — 任務板
Version: v1.0 | 建立: 2026-06-13
維護人: Claude Code（自動更新）

---

## 永久規則（每個 session 必讀）

1. **收到任何新任務** → 先在板上登記一行（排隊中）再開工
2. **開工** → 改「進行中」；結束 → 改「✅完成」或「❌失敗（附原因）」，填產出檔案路徑
3. **每次更新任務板** → 隨手 commit（訊息格式：`board: 任務名 狀態`）
4. **收到「報告任務板」指令** → 直接輸出整個表格
5. **狀態只有四種**：排隊中 / 進行中 / ✅完成 / ❌失敗（附原因）

---

## 任務板

| # | 任務 | 案子 | 狀態 | 開始 | 完成 | 產出/備註 |
|---|------|------|------|------|------|----------|
| 001 | Cutting/裁斷區 IE Process 導入 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | ie_import_cutting.py / ie_process 8081行 172 ARTs |
| 002 | 缺口清單 xlsx 輸出 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | flask_backend/test_output/cutting裁斷區_缺口清單.xlsx |
| 003 | /ie/cutting 界面 Cutting 段檢視 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | ie_cutting.html + /api/ie/cutting |
| 004 | 34_MASTER_WORK_ORDER.md 入庫 | 交接文件 | ✅完成 | 2026-06-13 | 2026-06-13 | 00_HANDOFF/34_MASTER_WORK_ORDER.md |
| 005 | SMARTPN_DEMO.html 補漏 | Brand Demo | ✅完成 | 2026-06-13 | 2026-06-13 | FSM開新視窗 + 評論同公司/公開分組 |
| 006 | SMARTPN_DEMO_SUPPLIER.html 補漏確認 | Supplier Demo | ✅完成 | 2026-06-13 | 2026-06-13 | 全部已存在，無需修改 |
| 007 | QC S01-S17 PPT 對照 16 號規格 | Demo QC | ✅完成 | 2026-06-12 | 2026-06-12 | docs/preview/PPT_QC_REPORT.md（上次 session） |
| 008 | flask_backend/data/*.db 入 .gitignore | 倉庫健康 | ✅完成 | 2026-06-12 | 2026-06-12 | .gitignore + git rm --cached atlas.db |
| 009 | Boss BI 8 指標（SMARTPN_DEMO_SUPPLIER） | Supplier Demo | ✅完成 | 2026-06-12 | 2026-06-12 | 8 KPIs CSS 圖表（commit 6674c07） |
| 010 | 「誰看過我的材料」隱私分級 | Supplier Demo | ✅完成 | 2026-06-12 | 2026-06-12 | view-who-viewed 隱私三層（commit 6674c07） |
| 011 | Brand 端補漏（星等/LT排序） | Brand Demo | ✅完成 | 2026-06-12 | 2026-06-12 | 星等 + LT/Price 排序按鈕（commit 0c9b9f4） |
| 012 | 21_CURRENT_STATUS.md 更新 | 交接文件 | ✅完成 | 2026-06-13 | 2026-06-13 | 今日全部進展記錄完畢 |
| 013 | 35_TASK_BOARD.md 建立任務板機制 | 交接文件 | ✅完成 | 2026-06-13 | 2026-06-13 | 00_HANDOFF/35_TASK_BOARD.md（本檔） |
| 014 | ie_process 重複行原因查證 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | 根因=腳本跑兩次，8081行×2=16162，等Jim授權修正 |
| 015 | 36 測試/Boss演示腳本 入庫 | 交接文件 | ✅完成 | 2026-06-13 | 2026-06-13 | 00_HANDOFF/36_UX_TEST_AND_BOSS_DEMO_SCRIPT.md + 索引更新 |
| 016 | ie_process去重重導（方案1+2） | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | 8081行乾淨，UNIQUE INDEX防重，ie_import_cutting.py INSERT OR IGNORE |
| 017 | Cutting段收尾掃描（待分區統計+L欄清單） | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | ATOM87/自動化651/L欄68種值，數字=刀數標準，見報告 |
| 018 | /ie/<id>詳細頁 4段結構重構 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | 4段tabs+7區zone+原始sheet切換+/api/ie/<id>/process |
| 019 | 37_DEMO_MOCK_DATA.md 入庫+索引 | 交接文件 | ✅完成 | 2026-06-13 | 2026-06-13 | 00_HANDOFF/37_DEMO_MOCK_DATA.md + 00_ENTRY_POINT.md更新 |
| 020 | SMARTPN_DEMO.html 替換37號數據世界 | Brand Demo | ✅完成 | 2026-06-13 | 2026-06-13 | 12材料/4供應商/4評論/FSM#1vs#7/外部視角切換/#10-12PRIVATE |
| 021 | SMARTPN_DEMO_SUPPLIER.html 替換37號數據 | Supplier Demo | ✅完成 | 2026-06-13 | 2026-06-13 | FMG母子/7材料/Boss BI $4.08M/報價到期/誰看過我 |
| 024 | IE標準樣本選取（四段覆蓋統計） | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | 全195份均四段全覆蓋；前10名按sheet數/manual格排列；1609ER RS=hdr49/160 |
| 022 | docs/preview/INDEX.html 審查中心 | 交接文件 | ✅完成 | 2026-06-13 | 2026-06-13 | Apple風格清單/2系統Demo/S01-S17 PPT+Demo/數據世界說明 |
| 023 | 任務板最終回報 | 管理 | ✅完成 | 2026-06-13 | 2026-06-13 | 見下方最終狀態 |

---

| 025 | LA TRAINER OG 四段導入+細表界面 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | ie_import_la_trainer.py / API 3端點 / ie_cell_detail.html / S1-S6全PASS |

| 026 | SMARTPN_DEMO.html 重建（EN/ZH toggle + Product/Option） | Brand Demo | ✅完成 | 2026-06-13 | 2026-06-13 | 21 patches OK：lang toggle/i18n/SPU→Product/SKU→Option/remove cta-note |
| 027 | SMARTPN_DEMO_SUPPLIER.html 重建（lang toggle） | Supplier Demo | ✅完成 | 2026-06-13 | 2026-06-13 | topbar lang toggle + i18n script 插入 |
| 028 | SMARTPN_SCENARIO_INDEX.html 建立 | 交接文件 | ✅完成 | 2026-06-13 | 2026-06-13 | docs/preview/SMARTPN_SCENARIO_INDEX.html — S01-S17 PPT links only |
| 029 | INDEX.html 簡化（僅2入口） | 交接文件 | ✅完成 | 2026-06-13 | 2026-06-13 | Brand Demo / Supplier Demo 兩卡片，移除 scenario table |
| 030 | 任務板更新（026-035） | 管理 | ✅完成 | 2026-06-13 | 2026-06-13 | 本行 |
| 031 | 修復 /ie/32/detail 路由 + Part2 細表界面確認 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | Flask重啟(PID 13884)→路由200；細表4段/7區/EOLR切換已驗 |
| 032 | SUM C2B API /api/ie/<id>/sum | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | database.py get_ie_sum() / app.py GET /api/ie/<id>/sum?eolr= |
| 033 | SUM C2B 界面 /ie/<id>/sum | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | ie_sum.html / /ie/<id>/sum 路由 / EOLR toggle / 驗收對照表 |
| 034 | SUM C2B 驗收 LA TRAINER OG EOLR=120 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | test_output/sum_verification_32.txt — STF=5.0 vs 16.0 待查 |
| 035 | 1609ER RS 四段導入 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | ie_import_1609er_rs.py / header49(EOLR=120)+160(EOLR=60) / 寬幅裁斷格式 |
| 036 | SUM C2B 驗算 1609ER（EOLR=60+120 對照） | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | test_output/sum_verification_1609.txt — EOLR=120: 裁12.29/針33.08/成35.52/貼14.11 |

| 037 | Assembly/STF 差異查證 + get_ie_sum 邏輯分析 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | 結論：code 邏輯正確(fallback=actual for theory=None)；差異是 SUM.C2B 用 actual_operators 非公式 |
| 038 | 更新 verification reports + 差距根因說明 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | sum_verification_1609.txt / sum_verification_32.txt 含根因分析 |
| 039 | 成型面照射歸段修正（zone→成型UV）+ LA TRAINER STF flag=待手工 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | 12行zone更名；5行flag=待手工；細表橙色badge |
| 040 | 水蜘蛛歸段→assembly/水蜘蛛(offline) + get_ie_sum 改 actual_ops + 細表雙欄 | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | STF WS→assembly; 打粗水洗actual清除; 4段PASS(切-1.7%/針0%/成0%/貼0%) |
| 041 | SMARTPN_DEMO.html 材料圖片換 Unsplash 真實照片 | Brand Demo | ✅完成 | 2026-06-13 | 2026-06-13 | SMARTPN_DEMO.html+SUPPLIER: 12張卡片+5分類縮圖+mat-row-img |

| 042 | IE 細表界面全面修正（10項） | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | ie_cell_detail.html 重寫：+/× row, 分組modal, 雙欄理/實, 水蜘蛛, 中/越toggle |
| 043 | IE 主表列表頁修正（EOLR分行） | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | ie_interface.html: 生產季度|鞋型+細表|ART|材料|EOLR行|4MP; rowspan=2雙EOLR |

| 044 | 兩 Demo 材料圖改 inline SVG 紋理（8 pattern，零外部 URL） | Brand+Supplier Demo | ✅完成 | 2026-06-13 | 2026-06-13 | SMARTPN_DEMO.html + SUPPLIER：8 種 SVG pattern 生成器；移除全部 unsplash |
| 045 | 31_DEMO_INTERFACE_SPEC_v1.md 補充確認（編碼/單向可見/Library/Requests/FSM範圍） | Spec | ✅完成 | 2026-06-13 | 2026-06-13 | 文末新增「補充確認（2026-06-13）」段 |
| 046 | SMARTPN_DEMO.html（Brand）完整重建 v3 | Brand Demo | ✅完成 | 2026-06-13 | 2026-06-13 | 首頁/搜尋/產品/公司/Find Same新視窗/My Library分享/Requests即時對話/External View；GS1+SmartPN碼；評論公開私密切換 |
| 047 | SMARTPN_DEMO_SUPPLIER.html 完整重建 v4 | Supplier Demo | ✅完成 | 2026-06-13 | 2026-06-13 | 兩選單：公司建立(5tab)/SmartPN建立(原物料/二次/權限/單價/誰看過)+Boss BI 8指標+Requests；SmartPN碼排除0/1/I/O/E |

## 待 Jim 決定（不擋工）

| 項目 | 說明 |
|------|------|
| Kate 郵件 | 29號文件 Part 2，READY |
| GTS note 聯絡人 | Part 3，等 Jim 填 |
| S02 LinkedIn post | Part 5，等確認 |
| GRANT 層名稱 | 暫定，等定案 |
