@echo off
rem Double-click launcher. Real logic: stop-server.ps1 (same folder)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-server.ps1" %*
echo.
pause
