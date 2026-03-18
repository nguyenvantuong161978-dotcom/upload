@echo off
chcp 65001 >nul 2>&1
title Tool Upload Video - Auto Update
cd /d "%~dp0"

echo ============================================
echo   DANG CAP NHAT TU GITHUB...
echo ============================================

REM Kiem tra neu co ban cap nhat run.bat tu lan truoc
if exist "run_update.bat" (
    echo Cap nhat run.bat thanh cong! Dang chay phien ban moi...
    copy /y "run_update.bat" "run.bat" >nul 2>&1
    del "run_update.bat" >nul 2>&1
)

REM Tai ZIP tu GitHub bang PowerShell (khong can cai Git)
set "GITHUB_URL=https://github.com/nguyenvantuong161978-dotcom/upload/archive/refs/heads/main.zip"
set "ZIP_FILE=%TEMP%\upload_update.zip"
set "EXTRACT_DIR=%TEMP%\upload_update"

echo Dang tai ban cap nhat moi nhat...
powershell -Command "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%GITHUB_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing; Write-Host 'Tai thanh cong!' } catch { Write-Host 'LOI: Khong the tai cap nhat. Kiem tra ket noi mang.'; Write-Host $_.Exception.Message; exit 1 }"

if %ERRORLEVEL% neq 0 (
    echo Khong the tai cap nhat. Chay phien ban hien tai...
    goto :run_scripts
)

REM Xoa thu muc giai nen cu neu co
if exist "%EXTRACT_DIR%" rd /s /q "%EXTRACT_DIR%"

REM Giai nen ZIP
echo Dang giai nen...
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%EXTRACT_DIR%' -Force"

REM Tim thu muc goc trong ZIP (thuong la upload-main)
set "SRC_DIR="
for /d %%D in ("%EXTRACT_DIR%\*") do set "SRC_DIR=%%D"

if not defined SRC_DIR (
    echo LOI: Khong tim thay thu muc trong file ZIP.
    goto :cleanup
)

echo Dang cap nhat cac file...

REM Cap nhat cmt.py
if exist "%SRC_DIR%\cmt.py" (
    copy /y "%SRC_DIR%\cmt.py" "%~dp0cmt.py" >nul
    echo   [OK] cmt.py
)

REM Cap nhat dang.py
if exist "%SRC_DIR%\dang.py" (
    copy /y "%SRC_DIR%\dang.py" "%~dp0dang.py" >nul
    echo   [OK] dang.py
)

REM Cap nhat thu muc icon (xoa cu, copy moi)
if exist "%SRC_DIR%\icon" (
    if exist "%~dp0icon" rd /s /q "%~dp0icon"
    xcopy "%SRC_DIR%\icon" "%~dp0icon\" /e /i /q >nul
    echo   [OK] icon/
)

REM Cap nhat run.bat (luu thanh run_update.bat, se ap dung lan chay sau)
if exist "%SRC_DIR%\run.bat" (
    fc /b "%SRC_DIR%\run.bat" "%~dp0run.bat" >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        copy /y "%SRC_DIR%\run.bat" "%~dp0run_update.bat" >nul
        echo   [OK] run.bat (se cap nhat lan chay tiep theo)
    )
)

:cleanup
REM Don dep file tam
del "%ZIP_FILE%" >nul 2>&1
if exist "%EXTRACT_DIR%" rd /s /q "%EXTRACT_DIR%"

echo ============================================
echo   CAP NHAT HOAN TAT!
echo ============================================
echo.

:run_scripts
echo Dang khoi dong cac script...
echo.

REM Chay dang.py trong cua so lenh moi
start "Dang Video" python\python.exe "%~dp0dang.py"

REM Chay cmt.py trong cua so lenh moi
start "Tra loi binh luan" python\python.exe "%~dp0cmt.py"

echo Cac script da duoc khoi dong thanh cong!
echo Ban co the dong cua so nay.
timeout /t 5
