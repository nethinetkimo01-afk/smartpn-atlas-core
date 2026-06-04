@echo off
REM ============================================================
REM  Atlas Nightly Scheduler Setup
REM  Run as Administrator to register scheduled tasks.
REM  Tasks run daily at 20:00 and 23:00.
REM ============================================================

SET PYTHON=python
SET SCRIPT=D:\smartpn-atlas-core\nightly\run_nightly.py
SET TASKNAME_1=Atlas_Nightly_2000
SET TASKNAME_2=Atlas_Nightly_2300

echo Setting up Atlas nightly tasks...

REM Remove existing tasks if present
schtasks /delete /tn "%TASKNAME_1%" /f 2>nul
schtasks /delete /tn "%TASKNAME_2%" /f 2>nul

REM Primary run at 20:00
schtasks /create ^
    /tn "%TASKNAME_1%" ^
    /tr "\"%PYTHON%\" \"%SCRIPT%\"" ^
    /sc daily ^
    /st 20:00 ^
    /ru "%USERNAME%" ^
    /rl highest ^
    /f
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create 20:00 task.
    pause
    exit /b 1
)

REM Backup run at 23:00
schtasks /create ^
    /tn "%TASKNAME_2%" ^
    /tr "\"%PYTHON%\" \"%SCRIPT%\"" ^
    /sc daily ^
    /st 23:00 ^
    /ru "%USERNAME%" ^
    /rl highest ^
    /f
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create 23:00 task.
    pause
    exit /b 1
)

echo.
echo Tasks registered:
echo   %TASKNAME_1%  daily at 20:00
echo   %TASKNAME_2%  daily at 23:00
echo.
echo To run manually:   schtasks /run /tn "%TASKNAME_1%"
echo To check status:   schtasks /query /tn "%TASKNAME_1%" /fo list
echo To remove tasks:   schtasks /delete /tn "%TASKNAME_1%" /f
echo.
echo Log location: D:\smartpn-atlas-core\nightly\logs\
echo.
pause
