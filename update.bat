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
echo   DONG TOOL + BROWSER...
echo ============================================
REM Dong GUI + dang/cmt + browser TRUOC khi bat IPv4 (tranh browser dinh IPv4)
taskkill /F /IM pythonw.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM chrome.exe /T >nul 2>&1
taskkill /F /IM msedge.exe /T >nul 2>&1
taskkill /F /IM firefox.exe /T >nul 2>&1
for /d %%C in ("%~dp0..\*") do taskkill /F /IM "%%~nxC.exe" /T >nul 2>&1
timeout /t 3 /nobreak >nul

echo ============================================
echo   BAT IPv4 DE TAI CAP NHAT...
echo ============================================

REM Bat IPv4
powershell -Command "Get-NetAdapter | ForEach-Object { Enable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip -ErrorAction SilentlyContinue }" >nul 2>&1
REM Dat DNS Google de phan giai duoc github.com
powershell -Command "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object { Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses @('8.8.8.8','8.8.4.4') -ErrorAction SilentlyContinue }" >nul 2>&1
echo Cho mang on dinh...
timeout /t 8 /nobreak >nul

REM Tai ZIP tu GitHub
set "GITHUB_URL=https://github.com/nguyenvantuong161978-dotcom/upload/archive/refs/heads/main.zip"
set "ZIP_FILE=%TEMP%\upload_update.zip"
set "EXTRACT_DIR=%TEMP%\upload_update"

echo Dang tai ban cap nhat (timeout 90s, retry 4 lan)...
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $ok=$false; for($i=1; $i -le 4 -and -not $ok; $i++){ try { Invoke-WebRequest -Uri '%GITHUB_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing -TimeoutSec 90; $ok=$true; Write-Host 'Tai thanh cong!' } catch { Write-Host ('Lan '+$i+'/4 loi, thu lai sau 5s: '+$_.Exception.Message); Start-Sleep 5 } }; if(-not $ok){ exit 1 }"

if %ERRORLEVEL% neq 0 (
    echo Khong the tai cap nhat sau 4 lan thu.
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

if exist "%SRC_DIR%\tool_gui.py" (
    copy /y "%SRC_DIR%\tool_gui.py" "%~dp0tool_gui.py" >nul
    echo   [OK] tool_gui.py
)

if exist "%SRC_DIR%\stats.py" (
    copy /y "%SRC_DIR%\stats.py" "%~dp0stats.py" >nul
    echo   [OK] stats.py
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

if exist "%SRC_DIR%\setup.bat" (
    copy /y "%SRC_DIR%\setup.bat" "%~dp0setup.bat" >nul
    echo   [OK] setup.bat
)

if exist "%SRC_DIR%\lay_token.bat" (
    copy /y "%SRC_DIR%\lay_token.bat" "%~dp0lay_token.bat" >nul
    echo   [OK] lay_token.bat
)

REM Tcl/Tk cho GUI: copy zip + tu cay lan dau (neu chua co tkinter)
if exist "%SRC_DIR%\tkinter-embed-py311.zip" (
    copy /y "%SRC_DIR%\tkinter-embed-py311.zip" "%~dp0tkinter-embed-py311.zip" >nul
    echo   [OK] tkinter-embed-py311.zip
    if not exist "%~dp0python\tkinter\__init__.py" (
        echo   Dang cay Tcl/Tk vao python (GUI)...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%~dp0tkinter-embed-py311.zip' -DestinationPath '%~dp0python' -Force"
        echo   [OK] da cay Tcl/Tk - GUI san sang
    )
)

if exist "%SRC_DIR%\VERSION" (
    copy /y "%SRC_DIR%\VERSION" "%~dp0VERSION" >nul
    for /f "delims=" %%V in ("%SRC_DIR%\VERSION") do echo   [OK] VERSION: %%V
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

echo ============================================
echo   MO LAI TOOL...
echo ============================================
start "" "%~dp0run.bat"
