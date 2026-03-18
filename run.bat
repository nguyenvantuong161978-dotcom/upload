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

REM Chay dang.py trong cua so lenh moi
start "Dang Video" python\python.exe "%~dp0dang.py"

REM Chay cmt.py trong cua so lenh moi
start "Tra loi binh luan" python\python.exe "%~dp0cmt.py"

echo Cac script da duoc khoi dong thanh cong!
echo Ban co the dong cua so nay.
timeout /t 5
