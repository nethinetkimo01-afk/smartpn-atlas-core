@echo off
REM pre_update.bat — backup DB then git pull
REM Usage: run this instead of "git pull origin main"

echo [pre_update] Backing up atlas.db...
python flask_backend\pre_update_backup.py
if errorlevel 1 (
    echo [pre_update] Backup failed. Aborting.
    pause
    exit /b 1
)
echo [pre_update] Pulling latest code...
git pull origin main
echo [pre_update] Done. Restart Flask if app.py changed.
pause
