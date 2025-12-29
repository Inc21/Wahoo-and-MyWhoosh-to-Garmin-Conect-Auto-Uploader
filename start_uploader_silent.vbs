Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c ""cd /d e:\Coding\scripts\ConnectUploader && set PYTHONIOENCODING=utf-8 && .venv\Scripts\python.exe sript.py""", 0, False
Set WshShell = Nothing
