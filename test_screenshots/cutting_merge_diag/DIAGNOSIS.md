# 裁斷合併 bug 診斷報告（只診斷，不修）— 2026-07-11

## 現象（回報）
裁斷（cutting）合併實際人數時，層數/數量/刀數 消失，疑似前端 re-render 問題，發生在合併瞬間。

## 重現方式
- 隔離 E2E 庫 + 最小 cutting 樣本（header 1，裁斷機 5 道工序，seq1-5，各有層/件/刀值）。
- Playwright 腳本：`e2e_taskB_cutting_merge_diag.js`（合併前後 DOM 快照）＋
  `e2e_taskB_cutting_merge_unsaved.js`（未存編輯測試）。截圖 01–05 + diag_data.json / unsaved_edit_test.json。

## 觀察一：對「已儲存」的資料，合併渲染是**正確**的（值不會消失）
合併前後每列 `data-cfield`（層/件/刀）值全數保留：

| 步驟 | 各列 層/件/刀 | 說明 |
|---|---|---|
| 01 合併前 | 2/4/11, 3/6/22, 1/2/33, 4/8/44, 2/3/55 | 每列 21 td |
| 02 連續合併(seq1,2,3, 人數9) | 值全保留；第1列出現 group-cell rowspan=3；第2、3列 td=20 | 少的 1 格＝實際人數欄被 rowspan 蓋住（**正確**）|
| 03 解除合併 | 還原 21 td，值不變 | 正確 |
| 04 非連續合併(seq1,3, 人數7) | 值全保留；群組成員被重排為相鄰(seq1,seq3,seq2…)；rowspan=2 | 重排讓 rowspan 對齊（**正確**）|

→ 結論：rowspan / 群組列渲染 / 欄位對齊 **沒有缺陷**；已儲存的層/件/刀不會因合併消失。
（推測先前 Task086/087 的合併 rowspan 重寫已修掉純渲染面的錯位。）

## 觀察二：真因＝合併觸發的整段重載會**丟棄未提交的編輯**（已重現，LOST=true）
- 在第1列「層數」輸入框輸入 `99`（**不 blur、不提交**）→ DOM 值＝99。
- 立即合併（`save_group` → `loadSegment('cutting')`）→ 重載後該格變回 `2`（伺服器舊值）。
- `unsaved_edit_test.json`：`typedValue=99, domValueAfterType=99, valueAfterMergeReload=2, LOST=true`。

### 真因定位（檔案 / 函數 / 行為）
`ie_cell_detail.html`：
1. 層/件/刀輸入格（`renderCuttingRow` 的 `edMA`，約 L908）：
   `oninput="recalcCuttingStdByPid(pid)"`（只即時重算，**不存**）＋
   `onblur="commitEditStatic(this,pid,field)"`（**blur 才存**）。
2. 合併提交 `submitMerge()`（約 L1708）多工序分支：`save_group` 成功後呼叫 `loadSegment(SEG)`。
   同型呼叫也在 `saveGroupHc()`(L1650)、`unmergeGroup()`(L1664)、單工序 `submitMerge` 分支(L1723)。
3. `loadSegment()`（L751）：`EDITS = {}` → 重新 fetch `/api/ie/cell/...` → `renderZones()` 整段重繪。
   → 任何「已輸入但未 blur 提交」的層/件/刀被伺服器舊值覆蓋 ＝ **合併瞬間消失**。

### 為何日常也會踩到（不只程式化）
使用者在層/件/刀輸入框打完字，直接點「合」鈕 → 點擊雖會觸發 blur（非同步 fetch 存檔），
但 `submitMerge` 的 `loadSegment` 重載 fetch 可能**先**回來（race），重繪用到尚未寫入的舊值 → 值不見。
以鍵盤/程式路徑（未 blur）則必定丟失（本測試即此情境，LOST=true）。

## 修復方案建議（等 Jim 拍板，未動任何程式碼）
- **建議 A（最小、最穩）**：合併/更新/解除前，先 flush 待提交編輯再重載。
  於 `submitMerge`/`saveGroupHc`/`unmergeGroup` 呼叫 `loadSegment` 前：
  `document.activeElement?.blur();` 並 `await` 所有進行中的 `commitEditStatic`（把 commit 收進一個
  可 await 的 in-flight 集合），確保存檔完成再 reload。
- **建議 B（更佳、治本）**：合併成功後**不整段重載**，只**局部更新**受影響 zone 的 tbody
  （插入 group rowspan 格、重繪該 zone），不呼叫 `loadSegment` → 保留其他格所有未存輸入。
- **建議 C（防呆）**：層/件/刀改為 `input` 去抖動即時存，或加 dirty 追蹤，重載前提示/自動提交。

> 未改任何計算邏輯或程式碼。材料：本資料夾 01–05 截圖、diag_data.json、unsaved_edit_test.json。
> 註：重現用的 5 道 cutting 樣本為 UI 重現 fixture（非業務資料），存於隔離 E2E 庫 atlas_e2e.db。
