import sys
import os
import subprocess
import json
import shutil
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QCheckBox, QMessageBox, QProgressBar
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
AE_NUX_DIR = os.path.expanduser('~/cutefishaep/AeNux')
PLUGIN_DIR = os.path.join(AE_NUX_DIR, "Plug-ins")
PRESET_DIR = os.path.expanduser('~/Documents/Adobe/After Effects 2024/User Presets')


class InstallThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    cancelled = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            # Check if wget is available
            if not shutil.which('wget'):
                self.log_signal.emit("[ERROR] wget is not installed. Please install wget first.")
                self.finished_signal.emit(False)
                return

            self.log_signal.emit("[INFO] Installing AeNux...")
            self.progress_signal.emit(10)
            
            if self._is_cancelled:
                self._cleanup_partial_install()
                self.cancelled.emit()
                return
            
            # Download the file
            self.log_signal.emit("[DEBUG] Downloading AeNux package, around 1.3gb...")
            result = subprocess.run([
                'wget', '-O', '2024.zip', 
                'https://huggingface.co/cutefishae/AeNux-model/resolve/main/2024.zip'
            ], capture_output=True, text=True)
            
            if self._is_cancelled:
                self._cleanup_partial_install()
                self.cancelled.emit()
                return
            
            if result.returncode != 0:
                self.log_signal.emit(f"[ERROR] Download failed: {result.stderr}")
                self.finished_signal.emit(False)
                return
            
            self.log_signal.emit("[DEBUG] Download completed successfully")
            self.progress_signal.emit(40)
            
            if self._is_cancelled:
                self._cleanup_partial_install()
                self.cancelled.emit()
                return
            
            # Unzip the file
            self.log_signal.emit("[DEBUG] Extracting files...")
            result = subprocess.run([
                'unzip', '-o', '2024.zip', '-d', 'Ae2024'
            ], capture_output=True, text=True)
            
            if self._is_cancelled:
                self._cleanup_partial_install()
                self.cancelled.emit()
                return
            
            if result.returncode != 0:
                self.log_signal.emit(f"[ERROR] Extraction failed: {result.stderr}")
                self.finished_signal.emit(False)
                return
            
            self.log_signal.emit("[DEBUG] Extraction completed")
            self.progress_signal.emit(60)
            
            # Remove zip file
            self.log_signal.emit("[DEBUG] Cleaning up temporary files...")
            if os.path.exists('2024.zip'):
                os.remove('2024.zip')
            
            if self._is_cancelled:
                self._cleanup_partial_install()
                self.cancelled.emit()
                return
            
            # Create directory and copy files
            self.log_signal.emit(f"[DEBUG] Creating directory: {AE_NUX_DIR}")
            os.makedirs(AE_NUX_DIR, exist_ok=True)
            self.progress_signal.emit(70)
            
            source_dir = 'Ae2024/Support Files'
            if os.path.exists(source_dir):
                self.log_signal.emit("[DEBUG] Copying files to installation directory...")
                
                # Copy files using Python instead of subprocess for better reliability
                for item in os.listdir(source_dir):
                    if self._is_cancelled:
                        self._cleanup_partial_install()
                        self.cancelled.emit()
                        return
                        
                    src_path = os.path.join(source_dir, item)
                    dst_path = os.path.join(AE_NUX_DIR, item)
                    
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src_path, dst_path)
                
                self.log_signal.emit("[DEBUG] Files copied successfully")
                self.progress_signal.emit(90)
            else:
                self.log_signal.emit(f"[ERROR] Source directory '{source_dir}' not found after extraction")
                self.finished_signal.emit(False)
                return
            
            if self._is_cancelled:
                self._cleanup_partial_install()
                self.cancelled.emit()
                return
            
            # Clean up extraction directory
            self.log_signal.emit("[DEBUG] Final cleanup...")
            if os.path.exists('Ae2024'):
                shutil.rmtree('Ae2024')
            
            self.progress_signal.emit(100)
            self.log_signal.emit("[INFO] AeNux installation completed successfully!")
            self.finished_signal.emit(True)
            
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Installation failed: {str(e)}")
            self.finished_signal.emit(False)

    def _cleanup_partial_install(self):
        """Clean up partially installed files"""
        self.log_signal.emit("[CANCEL] Cleaning up partially installed files...")
        
        # Remove downloaded zip if exists
        if os.path.exists('2024.zip'):
            os.remove('2024.zip')
            self.log_signal.emit("[CANCEL] Removed downloaded zip file")
        
        # Remove extraction directory if exists
        if os.path.exists('Ae2024'):
            shutil.rmtree('Ae2024')
            self.log_signal.emit("[CANCEL] Removed extraction directory")
        
        # Remove partially installed AeNux directory if empty or nearly empty
        if os.path.exists(AE_NUX_DIR):
            try:
                contents = os.listdir(AE_NUX_DIR)
                if len(contents) < 5:  # If very few files, likely incomplete install
                    shutil.rmtree(AE_NUX_DIR)
                    self.log_signal.emit("[CANCEL] Removed partially installed AeNux directory")
            except OSError:
                pass


class PatchThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    cancelled = pyqtSignal()

    def __init__(self, runner_path, wineprefix_path):
        super().__init__()
        self.runner_path = runner_path
        self.wineprefix_path = wineprefix_path
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            self.log_signal.emit("[INFO] Starting AeNux patch application...")
            self.progress_signal.emit(10)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            # Set environment variables
            env = os.environ.copy()
            env['WINEPREFIX'] = self.wineprefix_path
            
            # Get paths to wine and wineserver
            wine_path = os.path.join(self.runner_path, "bin", "wine")
            wineserver_path = os.path.join(self.runner_path, "bin", "wineserver")
            winetricks_path = os.path.join(os.path.dirname(__file__), "winetricks")
            
            # Check if required tools exist
            if not os.path.exists(wine_path):
                self.log_signal.emit(f"[ERROR] Wine not found at: {wine_path}")
                self.finished_signal.emit(False)
                return
                
            if not os.path.exists(winetricks_path):
                self.log_signal.emit(f"[ERROR] Winetricks not found at: {winetricks_path}")
                self.finished_signal.emit(False)
                return

            self.log_signal.emit("[DEBUG] Checking dependencies...")
            self.progress_signal.emit(20)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            # Check for cabextract
            if not shutil.which('cabextract'):
                self.log_signal.emit("[ERROR] cabextract is not installed. Please install cabextract first.")
                self.finished_signal.emit(False)
                return

            # Check if wineprefix already exists
            if os.path.exists(self.wineprefix_path):
                self.log_signal.emit("[WARNING] Wineprefix already exists. It will be used as-is.")
            else:
                self.log_signal.emit("[DEBUG] Initializing wineprefix...")
                result = subprocess.run([wine_path, "--version"], env=env, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log_signal.emit(f"[ERROR] Wine initialization failed: {result.stderr}")
                    self.finished_signal.emit(False)
                    return
                self.log_signal.emit(f"[DEBUG] Wine version: {result.stdout.strip()}")

            self.progress_signal.emit(30)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            # Configure registry and visual settings
            self.log_signal.emit("[DEBUG] Configuring registry and visual settings...")
            
            # Disable Windows theme
            subprocess.run([wine_path, "reg", "add", "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ThemeManager", 
                          "/v", "ThemeActive", "/t", "REG_SZ", "/d", "0", "/f"], env=env)
            
            # Create and import registry file for colors
            reg_file = os.path.join(os.path.dirname(__file__), "aenux-colors.reg")
            reg_content = """Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Control Panel\\Colors]
"ActiveBorder"="49 54 58"
"ActiveTitle"="49 54 58"
"AppWorkSpace"="60 64 72"
"Background"="49 54 58"
"ButtonAlternativeFace"="200 0 0"
"ButtonDkShadow"="154 154 154"
"ButtonFace"="49 54 58"
"ButtonHilight"="119 126 140"
"ButtonLight"="60 64 72"
"ButtonShadow"="60 64 72"
"ButtonText"="219 220 222"
"GradientActiveTitle"="49 54 58"
"GradientInactiveTitle"="49 54 58"
"GrayText"="155 155 155"
"Hilight"="119 126 140"
"HilightText"="255 255 255"
"InactiveBorder"="49 54 58"
"InactiveTitle"="49 54 58"
"InactiveTitleText"="219 220 222"
"InfoText"="159 167 180"
"InfoWindow"="49 54 58"
"Menu"="49 54 58"
"MenuBar"="49 54 58"
"MenuHilight"="119 126 140"
"MenuText"="219 220 222"
"Scrollbar"="73 78 88"
"TitleText"="219 220 222"
"Window"="35 38 41"
"WindowFrame"="49 54 58"
"WindowText"="219 220 222"
"""
            with open(reg_file, 'w') as f:
                f.write(reg_content)
            
            subprocess.run([wine_path, "regedit", reg_file], env=env)
            os.remove(reg_file)
            
            # Kill wineserver to apply changes
            subprocess.run([wineserver_path, "-k"], env=env)
            
            self.progress_signal.emit(50)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            # Run winetricks
            self.log_signal.emit("[DEBUG] Running winetricks...")
            subprocess.run([winetricks_path, "-q", "dxvk", "corefonts", "gdiplus", "fontsmooth=rgb"], env=env)
            
            # Run VCR install if available
            vcr_bat = os.path.join(os.path.dirname(__file__), "asset", "vcr", "install_all.bat")
            if os.path.exists(vcr_bat):
                self.log_signal.emit("[DEBUG] Installing VCR dependencies...")
                subprocess.run([wine_path, vcr_bat], env=env)
            else:
                self.log_signal.emit("[WARNING] VCR install_all.bat not found, skipping...")

            self.progress_signal.emit(70)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            # Create shortcuts to Linux folders
            self.log_signal.emit("[DEBUG] Creating shortcuts to Linux folders...")
            wine_drive_c = os.path.join(self.wineprefix_path, "drive_c")
            fav_dir = os.path.join(wine_drive_c, "users", "*", "Favorites")
            
            # Find the first Favorites directory that exists
            import glob
            fav_paths = glob.glob(fav_dir)
            if fav_paths:
                target_fav_dir = fav_paths[0]
                
                # Remove existing symlinks
                for folder in ["Documents", "Downloads", "Pictures", "Videos", "Music"]:
                    link_path = os.path.join(target_fav_dir, folder)
                    if os.path.exists(link_path):
                        os.remove(link_path)
                
                # Create new symlinks
                home_dir = os.path.expanduser("~")
                os.symlink(os.path.join(home_dir, "Documents"), os.path.join(target_fav_dir, "Documents"))
                os.symlink(os.path.join(home_dir, "Downloads"), os.path.join(target_fav_dir, "Downloads"))
                os.symlink(os.path.join(home_dir, "Pictures"), os.path.join(target_fav_dir, "Pictures"))
                os.symlink(os.path.join(home_dir, "Videos"), os.path.join(target_fav_dir, "Videos"))
                os.symlink(os.path.join(home_dir, "Music"), os.path.join(target_fav_dir, "Music"))
                os.symlink(AE_NUX_DIR, os.path.join(target_fav_dir, "AeNux"))
                
                subprocess.run([wineserver_path, "-k"], env=env)
            else:
                self.log_signal.emit("[WARNING] Favorites directory not found, skipping shortcuts...")

            self.progress_signal.emit(85)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            # Override DLL MSXML3
            self.log_signal.emit("[DEBUG] Overriding MSXML3 DLL...")
            system32_dir = os.path.join(wine_drive_c, "windows", "system32")
            
            if os.path.exists(system32_dir):
                msxml3_src = os.path.join(os.path.dirname(__file__), "asset", "System32", "msxml3.dll")
                if os.path.exists(msxml3_src):
                    shutil.copy2(msxml3_src, os.path.join(system32_dir, "msxml3.dll"))
                    shutil.copy2(msxml3_src, os.path.join(system32_dir, "msxml3r.dll"))
                    
                    # Set DLL override
                    subprocess.run([wine_path, "reg", "add", "HKCU\\Software\\Wine\\DllOverrides", 
                                  "/v", "msxml3", "/d", "native,builtin", "/f"], env=env)
                else:
                    self.log_signal.emit("[WARNING] msxml3.dll not found in asset/System32/, skipping...")
            else:
                self.log_signal.emit("[WARNING] System32 directory not found, skipping DLL override...")

            self.progress_signal.emit(100)
            self.log_signal.emit("[INFO] AeNux patch applied successfully!")
            self.finished_signal.emit(True)
            
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Patch application failed: {str(e)}")
            self.finished_signal.emit(False)


class AeNuxApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AeNux")
        self.resize(520, 350)
        self.config = self._load_config()
        self.install_thread = None
        self.patch_thread = None
        
        # Variabel untuk mencegah spam klik
        self.buttons_disabled = False
        self.button_cooldown_timer = QTimer()
        self.button_cooldown_timer.setSingleShot(True)
        self.button_cooldown_timer.timeout.connect(self._enable_buttons)
        
        # Simpan referensi tombol utama
        self.main_buttons = []

        icon_path = os.path.join(os.path.dirname(__file__), "asset/logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        root = QVBoxLayout(self)
        
        # Status row
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Checking...")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        self.install_button = QPushButton("Install")
        self.install_button.clicked.connect(self._install_aenux)
        status_row.addWidget(self.install_button)
        self.main_buttons.append(self.install_button)
        
        self.uninstall_button = QPushButton("Uninstall")
        self.uninstall_button.clicked.connect(self._uninstall_aenux)
        self.uninstall_button.hide()
        status_row.addWidget(self.uninstall_button)
        self.main_buttons.append(self.uninstall_button)
        root.addLayout(status_row)

        # Logs
        root.addWidget(QLabel("Logs:"))
        self.logs_box = QTextEdit()
        self.logs_box.setReadOnly(True)
        self.logs_box.setFixedHeight(140)
        root.addWidget(self.logs_box)

        # Progress Bar with Cancel button
        progress_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        progress_layout.addWidget(self.progress_bar)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self._cancel_operation)
        self.cancel_button.setStyleSheet("QPushButton { background-color: #ff6b6b; color: white; }")
        progress_layout.addWidget(self.cancel_button)
        self.main_buttons.append(self.cancel_button)
        
        root.addLayout(progress_layout)

        # Runner row
        runner_row = QHBoxLayout()
        runner_row.addWidget(QLabel("Runner:"))
        self.runner_dropdown = QComboBox()
        runner_row.addWidget(self.runner_dropdown)
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.clicked.connect(self._refresh_runner_list)
        runner_row.addWidget(self.btn_refresh)
        self.main_buttons.append(self.btn_refresh)
        
        root.addLayout(runner_row)

        # Checkboxes
        self.umu_checkbox = QCheckBox("Use Umu Launcher")
        self.patch_checkbox = QCheckBox("Apply AeNux Patch")
        cb_row = QHBoxLayout()
        cb_row.addWidget(self.umu_checkbox)
        cb_row.addWidget(self.patch_checkbox)
        root.addLayout(cb_row)

        # Execution buttons
        exec_row = QHBoxLayout()
        self.btn_run = QPushButton("Run AeNux")
        self.btn_kill = QPushButton("Kill AeNux")
        self.btn_run.clicked.connect(self._run_aenux)
        self.btn_kill.clicked.connect(self._kill_aenux)
        exec_row.addWidget(self.btn_run)
        exec_row.addWidget(self.btn_kill)
        self.main_buttons.extend([self.btn_run, self.btn_kill])
        root.addLayout(exec_row)

        # Folders
        folder_row = QHBoxLayout()
        self.folder_buttons = []
        for name in ["Runner", "Plugin", "Preset", "AeNux"]:
            btn = QPushButton(f"{name} Folder")
            btn.clicked.connect(lambda checked, n=name.lower(): self._open_folder(n))
            folder_row.addWidget(btn)
            self.folder_buttons.append(btn)
        self.main_buttons.extend(self.folder_buttons)
        root.addLayout(folder_row)

        # Footer
        footer = QLabel('Made with ❤️ by cutefishaep')
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(footer)

        # populate and apply config
        self._populate_runner_dropdown()
        self.runner_dropdown.currentIndexChanged.connect(self._runner_changed)
        self.umu_checkbox.stateChanged.connect(self._umu_checkbox_changed)
        self.patch_checkbox.stateChanged.connect(self._patch_checkbox_changed)

        self._apply_saved_config()
        self._check_installation_status()

    def _disable_buttons_temporarily(self, duration=1500):
        """Nonaktifkan sementara semua tombol utama"""
        if self.buttons_disabled:
            return
            
        self.buttons_disabled = True
        for button in self.main_buttons:
            button.setEnabled(False)
        
        # Juga nonaktifkan dropdown dan checkbox
        self.runner_dropdown.setEnabled(False)
        self.umu_checkbox.setEnabled(False)
        self.patch_checkbox.setEnabled(False)
        
        self.button_cooldown_timer.start(duration)

    def _enable_buttons(self):
        """Aktifkan kembali semua tombol"""
        self.buttons_disabled = False
        for button in self.main_buttons:
            button.setEnabled(True)
        
        # Aktifkan kembali dropdown dan checkbox dengan logika yang benar
        self.runner_dropdown.setEnabled(True)
        self._update_checkbox_states()

    def _update_checkbox_states(self):
        """Update status checkbox berdasarkan runner yang dipilih"""
        runner = self.runner_dropdown.currentText()
        if "proton" in runner.lower():
            self.umu_checkbox.setEnabled(False)
            self.patch_checkbox.setEnabled(False)
        else:
            self.umu_checkbox.setEnabled(True)
            self.patch_checkbox.setEnabled(True)

    def _cancel_operation(self):
        """Cancel the ongoing operation (install or patch)"""
        if self.buttons_disabled:
            return
            
        self._disable_buttons_temporarily(1000)
        
        if self.install_thread and self.install_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Cancel",
                "Are you sure you want to cancel the installation? Partially installed files will be cleaned up.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.install_thread.cancel()
                self.logs_box.append("[USER] Installation cancelled by user.")
                self.cancel_button.setVisible(False)
                self.progress_bar.setVisible(False)
                self.install_button.setEnabled(True)
                self.install_button.setText("Install")
        
        elif self.patch_thread and self.patch_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Confirm Cancel", 
                "Are you sure you want to cancel the patch application?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.patch_thread.cancel()
                self.logs_box.append("[USER] Patch application cancelled by user.")
                self.cancel_button.setVisible(False)
                self.progress_bar.setVisible(False)

    def _create_shortcut(self):
        """Create desktop shortcut and icon"""
        try:
            # Get current directory (where the script is located)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Create icons directory
            icons_dir = os.path.expanduser("~/.local/share/icons")
            os.makedirs(icons_dir, exist_ok=True)
            
            # Copy icon
            icon_src = os.path.join(current_dir, "asset", "logo.png")
            icon_dst = os.path.join(icons_dir, "AeNux.png")
            if os.path.exists(icon_src):
                shutil.copy2(icon_src, icon_dst)
                self.logs_box.append("[SHORTCUT] Icon copied successfully.")
            else:
                self.logs_box.append("[WARNING] Logo icon not found, skipping icon copy.")
            
            # Create desktop entry
            applications_dir = os.path.expanduser("~/.local/share/applications")
            os.makedirs(applications_dir, exist_ok=True)
            
            desktop_file = os.path.join(applications_dir, "AeNux.desktop")
            
            # Check if run_qt6.py exists in current directory
            run_script = os.path.join(current_dir, "run_qt6.py")
            if not os.path.exists(run_script):
                self.logs_box.append("[ERROR] run_qt6.py not found in current directory!")
                return False
            
            # Use absolute paths instead of $PWD
            venv_python = os.path.join(current_dir, "venv", "bin", "python")
            
            # Check if venv python exists, if not use system python
            if not os.path.exists(venv_python):
                venv_python = "python3"
                self.logs_box.append("[INFO] Using system python instead of venv")
            
            desktop_content = f"""[Desktop Entry]
Name=AeNux Loader
Comment=Run AeNux using Wine
Exec={venv_python} {run_script}
Path={current_dir}
Type=Application
Icon=AeNux
Terminal=false
Categories=AudioVideo;Video;
"""
            
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            # Make desktop file executable
            os.chmod(desktop_file, 0o755)
            
            # Update desktop database
            subprocess.run(["update-desktop-database", applications_dir], capture_output=True)
            
            self.logs_box.append("[SHORTCUT] Desktop shortcut created successfully with absolute paths.")
            return True
            
        except Exception as e:
            self.logs_box.append(f"[ERROR] Failed to create shortcut: {str(e)}")
            return False

    def _remove_shortcut(self):
        """Remove desktop shortcut and icon"""
        try:
            # Remove icon
            icon_path = os.path.expanduser("~/.local/share/icons/AeNux.png")
            if os.path.exists(icon_path):
                os.remove(icon_path)
                self.logs_box.append("[SHORTCUT] Icon removed.")
            
            # Remove desktop entry
            desktop_file = os.path.expanduser("~/.local/share/applications/AeNux.desktop")
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
                self.logs_box.append("[SHORTCUT] Desktop shortcut removed.")
            
            # Update desktop database
            applications_dir = os.path.expanduser("~/.local/share/applications")
            subprocess.run(["update-desktop-database", applications_dir], capture_output=True)
            
            return True
            
        except Exception as e:
            self.logs_box.append(f"[ERROR] Failed to remove shortcut: {str(e)}")
            return False

    def _check_installation_status(self):
        """Check if AeNux is installed"""
        if os.path.exists(AE_NUX_DIR):
            try:
                contents = [f for f in os.listdir(AE_NUX_DIR) if not f.startswith('.')]
                if contents:
                    self.status_label.setText("AeNux installed")
                    self.install_button.hide()
                    self.uninstall_button.show()
                    self.logs_box.append("[STATUS] AeNux is installed and ready to use.")
                    return
            except OSError:
                pass
        
        self.status_label.setText("AeNux is not installed")
        self.install_button.show()
        self.uninstall_button.hide()
        self.logs_box.append("[STATUS] AeNux is not installed. Click Install to proceed.")

    def _install_aenux(self):
        """Install AeNux"""
        if self.buttons_disabled:
            return
            
        if self.install_thread and self.install_thread.isRunning():
            self.logs_box.append("[INFO] Installation already in progress...")
            return

        reply = QMessageBox.question(
            self, 
            "Confirm Installation", 
            f"This will install AeNux to {AE_NUX_DIR}. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._disable_buttons_temporarily(500)  # Cooldown pendek untuk feedback
            self.install_button.setEnabled(False)
            self.install_button.setText("Installing...")
            self.progress_bar.setVisible(True)
            self.cancel_button.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.install_thread = InstallThread()
            self.install_thread.log_signal.connect(self.logs_box.append)
            self.install_thread.progress_signal.connect(self.progress_bar.setValue)
            self.install_thread.finished_signal.connect(self._installation_finished)
            self.install_thread.cancelled.connect(self._installation_cancelled)
            self.install_thread.start()

    def _uninstall_aenux(self):
        """Uninstall AeNux - FIXED: Only remove AeNux folder, not entire cutefishaep"""
        if self.buttons_disabled:
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Uninstall",
            "This will remove AeNux and all its data including wineprefix and shortcuts. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._disable_buttons_temporarily(2000)
            try:
                # Remove AeNux directory ONLY (not the entire cutefishaep folder)
                if os.path.exists(AE_NUX_DIR):
                    shutil.rmtree(AE_NUX_DIR)
                    self.logs_box.append("[UNINSTALL] AeNux directory removed.")
                
                # Remove wineprefix
                wineprefix_path = os.path.join(os.path.dirname(__file__), "aenux", "wineprefix")
                if os.path.exists(wineprefix_path):
                    shutil.rmtree(wineprefix_path)
                    self.logs_box.append("[UNINSTALL] Wineprefix removed.")
                
                # Remove shortcuts
                self._remove_shortcut()
                
                # Clear logs
                self.logs_box.clear()
                
                # Update status
                self._check_installation_status()
                self.logs_box.append("[UNINSTALL] AeNux has been completely uninstalled.")
                
            except Exception as e:
                self.logs_box.append(f"[ERROR] Uninstall failed: {str(e)}")
                QMessageBox.critical(self, "Uninstall Error", f"Failed to uninstall AeNux: {str(e)}")

    def _installation_finished(self, success):
        """Handle installation completion"""
        self.buttons_disabled = False
        self._enable_buttons()
        
        self.install_button.setEnabled(True)
        self.install_button.setText("Install")
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        
        if success:
            # Create desktop shortcut
            self._create_shortcut()
            
            import time
            time.sleep(0.5)
            self._check_installation_status()
        else:
            self.logs_box.append("[ERROR] Installation failed. Please check the logs above.")

    def _installation_cancelled(self):
        """Handle installation cancellation"""
        self.buttons_disabled = False
        self._enable_buttons()
        
        self.install_button.setEnabled(True)
        self.install_button.setText("Install")
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.logs_box.append("[INFO] Installation was cancelled and cleaned up.")

    def _check_wineprefix(self):
        """Check if wineprefix exists"""
        wineprefix_path = os.path.join(os.path.dirname(__file__), "aenux", "wineprefix")
        return os.path.exists(wineprefix_path)

    def _run_aenux(self):
        """Run AeNux with optional patch"""
        if self.buttons_disabled:
            return
            
        # Check if installed first
        if not os.path.exists(AE_NUX_DIR) or not any(not f.startswith('.') for f in os.listdir(AE_NUX_DIR)):
            QMessageBox.warning(self, "Not Installed", "Please install AeNux first before running.")
            return

        # Check if runner is selected
        runner = self.runner_dropdown.currentText()
        if runner.lower().startswith("select") or runner.lower() == "no runners found":
            QMessageBox.warning(self, "No Runner Selected", "Please select a runner first.")
            return

        afterfx_path = os.path.join(AE_NUX_DIR, "AfterFX.exe")
        if not os.path.exists(afterfx_path):
            QMessageBox.warning(self, "AfterFX Not Found", f"AfterFX.exe not found at: {afterfx_path}")
            return

        # Get paths
        runner_path = os.path.join(os.path.dirname(__file__), "runner", runner)
        wineprefix_path = os.path.join(os.path.dirname(__file__), "aenux", "wineprefix")
        
        # Create wineprefix directory if it doesn't exist
        os.makedirs(wineprefix_path, exist_ok=True)

        if self.patch_checkbox.isChecked():
            # Apply patch first, then run AfterFX
            self._disable_buttons_temporarily(1000)
            self.logs_box.append("[INFO] Applying AeNux patch before running...")
            self.progress_bar.setVisible(True)
            self.cancel_button.setVisible(True)
            self.progress_bar.setValue(0)
            
            self.patch_thread = PatchThread(runner_path, wineprefix_path)
            self.patch_thread.log_signal.connect(self.logs_box.append)
            self.patch_thread.progress_signal.connect(self.progress_bar.setValue)
            self.patch_thread.finished_signal.connect(lambda success: self._patch_finished(success, runner_path, wineprefix_path, afterfx_path))
            self.patch_thread.cancelled.connect(self._patch_cancelled)
            self.patch_thread.start()
        else:
            # Run AfterFX directly without patch
            self._disable_buttons_temporarily(1000)
            self._run_afterfx(runner_path, wineprefix_path, afterfx_path)

    def _patch_finished(self, success, runner_path, wineprefix_path, afterfx_path):
        """Handle patch completion"""
        self.buttons_disabled = False
        self._enable_buttons()
        
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        # Uncheck the patch checkbox after patch is completed
        self.patch_checkbox.setChecked(False)
        
        if success:
            self.logs_box.append("[INFO] Patch applied successfully, now running AfterFX...")
            self._run_afterfx(runner_path, wineprefix_path, afterfx_path)
        else:
            self.logs_box.append("[ERROR] Patch failed. AfterFX will not be run.")

    def _patch_cancelled(self):
        """Handle patch cancellation"""
        self.buttons_disabled = False
        self._enable_buttons()
        
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.patch_checkbox.setChecked(False)
        self.logs_box.append("[INFO] Patch application was cancelled.")

    def _run_afterfx(self, runner_path, wineprefix_path, afterfx_path):
        """Run AfterFX.exe with the selected runner"""
        try:
            wine_path = os.path.join(runner_path, "bin", "wine")
            
            # Set environment
            env = os.environ.copy()
            env['WINEPREFIX'] = wineprefix_path
            
            self.logs_box.append(f"[RUN] Starting AfterFX.exe with {os.path.basename(runner_path)}...")
            
            # Run AfterFX
            if self.umu_checkbox.isChecked():
                # Use Umu Launcher if enabled
                umu_path = os.path.join(os.path.dirname(__file__), "umu", "umu-run.sh")
                if os.path.exists(umu_path):
                    subprocess.Popen([umu_path, wine_path, afterfx_path], env=env)
                    self.logs_box.append("[RUN] AfterFX started with Umu Launcher.")
                else:
                    subprocess.Popen([wine_path, afterfx_path], env=env)
                    self.logs_box.append("[RUN] AfterFX started with Wine (Umu not found).")
            else:
                # Direct Wine execution
                subprocess.Popen([wine_path, afterfx_path], env=env)
                self.logs_box.append("[RUN] AfterFX started with Wine.")
                
        except Exception as e:
            self.logs_box.append(f"[ERROR] Failed to run AfterFX: {str(e)}")
            QMessageBox.critical(self, "Execution Error", f"Failed to run AfterFX: {str(e)}")

    def _kill_aenux(self):
        """Kill AeNux processes"""
        if self.buttons_disabled:
            return
            
        self._disable_buttons_temporarily(1000)
        try:
            # Kill wine processes
            subprocess.run(["pkill", "-f", "AfterFX.exe"])
            subprocess.run(["pkill", "-f", "wine"])
            subprocess.run(["pkill", "-f", "wineserver"])
            self.logs_box.append("[KILL] AeNux processes terminated.")
        except Exception as e:
            self.logs_box.append(f"[ERROR] Failed to kill processes: {str(e)}")

    def _load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_config(self):
        config = {
            "runner": self.runner_dropdown.currentText(),
            "use_umu": self.umu_checkbox.isChecked()
        }
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    def _apply_saved_config(self):
        if "runner" in self.config:
            idx = self.runner_dropdown.findText(self.config["runner"])
            if idx >= 0:
                self.runner_dropdown.setCurrentIndex(idx)
        if "use_umu" in self.config:
            self.umu_checkbox.setChecked(self.config["use_umu"])

    def _populate_runner_dropdown(self):
        self.runner_dropdown.clear()
        self.runner_dropdown.addItem("Select your runner")
        path = os.path.join(os.path.dirname(__file__), "runner")
        try:
            dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
            if dirs:
                self.runner_dropdown.addItems(dirs)
            else:
                self.runner_dropdown.addItem("No runners found")
        except FileNotFoundError:
            self.runner_dropdown.addItem("No runners found")

    def _runner_changed(self, index):
        runner = self.runner_dropdown.currentText()
        if runner.lower().startswith("select"):
            self.umu_checkbox.setEnabled(True)
            self.umu_checkbox.setChecked(False)
            self.patch_checkbox.setEnabled(True)
            return

        if "proton" in runner.lower():
            # For Proton runners
            self.umu_checkbox.setChecked(True)
            self.umu_checkbox.setEnabled(False)
            self.patch_checkbox.setChecked(False)
            self.patch_checkbox.setEnabled(False)
            self.logs_box.append(f"[AUTO] Detected Proton runner → Umu Launcher enabled (required).")
            self.logs_box.append(f"[INFO] AeNux Patch is not available for Proton runners.")
        else:
            # For non-Proton runners
            self.umu_checkbox.setEnabled(False)
            self.umu_checkbox.setChecked(False)
            self.patch_checkbox.setEnabled(True)
            self.logs_box.append(f"[AUTO] Detected Wine runner → Umu Launcher disabled.")
        
        self._save_config()

    def _umu_checkbox_changed(self, state):
        if self.buttons_disabled:
            return
            
        if self.runner_dropdown.currentText().lower().startswith("select"):
            return
        if state == Qt.CheckState.Checked.value:
            if "proton" not in self.runner_dropdown.currentText().lower():
                QMessageBox.warning(
                    self, "Warning",
                    "Only turn this on if you're using Proton GE instead of wine."
                )
            self.logs_box.append("[OPTION] Use Umu Launcher: ENABLED")
        else:
            self.logs_box.append("[OPTION] Use Umu Launcher: DISABLED")
        self._save_config()

    def _patch_checkbox_changed(self, state):
        if self.buttons_disabled:
            return
            
        if state == Qt.CheckState.Checked.value:
            # Check if wineprefix already exists
            if self._check_wineprefix():
                QMessageBox.warning(
                    self, "Wineprefix Exists",
                    "Wineprefix already exists, please remove it first before running patch!"
                )
                self.patch_checkbox.setChecked(False)
                return
            
            self.logs_box.append("[OPTION] Apply AeNux Patch: ENABLED")
        else:
            self.logs_box.append("[OPTION] Apply AeNux Patch: DISABLED")

    def _refresh_runner_list(self):
        if self.buttons_disabled:
            return
            
        self._disable_buttons_temporarily(1000)
        self.logs_box.append("[INFO] Refreshing runner list...")
        self._populate_runner_dropdown()

    def _open_folder(self, name):
        if self.buttons_disabled:
            return
            
        self._disable_buttons_temporarily(1000)
        
        if name == "aenux":
            path = AE_NUX_DIR
            if not os.path.exists(path):
                QMessageBox.warning(self, "Not Installed", "You need to install AeNux first")
                return
        elif name == "plugin":
            path = PLUGIN_DIR
            if not os.path.exists(AE_NUX_DIR):
                QMessageBox.warning(self, "Not Installed", "You need to install AeNux first")
                return
            os.makedirs(path, exist_ok=True)
        elif name == "preset":
            path = PRESET_DIR
            if not os.path.exists(AE_NUX_DIR):
                QMessageBox.warning(self, "Not Installed", "You need to install AeNux first")
                return
            os.makedirs(path, exist_ok=True)
        else:
            path = os.path.join(os.path.dirname(__file__), name)
            os.makedirs(path, exist_ok=True)
        
        try:
            subprocess.Popen(["xdg-open", path])
        except Exception:
            pass
        self.logs_box.append(f"[OPEN] {name} folder opened.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AeNuxApp()
    win.show()
    sys.exit(app.exec())