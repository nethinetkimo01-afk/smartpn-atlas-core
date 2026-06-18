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

| 048 | 勾選分配系統 Phase 1（IE後製工序→部件勾選外移→CSA MP扣除） | DATA SYSTEM | ✅完成 | 2026-06-13 | 2026-06-13 | schema(allocation_item/summary)+database.py(prefill/items/check/csa_mp/export)+app.py(8 routes+session)+allocation.html。Step1-6+5.5全做。zone→unit對應(ATOM/Laser/EMMA→同材共裁,電腦針車→電腦針車折邊,打粗/照射→打粗水洗)。權限：jim admin + tongcai/dianno/dacu unit_user，/check 後端強制 session.unit==target_unit 否則403。合成資料 KH9679 端到端驗證：prefill 7筆/csa cutting 10.115−0.05=10.065/3單位xlsx格式正確/跨部門403。⚠真資料需有 data/atlas.db 的機器(本checkout只有空schema) |

| 049 | 雙機作業交接機制（Code機↔結果機） | Infra | ✅完成 | 2026-06-13 | 2026-06-13 | flask_backend/sync.bat（git pull+重啟Flask）+ nightly/morning_sync.py（每日08:00自動同步,--install排程/--startup啟動資料夾,殺舊Flask不殺自己）+ 00_HANDOFF/雙機作業說明.md（程式碼自動同步/DB隨身碟手動同步） |

| 050 | IE細表界面修正7項（公式格/層數導入/+modal/表頭/版本切換/水蜘蛛/返回） | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | ie_cell_detail.html 重寫 + DB layers_per_cut 回填 + app.py/database.py add_row 擴充 |

| 052 | IE細表 Cutting段完整重建（DB重導入+像素還原界面） | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | ie_reimport_cutting_32.py + 12新欄位schema + ie_cell_detail.html 3列表頭+後製工序橫欄+inline+新增 |

| 053 | Cutting 標準時間改手工格 | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | ie_cell_detail.html renderCuttingRow 標準時間欄改白底手工格 |

| 054 | 四段界面公式精確還原（Cutting/Stitching/Assembly/STF） | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | ie_cell_detail.html：Cutting機器3600÷G÷E×F灰底/Auto 1.12灰底+生産目標/Stitching 1.1灰底+生産目標/STF貼底1.1公式+打粗手工/EOLR即時不重載 |

| 055 | IE細表全面修正5項（seq排序/+按鈕/tooltip/裁斷機資料/主表EOLR上下分行） | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | database.py ORDER BY zone,seq; 8行soft-delete; ie_cell_detail.html trigger-row+inline-add+tooltip; ie_interface.html 上下分行no-rowspan |

| 056 | ATOM/LASER/YINGHUI 區資料修正＋界面修正 | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | DB UPDATE: ATOM seq1 nt=19.99, seq2 std=7.168, seq3 nt=5.143; renderAutoCuttingRow 用儲存std; + 按鈕右對齊 |

| 057 | Cutting段最終修正：所有區統一19欄+DB修正 | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | ATOM qty_per_pair=2/Lưỡi gà std=7.2; renderCuttingZoneCard+renderCuttingRow統一; 2-row header; 標時用儲存值 |

| 058 | 主表+細表修正（EOLR分行/MP1位/+×按鈕/Output欄/水蜘蛛+） | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | ie_interface.html: EOLR第2行空格/act-cell+×/+按鈕/colspan10; ie_cell_detail.html: 水蜘蛛+修正; database.py+app.py: delete+create端點 |

| 059 | IE主表+細表+allocation 剩餘修正 | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | ie_interface.html: 120行act-cell空; ie_cell_detail.html: 表頭全名+×首欄+toFixed(1); allocation.html: UNIT_ZONES過濾+裁斷機完全隱藏+機台獨立欄 |

| 060 | 01_CONSTITUTION+21_STATUS+Demo設計決定同步 | SmartPN Atlas | ✅完成 | 2026-06-15 | 2026-06-15 | 01_CONSTITUTION §10-18新增; 21_CURRENT_STATUS今日確認清單; SUPPLIER Demo SPU→Product |

| 061 | DS-04 進度表解析+網頁+DB（1-12部全解析/ds04頁面/db入庫） | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | ds04_parsed.xlsx(1454筆/70外包) + /ds04 + ds04_orders + parse_ds04.py + import_ds04.py |

| 062 | ie_cell_detail Cutting段固定顯示所有區+標題修正 | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | CUTTING_FIXED_ORDER固定7區+_summary+WS; renderZones重寫; cleanName移除Target Output |

| 063 | Cutting段完全重建照LA TRAINER OG xlsx (Cutting da thật) 19欄19欄4層表頭 + 最重要規則 | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | 4層表頭(群組/越文/英文/中文); 19欄=材料/序號/名稱/層/件/刀/裁断std+theory+actual+5×post(std+ops); 七區①-⑦固定編號; 最重要規則00_MUST_READ_FIRST.md |

| 062b | 廠務編制系統：DS-04明細表CRUD+EOLR設定+廠務編制表 | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | /ds04(CRUD)+/eolr-settings(33 LEAN)+/bianche(440筆 MP)+schema+5fd0261 |

