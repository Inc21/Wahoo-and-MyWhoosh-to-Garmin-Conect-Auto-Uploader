# Garmin Connect Uploader

Automatically upload workout activities from Wahoo and MyWhoosh to Garmin Connect.

Version 1.0.0 | Windows Desktop Application

---

## What It Does

This app automatically syncs your Wahoo and MyWhoosh workout files (.FIT) to Garmin Connect, so your activities appear in your Garmin dashboard without manual uploads.

**Key Features:**

- ✅ Automatic background syncing
- ✅ Starts with Windows (optional)
- ✅ Secure password encryption
- ✅ Validates credentials before saving
- ✅ Detailed activity logging
- ✅ System tray support

---

## ⚠️ Important Sync Behavior

The app handles the two platforms differently based on how they store files:

- **Wahoo (Persistent):** If you connect a Dropbox account that has a history of Wahoo rides, the app **will** detect those files and upload your history to Garmin Connect automatically.
- **MyWhoosh (Volatile):** MyWhoosh only stores the **most recent** activity in its local cache and overwrites it when you start a new session.
  - **The Catch:** Your PC doesn't always have to be on for the sync to work eventually, **but** if you record multiple MyWhoosh activities while the app is closed (or the PC is off), the uploader will only "see" and sync the **very last one** when it finally boots up.
  - **Recommendation:** Use the "Start with Windows" option so the app is always ready to catch MyWhoosh files before they are lost.

---

## 🔒 Security & Privacy

I built this originally as a personal Python script to solve my own manual upload frustrations. Because this app handles Garmin credentials, transparency is a priority:

- **Local Only:** Your credentials are never sent to any server except Garmin’s official login endpoint.
- **Encryption:** Your Garmin password is not stored in plain text. It is encrypted locally on your machine using a unique hardware-linked key before being saved to `uploader_config.json`.
- **Open Source:** The full source code is available here on GitHub for anyone to audit.

---

## Download & Install

### Step 1: Download

1. Download `GarminUploader.exe` from the releases/dist folder
2. Place it anywhere you like (Desktop, Documents, etc.)
3. Double-click to run

**Note:** Windows may show a security warning ("Windows protected your PC") - click "More info" → "Run anyway"

---

## First Time Setup

### Step 2: Enter Garmin Credentials

1. Enter your **Garmin Connect email**
2. Enter your **Garmin Connect password**
3. Click **"Save Settings"** button

**Important:** The app will test your login and show ✅ or ❌. Your password is encrypted in the settings file.

### Step 3: Configure Your Folders

You need **at least one folder** configured:

#### **Option A: Wahoo (via Dropbox)**

1. Click **"📖 Help"** button next to Wahoo Folder
2. Follow the instructions to:
   - Create free Dropbox account
   - Connect Wahoo ELEMNT to Dropbox
   - Install Dropbox on PC
3. Click **"Browse"** and select your Dropbox Wahoo folder:

   ```text
   C:\Users\YourName\Dropbox\Apps\WahooFitness
   ```

#### **Option B: MyWhoosh**

1. Click **"📖 Help"** button next to MyWhoosh Folder
2. Follow the instructions to find your MyWhoosh cache folder
3. Click **"Browse"** and navigate to:

   ```text
   C:\Users\YourName\AppData\Local\MyWhoosh\MyWhoosh\Cache\Cache_Data
   ```

**Tip:** Press `Win + R`, paste `%LOCALAPPDATA%\MyWhoosh\MyWhoosh\Cache\Cache_Data`, press Enter

### Step 4: Set Check Interval (Optional)

Default is **5 minutes**. Adjust if you want faster/slower checking.

### Step 5: Save Settings

Click **"Save Settings"** - this will:

- ✅ Validate your Garmin credentials
- ✅ Encrypt your password
- ✅ Save all settings

---

## Daily Use

### Manual Upload (One-Time)

1. Click **"Sync Now"** button
2. App will upload any new .FIT files immediately
3. Check status at bottom of window

### Automatic Background Uploads

**For set-and-forget automation:**

1. ✅ Check **"Start with Windows"**
2. ✅ Check **"Start Auto-Sync"** checkbox
3. Click **"Start Auto-Sync"** button

**What happens:**

- App checks for new files every 5 minutes (or your interval)
- Shows status updates at bottom
- Can minimize to system tray (bottom-right corner)

**To minimize to tray:**

- Click the **[X]** close button
- If auto-sync is running, you'll be asked if you want to minimize to tray
- Click **YES** to keep it running in background
- Look for Garmin icon in system tray

**To restore from tray:**

- Click the Garmin icon in system tray
- Select "Show"

---

## Auto-Start on Windows Boot

**Make it fully automatic:**

1. ✅ Check **"Start with Windows"**
2. ✅ Ensure **"Start Auto-Sync"** is also checked (optional but recommended)
3. Click **"Save Settings"**
4. Restart your computer to test

**What happens on boot:**

- App starts automatically (minimized to tray)
- Begins auto-sync if you have credentials and folders configured
- Runs silently in background
- Check system tray for Garmin icon

**To disable auto-start:**

- Uncheck "Start with Windows"
- Click "Save Settings"

---

## Files Created

The app creates 2 files in the **same folder as the EXE**:

1. **`uploader_config.json`** - Your settings (password is encrypted)
2. **`garmin_uploader.log`** - Activity log with timestamps

**View the log:**

- Click **"ℹ️ About"** button
- Click **"📄 View Log"** button
- Opens in Notepad for searching

**What's logged:**

- App startup/shutdown
- Garmin login attempts (success/failure)
- File uploads (filename, timestamp)
- Errors and warnings
- Auto-sync start/stop
- Settings changes

---

## Troubleshooting

### ❌ "Invalid Credentials" Error

- Double-check email/password at garmin.com
- Click "Save Settings" again to re-test
- Check log file for detailed error

### ❌ "No Folders Configured" Error

- You must configure at least ONE folder (Wahoo OR MyWhoosh)
- Click Browse to select folder
- Click Help button for setup instructions

### ❌ Auto-Start Not Working After Reboot

1. Press `Win + R`, type: `shell:startup`, press Enter
2. Look for `GarminUploader.lnk` shortcut
3. If missing: Re-enable "Start with Windows" in app
4. If present: Check log file for startup errors
5. Make sure EXE location hasn't moved

### ❌ Files Not Uploading

- Click "Sync Now" to test immediately
- Check if .FIT files exist in your folders
- View log file for upload attempts
- Verify Garmin credentials are valid
- Check folder paths are correct

### ⚠️ "File Already Uploaded (409)" in Log

- This is normal - means Garmin already has this activity
- File is moved to "uploaded" subfolder anyway
- No action needed

### 🔍 Can't Find System Tray Icon

- Look in bottom-right corner of Windows taskbar
- Click small **^** arrow to show hidden icons
- Garmin logo should appear there

---

## Uninstalling

1. Uncheck "Start with Windows" in app
2. Click "Save Settings"
3. Close the app
4. Delete `GarminUploader.exe`
5. Delete `uploader_config.json` and `garmin_uploader.log` (optional)

---

## Support

**Developer:** [inc21](https://github.com/Inc21)  
**Buy me a coffee:** [☕ Support](https://buymeacoffee.com/inc21)

---

## License

MIT License
