import sys
import os
import subprocess
import json
import shutil
import glob
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QCheckBox, QMessageBox, QProgressBar, QFileDialog
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

# Constants
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
AE_NUX_DIR = os.path.expanduser('~/cutefishaep/AeNux')
PLUGIN_DIR = os.path.join(AE_NUX_DIR, "Plug-ins")
PRESET_DIR = os.path.expanduser('~/Documents/Adobe/After Effects 2024/User Presets')
WINE_PREFIX_DIR = os.path.join(os.path.dirname(__file__), "aenux", "wineprefix")


class InstallThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    cancelled = pyqtSignal()

    def __init__(self, zip_file_path=None):
        super().__init__()
        self._is_cancelled = False
        self.zip_file_path = zip_file_path

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            self.log_signal.emit("[INFO] Installing AeNux from local file...")
            self.progress_signal.emit(10)
            
            if not os.path.exists(self.zip_file_path):
                self.log_signal.emit(f"[ERROR] Local file not found: {self.zip_file_path}")
                self.finished_signal.emit(False)
                return
            
            # Copy local file to current directory
            self.log_signal.emit("[DEBUG] Copying local file...")
            shutil.copy2(self.zip_file_path, '2024.zip')
            self.progress_signal.emit(40)
            
            if self._is_cancelled:
                self._cleanup_partial_install()
                self.cancelled.emit()
                return
            
            # Extract files
            self.log_signal.emit("[DEBUG] Extracting files...")
            result = subprocess.run(['unzip', '-o', '2024.zip', '-d', 'Ae2024'], 
                                  capture_output=True, text=True)
            
            if self._is_cancelled:
                self._cleanup_partial_install()
                self.cancelled.emit()
                return
            
            if result.returncode != 0:
                self.log_signal.emit(f"[ERROR] Extraction failed: {result.stderr}")
                self.finished_signal.emit(False)
                return
            
            self.progress_signal.emit(60)
            
            # Clean up zip file
            if os.path.exists('2024.zip'):
                os.remove('2024.zip')
            
            if self._is_cancelled:
                self._cleanup_partial_install()
                self.cancelled.emit()
                return
            
            # Create directory and copy files
            os.makedirs(AE_NUX_DIR, exist_ok=True)
            self.progress_signal.emit(70)
            
            source_dir = 'Ae2024/Support Files'
            if os.path.exists(source_dir):
                self.log_signal.emit("[DEBUG] Copying files to installation directory...")
                
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
                
                self.progress_signal.emit(90)
            else:
                self.log_signal.emit(f"[ERROR] Source directory '{source_dir}' not found")
                self.finished_signal.emit(False)
                return
            
            if self._is_cancelled:
                self._cleanup_partial_install()
                self.cancelled.emit()
                return
            
            # Clean up extraction directory
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
        
        for file_path in ['2024.zip', 'Ae2024']:
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                else:
                    shutil.rmtree(file_path)
                self.log_signal.emit(f"[CANCEL] Removed {file_path}")
        
        # Remove partially installed AeNux directory if empty
        if os.path.exists(AE_NUX_DIR):
            try:
                if len(os.listdir(AE_NUX_DIR)) < 5:
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
            
            # Get paths to wine tools
            wine_path = os.path.join(self.runner_path, "bin", "wine")
            wineserver_path = os.path.join(self.runner_path, "bin", "wineserver")
            winetricks_path = os.path.join(os.path.dirname(__file__), "winetricks")
            
            # Check if required tools exist
            if not all(os.path.exists(path) for path in [wine_path, winetricks_path]):
                self.log_signal.emit("[ERROR] Required tools not found")
                self.finished_signal.emit(False)
                return

            self.progress_signal.emit(20)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            # Check for cabextract
            if not shutil.which('cabextract'):
                self.log_signal.emit("[ERROR] cabextract is not installed")
                self.finished_signal.emit(False)
                return

            # Initialize wineprefix if needed
            if not os.path.exists(self.wineprefix_path):
                self.log_signal.emit("[DEBUG] Initializing wineprefix...")
                result = subprocess.run([wine_path, "--version"], env=env, capture_output=True, text=True)
                if result.returncode != 0:
                    self.log_signal.emit(f"[ERROR] Wine initialization failed: {result.stderr}")
                    self.finished_signal.emit(False)
                    return

            self.progress_signal.emit(30)

            # Configure registry and visual settings
            self.log_signal.emit("[DEBUG] Configuring registry settings...")
            subprocess.run([wine_path, "reg", "add", 
                          "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ThemeManager", 
                          "/v", "ThemeActive", "/t", "REG_SZ", "/d", "0", "/f"], env=env)
            
            # Import registry file for colors
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
            subprocess.run([wineserver_path, "-k"], env=env)
            
            self.progress_signal.emit(50)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            # Run winetricks and VCR install
            self.log_signal.emit("[DEBUG] Running winetricks...")
            subprocess.run([winetricks_path, "-q", "dxvk", "corefonts", "gdiplus", "fontsmooth=rgb"], env=env)
            
            vcr_bat = os.path.join(os.path.dirname(__file__), "asset", "vcr", "install_all.bat")
            if os.path.exists(vcr_bat):
                self.log_signal.emit("[DEBUG] Installing VCR dependencies...")
                subprocess.run([wine_path, vcr_bat], env=env)

            self.progress_signal.emit(70)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            # Create shortcuts to Linux folders
            self.log_signal.emit("[DEBUG] Creating shortcuts...")
            wine_drive_c = os.path.join(self.wineprefix_path, "drive_c")
            fav_dir = os.path.join(wine_drive_c, "users", "*", "Favorites")
            
            fav_paths = glob.glob(fav_dir)
            if fav_paths:
                target_fav_dir = fav_paths[0]
                home_dir = os.path.expanduser("~")
                
                # Remove existing symlinks and create new ones
                for folder in ["Documents", "Downloads", "Pictures", "Videos", "Music"]:
                    link_path = os.path.join(target_fav_dir, folder)
                    if os.path.exists(link_path):
                        os.remove(link_path)
                    os.symlink(os.path.join(home_dir, folder), link_path)
                
                os.symlink(AE_NUX_DIR, os.path.join(target_fav_dir, "AeNux"))
                subprocess.run([wineserver_path, "-k"], env=env)

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
                    subprocess.run([wine_path, "reg", "add", "HKCU\\Software\\Wine\\DllOverrides", 
                                  "/v", "msxml3", "/d", "native,builtin", "/f"], env=env)

            self.progress_signal.emit(100)
            self.log_signal.emit("[INFO] AeNux patch applied successfully!")
            self.finished_signal.emit(True)
            
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Patch application failed: {str(e)}")
            self.finished_signal.emit(False)


class PluginThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    cancelled = pyqtSignal()

    def __init__(self, runner_path, wineprefix_path, zip_file_path=None):
        super().__init__()
        self.runner_path = runner_path
        self.wineprefix_path = wineprefix_path
        self._is_cancelled = False
        self.zip_file_path = zip_file_path

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            self.log_signal.emit("[INFO] Starting plugin installation...")
            self.progress_signal.emit(10)

            if self._is_cancelled:
                self.cancelled.emit()
                return

            # Set environment variables
            env = os.environ.copy()
            env['WINEPREFIX'] = self.wineprefix_path
            wine_path = os.path.join(self.runner_path, "bin", "wine")
            
            if not os.path.exists(wine_path):
                self.log_signal.emit("[ERROR] Wine not found")
                self.finished_signal.emit(False)
                return

            # Check for zenity
            if not shutil.which('zenity'):
                self.log_signal.emit("[INFO] Installing zenity...")
                subprocess.run(['sudo', 'apt', 'install', 'zenity', '-y'], capture_output=True)

            self.progress_signal.emit(20)

            # Handle plugin zip file
            zip_file_path = 'aenux-require-plugin.zip'
            if self.zip_file_path and os.path.exists(self.zip_file_path):
                self.log_signal.emit(f"[INFO] Using local plugin file: {self.zip_file_path}")
                shutil.copy2(self.zip_file_path, zip_file_path)
            else:
                self.log_signal.emit("[ERROR] No plugin file provided")
                self.finished_signal.emit(False)
                return

            # Extract plugin package
            if os.path.exists(zip_file_path):
                self.log_signal.emit("[DEBUG] Extracting plugin package...")
                result = subprocess.run(['unzip', '-o', zip_file_path], capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.log_signal.emit(f"[ERROR] Extraction failed: {result.stderr}")
                    self.finished_signal.emit(False)
                    return
                
                os.remove(zip_file_path)

            self.progress_signal.emit(50)

            # Install components
            self._install_aex_plugins()
            self._install_cep_extension(env, wine_path)
            self._install_presets()
            self._run_installers(env, wine_path)

            self.progress_signal.emit(90)
            self._cleanup_leftovers()
            self.progress_signal.emit(100)
            self.log_signal.emit("[INFO] Plugin installation completed successfully!")
            self.finished_signal.emit(True)
            
        except Exception as e:
            self._cleanup_leftovers()
            self.log_signal.emit(f"[ERROR] Plugin installation failed: {str(e)}")
            self.finished_signal.emit(False)

    def _install_aex_plugins(self):
        """Install AEX plugins"""
        aex_src = "aex"
        if os.path.exists(aex_src) and os.listdir(aex_src):
            os.makedirs(PLUGIN_DIR, exist_ok=True)
            for item in os.listdir(aex_src):
                if self._is_cancelled:
                    self.cancelled.emit()
                    return
                src_path = os.path.join(aex_src, item)
                dst_path = os.path.join(PLUGIN_DIR, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dst_path)
            self.log_signal.emit("[INFO] AEX plugins installed")

    def _install_cep_extension(self, env, wine_path):
        """Install CEP extension"""
        if os.path.exists("CEP/AddKeys.reg"):
            subprocess.run([wine_path, "regedit", "CEP/AddKeys.reg"], env=env, capture_output=True)
        
        cep_src = "CEP/flowv1.4.2"
        cep_dst = os.path.join(self.wineprefix_path, "drive_c", "Program Files (x86)", 
                              "Common Files", "Adobe", "CEP", "extensions")
        
        if os.path.exists(cep_src):
            os.makedirs(cep_dst, exist_ok=True)
            shutil.copytree(cep_src, os.path.join(cep_dst, "flowv1.4.2"), dirs_exist_ok=True)
            self.log_signal.emit("[INFO] CEP extension installed")

    def _install_presets(self):
        """Install presets"""
        preset_src = "preset-backup/"
        if os.path.exists(preset_src) and os.listdir(preset_src):
            os.makedirs(PRESET_DIR, exist_ok=True)
            for item in os.listdir(preset_src):
                if self._is_cancelled:
                    self.cancelled.emit()
                    return
                src_path = os.path.join(preset_src, item)
                dst_path = os.path.join(PRESET_DIR, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dst_path)
            self.log_signal.emit("[INFO] Presets installed")

    def _run_installers(self, env, wine_path):
        """Run installer executables"""
        if not os.path.exists("installer"):
            return

        original_dir = os.getcwd()
        os.chdir("installer")
        
        # Install regular executables
        for exe in os.listdir('.'):
            if exe.endswith('.exe') and exe not in ['E3D.exe', 'saber.exe']:
                if self._is_cancelled:
                    self.cancelled.emit()
                    return
                self.log_signal.emit(f"[INFO] Installing: {exe}")
                subprocess.run([wine_path, exe, '/verysilent', '/suppressmsgboxes'], 
                             env=env, capture_output=True)
        
        # Special handling for E3D and saber
        for exe in ['E3D.exe', 'saber.exe']:
            if os.path.exists(exe):
                self.log_signal.emit(f"[INFO] Please manually install: {exe}")
                subprocess.run([wine_path, exe], env=env)
        
        os.chdir(original_dir)
        self._copy_element_files()

    def _copy_element_files(self):
        """Copy Element files after installation"""
        video_copilot_dir = os.path.join(PLUGIN_DIR, "VideoCopilot")
        if not os.path.exists(video_copilot_dir):
            return

        element_files = [
            ("Element.aex", "Element.aex"),
            ("Element.license", "Element.license")
        ]
        
        for src_name, dst_name in element_files:
            src_path = os.path.join("installer", src_name)
            if os.path.exists(src_path):
                shutil.copy2(src_path, os.path.join(video_copilot_dir, dst_name))
                self.log_signal.emit(f"[INFO] {src_name} copied successfully")

    def _cleanup_leftovers(self):
        """Clean up leftover files"""
        try:
            for folder in ["CEP", "aex", "installer", "preset-backup", "scripts"]:
                if os.path.exists(folder):
                    shutil.rmtree(folder)
        except Exception as e:
            self.log_signal.emit(f"[WARNING] Cleanup failed: {str(e)}")


class AeNuxApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AeNux Halloween Edition")
        self.resize(520, 350)
        self.config = self._load_config()
        self.install_thread = None
        self.patch_thread = None
        self.plugin_thread = None
        
        # UI state management
        self.buttons_disabled = False
        self.button_cooldown_timer = QTimer()
        self.button_cooldown_timer.setSingleShot(True)
        self.button_cooldown_timer.timeout.connect(self._enable_buttons)
        self.main_buttons = []

        self._setup_ui()
        self._setup_connections()
        self._check_installation_status()

    def _setup_ui(self):
        """Setup the user interface"""
        root = QVBoxLayout(self)
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(__file__), "asset/logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Status row
        status_row = QHBoxLayout()
        status_row.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Checking...")
        status_row.addWidget(self.status_label)
        status_row.addStretch()
        
        self.install_button = QPushButton("Install")
        status_row.addWidget(self.install_button)
        self.main_buttons.append(self.install_button)
        
        self.uninstall_button = QPushButton("Uninstall")
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
        runner_row.addWidget(self.btn_refresh)
        self.main_buttons.append(self.btn_refresh)
        root.addLayout(runner_row)

        # Checkboxes and Plugin button
        cb_row = QHBoxLayout()
        self.patch_checkbox = QCheckBox("Apply AeNux Patch")
        cb_row.addWidget(self.patch_checkbox)
        
        self.btn_install_plugin = QPushButton("Install Plugin")
        self.btn_install_plugin.setEnabled(False)
        cb_row.addWidget(self.btn_install_plugin)
        self.main_buttons.append(self.btn_install_plugin)
        root.addLayout(cb_row)

        # Execution buttons
        exec_row = QHBoxLayout()
        self.btn_run = QPushButton("Run AeNux")
        self.btn_kill = QPushButton("Kill AeNux")
        exec_row.addWidget(self.btn_run)
        exec_row.addWidget(self.btn_kill)
        self.main_buttons.extend([self.btn_run, self.btn_kill])
        root.addLayout(exec_row)

        # Folders
        folder_row = QHBoxLayout()
        for name in ["Runner", "Plugin", "Preset", "Wineprefix"]:
            btn = QPushButton(f"{name} Folder")
            btn.clicked.connect(lambda checked, n=name.lower(): self._open_folder(n))
            folder_row.addWidget(btn)
            self.main_buttons.append(btn)
        root.addLayout(folder_row)

        # Footer
        footer = QLabel('Made with 🎃 by cutefishaep')
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(footer)

    def _setup_connections(self):
        """Setup signal connections"""
        self.install_button.clicked.connect(self._install_aenux)
        self.uninstall_button.clicked.connect(self._uninstall_aenux)
        self.cancel_button.clicked.connect(self._cancel_operation)
        self.btn_refresh.clicked.connect(self._refresh_runner_list)
        self.btn_install_plugin.clicked.connect(self._install_plugin)
        self.btn_run.clicked.connect(self._run_aenux)
        self.btn_kill.clicked.connect(self._kill_aenux)
        self.runner_dropdown.currentIndexChanged.connect(self._runner_changed)
        self.patch_checkbox.stateChanged.connect(self._patch_checkbox_changed)

        self._populate_runner_dropdown()
        self._apply_saved_config()

    def _choose_local_zip_file(self, file_type="AeNux"):
        """Open file dialog to choose local zip file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Select {file_type} Zip File", "", "Zip Files (*.zip);;All Files (*)"
        )
        return file_path

    def _disable_buttons_temporarily(self, duration=1500):
        """Temporarily disable all main buttons"""
        if self.buttons_disabled:
            return
            
        self.buttons_disabled = True
        for button in self.main_buttons:
            button.setEnabled(False)
        
        self.runner_dropdown.setEnabled(False)
        self.patch_checkbox.setEnabled(False)
        self.button_cooldown_timer.start(duration)

    def _enable_buttons(self):
        """Re-enable all buttons"""
        self.buttons_disabled = False
        for button in self.main_buttons:
            button.setEnabled(True)
        
        self.runner_dropdown.setEnabled(True)
        self._update_checkbox_states()
        self._check_runner_support()
        self._check_installation_status()

    def _update_checkbox_states(self):
        """Update checkbox status based on selected runner"""
        runner = self.runner_dropdown.currentText()
        self.patch_checkbox.setEnabled("proton" not in runner.lower())

    def _cancel_operation(self):
        """Cancel the ongoing operation"""
        if self.buttons_disabled:
            return
            
        self._disable_buttons_temporarily(1000)
        
        threads = [
            (self.install_thread, "installation"),
            (self.patch_thread, "patch application"), 
            (self.plugin_thread, "plugin installation")
        ]
        
        for thread, operation_name in threads:
            if thread and thread.isRunning():
                reply = QMessageBox.question(
                    self, "Confirm Cancel",
                    f"Are you sure you want to cancel the {operation_name}?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    thread.cancel()
                    self.logs_box.append(f"[USER] {operation_name.capitalize()} cancelled by user.")
                    self.cancel_button.setVisible(False)
                    self.progress_bar.setVisible(False)
                break

    def _create_shortcut(self):
        """Create desktop shortcut and icon"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Create icons directory
            icons_dir = os.path.expanduser("~/.local/share/icons")
            os.makedirs(icons_dir, exist_ok=True)
            
            # Copy icon
            icon_src = os.path.join(current_dir, "asset", "logo.png")
            icon_dst = os.path.join(icons_dir, "AeNux.png")
            if os.path.exists(icon_src):
                shutil.copy2(icon_src, icon_dst)

            # Create desktop entry
            applications_dir = os.path.expanduser("~/.local/share/applications")
            os.makedirs(applications_dir, exist_ok=True)
            
            desktop_file = os.path.join(applications_dir, "AeNux.desktop")
            run_script = os.path.join(current_dir, "run_qt6.py")
            
            if not os.path.exists(run_script):
                self.logs_box.append("[ERROR] run_qt6.py not found!")
                return False
            
            desktop_content = f"""[Desktop Entry]
Name=AeNux Loader
Comment=Run AeNux using Wine
Exec=python3 {run_script}
Path={current_dir}
Type=Application
Icon=AeNux
Terminal=false
Categories=AudioVideo;Video;
"""
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            os.chmod(desktop_file, 0o755)
            subprocess.run(["update-desktop-database", applications_dir], capture_output=True)
            self.logs_box.append("[SHORTCUT] Desktop shortcut created successfully.")
            return True
            
        except Exception as e:
            self.logs_box.append(f"[ERROR] Failed to create shortcut: {str(e)}")
            return False

    def _remove_shortcut(self):
        """Remove desktop shortcut and icon"""
        try:
            icon_path = os.path.expanduser("~/.local/share/icons/AeNux.png")
            if os.path.exists(icon_path):
                os.remove(icon_path)
            
            desktop_file = os.path.expanduser("~/.local/share/applications/AeNux.desktop")
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
            
            applications_dir = os.path.expanduser("~/.local/share/applications")
            subprocess.run(["update-desktop-database", applications_dir], capture_output=True)
            self.logs_box.append("[SHORTCUT] Desktop shortcut removed.")
            return True
            
        except Exception as e:
            self.logs_box.append(f"[ERROR] Failed to remove shortcut: {str(e)}")
            return False

    def _check_installation_status(self):
        """Check if AeNux is installed"""
        if os.path.exists(AE_NUX_DIR) and any(not f.startswith('.') for f in os.listdir(AE_NUX_DIR)):
            self.status_label.setText("AeNux installed")
            self.install_button.hide()
            self.uninstall_button.show()
            self.btn_install_plugin.setEnabled(True)
            self.logs_box.append("[STATUS] AeNux is installed and ready to use.")
        else:
            self.status_label.setText("AeNux is not installed")
            self.install_button.show()
            self.uninstall_button.hide()
            self.btn_install_plugin.setEnabled(False)
            self.logs_box.append("[STATUS] AeNux is not installed. Click Install to proceed.")

    def _install_aenux(self):
        """Install AeNux"""
        if self.buttons_disabled:
            return
            
        if self.install_thread and self.install_thread.isRunning():
            self.logs_box.append("[INFO] Installation already in progress...")
            return

        reply = QMessageBox.question(
            self, "Confirm Installation",
            f"This will install AeNux to {AE_NUX_DIR}. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            zip_file_path = self._choose_local_zip_file("AeNux")
            if zip_file_path:
                self._start_installation(zip_file_path)
            else:
                self.logs_box.append("[USER] No file selected. Installation cancelled.")

    def _start_installation(self, zip_file_path):
        """Start the installation process"""
        self._disable_buttons_temporarily(500)
        self.install_button.setText("Installing...")
        self.progress_bar.setVisible(True)
        self.cancel_button.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.install_thread = InstallThread(zip_file_path)
        self.install_thread.log_signal.connect(self.logs_box.append)
        self.install_thread.progress_signal.connect(self.progress_bar.setValue)
        self.install_thread.finished_signal.connect(self._installation_finished)
        self.install_thread.cancelled.connect(self._installation_cancelled)
        self.install_thread.start()

    def _uninstall_aenux(self):
        """Uninstall AeNux"""
        if self.buttons_disabled:
            return
            
        reply = QMessageBox.question(
            self, "Confirm Uninstall",
            "This will remove AeNux and all its data. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._disable_buttons_temporarily(2000)
            try:
                for path in [AE_NUX_DIR, WINE_PREFIX_DIR]:
                    if os.path.exists(path):
                        shutil.rmtree(path)
                        self.logs_box.append(f"[UNINSTALL] Removed {path}")
                
                self._remove_shortcut()
                self.logs_box.clear()
                self._check_installation_status()
                self.logs_box.append("[UNINSTALL] AeNux has been completely uninstalled.")
                
            except Exception as e:
                self.logs_box.append(f"[ERROR] Uninstall failed: {str(e)}")
                QMessageBox.critical(self, "Uninstall Error", f"Failed to uninstall AeNux: {str(e)}")

    def _installation_finished(self, success):
        """Handle installation completion"""
        self._enable_buttons()
        self.install_button.setText("Install")
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        
        if success:
            self._create_shortcut()
            self._check_installation_status()
        else:
            self.logs_box.append("[ERROR] Installation failed. Please check the logs above.")

    def _installation_cancelled(self):
        """Handle installation cancellation"""
        self._enable_buttons()
        self.install_button.setText("Install")
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.logs_box.append("[INFO] Installation was cancelled and cleaned up.")

    def _check_wineprefix(self):
        """Check if wineprefix exists"""
        return os.path.exists(WINE_PREFIX_DIR)

    def _install_plugin(self):
        """Install plugins for AeNux"""
        if self.buttons_disabled:
            return
            
        if not os.path.exists(AE_NUX_DIR):
            QMessageBox.warning(self, "Not Installed", "Please install AeNux first.")
            return

        runner = self.runner_dropdown.currentText()
        if self._is_invalid_runner(runner):
            return

        zip_file_path = self._choose_local_zip_file("Plugin")
        if not zip_file_path:
            return

        reply = QMessageBox.question(
            self, "Confirm Plugin Installation",
            "This will install additional plugins for AeNux. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._disable_buttons_temporarily(500)
            self.btn_install_plugin.setText("Installing...")
            self.progress_bar.setVisible(True)
            self.cancel_button.setVisible(True)
            self.progress_bar.setValue(0)
            
            runner_path = os.path.join(os.path.dirname(__file__), "runner", runner)
            
            self.plugin_thread = PluginThread(runner_path, WINE_PREFIX_DIR, zip_file_path)
            self.plugin_thread.log_signal.connect(self.logs_box.append)
            self.plugin_thread.progress_signal.connect(self.progress_bar.setValue)
            self.plugin_thread.finished_signal.connect(self._plugin_installation_finished)
            self.plugin_thread.cancelled.connect(self._plugin_installation_cancelled)
            self.plugin_thread.start()

    def _is_invalid_runner(self, runner):
        """Check if runner is invalid for operations"""
        if runner.lower().startswith("select") or runner.lower() == "no runners found":
            QMessageBox.warning(self, "No Runner Selected", "Please select a runner first.")
            return True
        if "proton" in runner.lower():
            QMessageBox.warning(self, "Proton Not Supported", "Proton runners are not supported.")
            return True
        return False

    def _plugin_installation_finished(self, success):
        """Handle plugin installation completion"""
        self._enable_buttons()
        self.btn_install_plugin.setText("Install Plugin")
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        
        if success:
            self.logs_box.append("[INFO] Plugin installation completed successfully!")
        else:
            self.logs_box.append("[ERROR] Plugin installation failed. Please check the logs above.")

    def _plugin_installation_cancelled(self):
        """Handle plugin installation cancellation"""
        self._enable_buttons()
        self.btn_install_plugin.setText("Install Plugin")
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.logs_box.append("[INFO] Plugin installation was cancelled.")

    def _run_aenux(self):
        """Run AeNux with optional patch"""
        if self.buttons_disabled:
            return
            
        if not self._validate_ae_nux_installation():
            return

        runner = self.runner_dropdown.currentText()
        if self._is_invalid_runner(runner):
            return

        afterfx_path = os.path.join(AE_NUX_DIR, "AfterFX.exe")
        if not os.path.exists(afterfx_path):
            QMessageBox.warning(self, "AfterFX Not Found", f"AfterFX.exe not found at: {afterfx_path}")
            return

        runner_path = os.path.join(os.path.dirname(__file__), "runner", runner)
        os.makedirs(WINE_PREFIX_DIR, exist_ok=True)

        if self.patch_checkbox.isChecked():
            self._apply_patch_then_run(runner_path, afterfx_path)
        else:
            self._disable_buttons_temporarily(1000)
            self._run_afterfx(runner_path, WINE_PREFIX_DIR, afterfx_path)

    def _validate_ae_nux_installation(self):
        """Validate that AeNux is properly installed"""
        if not os.path.exists(AE_NUX_DIR) or not any(not f.startswith('.') for f in os.listdir(AE_NUX_DIR)):
            QMessageBox.warning(self, "Not Installed", "Please install AeNux first.")
            return False
        return True

    def _apply_patch_then_run(self, runner_path, afterfx_path):
        """Apply patch first, then run AfterFX"""
        self._disable_buttons_temporarily(1000)
        self.logs_box.append("[INFO] Applying AeNux patch before running...")
        self.progress_bar.setVisible(True)
        self.cancel_button.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.patch_thread = PatchThread(runner_path, WINE_PREFIX_DIR)
        self.patch_thread.log_signal.connect(self.logs_box.append)
        self.patch_thread.progress_signal.connect(self.progress_bar.setValue)
        self.patch_thread.finished_signal.connect(
            lambda success: self._patch_finished(success, runner_path, WINE_PREFIX_DIR, afterfx_path)
        )
        self.patch_thread.cancelled.connect(self._patch_cancelled)
        self.patch_thread.start()

    def _patch_finished(self, success, runner_path, wineprefix_path, afterfx_path):
        """Handle patch completion"""
        self._enable_buttons()
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.patch_checkbox.setChecked(False)
        
        if success:
            self.logs_box.append("[INFO] Patch applied successfully, now running AfterFX...")
            self._run_afterfx(runner_path, wineprefix_path, afterfx_path)
        else:
            self.logs_box.append("[ERROR] Patch failed. AfterFX will not be run.")

    def _patch_cancelled(self):
        """Handle patch cancellation"""
        self._enable_buttons()
        self.progress_bar.setVisible(False)
        self.cancel_button.setVisible(False)
        self.patch_checkbox.setChecked(False)
        self.logs_box.append("[INFO] Patch application was cancelled.")

    def _run_afterfx(self, runner_path, wineprefix_path, afterfx_path):
        """Run AfterFX.exe with the selected runner"""
        try:
            wine_path = os.path.join(runner_path, "bin", "wine")
            env = os.environ.copy()
            env['WINEPREFIX'] = wineprefix_path
            
            self.logs_box.append(f"[RUN] Starting AfterFX.exe with {os.path.basename(runner_path)}...")
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
            for process in ["AfterFX.exe", "wine", "wineserver"]:
                subprocess.run(["pkill", "-f", process])
            self.logs_box.append("[KILL] AeNux processes terminated.")
        except Exception as e:
            self.logs_box.append(f"[ERROR] Failed to kill processes: {str(e)}")

    def _load_config(self):
        """Load configuration from file"""
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_config(self):
        """Save configuration to file"""
        config = {"runner": self.runner_dropdown.currentText()}
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    def _apply_saved_config(self):
        """Apply saved configuration"""
        if "runner" in self.config:
            idx = self.runner_dropdown.findText(self.config["runner"])
            if idx >= 0:
                self.runner_dropdown.setCurrentIndex(idx)

    def _populate_runner_dropdown(self):
        """Populate runner dropdown with available runners"""
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
        """Handle runner selection change"""
        runner = self.runner_dropdown.currentText()
        
        if "proton" in runner.lower():
            self._disable_proton_buttons()
            self.logs_box.append("[ERROR] Proton is not supported! Please select a Wine runner.")
        else:
            self._enable_normal_buttons()
            if not runner.lower().startswith("select"):
                self.logs_box.append(f"[INFO] Selected runner: {runner}")
        
        self._save_config()

    def _disable_proton_buttons(self):
        """Disable buttons for Proton runner"""
        self.btn_run.setEnabled(False)
        self.btn_kill.setEnabled(False)
        self.btn_install_plugin.setEnabled(False)
        self.patch_checkbox.setEnabled(False)

    def _enable_normal_buttons(self):
        """Enable buttons for normal Wine runner"""
        self.btn_run.setEnabled(True)
        self.btn_kill.setEnabled(True)
        self.patch_checkbox.setEnabled(True)
        if os.path.exists(AE_NUX_DIR):
            self.btn_install_plugin.setEnabled(True)

    def _patch_checkbox_changed(self, state):
        """Handle patch checkbox state change"""
        if self.buttons_disabled:
            return
            
        if state == Qt.CheckState.Checked.value and self._check_wineprefix():
            QMessageBox.warning(self, "Wineprefix Exists",
                              "Wineprefix already exists, please remove it first before running patch!")
            self.patch_checkbox.setChecked(False)
            return
        
        status = "ENABLED" if state == Qt.CheckState.Checked.value else "DISABLED"
        self.logs_box.append(f"[OPTION] Apply AeNux Patch: {status}")

    def _check_runner_support(self):
        """Check if current runner is supported"""
        runner = self.runner_dropdown.currentText()
        if "proton" in runner.lower():
            self._disable_proton_buttons()
            self.logs_box.append("[ERROR] Proton is not supported!")
        else:
            self._enable_normal_buttons()

    def _refresh_runner_list(self):
        """Refresh the list of available runners"""
        if self.buttons_disabled:
            return
            
        self._disable_buttons_temporarily(1000)
        self.logs_box.append("[INFO] Refreshing runner list...")
        self._populate_runner_dropdown()
        self._check_runner_support()

    def _open_folder(self, name):
        """Open the specified folder"""
        if self.buttons_disabled:
            return
            
        self._disable_buttons_temporarily(1000)
        
        folder_paths = {
            "wineprefix": WINE_PREFIX_DIR,
            "plugin": PLUGIN_DIR,
            "preset": PRESET_DIR,
            "runner": os.path.join(os.path.dirname(__file__), "runner")
        }
        
        path = folder_paths.get(name)
        if not path:
            return

        # Validate installation for certain folders
        if name in ["plugin", "preset"] and not os.path.exists(AE_NUX_DIR):
            QMessageBox.warning(self, "Not Installed", "You need to install AeNux first")
            return

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
