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
| 019 | 37_DEMO_MOCK_DATA.md 入庫+索引 | 交接文件 | 進行中 | 2026-06-13 | — | 複製到00_HANDOFF/，更新索引和任務板 |
| 020 | SMARTPN_DEMO.html 替換37號數據世界 | Brand Demo | 排隊中 | — | — | 12材料/4供應商/4評論/FindSameMaterial/External view |
| 021 | SMARTPN_DEMO_SUPPLIER.html 替換37號數據 | Supplier Demo | 排隊中 | — | — | Formosa母子結構/8材料/Boss BI全數字 |
| 022 | docs/preview/INDEX.html 審查中心 | 交接文件 | 排隊中 | — | — | Apple風格清單，連結所有Demo+PPT |
| 023 | 任務板最終回報 | 管理 | 排隊中 | — | — | 收斂後輸出 |

---

## 待 Jim 決定（不擋工）

| 項目 | 說明 |
|------|------|
| Kate 郵件 | 29號文件 Part 2，READY |
| GTS note 聯絡人 | Part 3，等 Jim 填 |
| S02 LinkedIn post | Part 5，等確認 |
| GRANT 層名稱 | 暫定，等定案 |
