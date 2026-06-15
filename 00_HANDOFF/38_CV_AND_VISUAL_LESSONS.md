# CV 製作與視覺系統教訓記錄
Version: v1.0 | 2026-06-15
Status: CONFIRMED — 從今天的錯誤中整理，新視窗必讀

---

## 今天犯的錯誤，不能再犯

### 錯誤 1：沒有先定義目標就開始做
Claude 直接開始做圖，沒有先問「CV 的目標是什麼」「輸出物是什麼」「結構是什麼」。
**正確做法：** 定義目標 → 確認輸出 → 拆解步驟 → 派工。永遠不跳步驟。

### 錯誤 2：讀文件只看有沒有，不看內容
Claude 讀了 S01 Demo Logic，但做圖時完全沒有用 S01 的表格邏輯、顏色規則、before/after 結構。
**正確做法：** 讀完立刻用。讀而不用 = 沒讀。

### 錯誤 3：自己設計視覺風格
Claude 自己畫了 before/after 方塊圖，沒有照 Jim 已有的三張參考圖。
**正確做法：** 做任何 CV 或簡報圖片前，必須先看參考圖。參考圖在這個 repo：
- Transparency.png
- What_is_the_problem.png
- Root_cause_and_solution.png

### 錯誤 4：把 SmartPN Atlas 放進 CV 圖片
CV 是賣 Jim 這個人，不是賣 SmartPN Atlas。品牌高層要看到的是「這個人解決過我的問題」，不是「這個產品有多厲害」。
**正確做法：** 圖片邏輯 = 品牌的痛（左）→ 解決後的結果（右）。不提工具名稱。

### 錯誤 5：不知道 CV 視覺系統就開始做
黑底金字 = LinkedIn 圖片 / PPT 視覺系統。
白底 Apple 風格 = Demo 軟件 / CV 視覺系統。
**正確做法：** 先確認用哪套視覺系統，再做圖。

### 錯誤 6：派工錯誤
圖片生成是 ChatGPT 的工作，不是 Claude 的工作。Claude 的工作是給正確的 image prompt。
**正確做法：** Claude 寫 prompt → Jim 用 ChatGPT 生成 → Jim 確認 → 繼續下一張。

### 錯誤 7：讓 Jim 重傳已傳過的圖
Jim 在這個對話傳過三張參考圖，Claude 沒有用，逼 Jim 重傳。
**正確做法：** 收到圖的那一刻，立刻確認視覺系統，然後才開始做。

---

## CV 結構（已確認）

**格式：** 橫式，白底，Apple 風格，1分鐘讀完

**Section 1 — What I Can Contribute**
- 總結一句話：整合製造端供應鏈，讓品牌拿回利潤、減少人員、擴大材料庫、為 downstream 做準備
- 六張圖（P1–P6），每張圖下一句說明

**Section 2 — Who I Am**
- PDM / ERP / 標準化經驗
- 懂 Brand / Factory / Supplier 三方關係
- 英文非母語，面試前請考慮

**Section 3 — What I'm Looking For**
- 重視數據管理的公司
- 尊重無形資產的公司
- 提供高於市場標準薪資的公司

---

## 六個 Contribution Title（已確認）

P1 — 拿回存在已久，製造端供應鏈內 hidden margin
P2 — Less manpower. More accuracy. In your material library.
P3 — 鞋型轉移快，品質一致，FOB 談得準
P4 — 依實際採購量與 supplier 集團議價，FOB 不再靠固定報價
P5 — 供應商評價線上收集，開發與採購決策有據可查
P6 — 快時尚設計，找到完全相同的材料，最少 LT，縮短上市時間

---

## 視覺系統對照

| 用途 | 視覺系統 |
|------|---------|
| LinkedIn 圖片 / PPT | 黑底、白字主標題、金色關鍵字、左右對比、問題紅色、解法藍色 |
| Demo 軟件 / CV | 白底、Apple 風格、乾淨卡片、無裝飾 |

---

## 圖片派工規則

1. Claude 確認每張圖的邏輯（對應哪個 Scenario，左邊是什麼問題，右邊是什麼結果）
2. Claude 寫 ChatGPT image prompt
3. Jim 生成圖片
4. Jim 確認後繼續下一張
5. 六張全部確認後，Claude 整合成完整 CV 文件

---

## Jim 的做事邏輯（永遠遵守）

定義目標 → 確認輸出 → 拆解步驟 → 派工 → 永遠不跳步驟

Claude 的角色：Central brain — 分析、討論、拆解、派工、抓錯誤。
不是執行者。不是圖片生成工具。不是自動決策者。

---

## 當前狀態（2026-06-15）

- CV 結構：確認
- Section 1 文字：確認
- 六個 title：確認
- 圖片：待 ChatGPT 生成（P1–P6 prompt 待 Claude 輸出）
- Section 2 / Section 3 文字：待細化
- CV 文件整合：待圖片確認後進行
