@echo off
REM ============================================================
REM  Atlas Nightly Scheduler Setup
REM  雙擊此 bat 即可設定 Windows Task Scheduler
REM  每天 20:00 執行，23:00 再補跑一次
REM ============================================================

SET PYTHON=python
SET SCRIPT=D:\smartpn-atlas-core\nightly\run_nightly.py
SET TASKNAME_1=Atlas_Nightly_2000
SET TASKNAME_2=Atlas_Nightly_2300

echo 設定夜間自動任務...

REM 刪除舊任務（若存在）
schtasks /delete /tn "%TASKNAME_1%" /f 2>nul
schtasks /delete /tn "%TASKNAME_2%" /f 2>nul

REM 20:00 主執行
schtasks /create ^
    /tn "%TASKNAME_1%" ^
    /tr "\"%PYTHON%\" \"%SCRIPT%\"" ^
    /sc daily ^
    /st 20:00 ^
    /ru "%USERNAME%" ^
    /rl highest ^
    /f
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: 無法建立 20:00 任務
    pause
    exit /b 1
)

REM 23:00 補跑
schtasks /create ^
    /tn "%TASKNAME_2%" ^
    /tr "\"%PYTHON%\" \"%SCRIPT%\"" ^
    /sc daily ^
    /st 23:00 ^
    /ru "%USERNAME%" ^
    /rl highest ^
    /f
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: 無法建立 23:00 任務
    pause
    exit /b 1
)

echo.
echo ✓ 任務已設定完成：
echo   %TASKNAME_1%  每天 20:00
echo   %TASKNAME_2%  每天 23:00
echo.
echo 手動執行：schtasks /run /tn "%TASKNAME_1%"
echo 查看狀態：schtasks /query /tn "%TASKNAME_1%" /fo list
echo 刪除任務：schtasks /delete /tn "%TASKNAME_1%" /f
echo.
echo Log 位置：D:\smartpn-atlas-core\nightly\logs\
echo.
pause
