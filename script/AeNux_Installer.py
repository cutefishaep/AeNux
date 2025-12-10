#!/usr/bin/python3
"""AeNux Installer v2.0"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os, json, subprocess, tarfile, zipfile, shutil, requests, threading, stat, glob
from urllib.request import urlretrieve

DEBUG = True

def debug_print(msg):
    if DEBUG: print(f"[DEBUG] {msg}")

class AeNuxInstaller:
    def __init__(self):
        self.builder = Gtk.Builder()
        ui_file = os.path.join(os.path.dirname(__file__), 'gui.ui')
        
        try:
            self.builder.add_from_file(ui_file)
        except Exception as e:
            debug_print(f"UI Error: {e}")
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
        
        debug_print(f"Installer ready. Config: {self.config_path}")
    
    def check_ready(self, widget):
        """Enable install button when both selections made"""
        has_location = self.location.get_filename()
        has_zip = self.zip_chooser.get_filename()
        self.install_btn.set_sensitive(bool(has_location and has_zip))
    
    def on_window_close(self, widget, event):
        """Handle window close event - cleanup TEMP if installing"""
        if self.is_installing:
            debug_print("Window closed during installation - cleaning up TEMP folder")
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                    debug_print(f"TEMP folder cleaned: {self.temp_dir}")
                except Exception as e:
                    debug_print(f"Error cleaning TEMP: {e}")
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
                self._show_error(f"{dll_name} tidak dipilih")
                return False
            
            filename = os.path.basename(file_path)
            if filename != dll_name:
                self._show_error(f"File name mismatch!\nExpected: {dll_name}\nGot: {filename}")
                return False
            
            self.dll_files[dll_name] = file_path
            debug_print(f"Selected: {dll_name}")
        
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
    
    def _show_error(self, msg):
        """Show error popup"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()
    
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
            debug_print(f"Created TEMP directory: {self.temp_dir}")
            
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
                debug_print(msg)
                func()
            
            self.update_progress(1.0, "Complete!")
            debug_print("Installation finished")
            GLib.idle_add(self._show_success)
            
        except Exception as e:
            debug_print(f"Error: {e}")
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                    debug_print(f"TEMP folder cleaned on error: {self.temp_dir}")
                except Exception as cleanup_error:
                    debug_print(f"Error cleaning TEMP on error: {cleanup_error}")
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
        
        debug_print(f"Starting download process to: {temp_dir}")
        debug_print(f"Total files to download: {len(urls)}")
        
        for idx, (filename, url) in enumerate(urls.items(), 1):
            filepath = os.path.join(temp_dir, filename)
            
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                debug_print(f"[{idx}/{len(urls)}] File already exists (cached): {filename} ({file_size} bytes)")
                continue
            
            debug_print(f"[{idx}/{len(urls)}] Starting download: {filename}")
            debug_print(f"  URL: {url}")
            debug_print(f"  Destination: {filepath}")
            
            try:
                if filename == 'winetricks':
                    # Use requests for winetricks
                    debug_print(f"  Method: requests.get (text file)")
                    response = requests.get(url)
                    response.raise_for_status()
                    debug_print(f"  Response status: {response.status_code}")
                    
                    with open(filepath, 'w') as f:
                        f.write(response.text)
                    
                    file_size = os.path.getsize(filepath)
                    debug_print(f"  Downloaded successfully: {filename} ({file_size} bytes)")
                    
                    # Make executable
                    os.chmod(filepath, os.stat(filepath).st_mode | stat.S_IEXEC)
                    debug_print(f"  File made executable")
                else:
                    # For binary files, using urlretrieve with progress callback
                    debug_print(f"  Method: urlretrieve (binary file)")
                    
                    def download_progress(block_num, block_size, total_size):
                        downloaded = block_num * block_size
                        if total_size > 0:
                            percent = min(downloaded * 100 // total_size, 100)
                            debug_print(f"  Progress: {downloaded}/{total_size} bytes ({percent}%)")
                    
                    urlretrieve(url, filepath, reporthook=download_progress)
                    
                    file_size = os.path.getsize(filepath)
                    debug_print(f"  Downloaded successfully: {filename} ({file_size} bytes)")
                    
            except Exception as e:
                debug_print(f"  ERROR downloading {filename}: {type(e).__name__}: {e}")
                debug_print(f"  Failed file path: {filepath}")
                # Clean up partial download
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        debug_print(f"  Cleaned up partial download")
                    except Exception as cleanup_e:
                        debug_print(f"  Could not clean up partial: {cleanup_e}")
                raise
        
        debug_print(f"All downloads completed successfully")
    
    def extract_aenux(self):
        """Extract AeNux"""
        aenux_dir = os.path.join(self.user_location, 'AeNux')
        os.makedirs(aenux_dir, exist_ok=True)
        with zipfile.ZipFile(self.zip_file, 'r') as z:
            z.extractall(aenux_dir)
        debug_print(f"AeNux extracted")
    
    def extract_wine(self, temp_dir):
        """Extract Wine"""
        wine_file = os.path.join(temp_dir, 'wine-10.20-amd64-wow64.tar.xz')
        wine_dir = os.path.join(self.user_location, 'wine')
        os.makedirs(wine_dir, exist_ok=True)
        
        with tarfile.open(wine_file, 'r:xz') as tar:
            for member in tar.getmembers():
                if '/' in member.name:
                    member.name = member.name.split('/', 1)[1]
                if member.name:
                    tar.extract(member, wine_dir)
        debug_print(f"Wine extracted")
    
    def copy_winetricks(self, temp_dir):
        """Copy winetricks"""
        src = os.path.join(temp_dir, 'winetricks')
        dst = os.path.join(self.user_location, 'wine', 'bin', 'winetricks')
        shutil.copy2(src, dst)
        os.chmod(dst, os.stat(dst).st_mode | stat.S_IEXEC)
        debug_print(f"Winetricks copied")
    
    def setup_wine(self):
        """Setup Wine prefix"""
        prefix = os.path.join(self.user_location, 'Wineprefix')
        wine_bin = os.path.join(self.user_location, 'wine', 'bin', 'wine')
        os.makedirs(prefix, exist_ok=True)
        
        env = os.environ.copy()
        env['WINEPREFIX'] = prefix
        subprocess.run([wine_bin, 'wineboot', '--init'], env=env, check=True)
        debug_print(f"Wine prefix created")
    
    def install_deps(self, temp_dir):
        """Install dependencies"""
        prefix = os.path.join(self.user_location, 'Wineprefix')
        wine = os.path.join(self.user_location, 'wine', 'bin', 'wine')
        tricks = os.path.join(self.user_location, 'wine', 'bin', 'winetricks')
        
        env = os.environ.copy()
        env['WINEPREFIX'] = prefix
        
        # Wine Gecko
        gecko = os.path.join(temp_dir, 'wine-gecko-2.47.4-x86_64.msi')
        debug_print("Installing wine-gecko...")
        subprocess.run([wine, 'msiexec', '/i', gecko], env=env, check=True)
        
        # VC Redist
        for arch in ['x64', 'x86']:
            vc = os.path.join(temp_dir, f'vc_redist.{arch}.exe')
            debug_print(f"Installing VC Redist {arch}...")
            subprocess.run([wine, vc, '/install', '/quiet', '/norestart'], env=env, check=True)
        
        # Winetricks
        debug_print("Installing dxvk + corefonts...")
        subprocess.run([tricks, '-q', 'dxvk', 'corefonts'], env=env, check=True)
        
        debug_print("Installing gdiplus + fontsmooth...")
        subprocess.run([tricks, '-q', 'gdiplus', 'fontsmooth=rgb'], env=env, check=True)
    
    def finalize(self, temp_dir):
        """Finalize installation"""
        prefix = os.path.join(self.user_location, 'Wineprefix')
        wine = os.path.join(self.user_location, 'wine', 'bin', 'wine')
        system32 = os.path.join(prefix, 'drive_c', 'windows', 'system32')
        
        # Copy DLLs
        for dll_name, dll_path in self.dll_files.items():
            dst = os.path.join(system32, dll_name)
            shutil.copy2(dll_path, dst)
            debug_print(f"Copied {dll_name}")
        
        # Registry
        env = os.environ.copy()
        env['WINEPREFIX'] = prefix
        subprocess.run([wine, 'reg', 'add', 'HKCU\\Software\\Wine\\DllOverrides',
                       '/v', 'msxml3', '/d', 'native,builtin', '/f'], env=env, check=True)
        debug_print("Registry set")
        
        # Set theme/colors registry
        self.set_theme_registry(wine, prefix)
        
        # Save config
        config = {
            'version': '2.0',
            'user_location': self.user_location,
            'wine_path': os.path.join(self.user_location, 'wine'),
            'wineprefix': prefix,
            'aenux_path': os.path.join(self.user_location, 'AeNux')
        }
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
        debug_print(f"Config saved")
        
        # Create shortcuts
        env = os.environ.copy()
        env['WINEPREFIX'] = prefix
        wine_path = os.path.join(self.user_location, 'wine')
        wineserver = os.path.join(wine_path, 'bin', 'wineserver')
        self._create_shortcuts(env, wine_path, wineserver, prefix)
        
        # Run AppShortcutMake.sh to create desktop shortcuts
        script_dir = os.path.dirname(__file__)
        shortcut_script = os.path.join(script_dir, 'AppShortcutMake.sh')
        if os.path.exists(shortcut_script):
            try:
                debug_print("Running AppShortcutMake.sh...")
                subprocess.run(['bash', shortcut_script], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                debug_print("Desktop shortcuts created successfully")
            except Exception as e:
                debug_print(f"Warning: Failed to create desktop shortcuts: {e}")
        
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        debug_print("Cleaned up TEMP")
    
    def set_theme_registry(self, wine_bin, prefix):
        """Set Wine theme/colors registry"""
        # Theme colors mapping
        colors = {
            "ActiveBorder": "49 54 58",
            "ActiveTitle": "49 54 58",
            "AppWorkSpace": "60 64 72",
            "Background": "49 54 58",
            "ButtonAlternativeFace": "60 64 72",
            "ButtonDkShadow": "30 33 36",
            "ButtonFace": "49 54 58",
            "ButtonHilight": "119 126 140",
            "ButtonLight": "60 64 72",
            "ButtonShadow": "40 43 47",
            "ButtonText": "219 220 222",
            "GradientActiveTitle": "49 54 58",
            "GradientInactiveTitle": "49 54 58",
            "GrayText": "100 104 110",
            "Hilight": "119 126 140",
            "HilightText": "255 255 255",
            "InactiveBorder": "49 54 58",
            "InactiveTitle": "49 54 58",
            "InactiveTitleText": "219 220 222",
            "InfoText": "180 185 190",
            "InfoWindow": "49 54 58",
            "Menu": "40 43 47",
            "MenuBar": "40 43 47",
            "MenuHilight": "119 126 140",
            "MenuText": "219 220 222",
            "Scrollbar": "60 64 72",
            "TitleText": "219 220 222",
            "Window": "35 38 41",
            "WindowFrame": "49 54 58",
            "WindowText": "219 220 222",
        }
        
        env = os.environ.copy()
        env['WINEPREFIX'] = prefix
        
        # Set each color
        for key, value in colors.items():
            try:
                subprocess.run(
                    [wine_bin, 'reg', 'add',
                     'HKCU\\Control Panel\\Colors',
                     '/v', key,
                     '/d', value,
                     '/f'],
                    env=env,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError as e:
                debug_print(f"Warning: Failed to set {key}: {e}")
    def _show_success(self):
        """Show success dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Installation Complete!"
        )
        dialog.format_secondary_text("AeNux installed successfully!")
        dialog.run()
        dialog.destroy()
        # Attempt to stop any running Wine processes for the created prefix
        try:
            wine_path = os.path.join(self.user_location, 'wine')
            wine_prefix = os.path.join(self.user_location, 'Wineprefix')
            self._kill_wine_processes(wine_path, wine_prefix)
        except Exception:
            pass

        self.is_installing = False
        self.install_btn.set_label("Installed")
        self.install_btn.set_sensitive(False)
        Gtk.main_quit()

    def _create_shortcuts(self, env, wine_path, wineserver_path, wineprefix):
        """Create shortcuts to Linux folders in wineprefix"""
        try:
            debug_print("[DEBUG] Creating shortcuts...")
            
            wine_drive_c = os.path.join(wineprefix, "drive_c")
            fav_dir = os.path.join(wine_drive_c, "users", "*", "Favorites")
            
            fav_paths = glob.glob(fav_dir)
            if not fav_paths:
                debug_print("[DEBUG] No Favorites directory found, skipping shortcuts")
                return True
            
            target_fav_dir = fav_paths[0]
            home_dir = os.path.expanduser("~")
            
            # Remove existing symlinks and create new ones
            folders = ["Documents", "Downloads", "Pictures", "Videos", "Music"]
            for folder in folders:
                link_path = os.path.join(target_fav_dir, folder)
                
                # Remove existing link if it exists
                if os.path.exists(link_path):
                    if os.path.islink(link_path):
                        os.remove(link_path)
                    elif os.path.isdir(link_path):
                        shutil.rmtree(link_path)
                    else:
                        os.remove(link_path)
                
                # Create new symlink
                linux_path = os.path.join(home_dir, folder)
                if os.path.exists(linux_path):
                    os.symlink(linux_path, link_path)
                    debug_print(f"[DEBUG] Created shortcut: {folder}")
            
            # Create AeNux shortcut from config
            aenux_path = self.config.get('aenux_path', os.path.join(self.user_location, 'AeNux'))
            if os.path.exists(aenux_path):
                ae_nux_link = os.path.join(target_fav_dir, "AeNux")
                if os.path.exists(ae_nux_link):
                    if os.path.islink(ae_nux_link):
                        os.remove(ae_nux_link)
                    elif os.path.isdir(ae_nux_link):
                        shutil.rmtree(ae_nux_link)
                    else:
                        os.remove(ae_nux_link)
                os.symlink(aenux_path, ae_nux_link)
                debug_print(f"[DEBUG] Created AeNux shortcut")
            
            subprocess.run([wineserver_path, "-k"], env=env, capture_output=True)
            debug_print("[DEBUG] Shortcuts created successfully")
            return True
            
        except Exception as e:
            debug_print(f"[WARNING] Shortcut creation failed: {str(e)}")
            return True  # Not critical, continue anyway
    
    def _kill_wine_processes(self, wine_path, wineprefix):
        """Kill wineserver processes for a given wine installation."""
        wineserver = os.path.join(wine_path, 'bin', 'wineserver')
        if not os.path.exists(wineserver):
            debug_print(f"Wineserver not found at {wineserver}")
            return

        env = os.environ.copy()
        env['WINEPREFIX'] = wineprefix

        try:
            subprocess.run([wineserver, '-k'], env=env, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([wineserver, '-w'], env=env, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            debug_print("Wineserver killed")
        except Exception as e:
            debug_print(f"Failed to kill wineserver: {e}")
    
    def _show_error_final(self, msg):
        """Show error and exit"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Installation Error!"
        )
        dialog.format_secondary_text(msg)
        dialog.run()
        dialog.destroy()
        self.install_btn.set_label("Install")
        self.install_btn.set_sensitive(False)
        Gtk.main_quit()
    
    def run(self):
        """Start app"""
        debug_print("Starting installer")
        self.window.show_all()
        Gtk.main()

if __name__ == '__main__':
    app = AeNuxInstaller()
    app.run()
