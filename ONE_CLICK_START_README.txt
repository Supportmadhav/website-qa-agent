WEBSITE QA AGENT - ONE CLICK START V21
======================================

THIS VERSION REMOVES POWERSHELL FROM THE START/STOP PROCESS.

WHY
---
The previous V20 start script failed with PowerShell parser errors such as:

Missing closing ')' in expression.
The Try statement is missing its Catch or Finally block.
Unexpected token '-and'.

This was caused by Windows PowerShell 5.1 parsing multi-line boolean
expressions differently than expected.


V21 FIX
-------
The launcher no longer depends on PowerShell.

START uses:
- Windows BAT
- your existing Python .venv
- a small standard-library Python wait script

STOP uses:
- Windows BAT
- netstat
- taskkill

DESKTOP SHORTCUT uses:
- Windows Script Host (VBScript)

This is much simpler and more compatible with Windows 11.


NORMAL USE
----------
Double-click:

Start Website QA Agent.bat

It will:

1. start FastAPI backend
2. start Vite frontend
3. show live READY/starting status
4. automatically open http://127.0.0.1:5173


FIRST TIME ONLY - DESKTOP SHORTCUT
----------------------------------
Double-click:

Create Desktop Shortcut.bat

After that, use the:

Website QA Agent

desktop shortcut.


STOP
----
Double-click:

Stop Website QA Agent.bat


LOGS
----
If startup fails, the same window shows the last log lines.

Full logs are saved in:

E:\website-qa-agent\.qa-agent\logs\backend.log
E:\website-qa-agent\.qa-agent\logs\frontend.log


INSTALL
-------
Extract this ZIP directly into:

E:\website-qa-agent

Choose:

Replace the files in the destination


FILES
-----
Start Website QA Agent.bat
Stop Website QA Agent.bat
Create Desktop Shortcut.bat

scripts\run-backend.bat
scripts\run-frontend.bat
scripts\wait-for-qa-agent.py
scripts\create-desktop-shortcut.vbs


The old PowerShell scripts may remain in the scripts folder, but V21
does NOT use them.

No npm install is required.
No Python package installation is required.
