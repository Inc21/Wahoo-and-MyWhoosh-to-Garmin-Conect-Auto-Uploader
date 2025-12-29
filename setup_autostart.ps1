# This script adds ConnectUploader to Windows startup
# Run this as Administrator

$shortcutPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ConnectUploader.lnk"
$vbsFilePath = "e:\Coding\scripts\ConnectUploader\start_uploader_silent.vbs"
$workingDir = "e:\Coding\scripts\ConnectUploader"

# Create COM object for shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)

# Set shortcut properties
$Shortcut.TargetPath = $vbsFilePath
$Shortcut.WorkingDirectory = $workingDir
$Shortcut.Description = "ConnectUploader - Auto uploads workouts to Garmin (Silent)"
$Shortcut.IconLocation = "$workingDir\g.png"

# Save the shortcut
$Shortcut.Save()

Write-Host "ConnectUploader shortcut created in Startup folder!"
Write-Host "Shortcut path: $shortcutPath"
Write-Host "The script will now run SILENTLY in the background at Windows startup"
Write-Host "It will check for new workouts every 5 minutes"
Write-Host "To stop it, close it from the system tray icon"
