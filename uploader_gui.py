# flake8: noqa: E501
# GUI application for Garmin Connect automatic uploader
# Line length limit relaxed for readability in GUI code

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json
import os
import sys
import threading
import time
import logging
import base64
from garminconnect import Garmin
from PIL import Image, ImageTk
from pystray import Icon, Menu, MenuItem
import webbrowser
import shutil

# Configuration file
CONFIG_FILE = "uploader_config.json"

# Get the correct path for bundled resources (PyInstaller)
if getattr(sys, 'frozen', False):
    # Running as compiled EXE
    BASE_DIR = sys._MEIPASS
    LOG_DIR = os.path.dirname(sys.executable)
else:
    # Running as script
    BASE_DIR = os.path.dirname(__file__)
    LOG_DIR = os.path.dirname(__file__)

LOGO_PATH = os.path.join(BASE_DIR, "garmin-uploader-logo.PNG")
VERSION = "1.0.0"
LOG_FILE = os.path.join(LOG_DIR, "garmin_uploader.log")

# Setup logging (standard format without icons by default)
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger(__name__)

# Custom log functions with icons for specific events
def log_success(message):
    """Log a success message with green checkmark"""
    logger.info(f"✅ {message}")

def log_error(message):
    """Log an error message with red X"""
    logger.error(f"❌ {message}")

def log_warning(message):
    """Log a warning message with warning sign"""
    logger.warning(f"⚠️ {message}")

def log_info(message):
    """Log an info message (no icon)"""
    logger.info(message)

# Simple encryption key (better than plain text)
# In production, consider using cryptography library
ENCRYPTION_KEY = "GarminUploaderV1SecretKey2024"


def encrypt_password(password):
    """Simple encryption using base64 and XOR"""
    if not password:
        return ""
    # XOR with key
    encrypted = ''.join(
        chr(ord(c) ^ ord(ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)]))
        for i, c in enumerate(password)
    )
    # Base64 encode
    return base64.b64encode(encrypted.encode('latin-1')).decode('utf-8')


def decrypt_password(encrypted_password):
    """Decrypt password"""
    if not encrypted_password:
        return ""
    try:
        # Base64 decode
        decoded = base64.b64decode(
            encrypted_password.encode('utf-8')
        ).decode('latin-1')
        # XOR with key to decrypt
        decrypted = ''.join(
            chr(ord(c) ^ ord(ENCRYPTION_KEY[i % len(ENCRYPTION_KEY)]))
            for i, c in enumerate(decoded)
        )
        return decrypted
    except Exception:  # noqa: E722
        return ""  # Return empty if decryption fails


class ConnectUploaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Garmin Connect Uploader v{VERSION}")
        self.root.geometry("650x850")
        self.root.resizable(True, True)  # Allow resizing
        
        # Set modern styling
        style = ttk.Style()
        style.theme_use('clam')  # More modern theme
        
        # Configure colors
        style.configure('TLabel', background='#f0f0f0')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', padding=6)
        style.configure('Header.TLabel', font=('Arial', 11, 'bold'), background='#f0f0f0')
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), background='#f0f0f0', foreground='#2c3e50')
        
        # Set window background
        self.root.configure(bg='#f0f0f0')
        
        # Set window icon
        try:
            if os.path.exists(LOGO_PATH):
                # Load PNG and set as window icon
                logo_img = Image.open(LOGO_PATH)
                logo_photo = ImageTk.PhotoImage(logo_img)
                self.root.iconphoto(True, logo_photo)
                self.logo_image = logo_photo  # Keep reference
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        # Load saved configuration
        self.config = self.load_config()
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        self.garmin_client = None
        self.logo_image = None  # Keep reference to prevent garbage collection
        self.tray_icon = None
        self.check_interval = 300  # Default 5 minutes
        self.settings_changed = False  # Track if settings have been modified
        
        self.create_widgets()
        self.load_settings()
        
        # Handle window close (minimize to tray if monitoring)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Create canvas with scrollbar for content
        canvas = tk.Canvas(self.root, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        
        # Main container inside canvas
        main_frame = ttk.Frame(canvas, padding="20")
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create window in canvas
        canvas_frame = canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # Update scroll region when frame size changes
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Center the frame horizontally
            canvas_width = event.width
            frame_width = main_frame.winfo_reqwidth()
            x_position = max(0, (canvas_width - frame_width) // 2)
            canvas.coords(canvas_frame, x_position, 0)
        
        main_frame.bind("<Configure>", on_frame_configure)
        
        # Bind mousewheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Title with logo
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 25))
        
        # Load and display logo
        try:
            logo_img = Image.open(LOGO_PATH)
            logo_img.thumbnail((45, 45))  # Resize to 45x45
            self.title_logo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(title_frame, image=self.title_logo)
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        except Exception:
            pass  # If logo fails to load, just skip it
        
        # Title text
        ttk.Label(title_frame, text="Garmin Connect Uploader", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Garmin Settings
        ttk.Label(main_frame, text="🔑 Garmin Connect Settings", style='Header.TLabel').grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        # Quick link to Garmin Connect
        garmin_link = ttk.Label(
            main_frame,
            text="Open Garmin Connect in Browser",
            foreground='blue',
            cursor='hand2',
            font=('Arial', 9, 'underline')
        )
        garmin_link.grid(row=1, column=2, sticky=tk.E, pady=(10, 5))
        garmin_link.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://connect.garmin.com")
        )
        
        ttk.Label(main_frame, text="Email:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.garmin_email = ttk.Entry(main_frame, width=40)
        self.garmin_email.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.garmin_email.bind('<KeyRelease>', lambda e: self.mark_settings_changed())
        
        ttk.Label(main_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.garmin_password = ttk.Entry(main_frame, width=40, show="*")
        self.garmin_password.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        self.garmin_password.bind('<KeyRelease>', lambda e: self.mark_settings_changed())
        
        # Folder Settings
        ttk.Label(main_frame, text="📁 Folder Settings", style='Header.TLabel').grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))
        
        # Wahoo Folder
        ttk.Label(main_frame, text="Wahoo Folder (via Dropbox):").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.wahoo_folder = ttk.Entry(main_frame, width=35)
        self.wahoo_folder.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(main_frame, text="Browse", command=lambda: self.browse_folder(self.wahoo_folder)).grid(row=5, column=2, pady=5)
        
        # Wahoo help button
        ttk.Button(main_frame, text="📖 How to Setup Wahoo with Dropbox", command=self.show_wahoo_help).grid(row=6, column=1, columnspan=2, sticky=tk.W, pady=(0,5), padx=5)
        
        ttk.Label(main_frame, text="Example: C:\\Users\\YourName\\Dropbox\\Apps\\WahooFitness", font=('Arial', 8), foreground='gray').grid(row=7, column=1, columnspan=2, sticky=tk.W, padx=5)
        
        # MyWhoosh Folder
        ttk.Label(main_frame, text="MyWhoosh Folder:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.mywhoosh_folder = ttk.Entry(main_frame, width=35)
        self.mywhoosh_folder.grid(row=8, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(main_frame, text="Browse", command=lambda: self.browse_folder(self.mywhoosh_folder)).grid(row=8, column=2, pady=5)
        
        # MyWhoosh help button
        ttk.Button(main_frame, text="📖 How to Find MyWhoosh Folder", command=self.show_mywhoosh_help).grid(row=9, column=1, columnspan=2, sticky=tk.W, pady=(0,5), padx=5)
        
        ttk.Label(main_frame, text="Example: C:\\Users\\YourName\\AppData\\Local\\...\\MyWhoosh\\Content\\Data", font=('Arial', 8), foreground='gray').grid(row=10, column=1, columnspan=2, sticky=tk.W, padx=5)
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        
        # Auto-Start Settings
        ttk.Label(main_frame, text="⏰ Auto-Start Settings", style='Header.TLabel').grid(row=12, column=0, columnspan=3, sticky=tk.W, pady=(5, 5))
        
        # Helpful note
        note_text = "💡 Tip: Enable both 'Start with Windows' AND 'Start Auto-Sync' for automatic background uploads"
        ttk.Label(main_frame, text=note_text, font=('Arial', 8, 'italic'), foreground='#0066cc', wraplength=600).grid(row=13, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        # Start with Windows checkbox
        self.start_with_windows = tk.BooleanVar()
        ttk.Checkbutton(main_frame, text="Start with Windows (run in background at startup)", variable=self.start_with_windows, command=self.toggle_autostart).grid(row=14, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Check interval
        interval_frame = ttk.Frame(main_frame)
        interval_frame.grid(row=15, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        ttk.Label(interval_frame, text="Check for new activities every:").pack(side=tk.LEFT, padx=(0, 5))
        self.interval_var = tk.IntVar(value=5)
        interval_spinbox = ttk.Spinbox(interval_frame, from_=1, to=30, textvariable=self.interval_var, width=5, command=self.mark_settings_changed)
        interval_spinbox.pack(side=tk.LEFT)
        ttk.Label(interval_frame, text="minutes").pack(side=tk.LEFT, padx=(5, 0))
        
        # Save Settings Button
        ttk.Button(main_frame, text="Save Settings", command=self.save_settings).grid(row=16, column=0, columnspan=3, pady=(20, 10))
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(row=17, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Actions
        ttk.Label(main_frame, text="▶️ Actions", style='Header.TLabel').grid(row=18, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        # Sync Now Button
        self.sync_button = ttk.Button(main_frame, text="Sync Now", command=self.sync_now, width=20)
        self.sync_button.grid(row=19, column=0, pady=10, padx=5)
        
        # Start/Stop Monitoring
        self.monitor_button = ttk.Button(main_frame, text="Start Auto-Sync", command=self.toggle_monitoring, width=20)
        self.monitor_button.grid(row=19, column=1, pady=10, padx=5)
        
        # About Button
        about_btn = ttk.Button(main_frame, text="ℹ️ About", command=self.show_about, width=20)
        about_btn.grid(row=19, column=2, pady=10, padx=5)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Status: Idle", foreground='blue', font=('Arial', 9))
        self.status_label.grid(row=20, column=0, columnspan=3, pady=(10, 0))
        
        # Last sync time
        self.last_sync_label = ttk.Label(main_frame, text="Last sync: Never", foreground='gray', font=('Arial', 8))
        self.last_sync_label.grid(row=21, column=0, columnspan=3)
        
        # Last upload info
        self.last_upload_label = ttk.Label(main_frame, text="Last upload: None", foreground='gray', font=('Arial', 8))
        self.last_upload_label.grid(row=22, column=0, columnspan=3)
        
        # View full log link
        log_link = ttk.Label(
            main_frame,
            text="View Full Log",
            foreground='blue',
            cursor='hand2',
            font=('Arial', 8, 'underline')
        )
        log_link.grid(row=23, column=0, columnspan=3, pady=(5, 10))
        log_link.bind("<Button-1>", lambda e: self.open_log_file())
        
    def show_wahoo_help(self):
        # Create a new window with selectable text
        help_window = tk.Toplevel(self.root)
        help_window.title("Wahoo Setup Instructions")
        help_window.geometry("550x500")
        help_window.resizable(False, False)
        
        # Title
        title_label = ttk.Label(help_window, text="How to Setup Wahoo with Dropbox", font=('Arial', 12, 'bold'))
        title_label.pack(pady=10)
        
        # Dropbox install link button
        dropbox_btn = ttk.Button(
            help_window,
            text="📥 Download Dropbox Desktop App",
            command=lambda: webbrowser.open("https://www.dropbox.com/install")
        )
        dropbox_btn.pack(pady=(0, 10))
        
        # Scrollable text area
        text_area = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, width=65, height=20, font=('Arial', 9))
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        help_text = """1. Create a Dropbox account (free):
   → Go to dropbox.com and sign up

2. Connect Wahoo to Dropbox:
   → Open Wahoo ELEMNT app on your phone
   → Go to Settings → Cloud Services
   → Enable Dropbox and authorize

3. Install Dropbox on your PC:
   → Download from dropbox.com/install
   → Sign in with your account
   → Let it sync

4. Find the Wahoo folder:
   → Open File Explorer
   → Navigate to:
   
   C:\\Users\\YourName\\Dropbox\\Apps\\WahooFitness
   
   → Copy this path and paste it in the Wahoo Folder field

Note: The app will automatically create an 'uploaded' subfolder to move processed .fit files there.

You can select and copy text from this window!"""
        
        text_area.insert(1.0, help_text)
        text_area.config(state='normal')  # Keep it editable so users can select/copy
        
        # Close button
        close_btn = ttk.Button(help_window, text="Close", command=help_window.destroy)
        close_btn.pack(pady=10)
    
    def show_mywhoosh_help(self):
        # Create a new window with selectable text
        help_window = tk.Toplevel(self.root)
        help_window.title("MyWhoosh Folder Instructions")
        help_window.geometry("600x500")
        help_window.resizable(False, False)
        
        # Title
        title_label = ttk.Label(help_window, text="How to Find MyWhoosh Cache Folder", font=('Arial', 12, 'bold'))
        title_label.pack(pady=10)
        
        # Scrollable text area
        text_area = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, width=70, height=24, font=('Arial', 9))
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        help_text = """MyWhoosh only keeps the LAST activity in its cache folder.
This folder is hidden deep in Windows AppData.

How to find it:

1. Open File Explorer

2. In the address bar, paste this and press Enter:

   %localappdata%\\Packages

3. Look for a folder starting with:

   MyWhooshTechnologyService.644173E064ED2
   
   Full example:
   MyWhooshTechnologyService.644173E064ED2_eps1123pz0kt0

4. Open that folder, then navigate to:

   LocalCache\\Local\\MyWhoosh\\Content\\Data

5. Full path example (copy this format):

   C:\\Users\\YourName\\AppData\\Local\\Packages\\MyWhooshTechnologyService.644173E064ED2_eps1123pz0kt0\\LocalCache\\Local\\MyWhoosh\\Content\\Data

6. Copy YOUR path and paste it in the MyWhoosh Folder field

Note: MyWhoosh typically only keeps the most recent activity file (usually MyNewActivity-5.5.1.fit or similar) in this folder. The app will process ALL .fit files it finds there.

You can select and copy text from this window!"""
        
        text_area.insert(1.0, help_text)
        text_area.config(state='normal')  # Keep it editable so users can select/copy
        
        # Close button
        close_btn = ttk.Button(help_window, text="Close", command=help_window.destroy)
        close_btn.pack(pady=10)
    
    def browse_folder(self, entry_widget):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'garmin_email': '',
            'garmin_password': '',
            'wahoo_folder': '',
            'mywhoosh_folder': '',
            'start_with_windows': False,
            'check_interval': 5
        }
    
    def save_config(self):
        config = {
            'garmin_email': self.garmin_email.get(),
            'garmin_password': encrypt_password(self.garmin_password.get()),  # Encrypt password
            'wahoo_folder': self.wahoo_folder.get(),
            'mywhoosh_folder': self.mywhoosh_folder.get(),
            'start_with_windows': self.start_with_windows.get(),
            'check_interval': self.interval_var.get()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info("Configuration saved (password encrypted)")
        return config
    
    def load_settings(self):
        self.garmin_email.insert(0, self.config.get('garmin_email', ''))
        # Decrypt password when loading
        encrypted_password = self.config.get('garmin_password', '')
        decrypted_password = decrypt_password(encrypted_password)
        self.garmin_password.insert(0, decrypted_password)
        self.wahoo_folder.insert(0, self.config.get('wahoo_folder', ''))
        self.mywhoosh_folder.insert(0, self.config.get('mywhoosh_folder', ''))
        self.start_with_windows.set(self.config.get('start_with_windows', False))
        self.interval_var.set(self.config.get('check_interval', 5))
        self.check_interval = self.interval_var.get() * 60  # Convert to seconds
    
    def save_settings(self):
        # Validate Garmin credentials if they've been entered
        if self.garmin_email.get() and self.garmin_password.get():
            if not self.validate_garmin_credentials():
                return  # Don't save if validation fails
        
        self.config = self.save_config()
        self.check_interval = self.interval_var.get() * 60  # Update interval in seconds
        self.settings_changed = False  # Reset flag after saving
        log_success("Settings saved successfully")
        messagebox.showinfo("Settings Saved", "Your settings have been saved successfully!")
        self.update_status("Settings saved", "green")
    
    def validate_garmin_credentials(self):
        """Test Garmin credentials to ensure they're valid"""
        email = self.garmin_email.get()
        password = self.garmin_password.get()
        
        if not email or not password:
            return True  # Skip validation if empty
        
        # Show progress
        self.update_status("Validating Garmin credentials...", "orange")
        logger.info(f"Validating Garmin credentials for: {email}")
        
        try:
            # Test login in background thread to avoid blocking UI
            test_client = Garmin(email, password)
            test_client.login()
            log_success("Garmin credentials validated successfully")
            messagebox.showinfo("Credentials Valid", "✅ Garmin credentials are valid!")
            self.update_status("Garmin credentials validated", "green")
            return True
        except Exception as e:
            logger.error(f"Garmin credential validation failed: {str(e)}")
            messagebox.showerror(
                "Invalid Credentials",
                f"❌ Could not login to Garmin Connect.\n\nError: {str(e)}\n\nPlease check your email and password."
            )
            self.update_status("Garmin login failed", "red")
            return False
    
    def mark_settings_changed(self):
        """Mark that settings have been modified"""
        self.settings_changed = True
    
    def toggle_autostart(self):
        """Toggle Windows startup using shortcut"""
        startup_folder = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        shortcut_path = os.path.join(startup_folder, 'GarminUploader.lnk')
        
        if self.start_with_windows.get():
            # Create startup shortcut
            try:
                # Get the current executable path
                if getattr(sys, 'frozen', False):
                    # Running as EXE
                    exe_path = sys.executable
                else:
                    # Running as script - create VBS to run it
                    exe_path = os.path.join(os.path.dirname(__file__), 'start_uploader_silent.vbs')
                    if not os.path.exists(exe_path):
                        messagebox.showerror("Error", "start_uploader_silent.vbs not found!\nPlease run from the installed location.")
                        self.start_with_windows.set(False)
                        return
                
                # Create shortcut using PowerShell with proper escaping
                working_dir = os.path.dirname(exe_path)
                ps_command = (
                    f"$WshShell = New-Object -ComObject WScript.Shell; "
                    f"$Shortcut = $WshShell.CreateShortcut('{shortcut_path}'); "
                    f"$Shortcut.TargetPath = '{exe_path}'; "
                    f"$Shortcut.Arguments = '--minimized'; "
                    f"$Shortcut.WorkingDirectory = '{working_dir}'; "
                    f"$Shortcut.WindowStyle = 7; "
                    f"$Shortcut.Description = 'Garmin Connect Uploader'; "
                    f"$Shortcut.Save()"
                )
                
                result = os.system(f'powershell -Command "{ps_command}"')
                
                if result == 0:
                    logger.info(f"Auto-start shortcut created: {shortcut_path}")
                    messagebox.showinfo("Auto-Start Enabled", "Garmin Uploader will now start automatically when Windows starts!\n\nIt will start minimized to system tray.")
                    self.update_status("Auto-start enabled", "green")
                else:
                    raise Exception("PowerShell command failed")
                    
            except Exception as e:
                logger.error(f"Failed to enable auto-start: {str(e)}")
                messagebox.showerror("Error", f"Could not enable auto-start: {e}")
                self.start_with_windows.set(False)
        else:
            # Remove startup shortcut
            try:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    logger.info(f"Auto-start shortcut removed: {shortcut_path}")
                    messagebox.showinfo("Auto-Start Disabled", "Garmin Uploader will no longer start automatically.")
                self.update_status("Auto-start disabled", "blue")
            except Exception as e:
                logger.error(f"Failed to disable auto-start: {str(e)}")
                messagebox.showerror("Error", f"Could not disable auto-start: {e}")
    
    def validate_settings(self):
        if not self.garmin_email.get() or not self.garmin_password.get():
            messagebox.showerror("Error", "Please enter your Garmin email and password")
            log_warning("Sync attempted without Garmin credentials")
            return False
        
        wahoo = self.wahoo_folder.get()
        mywhoosh = self.mywhoosh_folder.get()
        
        # At least one folder must be configured
        if not wahoo and not mywhoosh:
            messagebox.showerror(
                "No Folders Configured",
                "Please configure at least one folder:\n\n• Wahoo Folder (for Wahoo fitness files)\n• MyWhoosh Folder (for MyWhoosh activities)\n\nUse the Browse buttons to select your folders."
            )
            log_warning("Sync attempted without any folders configured")
            return False
        
        # Warn about non-existent folders but allow sync
        if wahoo and not os.path.isdir(wahoo):
            response = messagebox.askyesno(
                "Wahoo Folder Not Found",
                f"Wahoo folder not found:\n{wahoo}\n\nContinue anyway?"
            )
            if not response:
                return False
            log_warning(f"Wahoo folder not found but user chose to continue: {wahoo}")
        
        if mywhoosh and not os.path.isdir(mywhoosh):
            response = messagebox.askyesno(
                "MyWhoosh Folder Not Found",
                f"MyWhoosh folder not found:\n{mywhoosh}\n\nContinue anyway?"
            )
            if not response:
                return False
            log_warning(f"MyWhoosh folder not found but user chose to continue: {mywhoosh}")
        
        return True
    
    def login_garmin(self):
        try:
            self.update_status("Logging into Garmin...", "orange")
            logger.info("Attempting Garmin login")
            self.garmin_client = Garmin(self.garmin_email.get(), self.garmin_password.get())
            self.garmin_client.login()
            log_success("Garmin login successful")
            self.update_status("Logged into Garmin successfully", "green")
            return True
        except Exception as e:
            logger.error(f"Garmin login failed: {str(e)}")
            self.update_status(f"Garmin login failed: {str(e)}", "red")
            messagebox.showerror("Login Failed", f"Could not login to Garmin:\n{str(e)}")
            return False
    
    def sync_now(self):
        if not self.validate_settings():
            return
        
        # Run sync in background thread
        thread = threading.Thread(target=self._sync_files, daemon=True)
        thread.start()
    
    def _sync_files(self):
        self.sync_button.config(state='disabled')
        
        # Login to Garmin
        if not self.garmin_client:
            if not self.login_garmin():
                self.sync_button.config(state='normal')
                return
        
        uploaded_count = 0
        last_uploaded_file = None
        
        # Sync Wahoo files
        wahoo_folder = self.wahoo_folder.get()
        if wahoo_folder and os.path.isdir(wahoo_folder):
            count, last_file = self._process_folder(wahoo_folder, "Wahoo")
            uploaded_count += count
            if last_file:
                last_uploaded_file = last_file
        
        # Sync MyWhoosh files
        mywhoosh_folder = self.mywhoosh_folder.get()
        if mywhoosh_folder and os.path.isdir(mywhoosh_folder):
            count, last_file = self._process_folder(mywhoosh_folder, "MyWhoosh")
            uploaded_count += count
            if last_file:
                last_uploaded_file = last_file
        
        # Update UI
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        self.last_sync_label.config(text=f"Last sync: {current_time}")
        
        if uploaded_count > 0:
            self.update_status(f"Sync complete! Uploaded {uploaded_count} activities", "green")
            # Update last upload info
            upload_time = time.strftime("%Y-%m-%d %H:%M")
            self.last_upload_label.config(
                text=f"Last upload: {upload_time} - {uploaded_count} file(s) - Latest: {last_uploaded_file}",
                foreground='green'
            )
            log_success(f"Sync completed: {uploaded_count} activities uploaded")
        else:
            self.update_status("Sync complete - no new activities found", "blue")
            log_success("Sync completed: No new activities found")
        
        self.sync_button.config(state='normal')
    
    def _process_folder(self, folder, source_name):
        uploaded = 0
        last_uploaded_file = None
        uploaded_folder = os.path.join(folder, "uploaded")
        os.makedirs(uploaded_folder, exist_ok=True)
        
        logger.info(f"Processing {source_name} folder: {folder}")
        
        try:
            for filename in os.listdir(folder):
                if filename.lower().endswith('.fit'):
                    file_path = os.path.join(folder, filename)
                    
                    if os.path.isfile(file_path):
                        self.update_status(f"Uploading {filename}...", "orange")
                        log_info(f"Uploading file: {filename} from {source_name}")
                        
                        try:
                            self.garmin_client.upload_activity(file_path)
                            uploaded += 1
                            last_uploaded_file = filename
                            log_success(f"Successfully uploaded: {filename}")
                            
                            # Move to uploaded folder
                            dest_path = os.path.join(uploaded_folder, filename)
                            try:
                                shutil.move(file_path, dest_path)
                                log_info(f"Moved {filename} to uploaded folder")
                            except PermissionError:
                                shutil.copy2(file_path, dest_path)
                                log_warning(f"File locked, copied instead of moved: {filename}")
                            
                            self.update_status(f"Uploaded {filename}", "green")
                        
                        except Exception as e:
                            error_msg = str(e)
                            if "409" in error_msg or "Conflict" in error_msg:
                                log_info(f"File already uploaded (409 conflict): {filename}")
                                # Already uploaded, move it
                                dest_path = os.path.join(uploaded_folder, filename)
                                try:
                                    shutil.move(file_path, dest_path)
                                except PermissionError:
                                    shutil.copy2(file_path, dest_path)
                            else:
                                log_error(f"Failed to upload {filename}: {error_msg}")
                                self.update_status(f"Failed to upload {filename}: {error_msg}", "red")
        
        except Exception as e:
            log_error(f"Error processing {source_name} folder: {str(e)}")
            self.update_status(f"Error processing {source_name} folder: {str(e)}", "red")
        
        # Log completion with success icon
        if uploaded > 0:
            log_success(f"Completed {source_name} processing. Uploaded: {uploaded} files")
        else:
            log_success(f"Completed {source_name} processing. No new files to upload")
        return uploaded, last_uploaded_file
    
    def toggle_monitoring(self):
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        if not self.validate_settings():
            return
        
        if not self.garmin_client:
            if not self.login_garmin():
                return
        
        logger.info(f"Starting auto-sync monitoring (interval: {self.check_interval//60} minutes)")
        self.is_monitoring = True
        self.monitor_button.config(text="Stop Auto-Sync")
        self.sync_button.config(state='disabled')
        self.update_status("Auto-sync started (checking every 5 minutes)", "green")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        logger.info("Stopping auto-sync monitoring")
        self.is_monitoring = False
        self.monitor_button.config(text="Start Auto-Sync")
        self.sync_button.config(state='normal')
        self.update_status("Auto-sync stopped", "blue")
    
    def _monitor_loop(self):
        while self.is_monitoring:
            self._sync_files()
            
            # Wait using check_interval
            for _ in range(self.check_interval):
                if not self.is_monitoring:
                    break
                time.sleep(1)
    
    def update_status(self, message, color="blue"):
        # Add colored icons based on status type
        icon = ""
        if color == "green":
            icon = "✅ "  # Success
        elif color == "red":
            icon = "❌ "  # Error
        elif color == "orange":
            icon = "🔄 "  # In progress
        elif color == "blue":
            icon = "ℹ️ "  # Info
        
        self.status_label.config(text=f"Status: {icon}{message}", foreground=color)
        self.root.update_idletasks()
    
    def on_closing(self):
        """Handle window close - check for unsaved changes and minimize to tray if monitoring"""
        # Check for unsaved settings first
        if self.settings_changed:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved settings changes.\n\nDo you want to save them before closing?"
            )
            if response is None:  # Cancel
                return
            elif response:  # Yes - save
                self.save_settings()
        
        # Then handle minimize to tray if monitoring
        if self.is_monitoring:
            response = messagebox.askyesno(
                "Minimize to Tray?",
                "Auto-sync is currently running.\n\n• Click YES to minimize to system tray (keeps running in background)\n• Click NO to stop auto-sync and close the app\n\nTip: Look for the Garmin icon in your system tray (bottom-right corner)"
            )
            if response:
                self.root.withdraw()  # Hide window
                self.create_tray_icon()
                self.update_status("Running in system tray", "green")
            else:
                self.quit_app()
        else:
            self.quit_app()
    
    def create_tray_icon(self):
        """Create system tray icon"""
        if self.tray_icon:
            return  # Already created
        
        try:
            # Load icon image
            if os.path.exists(LOGO_PATH):
                icon_image = Image.open(LOGO_PATH)
            else:
                # Create a simple default icon if logo not found
                icon_image = Image.new('RGB', (64, 64), color='blue')
            
            # Create menu
            menu = Menu(
                MenuItem('Show Window', self.show_window),
                MenuItem('Sync Now', self.tray_sync_now),
                MenuItem('Exit', self.quit_app)
            )
            
            # Create tray icon
            self.tray_icon = Icon("GarminUploader", icon_image, "Garmin Uploader", menu)
            
            # Run in separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"Could not create tray icon: {e}")
    
    def show_window(self, icon=None, item=None):
        """Show the main window from tray"""
        self.root.deiconify()  # Show window
        self.root.lift()  # Bring to front
    
    def tray_sync_now(self, icon=None, item=None):
        """Trigger sync from tray menu"""
        threading.Thread(target=self._sync_files, daemon=True).start()
    
    def quit_app(self, icon=None, item=None):
        """Quit the application completely"""
        if self.is_monitoring:
            self.stop_monitoring()
        
        if self.tray_icon:
            self.tray_icon.stop()
        
        self.root.quit()
        self.root.destroy()
    
    def show_about(self):
        """Show About dialog with developer info"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About Garmin Connect Uploader")
        about_window.geometry("480x520")  # Increased height for more room
        about_window.resizable(False, False)
        
        # Center the window
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Content frame
        content = ttk.Frame(about_window, padding="20")
        content.pack(fill=tk.BOTH, expand=True)
        
        # App name and version
        ttk.Label(content, text="Garmin Connect Uploader", font=('Arial', 16, 'bold')).pack(pady=(0, 5))
        ttk.Label(content, text=f"Version {VERSION}", font=('Arial', 10)).pack(pady=(0, 15))
        
        # Description
        desc_text = "Automatically upload workout activities from Wahoo and MyWhoosh to Garmin Connect."
        ttk.Label(content, text=desc_text, wraplength=420, justify='center').pack(pady=(0, 15))
        
        # Developer info with logo
        ttk.Label(content, text="Developer", font=('Arial', 11, 'bold')).pack(pady=(10, 5))
        
        # Try to load developer logo
        dev_logo_path = os.path.join(BASE_DIR, "inc21.webp")
        if os.path.exists(dev_logo_path):
            try:
                dev_logo_img = Image.open(dev_logo_path)
                dev_logo_img.thumbnail((75, 75))  # Increased by 25% (60 -> 75)
                dev_logo_photo = ImageTk.PhotoImage(dev_logo_img)
                logo_label = ttk.Label(content, image=dev_logo_photo)
                logo_label.image = dev_logo_photo  # Keep reference
                logo_label.pack(pady=5)
            except:
                pass  # If fails, just skip the logo
        
        dev_frame = ttk.Frame(content)
        dev_frame.pack(pady=5)
        
        # GitHub link with logo
        github_frame = ttk.Frame(dev_frame)
        github_frame.pack(pady=5)
        
        # Try to load GitHub logo
        github_logo_path = os.path.join(BASE_DIR, "github_logo.png")
        if os.path.exists(github_logo_path):
            try:
                github_img = Image.open(github_logo_path)
                github_img.thumbnail((96, 96))  # Much larger - 3x bigger
                github_photo = ImageTk.PhotoImage(github_img)
                github_logo_label = ttk.Label(github_frame, image=github_photo, cursor='hand2')
                github_logo_label.image = github_photo  # Keep reference
                github_logo_label.pack()
                github_logo_label.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Inc21"))
            except:
                # Fallback to text if logo fails
                github_link = ttk.Label(
                    github_frame,
                    text="github.com/Inc21",
                    foreground='blue',
                    cursor='hand2',
                    font=('Arial', 9, 'underline')
                )
                github_link.pack()
                github_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/Inc21"))
        
        # Buttons frame
        btn_frame = ttk.Frame(content)
        btn_frame.pack(pady=10)
        
        # Buy Me a Coffee button with yellow background
        coffee_btn = tk.Button(
            btn_frame,
            text="☕ Buy me a coffee",
            command=lambda: webbrowser.open("https://buymeacoffee.com/inc21"),
            bg="#FFDD00",
            fg="black",
            font=('Arial', 9, 'bold'),
            cursor='hand2',
            relief=tk.RAISED,
            bd=2,
            padx=10,
            pady=5
        )
        coffee_btn.pack(side=tk.LEFT, padx=5)
        
        # View Log File button
        log_btn = ttk.Button(btn_frame, text="📄 View Log", command=self.open_log_file)
        log_btn.pack(side=tk.LEFT, padx=5)
        
        # Log file location
        ttk.Label(content, text=f"Log: {LOG_FILE}", font=('Arial', 7), foreground='gray', wraplength=420).pack(pady=(5, 15))
        
        # Close button - full width for better visibility
        close_btn = ttk.Button(content, text="Close", command=about_window.destroy, width=15)
        close_btn.pack(pady=(5, 0))
    
    def open_log_file(self):
        """Open the log file in the default text editor"""
        try:
            if os.path.exists(LOG_FILE):
                os.startfile(LOG_FILE)  # Windows-specific
                logger.info("Log file opened by user")
            else:
                messagebox.showinfo("Log File", f"Log file not found yet.\n\nIt will be created at:\n{LOG_FILE}\n\nonce you start using the app.")
        except Exception as e:
            logger.error(f"Failed to open log file: {str(e)}")
            messagebox.showerror("Error", f"Could not open log file:\n{str(e)}")

def main():
    logger.info(f"=" * 60)
    logger.info(f"Garmin Connect Uploader v{VERSION} - Starting")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"=" * 60)
    
    # Check if started from Windows Startup (minimized)
    import sys
    start_minimized = '--minimized' in sys.argv or '--startup' in sys.argv
    
    root = tk.Tk()
    app = ConnectUploaderGUI(root)
    
    # Auto-start monitoring if both settings are enabled and starting from startup
    if start_minimized:
        logger.info("Started from Windows Startup - checking auto-start settings")
        try:
            # Load config to check if auto-sync should start
            if app.config.get('start_with_windows') and os.path.exists(CONFIG_FILE):
                logger.info("Auto-start settings detected - starting monitoring and minimizing to tray")
                # Start monitoring if credentials are set
                if app.garmin_email.get() and app.garmin_password.get():
                    root.after(2000, lambda: app.start_monitoring() if not app.is_monitoring else None)
                    root.after(3000, lambda: root.withdraw())
                    root.after(3500, lambda: app.create_tray_icon())
        except Exception as e:
            logger.error(f"Error during startup auto-start: {str(e)}")
    
    try:
        root.mainloop()
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
    finally:
        logger.info("Garmin Connect Uploader - Shutting down")
        logger.info(f"=" * 60)

if __name__ == "__main__":
    main()
