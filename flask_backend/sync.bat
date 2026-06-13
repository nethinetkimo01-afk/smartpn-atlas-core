@echo off
chcp 65001 >nul
REM ============================================================
REM  SmartPN Atlas — 結果機同步 (sync.bat)
REM  結果機 (D:\smartpn-atlas-core) 早上手動雙擊執行：
REM    1) git pull 拉取 Code 機昨晚的程式碼
REM    2) 重啟 Flask
REM  ※ DB (*.db) 為「手動同步」：用隨身碟從 Code 機複製到
REM     flask_backend\data\，本腳本不碰 DB。
REM ============================================================
cd /d D:\smartpn-atlas-core

echo ============================================
echo  SmartPN Atlas - 結果機同步
echo ============================================
echo [1/3] 拉取最新程式碼 (git pull origin main)...
git pull origin main
echo.

echo 同步完成，重啟 Flask...
echo [2/3] 關閉舊的 Flask (python.exe)...
taskkill /f /im python.exe >nul 2>&1

echo [3/3] 啟動 Flask...
start "" /min cmd /c "python flask_backend\app.py >> flask_backend\flask_boot.log 2>&1"
timeout /t 4 /nobreak >nul

echo.
echo Flask 已重啟，請開瀏覽器：
echo     http://localhost:5000/ie          ^(IE 主表^)
echo     http://localhost:5000/ie/matrix   ^(矩陣^)
echo     http://localhost:5000/allocation  ^(勾選分配^)
echo.
echo ※ 提醒：DB 為手動同步。Code 機跑完導入後，
echo    用隨身碟複製 flask_backend\data\*.db 到本機同路徑。
echo.
pause