| 064 | Task062兩項修正：bianche全筆+ds04確認鎖定 | DATA SYSTEM | ✅完成 | 2026-06-15 | 2026-06-15 | bianche 440組(有IE=16/無IE=424灰字—); ds04_lock表+確認鎖定按鈕; 0502760 |

| 065 | GitHub 同步+環境確認+新界面盤點（/ds04,/eolr-settings,/bianche） | Infra | ✅完成 | 2026-06-15 | 2026-06-15 | pull faa4e5e→4343876; Py3.14.6/flask3.1.3/flask_cors/openpyxl3.1.5 全裝; app.py import OK(HAS_DS04=True); 3路由皆註冊(send_from_directory '..'); ds04/eolr_settings/bianche.html在repo根; data/atlas.db 172KB(本機有真資料) |

| 051 | Cutting段表頭重建 R3 colspan=6 + renderCuttingTab() | DATA SYSTEM | ✅完成 | 2026-06-16 | 2026-06-16 | ie_cell_detail.html: 裁断colspan=6(E-J六欄); CUTTING_ZONE_ORDER; renderCuttingTab() |
| 066 | 27_WORKING_RULES.md 建立 (完整IE規格+導入策略+帳號體系) | 交接文件 | ✅完成 | 2026-06-16 | 2026-06-16 | 00_HANDOFF/27_WORKING_RULES.md 5段：錯誤檢討/IE規格/Sheet對照/帳號/Excel規則 |
| 067 | 00_MUST_READ_FIRST.md 建立（做事方式+IE規格） | 交接文件 | ✅完成 | 2026-06-16 | 2026-06-16 | 00_HANDOFF/00_MUST_READ_FIRST.md |
| 068 | IE細表界面重建 + 全量IE導入 + 帳號管理 | DATA SYSTEM | ✅完成 | 2026-06-16 | 2026-06-16 | Step1:Cutting七區zone-type-aware欄位; Step2:全量155xlsx→ie_process 20,434筆(支流2555/0未知sheet); Step3:ie_import_comparison.xlsx; Step4:/admin/users+sys_users表 |

| 069 | IE導入對比表（人員數字） | DATA SYSTEM | ✅完成 | 2026-06-16 | 2026-06-16 | ie_mp_comparison.py; SUM.C2B四段人員 vs Σ(ST)/30 理論人數; 154筆/394紅格; ie_import_comparison.xlsx |

| 070 | 廠務編制系統驗收+bugfix（allocation prefill+xlsx export） | DATA SYSTEM | ✅完成 | 2026-06-16 | 2026-06-16 | 10項驗收全Pass; prefill lean從ds04_orders查(非ob_header); ws.protection修正; e431ee7 |

| 071 | /eolr-settings 界面修正（LEAN排序+年度橫向表格+年切換） | DATA SYSTEM | ✅完成 | 2026-06-16 | 2026-06-16 | eolr_settings.html: 35 LEAN固定順序+額外LEAN自動補尾; 2026(6月)/2027(12月)橫向表格; 年份切換; 即時儲存; 移除說明文字 |

| 072 | /ds04 明細表修正（部門/LEAN排序+預計完成日欄+統計標題） | DATA SYSTEM | ✅完成 | 2026-06-16 | 2026-06-16 | ds04.html+schema.sql+database.py: 部門→LEAN二層分組; 部門統計(N筆,M雙); LEAN統計(N筆,M雙); 預計完成日欄(空=—); estimated_completion欄位; 排序照規格 |

| 073 | /allocation 勾選分配系統完整重建（機台分區+LEAN分組+訂單來源） | DATA SYSTEM | ✅完成 | 2026-06-16 | 2026-06-16 | allocation.html 全重建：3 tabs(同材共裁/電腦針車/打粗水洗)+zone區段+LEAN分組+鞋型×ART子表頭+部件行(☑/CT/Output/理論人數)+STF需求人力公式; database.py: order_qty→ds04_orders JOIN/prefill is_checked=1/alloc_fix_default_checked; app.py: fix_defaults route; T1-T4全Pass(12067筆prefill/3A ATOM 3項/toggle ok) |

| 074 | /bianche 廠務編制表完整修正（CSA/OCS/RB/QC） | DATA SYSTEM | ✅完成 | 2026-06-16 | 2026-06-16 | bianche.html: 標籤CSA/OCS; LEAN固定排序; LEAN標題行(總訂單+編制input); 欄位=鞋型/ART/訂單/裁斷/針車/成型/協理給(刪合計MP+合計行); OCS 8區段(大底課/組底配套/自動化/電腦針車/印刷/設備工程/副總室/現場技轉KTHT); 大底課顯示鞋型明細; RB 18組; QC 48+4組; database.py: DEPT_GROUPS更新+bianche_lean_hc表+get/set函數; app.py: lean_hc GET/POST routes+export/import更新; T1-T6全Pass |

