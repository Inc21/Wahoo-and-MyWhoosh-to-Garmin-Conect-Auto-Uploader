@echo off
REM Start the ConnectUploader script with proper encoding
cd /d "e:\Coding\scripts\ConnectUploader"
set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe sript.py
pause
