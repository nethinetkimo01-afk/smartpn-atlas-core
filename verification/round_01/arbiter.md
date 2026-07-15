# 裁決書 arbiter — round_01

> 由 `mpv_feedback.py` 自動生成。依 45_MULTIPARTY_VERIFICATION：**全票制**，任一方紅即退回（非多數決）。

- 交付：FOUNDATION(1a) + clone斷言(2) + MPV落地(3)：WAL PRAGMA、複製忠實斷言+來源身分橫幅、breaker_gate=閘門13、mpv_feedback迴路
- commit：(待填 push 後 sha)

## 一、四方判定

| 方 | 判定 | 摘要 |
|---|---|---|
| 建造者 Code | 🔴 紅 | 程式面自證完成，但本機 atlas.db 不是 Jim 真庫（actual_headers=3，真庫應≈140）→ 依 27 規則十二-7 自判紅，任務4(IE-VER/BZ-VER 對帳) 在本機不成立，未做。 |
| 破壞者 Breaker | 🔴 紅 | （攻不破 / 攻破 N 處） |
| 對規者 Spec-Auditor | 🟢 綠 | （符合 N/N 條） |
| 使用者 User-Sim | 🟢 綠 | （全程走通 / 卡在第 N 步） |

## 二、交叉比對

- ⚖️ 建造者申報 data_source.actual_headers=3（真庫應 ≈140）→ **不是 Jim 真庫**。凡依賴真實資料的結論一律不成立，判紅。

## 三、證據清單

### 1. [建造者 Code] 本機 atlas.db 非 Jim 真庫：有 actual 的 header 只有 3（真庫應≈140），全庫 ie_process=8295（真庫應≈20434）

- 嚴重度：high
- 證據：本機所有 24 份 .db（含 backup/、test_isolated/）全為 8295 列/197 header；無任何一份是 20434 列/152 header
- 最小重現：python hub_ci.py 觀察啟動橫幅；或 sqlite3 flask_backend/data/atlas.db 'select count(distinct header_id) from ie_process where actual_operators is not null and actual_operators<>0' → 3

### 2. [建造者 Code] 任務4（IE-VER + BZ-VER 對帳/遷移）在本機無法執行，未做

- 嚴重度：high
- 證據：需 140 個有 actual 的 header 逐一 count+sum、全庫合計≈76357；本機只有 3 個 header／sum=262.5
- 最小重現：同上：本機不存在可對帳的真實資料。需在 ME129 或由中樞用真庫執行。

### 3. [破壞者 Breaker] （哪裡壞）

- 嚴重度：high
- 證據：（回應碼/錯誤訊息/數字）
- 最小重現：（最小重現步驟）

## 四、裁決

🔴 **退回（RETURN）** — 紅方：建造者 Code、破壞者 Breaker

### 退回令（貼給 Code）

```
RETURN / round_01 / commit (待填 push 後 sha)
紅方：建造者 Code、破壞者 Breaker

必修（逐項附修好後的重現結果）：
  1. [high] 本機 atlas.db 非 Jim 真庫：有 actual 的 header 只有 3（真庫應≈140），全庫 ie_process=8295（真庫應≈20434）
     重現：python hub_ci.py 觀察啟動橫幅；或 sqlite3 flask_backend/data/atlas.db 'select count(distinct header_id) from ie_process where actual_operators is not null and actual_operators<>0' → 3
  2. [high] 任務4（IE-VER + BZ-VER 對帳/遷移）在本機無法執行，未做
     重現：同上：本機不存在可對帳的真實資料。需在 ME129 或由中樞用真庫執行。
  3. [high] （哪裡壞）
     重現：（最小重現步驟）

修好後：python hub_ci.py 全綠 → 開新一輪 --new → 四方重驗。
不得修改任何閘門判定（改判定＝作弊，該次交付作廢）。
```
