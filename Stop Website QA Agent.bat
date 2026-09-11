@echo off
setlocal EnableExtensions

echo.
echo ============================================
echo   Website QA Agent - Stopping
echo ============================================
echo.

set "FOUND="

for %%G in (8000 5173) do (
    for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%%G .*LISTENING"') do (
        echo Stopping process on port %%G...
        taskkill /PID %%P /T /F >nul 2>&1
        set "FOUND=1"
    )
)

echo.

if defined FOUND (
    echo Website QA Agent stopped.
) else (
    echo Website QA Agent was not running.
)

echo.
pause
endlocal
