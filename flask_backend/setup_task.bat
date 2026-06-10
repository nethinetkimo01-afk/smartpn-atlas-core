@echo off
echo Registering SmartPN Flask Server scheduled task...
schtasks /Create /TN "SmartPN Flask Server" /TR "D:\smartpn-atlas-core\flask_backend\start.bat" /SC ONSTART /RU SYSTEM /F
if %errorlevel%==0 (
  echo SUCCESS: Task created. Flask will auto-start on next boot.
) else (
  echo FAILED: Please run this file as Administrator (right-click -> Run as administrator)
)
pause

