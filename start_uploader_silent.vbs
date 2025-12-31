Set WshShell = CreateObject("WScript.Shell")
exePath = WScript.ScriptFullName
exeDir = Left(exePath, InStrRev(exePath, "\\") - 1)
WshShell.CurrentDirectory = exeDir
WshShell.Run "GarminUploader-v1.0.2.exe", 0, False
Set WshShell = Nothing
