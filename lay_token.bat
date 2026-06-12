@echo off
chcp 65001 >nul 2>&1
title Lay Token CMT (tat ca kenh)
cd /d "%~dp0"

echo ============================================
echo   LAY TOKEN CMT CHO TAT CA KENH
echo ============================================
echo.

REM Tao san thu muc clients (de bo file .json client vao)
if not exist "%~dp0clients" mkdir "%~dp0clients"

REM Kiem tra co file client .json chua
dir /b "%~dp0clients\*.json" >nul 2>&1
if errorlevel 1 (
    echo [!] CHUA co file client trong thu muc clients\
    echo     Hay tai file OAuth client ^(.json, da Publish^) bo vao:
    echo       %~dp0clients\
    echo     roi chay lai lay_token.bat
    echo.
    pause
    exit /b 1
)

echo Dam bao da dang nhap YouTube dung tai khoan trong tung browser kenh.
echo.

REM Setup token cho tat ca kenh (folder co .exe). Tu mo browser, tu lay token, tu dong.
python\python.exe cmt.py setup

echo.
echo ============================================
echo   XONG. Gio co the chay run.bat (dang + cmt).
echo ============================================
pause
