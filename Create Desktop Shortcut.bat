@echo off
setlocal

cd /d "%~dp0"

cscript.exe //nologo "%~dp0scripts\create-desktop-shortcut.vbs"

echo.
pause
endlocal
