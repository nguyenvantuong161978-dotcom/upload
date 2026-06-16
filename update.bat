@echo off
REM === Tu dong chay voi quyen Administrator ===
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

chcp 65001 >nul 2>&1
title Cap Nhat Tool [ADMIN]
cd /d "%~dp0"

echo ============================================
echo   DONG TOOL + BROWSER...
echo ============================================
taskkill /F /IM pythonw.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM chrome.exe /T >nul 2>&1
taskkill /F /IM msedge.exe /T >nul 2>&1
taskkill /F /IM firefox.exe /T >nul 2>&1
for /d %%C in ("%~dp0..\*") do taskkill /F /IM "%%~nxC.exe" /T >nul 2>&1
timeout /t 3 /nobreak >nul

echo ============================================
echo   BAT IPv4 DE TAI...
echo ============================================
powershell -Command "Get-NetAdapter | ForEach-Object { Enable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip -ErrorAction SilentlyContinue }" >nul 2>&1
powershell -Command "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object { Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses @('8.8.8.8','8.8.4.4') -ErrorAction SilentlyContinue }" >nul 2>&1
timeout /t 6 /nobreak >nul

set "GITHUB_URL=https://github.com/nguyenvantuong161978-dotcom/upload/archive/refs/heads/main.zip"
set "ZIP_FILE=%TEMP%\upload_update.zip"
set "EXTRACT_DIR=%TEMP%\upload_update"

echo Dang tai (timeout 90s, retry 4 lan)...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $ok=$false; for($i=1; $i -le 4 -and -not $ok; $i++){ try { Invoke-WebRequest -Uri '%GITHUB_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing -TimeoutSec 90; $ok=$true } catch { Start-Sleep 5 } }; if(-not $ok){ exit 1 }"
if %ERRORLEVEL% neq 0 (
    echo Tai that bai.
    goto :relaunch
)

if exist "%EXTRACT_DIR%" rd /s /q "%EXTRACT_DIR%"
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%EXTRACT_DIR%' -Force"
set "SRC_DIR="
for /d %%D in ("%EXTRACT_DIR%\*") do set "SRC_DIR=%%D"
if not defined SRC_DIR goto :relaunch

echo Cap nhat file...
for %%F in (cmt.py dang.py tool_gui.py stats.py run.bat setup.bat lay_token.bat VERSION) do (
    if exist "%SRC_DIR%\%%F" copy /y "%SRC_DIR%\%%F" "%~dp0%%F" >nul
)
if exist "%SRC_DIR%\update.bat" copy /y "%SRC_DIR%\update.bat" "%~dp0update_new.bat" >nul
if exist "%SRC_DIR%\icon" (
    if exist "%~dp0icon" rd /s /q "%~dp0icon"
    xcopy "%SRC_DIR%\icon" "%~dp0icon\" /e /i /q >nul
)
if exist "%SRC_DIR%\tkinter-embed-py311.zip" (
    if not exist "%~dp0python\tkinter\__init__.py" (
        copy /y "%SRC_DIR%\tkinter-embed-py311.zip" "%~dp0tkinter-embed-py311.zip" >nul
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%~dp0tkinter-embed-py311.zip' -DestinationPath '%~dp0python' -Force"
    )
)
del "%ZIP_FILE%" >nul 2>&1
if exist "%EXTRACT_DIR%" rd /s /q "%EXTRACT_DIR%"
echo CAP NHAT XONG!

:relaunch
powershell -Command "Get-NetAdapter | ForEach-Object { Disable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip -ErrorAction SilentlyContinue }" >nul 2>&1
echo Mo lai tool...
start "" "%~dp0run.bat"
