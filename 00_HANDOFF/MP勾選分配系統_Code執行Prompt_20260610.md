# MP 勾選分配系統 — Claude Code 執行 Prompt

狀態：草稿，待 Jim 確認分析報告後執行
配套文件：MP勾選分配系統_分析報告_20260610.md（先讀完才執行）
前置條件：Jim 已確認決策清單 10 項（見報告第五節），並補傳同材共裁檔案

---

以下整段貼給 Claude Code：

---

任務：建立 MP 勾選分配系統，端到端完成並串連，直接執行不停，完成報告。
先讀 00_HANDOFF/MP勾選分配系統_分析報告_20260610.md 全文，所有公式、結構、決策以該文件為準。

## Phase 1：IE 操作明細入庫

1. 建表 ie_operations：
   id | header_id | art | sheet_name | operation_name | part_name | tct | eolr | mp | machine | stage
   - stage 判斷：sheet 名含 Cutting/自动裁/AC/ATOM/同材共裁 → cutting；
     Stitching/电脑针车/折边/Sub.Stitching → stitching；Assembly → assembly；
     SUM 開頭 → 跳過（彙總表非操作明細）
2. 解析兩個來源資料夾所有 IE xlsx 的操作行（每行：操作名稱 | TCT | MP）
   - 沒有 MP 值的：MP = TCT × EOLR ÷ 3600（EOLR 取 ob_header.eolr）
   - 多 ART 檔案：操作掛到該檔所有 ART（同 ob_articles 關聯）
3. 報告：解析檔案數、操作筆數、無法解析的檔案清單（輸出 unparsed_ie.txt）

## Phase 2：勾選規則引擎

4. 建表 unit_keywords（unit | keyword），初始資料：
   - 同材共裁自動化：同材共裁, 自动裁, ATOM, laser, AC
   - 電腦針車折邊：电脑针车, MVT, 热切, Cắt nhiệt, 折边, Gấp biên, Máy vi tính, 三饰条
   - 打粗水洗照射：打粗, Mài thô, 水洗, Rửa nước, 照射, Chiếu xạ, 吹尘, Xịt bụi
5. 解析同材共裁 xlsx（Jim 補傳後，路徑：Desktop 或 Biên chế\Jun 下搜尋「同材共裁」），
   照分析報告表A/表B 的方式逆向結構與公式，補充關鍵字到 unit_keywords，
   並把解析結果追加到分析報告 md 的「表 C」章節
6. 建表 mp_allocation：
   id | lean | art | operation_id | unit | stage | mp | checked | confirmed_by_jim
7. 建表 lean_hours：lean | base_hours | ot_hours | total
   - 從電腦針車檔「生管安排上班时数」sheet 導入（每月更新）
8. 自動預勾：ie_operations 的 operation_name 或 machine 命中 unit_keywords → 
   寫入 mp_allocation，checked=1
   - LEAN × ART 來源：auto_bianche 現有 (lean, art) 組合
9. 跨月繼承邏輯：新月份建 allocation 時，先複製上月同 (art, operation) 的勾選狀態，
   新鞋型才走關鍵字預勾

## Phase 3：帳號權限

10. 建表 users：id | username | password_hash | role | unit
    初始 4 帳號（密碼 Jim 之後自己改，先用預設）：
    - jim / admin / role=admin
    - tongcai / role=unit / unit=同材共裁自動化
    - dianno / role=unit / unit=電腦針車折邊
    - dacu / role=unit / unit=打粗水洗照射
11. Flask session 登入：/login 頁面，密碼 hash 用 werkzeug.security
12. 後端權限強制：所有 /api/allocation/* 寫入操作檢查 session：
    - role=unit → 只能改自己 unit 的 mp_allocation 行，跨單位請求回 403
    - role=admin → 全部可改 + 可執行鎖定
13. 建表 allocation_log：id | operation_id | unit | username | action | timestamp
    每次 check/uncheck 寫一筆

## Phase 4：勾選界面 /allocation

14. 登入後按身分顯示：
    - unit 帳號：只見自己單位。左側 LEAN 清單 → 該 LEAN 鞋型操作明細，
      系統預勾淺色標示，可勾/取消；底部顯示本單位本月勾走 MP 合計
    - admin（Jim）：三單位 tab 全見全改；每 LEAN 顯示對照行：
      IE原MP（三段）→ 各單位勾走 → CSA淨MP（三段）
    - 「確認鎖定」按鈕（admin 限定）：該月 mp_allocation 全部 confirmed_by_jim=1，
      之後唯讀，unit 帳號頁面顯示「本月已鎖定」
15. 界面樣式照 /ie 標準界面（深色 header、sticky、白底表格）

## Phase 5：串連產出

16. generate_bianche.py 加 MP 欄位：
    CSA 每行 cutting/stitching/assembly MP = ob_epph 對應段 − Σ(該lean該art已勾confirmed的MP)
    - 扣除公式統一用 TCT × EOLR ÷ 3600（與 ob_epph 同源）
    - 多 LEAN 合併操作的拆分、GCN 外包是否扣除：按 Jim 決策清單第 3/4 項定案執行
17. 輸出 3 個外單位自動表（格式照手工表）：
    - unit_打粗水洗照射.xlsx：需求人力 = 訂單÷(3600÷TCT)÷222
    - unit_电脑针车折边.xlsx：K欄 訂單÷(3600÷TCT)÷lean_hours.total + N欄 TCT×EOLR÷3600
    - unit_同材共裁.xlsx：公式按表C解析結果
18. nightly 加 task：每日重算 allocation 對照 + 3 表（僅未鎖定月份）

## Phase 6：驗證（Rule 15 + 17）

19. 用 1A 一個鞋型全鏈路樣本：
    IE 原 MP（三段數值）→ 預勾操作清單（名稱+TCT+MP）→ 各單位勾走合計 → CSA 淨 MP
    輸出 allocation_sample_1A.txt 給 Jim 核對
20. 對照手工表驗證：抽 3 個鞋型，自動表需求人力 vs 手工表數值，差異列出原因
21. git commit + push，報告全部結果

## 注意事項

- Rule 15：Phase 6 樣本 Jim 確認前，不寫「confirmed」進文件
- Rule 16：每個 Phase 跑完真實數據才進下一個
- 手工表的坑（分析報告第三節 6 項）：多LEAN合併格、多鞋型合併格、
  表A無ART欄需鞋型名匹配（用 normKey 清理）、大小寫全半形不一致
- 水洗固定 5 人不走 TCT 公式，hardcode 並標註
