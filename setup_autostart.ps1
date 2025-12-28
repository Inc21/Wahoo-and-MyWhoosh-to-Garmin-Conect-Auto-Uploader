# This script adds ConnectUploader to Windows startup
# Run this as Administrator

$shortcutPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\ConnectUploader.lnk"
$batFilePath = "e:\Coding\scripts\ConnectUploader\start_uploader.bat"
$workingDir = "e:\Coding\scripts\ConnectUploader"

# Create COM object for shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)

# Set shortcut properties
$Shortcut.TargetPath = $batFilePath
$Shortcut.WorkingDirectory = $workingDir
$Shortcut.Description = "ConnectUploader - Auto uploads workouts to Garmin"
$Shortcut.IconLocation = "$workingDir\g.png"

# Save the shortcut
$Shortcut.Save()

Write-Host "✅ ConnectUploader shortcut created in Startup folder!"
Write-Host "Shortcut path: $shortcutPath"
Write-Host "The script will now auto-start when Windows boots"
Write-Host "You can also manually run: $batFilePath"
