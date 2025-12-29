# Changelog

All notable changes to Garmin Connect Uploader will be documented in this file.

## ⚡ IMPORTANT: How to Update

From **v1.0.1** onwards, the app includes a "Smart Migration" feature to handle older versions automatically. To update correctly:

1. **Keep it in the family:** Place the new `.exe` in the same folder as your previous version. This ensures your settings (`uploader_config.json`) and logs are preserved.
2. **Run the new version:** Once launched, the app will detect if you have an old "Start with Windows" shortcut pointing to the previous file.
3. **One-Click Update:** A prompt will appear asking if you'd like to update the shortcut. Simply click **Yes** to ensure the new version is the one that launches at boot.

> [!IMPORTANT]  
> Your settings and logs are safe as long as the new EXE is in the same location as the old one. You can safely delete the old version's EXE file once the shortcut has been updated.

## [1.0.1] - 2025-12-29

### Added

- MyWhoosh sync behavior warning in main window with link to detailed documentation
- Log file auto-rotation (10MB limit with 3 backup files for ~3 months of history)
- Built-in log viewer that opens at the latest entries instead of external text editor
- Visual icons in logs for easier scanning (✅ success, ❌ error, ⚠️ warning)
- Persistent last sync/upload status that survives app restarts
- Automatic detection and update of old version auto-start shortcuts on first launch
- Interactive close button behavior: prompts user to run in background or close app
- "Minimize to Tray" button in Actions section for explicit tray minimization

### Fixed

- Bug where app would try to upload files from the "uploaded" subfolder
- GitHub repository link now points to correct URL
- Log viewer now allows text search (Ctrl+F) and selection while preventing edits
- GUI window scaling issues on high-DPI displays (user report) - added DPI awareness
- Unclear minimize to tray behavior - users weren't aware of tray functionality (user report)

### Changed

- Log viewer now auto-scrolls to show latest entries first
- Updated README with new log retention policy and viewer behavior
- Optimized startup timing for Windows auto-start (reduced from 3.5s to 1s)
- Improved folder settings layout with wider entry fields and compact help buttons
- Enhanced MyWhoosh warning with larger icon, improved layout, and clearer messaging
- Adjusted window size to 600x825 with enforced minimum dimensions
- Cleaner UI spacing and alignment throughout

## [1.0.0] - 2025-12-28

### Initial Release

- Automatic upload of Wahoo and MyWhoosh .FIT files to Garmin Connect
- Secure password encryption using hardware-linked keys
- Auto-sync with configurable check intervals
- System tray support with minimize functionality
- Windows auto-start on boot
- Custom GUI with logo and developer attribution
- Detailed activity logging
- Folder validation and credential testing
