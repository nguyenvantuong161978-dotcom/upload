@echo off
REM === Tu dong chay voi quyen Administrator ===
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

chcp 65001 >nul 2>&1
title Cai thu vien Tool Upload [ADMIN]
cd /d "%~dp0"

set "PY=%~dp0python\python.exe"

if not exist "%PY%" (
    echo Khong tim thay Python portable: %PY%
    echo Hay copy thu muc python vao cung thu muc voi setup.bat truoc.
    pause
    exit /b 1
)

echo ============================================
echo   CAI THU VIEN CHO dang.py VA cmt.py
echo ============================================
echo.

REM Bat IPv4 + DNS de tai thu vien
echo Bat IPv4 de tai thu vien...
powershell -Command "Get-NetAdapter | ForEach-Object { Enable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip -ErrorAction SilentlyContinue }" >nul 2>&1
powershell -Command "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object { Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses @('8.8.8.8','8.8.4.4') -ErrorAction SilentlyContinue }" >nul 2>&1
timeout /t 8 /nobreak >nul

REM Xoa file .pth loi (neu co)
if exist "%~dp0python\Lib\site-packages\distutils-precedence.pth" del /f "%~dp0python\Lib\site-packages\distutils-precedence.pth" >nul 2>&1

REM Thu ensurepip truoc
"%PY%" -m ensurepip --default-pip >nul 2>&1
"%PY%" -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ensurepip khong co, tai get-pip.py...
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%TEMP%\get-pip.py' -UseBasicParsing"
    "%PY%" "%TEMP%\get-pip.py" --no-warn-script-location
    del "%TEMP%\get-pip.py" >nul 2>&1
)

"%PY%" -m pip install --upgrade pip --no-warn-script-location
if errorlevel 1 goto :fail

"%PY%" -m pip install --no-warn-script-location ^
    gspread ^
    oauth2client ^
    pyautogui ^
    pyperclip ^
    opencv-python ^
    pillow ^
    google-api-python-client ^
    google-auth ^
    google-auth-oauthlib ^
    google-auth-httplib2 ^
    httplib2 ^
    certifi ^
    youtube-transcript-api ^
    requests ^
    PyYAML
if errorlevel 1 goto :fail

echo.
echo Cai thu vien xong.
goto :cleanup

:fail
echo.
echo Cai thu vien bi loi. Hay xem log phia tren.

:cleanup
REM Tat IPv4
echo Tat IPv4...
powershell -Command "Get-NetAdapter | ForEach-Object { Disable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip -ErrorAction SilentlyContinue }" >nul 2>&1
pause
