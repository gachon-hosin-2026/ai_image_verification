@echo off
rem Double-click launcher. Real logic: start-dev.ps1 (same folder)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1" %*
echo.
pause
