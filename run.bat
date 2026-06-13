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

REM Cay Tcl/Tk lan dau (giai nen zip vao python\) de Tkinter/GUI chay duoc
if not exist "%~dp0python\tkinter\__init__.py" (
    if exist "%~dp0tkinter-embed-py311.zip" (
        echo Dang cay Tcl/Tk cho GUI lan dau...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%~dp0tkinter-embed-py311.zip' -DestinationPath '%~dp0python' -Force"
    )
)

REM Neu co tkinter -> mo GUI dieu khien (an 2 cmd den).
REM Neu chua -> chay truc tiep 2 cua so de tool van hoat dong.
if exist "%~dp0python\tkinter\__init__.py" (
    echo Mo GUI dieu khien...
    start "" "%~dp0python\pythonw.exe" "%~dp0tool_gui.py"
) else (
    echo Chua co GUI - chay che do 2 cua so...
    start "Dang Video" python\python.exe "%~dp0dang.py"
    start "Tra Loi Comment" python\python.exe "%~dp0cmt.py"
)

exit /b
