# 新機（資料庫專用電腦）初始化部署 Prompt

日期：2026-06-13
狀態：備用，新機到位時執行
前置：Jim 在新機用自己帳戶登入 Windows，裝好 Git + Claude Code，開 cmd 執行
配套：MP勾選分配系統_分析報告_20260610.md（Stage 2 設計）

---

## 今日結論（2026-06-13，寫入存檔）

1. **連線方式定案：用電腦名稱，不用 IP**
   - 筆電 IP 三天換三次（172.16.5.106 → 10.0.5.62 → 172.16.5.115），DHCP 浮動，固定不了
   - 員工統一連 `http://電腦名稱:5000`，Windows 內網自動解析，IP 飄移無感
   - **新機命名：SMARTPN** → 員工永久書籤 `http://SMARTPN:5000`
2. **Stage 1 已完成**（commit 921ad83）：290/291 檔導入，522,774 格
   （公式 130,889 鎖定 / manual 391,885），195/197 headers，11 個標準 sheet 類型，
   531 缺口待補，26 個 sheet 名待 Jim 判定
3. **遷移時機：Stage 2 員工進場前** — 員工第一天就用 SMARTPN 位址，不中途換
4. **帳號鏈定案**：Jim 建管理者（1人）→ 管理者建製作者（7-8人）+ 指派 + 核准
5. Jim 筆電在遷移後退出 server 角色，只作為 Claude Code 操作端之一

---

## 以下整段貼給新機上的 Claude Code

任務：初始化 SMARTPN 資料庫專用電腦，完成後報告每步結果。

### Step 1：環境
1. 確認/安裝 Python 3.14（官網 installer，勾 Add to PATH，避免 Windows Store Python）
2. git clone https://github.com/nethinetkimo01-afk/smartpn-atlas-core.git 到 D:\smartpn-atlas-core
   （無 D 槽則 C:\smartpn-atlas-core，後續路徑同步調整）
3. pip install flask openpyxl（及 requirements 其他依賴）

### Step 2：電腦名稱
1. 改名 SMARTPN：Rename-Computer -NewName "SMARTPN"（需重開機生效，最後一步再重啟）
2. 記錄原名稱供回溯

### Step 3：資料遷移
1. 從舊機（Jim 筆電）複製 SQLite DB 檔到新機同路徑
   （Jim 用隨身碟或網路共享拷貝 flask_backend/*.db；若拷不到，
    用 import 腳本從來源 xlsx 重建：import_ds03_batch.py → import_jun_ie.py →
    Stage 1 全量導入腳本 → populate_ie_material.py）
2. 驗證：ie_sheet_data 行數 = 522,774、ob_header = 197

### Step 4：服務常駐
1. watchdog.py 的 PYTHON 路徑改為新機實際 python.exe 完整路徑
2. 右鍵管理員執行 flask_backend/setup_task.bat（開機自啟，SYSTEM 權限）
   — 這台機器第一天就要裝好，不重蹈筆電覆轍
3. 防火牆：netsh advfirewall firewall add rule name="SmartPN Flask 5000"
   dir=in action=allow protocol=TCP localport=5000
4. 電源設定：永不睡眠、永不關硬碟（powercfg）

### Step 5：驗證
1. 本機 curl http://localhost:5000/api/health → ok
2. 重開機 → 不登入任何帳號的狀態下，從另一台電腦開 http://SMARTPN:5000/ie → 正常
3. watchdog.log 確認監控中
4. 報告：服務狀態 / 開機自啟驗證結果 / 員工連線位址

### Step 6：收尾
1. nightly 排程遷移到新機（同 setup_task 模式建第二個排程任務）
2. 舊機（筆電）排程任務停用，避免雙機同時跑 nightly 互推 git
3. git commit 新機相關設定變更 + push
