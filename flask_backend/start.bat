@echo off
cd /d D:\smartpn-atlas-core
REM serve.py = waitress(threads=8)，取代 app.py 開發伺服器（見 test_output\ie_stress_waitress.md）
start "" /min cmd /c "python flask_backend\serve.py >> flask_backend\flask_boot.log 2>&1"
timeout /t 5 /nobreak >nul
start "" /min cmd /c "python flask_backend\watchdog.py >> flask_backend\watchdog.log 2>&1"

