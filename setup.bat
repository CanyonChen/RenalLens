@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1"
set "setup_exit=%ERRORLEVEL%"
echo.
if not "%setup_exit%"=="0" echo Setup failed. See the error above.
if /I not "%~1"=="--no-pause" pause
exit /b %setup_exit%
