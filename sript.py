# flake8: noqa: E501, F541, W293
# Legacy script - see uploader_gui.py for the new GUI version

import os
import sys
import io

# Fix Unicode output in Windows PowerShell
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import time  # noqa: E402
import shutil  # noqa: E402
import threading  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from garminconnect import Garmin  # noqa: E402
from watchdog.observers import Observer  # noqa: E402
from watchdog.events import FileSystemEventHandler  # noqa: E402
from pystray import Icon, MenuItem, Menu  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

# Global state
tray_icon = None
status_messages = []

# Load environment variables
load_dotenv()
GARMIN_USER = os.getenv("GARMIN_USER")
GARMIN_PASSWORD = os.getenv("GARMIN_PASSWORD")
WATCH_FOLDER = r"C:\Users\Dell User\Dropbox\Apps\WahooFitness"
UPLOADED_FOLDER = os.path.join(WATCH_FOLDER, "uploaded")
ICON_PATH = os.path.join(os.path.dirname(__file__), "g.png")
MYWHOOSH_FOLDER = (
    r"C:\Users\Dell User\AppData\Local\Packages"
    r"\MyWhooshTechnologyService.644173E064ED2_eps1123pz0kt0"
    r"\LocalCache\Local\MyWhoosh\Content\Data"
)
MYWHOOSH_TRACK_FILE = os.path.join(
    os.path.dirname(__file__), "mywhoosh_processed.txt"
)
# Local cache for uploaded myWhoosh files
MYWHOOSH_UPLOADED_FOLDER = os.path.join(
    os.path.dirname(__file__), "mywhoosh_uploaded"
)


# Add a message and update the tray tooltip
def update_tray_tooltip(message):
    print(message)
    status_messages.append(message)
    if len(status_messages) > 10:
        status_messages.pop(0)
    if tray_icon:
        tray_icon.menu = Menu(
            *(MenuItem(msg, lambda: None, enabled=False) for msg in reversed(
                status_messages)),
            MenuItem("Exit", exit_action)
        )


# Exit from tray menu
def exit_action(icon, item):
    print("👋 Exiting uploader")
    icon.stop()
    observer.stop()


# Upload and move file
def process_file(file_path, icon=None):
    if not file_path.lower().endswith(".fit"):
        return
    print(f"📄 Uploading: {file_path}")
    try:
        client.upload_activity(file_path)  # ← send the path directly
        print("✅ Upload successful!")
        if icon:
            icon.notify("✅ Upload successful")
        new_path = os.path.join(UPLOADED_FOLDER, os.path.basename(file_path))
        # Try to move, if fails then just copy
        try:
            shutil.move(file_path, new_path)
        except PermissionError:
            print(f"⚠️ File locked, copying instead of moving")
            shutil.copy2(file_path, new_path)
        print(f"💾 Moved/copied to: {new_path}")
    except Exception as e:
        error_msg = str(e)
        print(f"⚠️ Upload issue: {error_msg}")
        # Check if it's a 409 conflict (already uploaded)
        if "409" in error_msg or "Conflict" in error_msg:
            print(f"ℹ️ Activity already exists in Garmin, moving file...")
            new_path = os.path.join(UPLOADED_FOLDER, os.path.basename(file_path))
            # Try to move, if fails then just copy
            try:
                shutil.move(file_path, new_path)
            except PermissionError:
                print(f"⚠️ File locked, copying instead of moving")
                shutil.copy2(file_path, new_path)
            print(f"💾 Moved/copied to: {new_path}")
        else:
            print(f"❌ Upload failed:", e)
            if icon:
                icon.notify(f"❌ Upload failed: {e}")


# File watcher handler
class FileHandler(FileSystemEventHandler):
    def __init__(self, icon):
        self.icon = icon

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".fit"):
            update_tray_tooltip(f"📂 New file detected: {event.src_path}")
            time.sleep(1)  # Let Dropbox finish syncing
            process_file(event.src_path, self.icon)


# Run folder check and watcher
def run_watcher(icon):
    update_tray_tooltip("🔍 Checking existing files...")
    for filename in os.listdir(WATCH_FOLDER):
        full_path = os.path.join(WATCH_FOLDER, filename)
        if os.path.isfile(full_path) and filename.lower().endswith(".fit"):
            update_tray_tooltip(f"👀 Found existing file: {full_path}")
            process_file(full_path, icon)
    update_tray_tooltip(f"👀 Watching folder: {WATCH_FOLDER}")
    handler = FileHandler(icon)
    observer.schedule(handler, path=WATCH_FOLDER, recursive=False)
    observer.start()