| 075 | 數據庫保護與備份機制 | Infra | ✅完成 | 2026-06-17 | 2026-06-17 | soft-delete ds04_orders / alloc+bianche edit_log / backup/ 4腳本 / migrate.py M001-M003 / 27_WORKING_RULES §六 |
| 076 | ie_cell_detail 手工格藍框+Cutting實際人數合併Modal | DATA SYSTEM | ✅完成 | 2026-06-17 | 2026-06-17 | 藍細框startEdit/commitEdit; cut-act-inp+合按鈕; mergeModal checklist; saveSingleActual; save_group API |
| 077 | 自我驗收所有界面：×首欄+寬放率手工格 | DATA SYSTEM | ✅完成 | 2026-06-17 | 2026-06-17 | ie_cell_detail.html renderZoneCard ×移首欄 / allowance_pct白底可編輯 / addRowInline佔位格 |
| 078 | IE細表界面視覺重設計（白底/公式灰字/手工黑字/黑框輸入） | DATA SYSTEM | ✅完成 | 2026-06-17 | 2026-06-17 | ie_cell_detail.html: formula-cell去灰底改#aaa灰字; num/.actual改#222黑字; input黑框#333; 移除所有background:#fff顯式設定 |
| 079 | IE細表合併功能完整版（rowspan/解除/多段/popup） | DATA SYSTEM | ✅完成 | 2026-06-17 | 2026-06-17 | renderGroupActualCell(rowspan) / openGroupAction popup / unmergeGroup / 全段支援 / DB: update+delete_group |
| 080 | 合併功能完整自測並修正所有問題 | DATA SYSTEM | ✅完成 | 2026-06-17 | 2026-06-17 | 4項全通過：Test1清空✅ Test2過濾✅ Test3改人數✅ Test4Stitching✅ 無需程式修正 |
| 081 | IE細表最終全面驗收（Step1-8）+ Cutting表頭對齊修正 | DATA SYSTEM | ✅完成 | 2026-06-17 | 2026-06-17 | V3/E3 th-vi/th-en left class; 全8步驗收通過：Cutting七區/表頭/×+/公式手工/Stitching-STF欄位/合併Test1-4/頂部功能/主表EOLR分行 |
| 082 | 完整角色模擬驗收 — 全功能實作（S1-S20） | DATA SYSTEM | ✅完成 | 2026-06-17 | 2026-06-17 | login/me/assign/review/approve/stage_approve; M004 migration; login.html; ie_interface.html(···menu/assign modal); ie_cell_detail.html(submit/approve); admin_users.html(assign panel); S1-S20全通過 |
| 083 | 主表 /ie 新增操作入口 | DATA SYSTEM | ✅完成 | 2026-06-17 | 2026-06-17 | 新增鞋型modal(多ART/材料/季度/階段); ···選單(+修改季度材料); manager角色; 移除舊+×按鈕; admin_users.html manager支援 |
| 084 | IE細表格子改表單風格（公式格/手工格/無hover） | DATA SYSTEM | ✅完成 | 2026-06-17 | 2026-06-17 | ie_cell_detail.html: formula-cell白底灰框灰字cursor:default; num白底黑框黑字; actual-cell同步; 移除所有hover; 移除inline color:#aaa覆蓋 |
| 085 | IE細表 input改type=text + 全格線統一 | DATA SYSTEM | ✅完成 | 2026-06-17 | 2026-06-17 | 所有type="number"→type="text"(移除step/min)共10處; proc-table td/del-cell border:#e8ecf4→#ddd統一灰框 |
| 086 | IE細表視覺全面重設計（Apple 風格） | DATA SYSTEM | ✅完成 | 2026-06-18 | 2026-06-18 | ie_cell_detail.html: 公式格#8E8E93灰字/#E5E5EA邊框/cursor:default; 手工格#1C1C1E黑字/#C7C7CC邊框/點擊#007AFF藍框; 表頭#1C1C1E白字統一; 刪除所有hover背景/綠橙highlight; JS inline border全改Apple色; commit 385bec7 |
| 087 | IE細表修正：tooltip跟鼠+合併格白底黑框+佔位格補邊 | DATA SYSTEM | ✅完成 | 2026-06-18 | 2026-06-18 | tooltip改mousemove跟隨; renderGroupActualCell移rowspan改inline樣式; renderGroupPlaceholder補#E5E5EA邊框; renderCuttingRow/renderZoneCard改呼叫renderGroupPlaceholder; commit ebd9bd6 |
| 088 | IE細表§9補完：無「—」+頂部列淺色+儲存▼下拉 | DATA SYSTEM | ✅完成 | 2026-06-18 | 2026-06-18 | 全格「—」→空白(含fmtNum/dv/ops/renderCell); body#FFF/topbar#F5F5F7淺灰; eolr-badge/stage-select/btn-outline全改淺色; 新建版本移除→「儲存▼」下拉(儲存/另存新階段); commit dff469d |

## 待 Jim 決定（不擋工）

| 項目 | 說明 |
|------|------|
| Kate 郵件 | 29號文件 Part 2，READY |
| GTS note 聯絡人 | Part 3，等 Jim 填 |
| S02 LinkedIn post | Part 5，等確認 |
| GRANT 層名稱 | 暫定，等定案 |
