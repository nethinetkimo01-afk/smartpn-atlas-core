# verification/ — 多方驗證資料交換點

> 配套 [45_MULTIPARTY_VERIFICATION.md](../00_HANDOFF/45_MULTIPARTY_VERIFICATION.md)
> ／[46_DELIVERY_CHECKLIST.md](../00_HANDOFF/46_DELIVERY_CHECKLIST.md)
> ／裁決程式 [`mpv_feedback.py`](../mpv_feedback.py)（在 repo 根）。

**JSON 格式即介面。** 這個資料夾是與外部 AI（Jim 的 GPT、獨立 Claude 視窗、自動閘門）
對接的交換點：誰驗的不重要，**交出來的 .json 長得一樣就能裁決**。

---

## 迴路

```
Code 做完 → builder.json（自證 + hub_ci 輸出）
   ↓
破壞者 / 對規者 / 使用者各跑 → breaker.json / auditor.json / user.json
（自動閘門、真人 AI 視窗、Jim 的 GPT —— 都寫進同一個 round_NN/）
   ↓
python mpv_feedback.py → 交叉比對 → arbiter.md
   ↓
全綠 → 放行（中樞用真庫複核，才對 Jim 說「可以看」）
任一紅 → arbiter.md 內含自動退回令 → 貼給 Code → 下一輪
```

## 用法

```bash
python mpv_feedback.py --new        # 開新一輪：建 round_NN/ + 四方 .json 範本
# → 四方各自獨立填寫（互不通氣，不看彼此結論）
python mpv_feedback.py              # 裁決最新一輪 → 印出並寫入 round_NN/arbiter.md
python mpv_feedback.py --round 3    # 裁決指定輪
```

離開碼：`0` = 四方全綠放行；`1` = 退回。

## 目錄結構

```
verification/
  README.md
  round_01/
    builder.json     建造者 Code（自證 + hub_ci）
    breaker.json     破壞者（並發/壞資料/權限/邊界/狀態殘留）
    auditor.json     對規者（逐條對規格，覆蓋率量化）
    user.json        使用者（真實點擊走完流程）
    arbiter.md       ← mpv_feedback.py 產出（裁決書 + 退回令）
  round_02/ ...
```

---

## 四方 .json 格式

### 共通欄位

| 欄位 | 型別 | 說明 |
|---|---|---|
| `party` | string | `builder` / `breaker` / `auditor` / `user` |
| `verdict` | string | `green` 或 `red` |
| `summary` | string | 一句話結論 |
| `what_i_did` | string[] | 我做了什麼（不是我覺得如何） |
| `evidence` | string[] | 證據（數字/輸出/截圖路徑） |
| `findings` | object[] | 發現的問題；**空陣列 = 沒發現** |

### `findings[]` 每項

| 欄位 | 說明 |
|---|---|
| `severity` | `high` / `medium` / `low` |
| `summary` | 哪裡壞 |
| `evidence` | 回應碼 / 錯誤訊息 / 數字差異 |
| `repro` | **最小重現步驟**（沒附 → 標「證據不足」，但**仍算紅**） |

### `builder.json` 額外必填 —— `data_source`

```json
"data_source": {
  "db": "flask_backend/data/atlas.db",
  "ie_process_rows": 20434,
  "ob_header_rows": 152,
  "actual_headers": 140
}
```

**貼 `hub_ci.py` 啟動時印的「來源身分」橫幅數字。**
未申報 → 綠燈不可採信，`mpv_feedback.py` 直接判紅。
`actual_headers < 100` → 判定「不是 Jim 真庫」，凡依賴真實資料的結論一律不成立（判紅）。

---

## 裁決規則（`mpv_feedback.py` 實作）

1. **全票制**：四方全綠才放行。任一方紅 = 退回。**非多數決**。
2. **交叉比對**：建造者說綠、他方有證據說紅 → **以紅為準**。
   建造者不得當自己的裁判；hub_ci 全綠只是入場券。
3. **說綠不算數，證據算數**：`verdict: "green"` 但 `findings` 非空 → 判紅。
4. **缺席即紅**：四方少一份 = 不放行（沒驗 ≠ 預設沒問題）。壞檔同理。
5. **證據不足仍算紅**：finding 缺 `repro` → 標記後仍算紅，中樞人工判定。
6. **資料來源自證**：見上 `data_source`。
7. **放行 ≠ 上線**：本檔只輸出「可送中樞複核」。
   **中樞必須用 Jim 真庫（ME129）獨立複跑**，全綠才對 Jim 說「可以看」。

---

## 給外部 AI（Jim 的 GPT / 獨立視窗）的最小指示

> 你是【破壞者 / 對規者 / 使用者】其中一角，立場見 45 號文件 §二。
> 先讀 GitHub 最新碼，依你的角色攻擊 / 對帳 / 走流程。
> **不要看其他方的結論。**
> 只輸出一份 JSON（格式見上），放進 `verification/round_NN/<你的角色>.json`。
> 只准寫「①我做了什麼 ②證據 ③紅或綠 ④若紅，最小重現」。
> 不接受「我覺得」「應該沒問題」。
