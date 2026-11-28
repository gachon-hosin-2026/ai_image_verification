@echo off
rem Double-click launcher. Real logic: update-server.ps1 (same folder)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update-server.ps1" %*
echo.
pause
