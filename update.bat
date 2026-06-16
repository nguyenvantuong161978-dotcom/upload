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
echo   LAY PHIEN BAN MOI NHAT (IPv4, request nho)...
echo ============================================
call :ipv4on
timeout /t 6 /nobreak >nul

set "SHA="
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; try { $j=Invoke-RestMethod 'https://api.github.com/repos/nguyenvantuong161978-dotcom/upload/git/refs/heads/main' -Headers @{'User-Agent'='tl'} -TimeoutSec 90; Set-Content -Path '%TEMP%\tlsha.txt' -Value $j.object.sha -NoNewline -Encoding ascii } catch { exit 1 }"
if %ERRORLEVEL% neq 0 goto :fallback
set /p SHA=<"%TEMP%\tlsha.txt"
if "%SHA%"=="" goto :fallback
echo Phien ban: %SHA%

REM Tat IPv4 -> tai qua jsDelivr (IPv6, nhanh)
call :ipv4off

echo ============================================
echo   TAI CODE MOI QUA jsDelivr (IPv6)...
echo ============================================
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; $sha='%SHA%'; $repo='nguyenvantuong161978-dotcom/upload'; $cdn='https://cdn.jsdelivr.net/gh/'+$repo+'@'+$sha; $haveTk=Test-Path '%~dp0python\tkinter\__init__.py'; try { $t=Invoke-RestMethod ('https://data.jsdelivr.com/v1/packages/gh/'+$repo+'@'+$sha+'?structure=flat') -TimeoutSec 40 } catch { Write-Host ('Loi danh sach file: '+$_.Exception.Message); exit 1 }; $exp=0; $n=0; foreach($f in $t.files){ $rel=$f.name.TrimStart('/'); if($haveTk -and $rel -eq 'tkinter-embed-py311.zip'){ continue }; $exp++; if($rel -eq 'update.bat'){ $out='update_new.bat' } else { $out=$rel }; $dest=(Join-Path '%~dp0' ($out -replace '/','\')); $dd=Split-Path $dest -Parent; if(-not(Test-Path $dd)){ New-Item -ItemType Directory -Force -Path $dd | Out-Null }; for($k=1;$k -le 3;$k++){ try { Invoke-WebRequest ($cdn+$f.name) -OutFile $dest -UseBasicParsing -TimeoutSec 60; $n++; break } catch { Start-Sleep 2 } } }; Write-Host ('Da tai '+$n+'/'+$exp+' file'); if($n -lt $exp){ exit 1 }"
if %ERRORLEVEL% equ 0 (
    echo jsDelivr OK.
    goto :cultivate
)
echo jsDelivr that bai -> chuyen sang GitHub zip qua IPv4...

:fallback
echo ============================================
echo   FALLBACK: TAI GITHUB ZIP QUA IPv4...
echo ============================================
call :ipv4on
timeout /t 6 /nobreak >nul
set "GITHUB_URL=https://github.com/nguyenvantuong161978-dotcom/upload/archive/refs/heads/main.zip"
set "ZIP_FILE=%TEMP%\upload_update.zip"
set "EXTRACT_DIR=%TEMP%\upload_update"
echo Dang tai zip (timeout 90s, retry 4)...
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $ok=$false; for($i=1; $i -le 4 -and -not $ok; $i++){ try { Invoke-WebRequest -Uri '%GITHUB_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing -TimeoutSec 90; $ok=$true } catch { Start-Sleep 5 } }; if(-not $ok){ exit 1 }"
if %ERRORLEVEL% neq 0 (
    echo Tai that bai ca 2 cach.
    goto :relaunch
)
if exist "%EXTRACT_DIR%" rd /s /q "%EXTRACT_DIR%"
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%EXTRACT_DIR%' -Force"
set "SRC_DIR="
for /d %%D in ("%EXTRACT_DIR%\*") do set "SRC_DIR=%%D"
if not defined SRC_DIR goto :relaunch
for %%F in (cmt.py dang.py tool_gui.py stats.py run.bat setup.bat lay_token.bat VERSION) do (
    if exist "%SRC_DIR%\%%F" copy /y "%SRC_DIR%\%%F" "%~dp0%%F" >nul
)
if exist "%SRC_DIR%\update.bat" copy /y "%SRC_DIR%\update.bat" "%~dp0update_new.bat" >nul
if exist "%SRC_DIR%\icon" ( if exist "%~dp0icon" rd /s /q "%~dp0icon" & xcopy "%SRC_DIR%\icon" "%~dp0icon\" /e /i /q >nul )
if exist "%SRC_DIR%\tkinter-embed-py311.zip" if not exist "%~dp0python\tkinter\__init__.py" copy /y "%SRC_DIR%\tkinter-embed-py311.zip" "%~dp0tkinter-embed-py311.zip" >nul
del "%ZIP_FILE%" >nul 2>&1
if exist "%EXTRACT_DIR%" rd /s /q "%EXTRACT_DIR%"
echo Fallback GitHub zip xong.

:cultivate
call :ipv4off
echo Cay Tcl/Tk neu chua co...
if not exist "%~dp0python\tkinter\__init__.py" (
    if exist "%~dp0tkinter-embed-py311.zip" (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%~dp0tkinter-embed-py311.zip' -DestinationPath '%~dp0python' -Force"
    )
)
echo ============================================
echo   CAP NHAT XONG!
echo ============================================

:relaunch
call :ipv4off
echo Mo lai tool...
start "" "%~dp0run.bat"
exit /b

:ipv4on
powershell -Command "Get-NetAdapter | ForEach-Object { Enable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip -ErrorAction SilentlyContinue }" >nul 2>&1
powershell -Command "Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | ForEach-Object { Set-DnsClientServerAddress -InterfaceIndex $_.ifIndex -ServerAddresses @('8.8.8.8','8.8.4.4') -ErrorAction SilentlyContinue }" >nul 2>&1
exit /b

:ipv4off
powershell -Command "Get-NetAdapter | ForEach-Object { Disable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip -ErrorAction SilentlyContinue }" >nul 2>&1
exit /b
