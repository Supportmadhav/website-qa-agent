@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "ROOT=%CD%"
set "PYTHON=%ROOT%\.venv\Scripts\python.exe"
set "FRONTEND=%ROOT%\frontend"
set "LOGDIR=%ROOT%\.qa-agent\logs"

echo.
echo ============================================
echo   Website QA Agent
echo ============================================
echo.

if not exist "%PYTHON%" (
    echo ERROR: Python virtual environment was not found.
    echo Expected:
    echo %PYTHON%
    echo.
    pause
    exit /b 1
)

if not exist "%FRONTEND%\package.json" (
    echo ERROR: frontend\package.json was not found.
    echo Expected:
    echo %FRONTEND%\package.json
    echo.
    pause
    exit /b 1
)

where npm.cmd >nul 2>&1
if errorlevel 1 (
    where npm >nul 2>&1
    if errorlevel 1 (
        echo ERROR: npm was not found in Windows PATH.
        echo Node.js/npm must be installed.
        echo.
        pause
        exit /b 1
    )
)

if not exist "%ROOT%\.qa-agent" mkdir "%ROOT%\.qa-agent"
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

echo Starting Website QA Agent...
echo.

set "BACKEND_RUNNING="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    set "BACKEND_RUNNING=1"
)

if defined BACKEND_RUNNING (
    echo [OK] Backend is already running.
) else (
    echo [1/2] Starting backend...
    start "Website QA Agent - Backend" /min cmd.exe /c call "%ROOT%\scripts\run-backend.bat"
)

set "FRONTEND_RUNNING="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":5173 .*LISTENING"') do (
    set "FRONTEND_RUNNING=1"
)

if defined FRONTEND_RUNNING (
    echo [OK] Frontend is already running.
) else (
    echo [2/2] Starting frontend...
    start "Website QA Agent - Frontend" /min cmd.exe /c call "%ROOT%\scripts\run-frontend.bat"
)

echo.

"%PYTHON%" "%ROOT%\scripts\wait-for-qa-agent.py"

if errorlevel 1 (
    echo.
    echo Website QA Agent could not start.
    echo The error details are shown above.
    echo.
    pause
    exit /b 1
)

exit /b 0
