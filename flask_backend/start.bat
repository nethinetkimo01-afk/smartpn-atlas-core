@echo off
cd /d D:\smartpn-atlas-core
start "" /min cmd /c "python flask_backend\app.py >> flask_backend\flask_boot.log 2>&1"
timeout /t 5 /nobreak >nul
start "" /min cmd /c "python flask_backend\watchdog.py >> flask_backend\watchdog.log 2>&1"