def _load_processed_mywhoosh():
    processed = set()
    if os.path.exists(MYWHOOSH_TRACK_FILE):
        try:
            with open(MYWHOOSH_TRACK_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        processed.add(line)
        except Exception as e:
            print("⚠️ Could not read myWhoosh processed file list:", e)
    return processed


def _get_file_signature(file_path):
    """Create a unique signature for a file based on name and modification time."""
    try:
        mod_time = os.path.getmtime(file_path)
        size = os.path.getsize(file_path)
        return f"{os.path.basename(file_path)}_{mod_time}_{size}"
    except Exception:
        return os.path.basename(file_path)


def _save_processed_mywhoosh(processed):
    try:
        with open(MYWHOOSH_TRACK_FILE, "w", encoding="utf-8") as f:
            for path in sorted(processed):
                f.write(path + "\n")
    except Exception as e:
        print("⚠️ Could not write myWhoosh processed file list:", e)


def run_mywhoosh_sync():
    if not os.path.isdir(MYWHOOSH_FOLDER):
        print(f"ℹ️ myWhoosh folder not found, skipping sync: {MYWHOOSH_FOLDER}")
        return

    update_tray_tooltip(f"🔄 Monitoring myWhoosh folder: {MYWHOOSH_FOLDER}")
    print(f"🔍 Starting myWhoosh monitor...")
    processed = _load_processed_mywhoosh()
    
    while True:
        try:
            for filename in os.listdir(MYWHOOSH_FOLDER):
                if not filename.lower().endswith(".fit"):
                    continue

                full_path = os.path.join(MYWHOOSH_FOLDER, filename)
                file_sig = _get_file_signature(full_path)

                # Check if this file signature has changed (newer version)
                if file_sig in processed:
                    continue

                # Found a new or updated file - upload it
                print(f"📤 Found new version: {filename}")
                update_tray_tooltip(f"📤 Found: {filename}")
                
                # Copy to watch folder
                dest_path = os.path.join(WATCH_FOLDER, filename)
                try:
                    shutil.copy2(full_path, dest_path)
                    print(f"✓ Copied: {filename}")
                    time.sleep(1)  # Give system time to process
                except Exception as e:
                    print(f"⚠️ Could not copy file: {e}")
                    continue

                # Mark as processed
                processed.add(file_sig)
                _save_processed_mywhoosh(processed)
            
            # Also check if uploaded files exist and move myWhoosh originals
            for filename in os.listdir(MYWHOOSH_FOLDER):
                if not filename.lower().endswith(".fit"):
                    continue
                
                # Check if this file has been uploaded to Dropbox
                uploaded_in_dropbox = os.path.join(UPLOADED_FOLDER, filename)
                if os.path.exists(uploaded_in_dropbox):
                    # File was successfully uploaded, move the myWhoosh original
                    source_path = os.path.join(MYWHOOSH_FOLDER, filename)
                    dest_cache_path = os.path.join(MYWHOOSH_UPLOADED_FOLDER, filename)
                    
                    try:
                        # Copy to our local mywhoosh_uploaded cache (can't delete from myWhoosh as it's system cache)
                        shutil.copy2(source_path, dest_cache_path)
                        print(f"💾 myWhoosh file cached: {filename}")
                    except Exception as e:
                        print(f"⚠️ Could not cache myWhoosh file: {e}")

        except Exception as e:
            print(f"❌ Error while monitoring myWhoosh: {e}")

        # Check for updates every 5 minutes (300 seconds) - activities don't change that frequently
        time.sleep(300)


# Create system tray icon
def create_icon():
    try:
        icon_image = Image.open(ICON_PATH)
    except Exception:
        # Fallback to blue "G" if image not found
        icon_image = Image.new("RGB", (64, 64), (30, 144, 255))
        draw = ImageDraw.Draw(icon_image)
        draw.text((22, 16), "G", fill="white")
    return Icon("GarminUploader", icon_image, "Garmin Uploader", menu=Menu(
        *(MenuItem(msg, lambda: None, enabled=False) for msg in reversed(
            status_messages)),
        MenuItem("Exit", exit_action)
    ))


# Create output folder for local tracking
os.makedirs(UPLOADED_FOLDER, exist_ok=True)
os.makedirs(MYWHOOSH_UPLOADED_FOLDER, exist_ok=True)

# Login
try:
    client = Garmin(GARMIN_USER, GARMIN_PASSWORD)
    client.login()
    update_tray_tooltip("✅ Logged in to Garmin Connect")
except Exception as e:
    print("❌ Login failed:", e)
    sys.exit(1)

# Start everything
observer = Observer()
tray_icon = create_icon()
threading.Thread(target=run_watcher, args=(tray_icon,), daemon=True).start()
threading.Thread(target=run_mywhoosh_sync, daemon=True).start()
threading.Thread(target=tray_icon.run, daemon=False).start()

print("✅ ConnectUploader started successfully!")
print("📊 System tray icon is running")
print("🔄 Watching for new workout files...")
print("\nPress Ctrl+C to stop the uploader\n")

# Keep the main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n👋 Shutting down ConnectUploader...")
    observer.stop()
    observer.join()
    tray_icon.stop()
    sys.exit(0)
