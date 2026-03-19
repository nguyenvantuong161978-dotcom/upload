@echo off
chcp 65001 >nul 2>&1
title Tool Upload Video
cd /d "%~dp0"

REM Neu co update.bat moi tu lan cap nhat truoc
if exist "update_new.bat" (
    copy /y "update_new.bat" "update.bat" >nul 2>&1
    del "update_new.bat" >nul 2>&1
)

echo ============================================
echo   DANG KHOI DONG TOOL...
echo ============================================
echo.

REM Chay watchdog (theo doi lenh tu may chu, chay ngam)
start /MIN "Watchdog" python\python.exe "%~dp0watchdog.py"

REM Chay dang.py (dang video)
start "Dang Video" python\python.exe "%~dp0dang.py"

echo Cac script da duoc khoi dong thanh cong!
exit /b
