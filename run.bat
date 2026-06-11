@echo off
chcp 65001 >nul 2>&1
title Tool Upload Video
cd /d "%~dp0"

REM Neu co update.bat moi tu lan cap nhat truoc
if exist "update_new.bat" (
    copy /y "update_new.bat" "update.bat" >nul 2>&1
    del "update_new.bat" >nul 2>&1
)

REM Xoa file .pth loi truoc khi chay Python
if exist "%~dp0python\Lib\site-packages\distutils-precedence.pth" del /f "%~dp0python\Lib\site-packages\distutils-precedence.pth" >nul 2>&1
if exist "%~dp0python\Lib\site-packages\pywin32.pth" del /f "%~dp0python\Lib\site-packages\pywin32.pth" >nul 2>&1

echo ============================================
echo   DANG KHOI DONG TOOL...
echo ============================================
echo.

REM Chay dang.py (dang video)
start "Dang Video" python\python.exe "%~dp0dang.py"

REM Chay cmt.py (tra loi binh luan - tu quet tokens, kenh nao co token thi chay)
start "Tra Loi Comment" python\python.exe "%~dp0cmt.py"

echo Cac script da duoc khoi dong thanh cong!
exit /b
