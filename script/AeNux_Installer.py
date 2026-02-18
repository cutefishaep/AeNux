#!/usr/bin/python3
"""AeNux Installer v2.0"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os, tarfile, zipfile, shutil, requests, threading, stat
from urllib.request import urlretrieve
import utils

class AeNuxInstaller:
    def __init__(self):
        self.builder = Gtk.Builder()
        ui_file = os.path.join(os.path.dirname(__file__), 'gui.ui')
        
        try:
            self.builder.add_from_file(ui_file)
        except Exception as e:
            utils.debug_print(f"UI Error: {e}")
            raise
        
        self.window = self.builder.get_object('main_window')
        self.install_btn = self.builder.get_object('InstallButton')
        self.location = self.builder.get_object('Location')
        self.zip_chooser = self.builder.get_object('zip_files1')
        self.progress = self.builder.get_object('install_progressbar')
        
        self.install_btn.set_sensitive(False)
        self.install_btn.connect('clicked', self.on_install)
        self.location.connect('selection-changed', self.check_ready)
        self.zip_chooser.connect('selection-changed', self.check_ready)
        self.window.connect('delete-event', self.on_window_close)
        
        self.is_installing = False
        self.temp_dir = None
        
        self.user_location = None
        self.zip_file = None
        self.dll_files = {}
        self.config_path = os.path.join(os.path.dirname(__file__), 'aenux_config.json')
        
        utils.debug_print(f"Installer ready. Config: {self.config_path}")
    
    def check_ready(self, widget):
        """Enable install button when both selections made"""
        has_location = self.location.get_filename()
        has_zip = self.zip_chooser.get_filename()
        self.install_btn.set_sensitive(bool(has_location and has_zip))
    
    def on_window_close(self, widget, event):
        """Handle window close event - cleanup TEMP if installing"""
        if self.is_installing:
            utils.debug_print("Window closed during installation - cleaning up TEMP folder")
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                    utils.debug_print(f"TEMP folder cleaned: {self.temp_dir}")
                except Exception as e:
                    utils.debug_print(f"Error cleaning TEMP: {e}")
        return False
    
    def on_install(self, widget):
        """Start installation"""
        self.user_location = self.location.get_filename()
        self.zip_file = self.zip_chooser.get_filename()
        
        if not self.user_location or not self.zip_file:
            return
        
        # Select DLL files FIRST before installation
        if not self.select_dlls():
            return
        
        self.install_btn.set_label("Installing...")
        self.install_btn.set_sensitive(False)
        self.is_installing = True
        
        thread = threading.Thread(target=self.install_process, daemon=True)
        thread.start()
    
    def select_dlls(self):
        """Select DLL files before installation starts"""
        self.dll_files = {}
        
        for dll_name in ['msxml3.dll', 'msxml3r.dll']:
            file_path = self._show_file_dialog(dll_name)
            
            if not file_path:
                utils.show_error(self.window, f"{dll_name} tidak dipilih")
                return False
            
            filename = os.path.basename(file_path)
            if filename != dll_name:
                utils.show_error(self.window, f"File name mismatch!\nExpected: {dll_name}\nGot: {filename}")
                return False
            
            self.dll_files[dll_name] = file_path
            utils.debug_print(f"Selected: {dll_name}")
        
        return True
    
    def _show_file_dialog(self, title):
        """Show GTK3 file chooser"""
        dialog = Gtk.FileChooserDialog(
            title=f"Select {title}",
            parent=self.window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        response = dialog.run()
        file_path = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        
        return file_path
    
    def update_progress(self, fraction, text=""):
        """Update progress bar"""
        GLib.idle_add(lambda f=fraction, t=text: self._update_ui(f, t))
    
    def _update_ui(self, fraction, text):
        self.progress.set_fraction(fraction)
        if text:
            self.progress.set_text(text)
        return False
    
    def install_process(self):
        """Main installation"""
        try:
            self.temp_dir = os.path.join(self.user_location, 'TEMP')
            os.makedirs(self.temp_dir, exist_ok=True)
            utils.debug_print(f"Created TEMP directory: {self.temp_dir}")
            
            steps = [
                (0.10, "Downloading...", lambda: self.download_files(self.temp_dir)),
                (0.35, "Extracting AeNux...", lambda: self.extract_aenux()),
                (0.50, "Extracting Wine...", lambda: self.extract_wine(self.temp_dir)),
                (0.60, "Copying winetricks...", lambda: self.copy_winetricks(self.temp_dir)),
                (0.70, "Setup Wine...", lambda: self.setup_wine()),
                (0.85, "Installing deps...", lambda: self.install_deps(self.temp_dir)),
                (0.95, "Finalizing...", lambda: self.finalize(self.temp_dir)),
            ]
            
            for progress, msg, func in steps:
                self.update_progress(progress, msg)
                utils.debug_print(msg)
                func()
            
            self.update_progress(1.0, "Complete!")
            utils.debug_print("Installation finished")
            GLib.idle_add(self._show_success)
            
        except Exception as e:
            utils.debug_print(f"Error: {e}")
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                    utils.debug_print(f"TEMP folder cleaned on error: {self.temp_dir}")
                except Exception as cleanup_error:
                    utils.debug_print(f"Error cleaning TEMP on error: {cleanup_error}")
            GLib.idle_add(lambda err=str(e): self._show_error_final(err))
        finally:
            self.is_installing = False
    
    def download_files(self, temp_dir):
        """Download all required files"""
        urls = {
            'vc_redist.x64.exe': 'https://aka.ms/vs/17/release/vc_redist.x64.exe',
            'vc_redist.x86.exe': 'https://aka.ms/vs/17/release/vc_redist.x86.exe',
            'wine-10.20-amd64-wow64.tar.xz': 'https://github.com/Kron4ek/Wine-Builds/releases/download/10.20/wine-10.20-amd64-wow64.tar.xz',
            'wine-gecko-2.47.4-x86_64.msi': 'https://dl.winehq.org/wine/wine-gecko/2.47.4/wine-gecko-2.47.4-x86_64.msi',
            'winetricks': 'https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks'
        }
        
        utils.debug_print(f"Downloading {len(urls)} files...")
        
        for idx, (filename, url) in enumerate(urls.items(), 1):
            filepath = os.path.join(temp_dir, filename)
            
            if os.path.exists(filepath):
                utils.debug_print(f"[{idx}/{len(urls)}] {filename} (cached)")
                continue
            
            utils.debug_print(f"[{idx}/{len(urls)}] Downloading {filename}...")
            
            try:
                if filename == 'winetricks':
                    response = requests.get(url)
                    response.raise_for_status()
                    with open(filepath, 'w') as f:
                        f.write(response.text)
                    os.chmod(filepath, os.stat(filepath).st_mode | stat.S_IEXEC)
                else:
                    urlretrieve(url, filepath)
                    
            except Exception as e:
                utils.debug_print(f"ERROR: Failed to download {filename}: {e}")
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
                raise
        
        utils.debug_print(f"Downloads completed")
    
    def extract_aenux(self):
        """Extract AeNux"""
        aenux_dir = os.path.join(self.user_location, 'AeNux')
        os.makedirs(aenux_dir, exist_ok=True)
        with zipfile.ZipFile(self.zip_file, 'r') as z:
            z.extractall(aenux_dir)
        utils.debug_print(f"AeNux extracted")
    
    def extract_wine(self, temp_dir):
        """Extract Wine"""
        wine_file = os.path.join(temp_dir, 'wine-10.20-amd64-wow64.tar.xz')
        wine_dir = os.path.join(self.user_location, 'wine')
        
        if not os.path.exists(wine_file):
            raise Exception(f"Wine archive not found: {wine_file}")
        
        os.makedirs(wine_dir, exist_ok=True)
        
        utils.debug_print(f"Extracting Wine from {wine_file}...")
        try:
            with tarfile.open(wine_file, 'r:xz') as tar:
                for member in tar.getmembers():
                    if '/' in member.name:
                        member.name = member.name.split('/', 1)[1]
                    if member.name:
                        tar.extract(member, wine_dir)
            utils.debug_print("Wine extracted successfully")
        except Exception as e:
            raise Exception(f"Failed to extract Wine: {str(e)}")
    
    def copy_winetricks(self, temp_dir):
        """Copy winetricks"""
        src = os.path.join(temp_dir, 'winetricks')
        dst = os.path.join(self.user_location, 'wine', 'bin', 'winetricks')
        
        if not os.path.exists(src):
            raise Exception(f"Winetricks source not found: {src}")
        
        # Ensure destination directory exists
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        shutil.copy2(src, dst)
        os.chmod(dst, os.stat(dst).st_mode | stat.S_IEXEC)
        utils.debug_print(f"Winetricks copied and made executable")
    
    def setup_wine(self):
        """Setup Wine prefix"""
        prefix = os.path.join(self.user_location, 'Wineprefix')
        wine_bin = os.path.join(self.user_location, 'wine', 'bin', 'wine')
        os.makedirs(prefix, exist_ok=True)
        
        if not os.path.exists(wine_bin):
            raise Exception(f"Wine binary not found: {wine_bin}")
        
        wine_path = os.path.join(self.user_location, 'wine')
        env = utils.get_wine_env(wine_path, prefix)
        
        utils.debug_print("Initializing Wine prefix...")
        utils.run_command([wine_bin, 'wineboot', '--init'], env=env)
        utils.debug_print("Wine prefix created")
    
    def install_deps(self, temp_dir):
        """Install dependencies"""
        prefix = os.path.join(self.user_location, 'Wineprefix')
        wine_path = os.path.join(self.user_location, 'wine')
        wine_bin = os.path.join(wine_path, 'bin', 'wine')
        tricks = os.path.join(self.user_location, 'wine', 'bin', 'winetricks')
        
        env = utils.get_wine_env(wine_path, prefix)
        
        # Verify winetricks exists and is executable
        if not os.path.exists(tricks):
            raise Exception(f"Winetricks not found at: {tricks}")
        
        if not os.access(tricks, os.X_OK):
            utils.debug_print(f"Making winetricks executable...")
            os.chmod(tricks, os.stat(tricks).st_mode | stat.S_IEXEC)
        
        # Wine Gecko
        gecko = os.path.join(temp_dir, 'wine-gecko-2.47.4-x86_64.msi')
        if not os.path.exists(gecko):
            raise Exception(f"Wine Gecko not found at: {gecko}")
        
        utils.debug_print("Installing wine-gecko...")
        utils.run_command([wine_bin, 'msiexec', '/i', gecko], env=env)
        
        # VC Redist
        for arch in ['x64', 'x86']:
            vc = os.path.join(temp_dir, f'vc_redist.{arch}.exe')
            if not os.path.exists(vc):
                raise Exception(f"VC Redist {arch} not found at: {vc}")
            
            utils.debug_print(f"Installing VC Redist {arch}...")
            utils.run_command([wine_bin, vc, '/install', '/quiet', '/norestart'], env=env)
        
        # Winetricks
        winetricks_verbs = ['dxvk', 'corefonts', 'gdiplus', 'fontsmooth=rgb']
        for verb in winetricks_verbs:
            utils.debug_print(f"Running winetricks: {verb}")
            utils.run_command([tricks, verb], env=env)
        
        utils.debug_print("Dependency installation completed.")
    
    def finalize(self, temp_dir):
        """Finalize installation"""
        prefix = os.path.join(self.user_location, 'Wineprefix')
        wine_path = os.path.join(self.user_location, 'wine')
        wine_bin = os.path.join(wine_path, 'bin', 'wine')
        system32 = os.path.join(prefix, 'drive_c', 'windows', 'system32')
        
        # Copy DLLs
        for dll_name, dll_path in self.dll_files.items():
            dst = os.path.join(system32, dll_name)
            shutil.copy2(dll_path, dst)
            utils.debug_print(f"Copied {dll_name}")
        
        # Registry
        env = utils.get_wine_env(wine_path, prefix)
        utils.run_command([wine_bin, 'reg', 'add', 'HKCU\\Software\\Wine\\DllOverrides',
                           '/v', 'msxml3', '/d', 'native,builtin', '/f'], env=env)
        utils.debug_print("Registry set")
        
        # Set theme/colors registry
        utils.set_theme_registry(wine_path, prefix)
        
        # Save config
        config = {
            'version': '2.0',
            'user_location': self.user_location,
            'wine_path': wine_path,
            'wineprefix': prefix,
            'aenux_path': os.path.join(self.user_location, 'AeNux')
        }
        utils.save_config(config)
        
        # Create shortcuts
        utils.create_shortcuts(wine_path, prefix, config['aenux_path'])
        
        # Run AppShortcutMake.sh to create desktop shortcuts
        script_dir = os.path.dirname(__file__)
        shortcut_script = os.path.join(script_dir, 'AppShortcutMake.sh')
        if os.path.exists(shortcut_script):
            try:
                utils.debug_print("Running AppShortcutMake.sh...")
                utils.run_command(['bash', shortcut_script])
                utils.debug_print("Desktop shortcuts created successfully")
            except Exception as e:
                utils.debug_print(f"Warning: Failed to create desktop shortcuts: {e}")
        
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        utils.debug_print("Cleaned up TEMP")
    
    def _show_success(self):
        """Show success dialog"""
        utils.show_info(self.window, "AeNux installed successfully!")
        # Attempt to stop any running Wine processes for the created prefix
        try:
            wine_path = os.path.join(self.user_location, 'wine')
            wine_prefix = os.path.join(self.user_location, 'Wineprefix')
            utils.kill_wine_processes(wine_path, wine_prefix)
        except Exception:
            pass

        self.is_installing = False
        self.install_btn.set_label("Installed")
        self.install_btn.set_sensitive(False)
        Gtk.main_quit()

    def _show_error_final(self, msg):
        """Show error and exit"""
        utils.show_error(self.window, msg)
        self.install_btn.set_label("Install")
        self.install_btn.set_sensitive(False)
        Gtk.main_quit()
    
    def run(self):
        """Start app"""
        utils.debug_print("Starting installer")
        self.window.show_all()
        Gtk.main()

if __name__ == '__main__':
    app = AeNuxInstaller()
    app.run()
