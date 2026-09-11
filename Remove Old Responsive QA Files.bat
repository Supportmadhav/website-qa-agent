@echo off
setlocal

cd /d "%~dp0"

echo.
echo Removing old Responsive QA test files...
echo.

if exist "checks\responsive_check.py" (
    del /q "checks\responsive_check.py"
)

if exist "frontend\src\components\ResponsiveReport.jsx" (
    del /q "frontend\src\components\ResponsiveReport.jsx"
)

echo Old Responsive QA files removed.
echo Responsive Studio is now a separate top-level workspace.
echo.
pause

endlocal
