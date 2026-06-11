@echo off
chcp 65001 >nul 2>&1
title Lay Token CMT (tat ca kenh)
cd /d "%~dp0"

echo ============================================
echo   LAY TOKEN CMT CHO TAT CA KENH
echo ============================================
echo.
echo Dam bao da:
echo   - Bo file client (.json) vao thu muc clients\
echo   - Dang nhap YouTube dung tai khoan trong tung browser kenh
echo.

REM Setup token cho tat ca kenh (folder co .exe). Tu mo browser, tu lay token, tu dong.
python\python.exe cmt.py setup

echo.
echo ============================================
echo   XONG. Gio co the chay run.bat (dang + cmt).
echo ============================================
pause
