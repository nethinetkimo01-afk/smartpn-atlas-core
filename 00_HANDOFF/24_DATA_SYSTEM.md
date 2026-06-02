# Data System — 內部數據自動化項目

Version: v1.0 | 2026-06-02
Status: 架構已確定，數據源定義進行中
Purpose: 新對話 Claude 讀此文件，從上次結束的地方繼續。

---

## 項目背景

這是 Jim 公司的**內部**數據自動化系統，與 SmartPN Atlas 無關。
Jim 負責規劃來源與報表結果，團隊負責日常維護資料。

---

## 系統架構（已確定，不再討論）

**部署方式：** 內網伺服器（Local Server）
**原因：** 辦公室部分電腦無外部網路，但可連內部網路
**伺服器：** 辦公室一台長期開著的電腦
**技術棧：** Python + Flask + SQLite
**團隊操作：** 瀏覽器開內網網址，不需安裝任何軟體

```
來源層：系統導出（Excel）+ 手工輸入（多人同時作業）
    ↓
導入層：瀏覽器界面（上傳檔案 / 填表單 / 查看導入狀態）
    ↓
伺服器層：Python 跑去重、變更追蹤、識別規則
    ↓
數據庫層：SQLite（主表 + 變更記錄表）
    ↓
報表層：Jim 的決策界面（只有 Jim 看）
```

---

## 角色分工（已確定）

| 角色 | 負責 |
|------|------|
| Jim | 定義數據源、定義識別規則、設計報表、做決策 |
| 團隊 | 上傳系統導出檔案、手工填表維護資料 |

---

## 核心機制（已確定）

**去重與變更追蹤：**
- 每個數據源獨立定義唯一值識別欄位組合（Jim 分開定義）
- 新增資料 → 直接寫入主表，不記錄
- 已存在但內容變更 → 更新主表 + 寫入變更記錄表
- 完全重複 → 跳過

**備份：**
- 每日定期自動備份 SQLite 整個數據庫
- 備份存伺服器獨立資料夾，保留天數待定

**報表機制（兩層）：**

| 層級 | 說明 |
|------|------|
| 固定報表 | Jim 確認後的正式報表，主界面 Tab，自動更新 |
| 探索分析 | Jim 自由拖拉欄位做樞紐分析，確認後升格為固定報表 |

報表界面支援：多 Tab、樞紐分析（欄位／維度／彙總方式）、一鍵升格固定報表

---

## 數據源登記冊

### DS-01：SP（Season Plan）

**工作表名稱：** `{Season} SP{N}-EVM`（例：FW26 SP7-EVM）
**數據類型：** 系統導出，Excel (.xlsx)，格式固定
**規模：** ~6,383 行 × 76 欄（FW26 SP7 為例）

**欄位群組：**

| 群組 | 主要欄位 |
|------|----------|
| 產品識別 | RecordID, Article ID, Article DESC, Model |
| 供應鏈 | GT1 FSC/Code, RT1 FSC/Code, GT1 LO, GT1 Group, GT1 COO |
| 產品屬性 | Division, Product Type DESC, Gender, Construction type, Technology Concept |
| 市場 | Market Group, Market (level 1~3), Forecast Customer Description, Forecast Customer No |
| 時間 | Marketing Season, Production Season, Calendar Month, CRD Month |
| 數量 | Metric, Total, Offered Capacity |

**待 Jim 定義：**
- 唯一值識別規則（哪幾欄組合 = 同一筆）
- 分析需求／固定報表內容
- 導入頻率

### DS-02 以後

待 Jim 提供

---

## 下次對話起點

1. 繼續定義 DS-01 唯一值規則和分析需求
2. 繼續收集 DS-02...N
3. 所有數據源定義完後，開始設計導入界面和伺服器架構細節

---

## 對 Claude 的指令

- 每次對話開始必須讀此文件
- 架構已確定，不再重新討論
- Jim 說「繼續」就從「下次對話起點」接著做
- 有新決定立即更新此文件，提醒 Jim commit
