@echo off
setlocal

cd /d "%~dp0..\frontend"

if not exist "..\.qa-agent\logs" mkdir "..\.qa-agent\logs"

npm.cmd run dev -- --host 127.0.0.1 --port 5173 1>"..\.qa-agent\logs\frontend.log" 2>&1
