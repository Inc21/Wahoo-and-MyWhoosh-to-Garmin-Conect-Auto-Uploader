# Changelog

All notable changes to Garmin Connect Uploader will be documented in this file.

## [1.0.1] - 2025-12-29

### Added

- MyWhoosh sync behavior warning in main window with link to detailed documentation
- Log file auto-rotation (10MB limit with 3 backup files for ~3 months of history)
- Built-in log viewer that opens at the latest entries instead of external text editor
- Visual icons in logs for easier scanning (✅ success, ❌ error, ⚠️ warning)
- Persistent last sync/upload status that survives app restarts
- Automatic detection and update of old version auto-start shortcuts on first launch

### Fixed

- Bug where app would try to upload files from the "uploaded" subfolder
- GitHub repository link now points to correct URL
- Log viewer now allows text search (Ctrl+F) and selection while preventing edits

### Changed

- Log viewer now auto-scrolls to show latest entries first
- Updated README with new log retention policy and viewer behavior

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
