@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM atlas_backup_task.bat — Windows 工作排程器用（Task FOUNDATION 1c）
REM
REM 做的事：一致性快照(backup API) → 驗證列數 → 複製到異地資料夾 → 輪替舊備份。
REM 異地路徑/頻率/保留天數 一律讀「管理頁 → 備份與還原 → 備份設定」(app_settings)，
REM 不在這裡寫死 → Jim 改設定不需要碰這個檔。
REM
REM 【安裝】在 ME129 上用系統管理員開 cmd，跑一次（每日 02:00）：
REM   schtasks /create /tn "Atlas 每日備份" /tr "\"D:\smartpn-atlas-core\flask_backend\atlas_backup_task.bat\"" /sc daily /st 02:00 /rl highest /f
REM
REM 若管理頁設「每 12 小時」，改用（02:00 起每 12 小時）：
REM   schtasks /create /tn "Atlas 每12小時備份" /tr "\"D:\smartpn-atlas-core\flask_backend\atlas_backup_task.bat\"" /sc hourly /mo 12 /st 02:00 /rl highest /f
REM
REM 【檢查】排程有沒有在跑：  schtasks /query /tn "Atlas 每日備份" /v /fo list
REM 【手動測一次】           直接雙擊本檔，看 backup_task.log
REM 【看結果】               管理頁 /backup-admin 會顯示最近備份時間/大小/成功否/異地狀態
REM ─────────────────────────────────────────────────────────────────────────────
setlocal
cd /d "%~dp0"

set LOG=%~dp0backup_task.log
echo. >> "%LOG%"
echo ===== %DATE% %TIME% 開始備份 ===== >> "%LOG%"

REM 用 py launcher；沒有就退回 python
where py >nul 2>&1 && (set PY=py -3) || (set PY=python)

%PY% db_backup.py backup >> "%LOG%" 2>&1
set RC=%ERRORLEVEL%

if %RC% NEQ 0 (
  echo [%DATE% %TIME%] X 備份失敗 rc=%RC% — 去管理頁 /backup-admin 看紅字告警 >> "%LOG%"
) else (
  echo [%DATE% %TIME%] V 備份成功 >> "%LOG%"
)

REM 回傳非 0 讓工作排程器把這次標成失敗（排程器歷程才看得出來，不會靜靜地一直失敗）
endlocal & exit /b %RC%
