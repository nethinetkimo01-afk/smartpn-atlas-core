@echo off
setlocal
echo ============================================================
echo  ClaudeSync Setup for smartpn-atlas-core
echo ============================================================
echo.
echo  To get your session key:
echo    1. Open https://claude.ai and log in
echo    2. Press F12 ^> Application ^> Cookies ^> https://claude.ai
echo    3. Copy the 'sessionKey' value (starts with sk-ant-...)
echo.
set /P CLAUDE_SESSION_KEY=Paste your sessionKey here:
if "%CLAUDE_SESSION_KEY%"=="" (
    echo ERROR: No session key entered.
    pause
    exit /b 1
)
echo.
echo Running setup...
set CLAUDE_SESSION_KEY=%CLAUDE_SESSION_KEY%
python D:\smartpn-atlas-core\nightly\claudesync_setup.py
pause
