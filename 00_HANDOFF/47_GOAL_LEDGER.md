# 47 — 目標總帳（Goal Ledger）

Version: v1.0 | 建立 2026-07-14（Task U）| Status: ACTIVE（活帳本，持續維護）

> **本帳本是「中樞本則訊息」的單一真相表。** 任何定案／需求一產生即入帳並編 ID；
> 每個新視窗開場、每批任務派發前，中樞先對帳；**只有 Jim 可關帳**（改狀態為 ✅CLOSED）。
> 規則正本見 `00_ENTRY_POINT.md` 與 `27_WORKING_RULES.md`。

## 狀態圖例
🟡OPEN（待辦）· 🔵IN-PROGRESS（進行中）· ⛔BLOCKED（卡住，註明卡點）· 😴DORMANT（休眠）·
🧹TO-CLEAN（待清檔）· ✅CLOSED（僅 Jim 可關）

---

## 未結事項總帳

| ID | 事項 | 狀態 | Owner | 卡點 / 下一步 | 來源檔 |
|----|------|------|-------|---------------|--------|
| **G-01** | ME129 按更新鍵 pull 最新碼（含第三批 Task F–O + Task S/T） | ⛔BLOCKED | ie5/Thanh（按）| 等有人在 ME129 按更新；抽查：標時39600、連刀欄在層數左、STF八欄舊值不變、tongcai全灰 | 41§四.1、21 |
| **G-02** | `/admin/recalc-cutting` 裁斷 ×1.0 重算：預覽→確認執行（自動備份可還原） | ⛔BLOCKED | **Jim** | 等 Jim 於瀏覽器執行；不派 cmd 到 ME129；`recalc_cutting_x10.py` 備援 | 41§四.2、21 Task F |
| **G-03** | IE 來源 xlsx（~623MB）進 Code 機 → 編制表 36欄產能/人數**真值** + 真資料逐欄比對 | ⛔BLOCKED（降級：**僅剩真資料比對**）| **Jim** | 邏輯層已由 Task V 合成資料**7/7 全驗證**（Step6 MP 0 差異、連刀÷N、offline撥人、缺IE不擋單、STF式、36欄已知人數欄填值）。剩：真 IE xlsx 進 Code 機（或 ME129）做真資料層＝對映覆蓋+廠務檔逐欄比對+未知欄(CT/產能/PPH)公式 | 41§四.4、21 Task G/V、驗收報告 |
| **G-04** | manager 對 IE 工序維持唯讀（編審分離）— 待 Jim 追認 | 🟡OPEN | **Jim** | 代決待追認；Thanh 需編輯時另開 editor 帳號 | 41§四.5、21 Task I 註 |
| **G-05** | GitHub Pages 開通（demo 對外連結可分享） | ⛔BLOCKED | **Jim** | 等 Jim 於 GitHub repo 設定開通 Pages | 中樞訊息 2026-07-14、INDEX |
| **G-06** | GRANT layer 名稱最終定案（暫定 GRANT，取代 MSDG/SGL/GATE 候選） | 🟡OPEN | **Jim** | 暫定可用，名稱未最終拍板 | 21(2026-06-12)、01_CONSTITUTION §9 |
| **G-07** | 設備種類選項維護（ie5 自助 `/admin/equipment-types`，不經 Code） | 🔵IN-PROGRESS | ie5 | 自助維護，無卡點 | 41§四.3、21 Task K |
| **G-08** | SaaS 介面 8 項設計需求落地到 demo | 🔵IN-PROGRESS | 中樞 | v3 已疊加八項（見 43）；持續依實際需求微調 | 43、41§四.6 |
| **G-09** | SmartPN 下一步候選：①品牌 KPI dashboard ②工廠視角 demo ③API 可行性驗證 | 🔵IN-PROGRESS | 中樞 / **Jim**(③) | **①＝Task W 已落地（V3 品牌端，8/8 PASS）**；②未起；③Jim 自留 | 43「未來事項」、21 Task W |
| **G-10** | 求職／外聯線（Partner Outreach、Kate Nishimura、GTS note、LinkedIn） | 😴DORMANT | **Jim** | 全線休眠，非當前優先；Jim 決定何時喚醒 | 21、25_PARTNER_OUTREACH |
| **G-11** | MP 勾選分配舊懸案（mp_mismatch KI1387 分配規則）＋舊分析檔待清 | 🧹TO-CLEAN | **Jim** | 分配規則等 Jim 確認（勿改計算邏輯）；`MP勾選系統_*_20260610.md` 等舊檔待清 | 21(mp_mismatch)、memory、00_HANDOFF/MP勾選* |

---

## 掃描結果：「已定案但無對應 commit/實作」條目（2026-07-14 掃 00_HANDOFF 全檔）

掃描全 00_HANDOFF（含『定案/決定/確認採用』字樣）比對現碼／git，結論：

- **無「可由 Code 立即實作卻漏做」的孤兒定案**。所有已定案功能項均已有對應 commit
  （第三批 Task F–O、Demo v2/v3 Task P/R/R-1、Task S/T 本批），或屬 Jim-blocked（G-01~G-05）／
  待 Jim 拍板（G-04、G-06）／休眠（G-10）／待清檔（G-11）。
- **已定案已實作、僅待真資料驗證**：36欄導出（Task G）＋編制表 Step5/6（Task V 合成驗證）→ 併入 G-03。
- **已定案已拆除**：Demo 三違規（SmartPN Verified／毛利率卡／誰看過）v2/v3 全域 0 命中（已實作）。
- **DS 系列殘留待決**（次要，未入主帳）：DS-04有/廠務無 17 筆、廠務有/DS04無 1 筆(JS1068)、DS-06 定義
  → 皆等 Jim 輸入，非中樞可代決；列此備查。

| **G-12** | Task X：SmartPN 品牌端交換機制實作 + 死按鈕歸零 | ✅ 已完成（待 Jim 關帳）| 中樞 | Jim 提供 44 規格+real_click_test.js 內容後建檔；v3 兩檔疊加 44 資料模型 + 死按鈕歸零(0/0) + 引導 A→B→C。**node real_click_test.js 兩檔 8/8 全綠** | 44 號檔、commit 2a85a0e |

> 若後續發現新的孤兒定案，即刻編 ID 入帳（下一個可用 ID：G-13）。

---

## 對帳規則（正本同見 00_ENTRY_POINT / 27_WORKING_RULES）
1. **入帳**：任何定案/需求一產生，中樞立即在此表新增一列並編 ID（G-NN）。
2. **開場對帳**：每個新視窗開場、每批任務派發前，中樞先讀本表對帳，回報未結項。
3. **關帳**：狀態改 ✅CLOSED **只有 Jim 可為之**；中樞只能更新進度/卡點，不得自行關帳。
