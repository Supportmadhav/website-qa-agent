@echo off
setlocal

cd /d "%~dp0.."

if not exist ".qa-agent\logs" mkdir ".qa-agent\logs"

".venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000 1>".qa-agent\logs\backend.log" 2>&1
