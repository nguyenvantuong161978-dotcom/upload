@echo off
chcp 65001 >nul 2>&1
setlocal

set "CMD_DIR=D:\AUTO\commands"
set "STATUS_DIR=D:\AUTO\status"

if "%~1"=="" goto :usage
if /i "%~1"=="status" goto :status

if "%~2"=="" goto :usage

REM Kiem tra lenh hop le
set "VALID="
if /i "%~1"=="restart" set "VALID=1"
if /i "%~1"=="update"  set "VALID=1"
if /i "%~1"=="kill"    set "VALID=1"
if not defined VALID (
    echo [LOI] Lenh khong hop le: "%~1"
    echo Cac lenh: restart, update, kill, status
    goto :eof
)

REM Tao thu muc commands neu chua co
if not exist "%CMD_DIR%" mkdir "%CMD_DIR%"

REM Tao file tin hieu
set "TARGET=%~2"
echo.> "%CMD_DIR%\%TARGET%.%~1"
echo [OK] Da gui lenh: %~1 -^> %TARGET%
echo     File: %CMD_DIR%\%TARGET%.%~1

REM Neu la ALL, liet ke tat ca VM se nhan lenh
if /i "%TARGET%"=="ALL" (
    echo.
    echo TAT CA may ao se nhan lenh nay.
)
goto :eof

:status
echo.
echo ============================================
echo   TRANG THAI CAC MAY AO
echo ============================================
echo.

if not exist "%STATUS_DIR%" (
    echo [!] Thu muc status chua ton tai: %STATUS_DIR%
    echo     Tao thu muc va cho may ao bao cao...
    mkdir "%STATUS_DIR%" 2>nul
    goto :eof
)

REM Dem so file
set "COUNT=0"
for %%F in ("%STATUS_DIR%\*.json") do set /a COUNT+=1

if %COUNT%==0 (
    echo Chua co may ao nao bao cao trang thai.
    goto :eof
)

REM Hien thi trang thai tung may
powershell -NoProfile -Command ^
  "$files = Get-ChildItem '%STATUS_DIR%\*.json' -ErrorAction SilentlyContinue;" ^
  "foreach ($f in $files) {" ^
  "  try {" ^
  "    $d = Get-Content $f.FullName -Raw | ConvertFrom-Json;" ^
  "    $color = if ($d.state -eq 'running') {'Green'} elseif ($d.state -like '*stop*' -or $d.state -eq 'killed') {'Red'} else {'Yellow'};" ^
  "    Write-Host ('  ' + $d.channel.PadRight(12)) -NoNewline;" ^
  "    Write-Host ($d.state.PadRight(18)) -ForegroundColor $color -NoNewline;" ^
  "    Write-Host ('dang.py=' + $d.dang_py.PadRight(10)) -NoNewline;" ^
  "    Write-Host ('uptime=' + [string]$d.uptime_minutes + 'p') -NoNewline;" ^
  "    Write-Host ('  ' + $d.timestamp);" ^
  "    if ($d.last_error) { Write-Host ('             err: ' + $d.last_error) -ForegroundColor Red }" ^
  "  } catch { Write-Host ('  ' + $f.BaseName + ': [doc file loi]') -ForegroundColor Red }" ^
  "}"

echo.
echo ============================================

REM Hien thi lenh dang cho xu ly
if exist "%CMD_DIR%\*.*" (
    echo.
    echo   LENH DANG CHO:
    for %%F in ("%CMD_DIR%\*.*") do echo     - %%~nxF
    echo.
)
goto :eof

:usage
echo.
echo   DIEU KHIEN MAY AO TU MAY CHU
echo   ==============================
echo.
echo   Cach dung:
echo     control.bat restart ^<CHANNEL^|ALL^>   Khoi dong lai tool
echo     control.bat update  ^<CHANNEL^|ALL^>   Cap nhat code + khoi dong lai
echo     control.bat kill    ^<CHANNEL^|ALL^>   Dung tool hoan toan
echo     control.bat status                    Xem trang thai tat ca may
echo.
echo   Vi du:
echo     control.bat restart KA1-T3
echo     control.bat update ALL
echo     control.bat kill TA2-T1
echo     control.bat status
echo.
