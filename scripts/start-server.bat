@echo off
rem Double-click launcher. Real logic: start-server.ps1 (same folder)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-server.ps1" %*
echo.
pause
