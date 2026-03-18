@echo off
REM === Tu dong chay voi quyen Administrator ===
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

chcp 65001 >nul 2>&1
title Cap Nhat Tu GitHub [ADMIN]
cd /d "%~dp0"

echo ============================================
echo   BAT IPv4 DE TAI CAP NHAT...
echo ============================================

REM Bat IPv4
powershell -Command "Get-NetAdapter | ForEach-Object { Enable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip -ErrorAction SilentlyContinue }" >nul 2>&1
echo Cho mang on dinh...
timeout /t 5 /nobreak >nul

REM Tai ZIP tu GitHub
set "GITHUB_URL=https://github.com/nguyenvantuong161978-dotcom/upload/archive/refs/heads/main.zip"
set "ZIP_FILE=%TEMP%\upload_update.zip"
set "EXTRACT_DIR=%TEMP%\upload_update"

echo Dang tai ban cap nhat moi nhat...
powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GITHUB_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing; Write-Host 'Tai thanh cong!' } catch { Write-Host 'LOI: Khong the tai cap nhat.'; Write-Host $_.Exception.Message; exit 1 }"

if %ERRORLEVEL% neq 0 (
    echo Khong the tai cap nhat.
    goto :done
)

REM Giai nen
if exist "%EXTRACT_DIR%" rd /s /q "%EXTRACT_DIR%"
echo Dang giai nen...
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%EXTRACT_DIR%' -Force"

set "SRC_DIR="
for /d %%D in ("%EXTRACT_DIR%\*") do set "SRC_DIR=%%D"

if not defined SRC_DIR (
    echo LOI: Khong tim thay thu muc trong file ZIP.
    goto :done
)

echo Dang cap nhat cac file...

if exist "%SRC_DIR%\cmt.py" (
    copy /y "%SRC_DIR%\cmt.py" "%~dp0cmt.py" >nul
    echo   [OK] cmt.py
)

if exist "%SRC_DIR%\dang.py" (
    copy /y "%SRC_DIR%\dang.py" "%~dp0dang.py" >nul
    echo   [OK] dang.py
)

if exist "%SRC_DIR%\icon" (
    if exist "%~dp0icon" rd /s /q "%~dp0icon"
    xcopy "%SRC_DIR%\icon" "%~dp0icon\" /e /i /q >nul
    echo   [OK] icon/
)

if exist "%SRC_DIR%\run.bat" (
    copy /y "%SRC_DIR%\run.bat" "%~dp0run.bat" >nul
    echo   [OK] run.bat
)

if exist "%SRC_DIR%\update.bat" (
    copy /y "%SRC_DIR%\update.bat" "%~dp0update_new.bat" >nul
    echo   [OK] update.bat (ap dung lan sau)
)

REM Don dep
del "%ZIP_FILE%" >nul 2>&1
if exist "%EXTRACT_DIR%" rd /s /q "%EXTRACT_DIR%"

echo ============================================
echo   CAP NHAT HOAN TAT!
echo ============================================

:done
REM Tat IPv4
echo Tat IPv4...
powershell -Command "Get-NetAdapter | ForEach-Object { Disable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip -ErrorAction SilentlyContinue }" >nul 2>&1

echo.
echo Ban co the chay run.bat de bat dau.
timeout /t 5
