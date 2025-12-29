# Changelog

All notable changes to Garmin Connect Uploader will be documented in this file.

## [1.0.1] - 2025-12-29

> **⚡ IMPORTANT for Users Updating:**  
> This version automatically detects and updates Windows auto-start shortcuts from previous versions! Simply run the new exe from the same folder as your old one. If you had "Start with Windows" enabled, the app will offer to update the shortcut to the new version. Your settings (`uploader_config.json`) and logs (`garmin_uploader.log`) are preserved as long as the new exe is in the same location.

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
