#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os
import json
import subprocess
import shutil
import threading
from pathlib import Path
import sys

# Enable stdout/stderr flushing
sys.stdout = sys.stderr = __builtins__.open(sys.stdout.fileno(), 'w', 1)

print("[DEBUG] PlugIn.py started")
print(f"[DEBUG] Python version: {sys.version}")

class PluginInstaller:
    def __init__(self):
        print("[DEBUG] Initializing PluginInstaller")
        self.plugin_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"[DEBUG] Plugin directory: {self.plugin_dir}")
        
        self.config_path = os.path.join(os.path.dirname(self.plugin_dir), "script", "aenux_config.json")
        print(f"[DEBUG] Config path: {self.config_path}")
        
        self.config = self.load_config()
        print(f"[DEBUG] Config loaded: {self.config}")
        
        self.plugins = {}
        self.selected_plugins = {}
        self.installer_window = None
        self.progress_window = None
        print("[DEBUG] PluginInstaller initialized")
        
    def load_config(self):
        """Load configuration from aenux_config.json"""
        try:
            print(f"[DEBUG] Loading config from: {self.config_path}")
            if not os.path.exists(self.config_path):
                print(f"[ERROR] Config file not found: {self.config_path}")
                self.show_error_dialog(f"Config file not found: {self.config_path}")
                return None
            
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                print(f"[DEBUG] Config loaded successfully: {config}")
                return config
        except Exception as e:
            print(f"[ERROR] Failed to load config: {str(e)}")
            self.show_error_dialog(f"Failed to load config: {str(e)}")
            return None
    
    def scan_plugins(self):
        """Scan and categorize all plugins"""
        print("[DEBUG] Scanning plugins...")
        self.plugins = {
            'AEX': [],
            'CEP': [],
            'Installer': [],
            'Scripts': [],
            'Presets': []
        }
        
        plugin_path = self.plugin_dir
        
        # Create necessary folders if they don't exist
        required_folders = ['aex', 'CEP', 'installer', 'preset-backup', 'scripts']
        for folder in required_folders:
            folder_path = os.path.join(plugin_path, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                print(f"[DEBUG] Created missing folder: {folder_path}")
        
        # Scan AEX folder
        aex_path = os.path.join(plugin_path, 'aex')
        print(f"[DEBUG] Scanning AEX folder: {aex_path}")
        if os.path.exists(aex_path):
            for item in os.listdir(aex_path):
                item_path = os.path.join(aex_path, item)
                if item.endswith('.aex') or os.path.isdir(item_path):
                    self.plugins['AEX'].append({
                        'name': item,
                        'path': item_path,
                        'type': 'file' if item.endswith('.aex') else 'folder'
                    })
                    print(f"[DEBUG] Found AEX: {item}")
        else:
            print(f"[WARNING] AEX folder not found: {aex_path}")
        
        # Scan CEP folder (only main folders)
        cep_path = os.path.join(plugin_path, 'CEP')
        print(f"[DEBUG] Scanning CEP folder: {cep_path}")
        if os.path.exists(cep_path):
            for item in os.listdir(cep_path):
                item_path = os.path.join(cep_path, item)
                if os.path.isdir(item_path):
                    self.plugins['CEP'].append({
                        'name': item,
                        'path': item_path,
                        'type': 'folder'
                    })
                    print(f"[DEBUG] Found CEP folder: {item}")
            
            # Check for AddKeys.reg
            addkeys_path = os.path.join(cep_path, 'AddKeys.reg')
            if os.path.exists(addkeys_path):
                self.plugins['CEP'].append({
                    'name': 'AddKeys.reg',
                    'path': addkeys_path,
                    'type': 'file'
                })
                print(f"[DEBUG] Found AddKeys.reg")
        else:
            print(f"[WARNING] CEP folder not found: {cep_path}")
        
        # Scan Installer folder (only .exe files)
        installer_path = os.path.join(plugin_path, 'installer')
        print(f"[DEBUG] Scanning Installer folder: {installer_path}")
        if os.path.exists(installer_path):
            for item in os.listdir(installer_path):
                if item.endswith('.exe'):
                    item_path = os.path.join(installer_path, item)
                    self.plugins['Installer'].append({
                        'name': item,
                        'path': item_path,
                        'type': 'file'
                    })
                    print(f"[DEBUG] Found Installer: {item}")
        else:
            print(f"[WARNING] Installer folder not found: {installer_path}")
        
        # Scan preset-backup folder
        preset_path = os.path.join(plugin_path, 'preset-backup')
        print(f"[DEBUG] Scanning Presets folder: {preset_path}")
        if os.path.exists(preset_path):
            for item in os.listdir(preset_path):
                item_path = os.path.join(preset_path, item)
                if os.path.isdir(item_path):
                    self.plugins['Presets'].append({
                        'name': item,
                        'path': item_path,
                        'type': 'folder'
                    })
                    print(f"[DEBUG] Found Preset: {item}")
        else:
            print(f"[WARNING] Presets folder not found: {preset_path}")
        
        # Scan scripts folder
        scripts_path = os.path.join(plugin_path, 'scripts')
        print(f"[DEBUG] Scanning Scripts folder: {scripts_path}")
        if os.path.exists(scripts_path):
            for item in os.listdir(scripts_path):
                item_path = os.path.join(scripts_path, item)
                self.plugins['Scripts'].append({
                    'name': item,
                    'path': item_path,
                    'type': 'file' if os.path.isfile(item_path) else 'folder'
                })
                print(f"[DEBUG] Found Script: {item}")
        else:
            print(f"[WARNING] Scripts folder not found: {scripts_path}")
        
        print(f"[DEBUG] Plugin scan complete. Total plugins: {sum(len(v) for v in self.plugins.values())}")
        
        # Initialize selected plugins dict
        for category in self.plugins:
            self.selected_plugins[category] = {}
            for plugin in self.plugins[category]:
                self.selected_plugins[category][plugin['name']] = False
    
    def show_plugin_list(self):
        """Show the Plugin Installer GUI"""
        print("[DEBUG] show_plugin_list called")
        self.scan_plugins()
        
        print("[DEBUG] Creating main window")
        self.installer_window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.installer_window.set_title("Plugin Installer")
        self.installer_window.set_default_size(700, 500)
        self.installer_window.set_border_width(10)
        
        # Main VBox
        main_box = Gtk.VBox(spacing=10)
        self.installer_window.add(main_box)
        
        # Create scrolled window for the table
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        main_box.pack_start(scrolled_window, True, True, 0)
        
        # Create the store
        self.store = Gtk.ListStore(bool, str, str)  # checkbox, plugin name, category
        
        # Populate store
        print("[DEBUG] Populating store with plugins")
        for category in ['Installer', 'AEX', 'CEP', 'Presets', 'Scripts']:
            for plugin in self.plugins.get(category, []):
                self.store.append([False, plugin['name'], category])
                print(f"[DEBUG] Added to store: {plugin['name']} ({category})")
        
        # Create tree view
        tree_view = Gtk.TreeView(model=self.store)
        tree_view.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        
        # Checkbox column
        checkbox_renderer = Gtk.CellRendererToggle()
        checkbox_renderer.connect("toggled", self.on_checkbox_toggled)
        checkbox_column = Gtk.TreeViewColumn("Select", checkbox_renderer, active=0)
        tree_view.append_column(checkbox_column)
        
        # Plugin name column
        name_renderer = Gtk.CellRendererText()
        name_column = Gtk.TreeViewColumn("Plugin Name", name_renderer, text=1)
        name_column.set_expand(True)
        tree_view.append_column(name_column)
        
        # Category column
        category_renderer = Gtk.CellRendererText()
        category_column = Gtk.TreeViewColumn("Category", category_renderer, text=2)
        tree_view.append_column(category_column)
        
        scrolled_window.add(tree_view)
        
        # Select All checkbox
        select_all_box = Gtk.HBox(spacing=10)
        main_box.pack_start(select_all_box, False, False, 0)
        
        select_all_checkbox = Gtk.CheckButton(label="Select All")
        select_all_checkbox.connect("toggled", self.on_select_all_toggled, tree_view)
        select_all_box.pack_start(select_all_checkbox, False, False, 0)
        
        # Buttons
        button_box = Gtk.HBox(spacing=10)
        main_box.pack_start(button_box, False, False, 0)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", self.on_cancel)
        button_box.pack_start(cancel_button, False, False, 0)
        
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", self.on_refresh)
        button_box.pack_start(refresh_button, False, False, 0)
        
        install_selected_button = Gtk.Button(label="Install Selected")
        install_selected_button.connect("clicked", self.on_install_selected)
        button_box.pack_start(install_selected_button, False, False, 0)
        
        self.installer_window.connect("destroy", Gtk.main_quit)
        print("[DEBUG] Showing window")
        self.installer_window.show_all()
        
        self.tree_view = tree_view
        self.select_all_checkbox = select_all_checkbox
        print("[DEBUG] show_plugin_list complete")
    
    def on_checkbox_toggled(self, widget, path):
        """Handle checkbox toggle"""
        self.store[path][0] = not self.store[path][0]
    
    def on_select_all_toggled(self, widget, tree_view):
        """Handle select all checkbox"""
        state = widget.get_active()
        for row in self.store:
            row[0] = state
    
    def on_cancel(self, widget):
        """Handle cancel button"""
        self.installer_window.destroy()
    
    def on_refresh(self, widget):
        """Handle refresh button - rescan plugins and update list"""
        print("[DEBUG] Refresh button clicked")
        # Rescan plugins
        self.scan_plugins()
        
        # Clear existing store
        self.store.clear()
        
        # Repopulate store with updated plugin list
        for category in ['Installer', 'AEX', 'CEP', 'Presets', 'Scripts']:
            for plugin in self.plugins.get(category, []):
                self.store.append([False, plugin['name'], category])
                print(f"[DEBUG] Added to store after refresh: {plugin['name']} ({category})")
        
        # Uncheck select all checkbox
        if self.select_all_checkbox:
            self.select_all_checkbox.set_active(False)
        
        print("[DEBUG] Plugin list refreshed successfully")
    
    def on_install_selected(self, widget):
        """Handle install selected button"""
        print("[DEBUG] Install Selected clicked")
        selected = []
        for row in self.store:
            if row[0]:  # If checkbox is checked
                selected.append({
                    'name': row[1],
                    'category': row[2]
                })
                print(f"[DEBUG] Selected: {row[1]} ({row[2]})")
        
        if not selected:
            print("[WARNING] No plugins selected")
            self.show_error_dialog("No plugins selected for installation")
            return
        
        print(f"[DEBUG] Total selected: {len(selected)}")
        # Hide installer window instead of destroying it
        self.installer_window.hide()
        self.start_installation(selected)
           
    def start_installation(self, selected_plugins):
        """Start the installation process"""
        print("[DEBUG] start_installation called")
        self.progress_window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.progress_window.set_title("Installing plugin")
        self.progress_window.set_default_size(600, 450)
        self.progress_window.set_border_width(10)
        self.progress_window.set_deletable(False)  # Prevent closing during installation
        
        main_vbox = Gtk.VBox(spacing=10)
        self.progress_window.add(main_vbox)
        
        # Status label
        self.progress_label = Gtk.Label(label="Initializing installation...")
        self.progress_label.set_line_wrap(True)
        main_vbox.pack_start(self.progress_label, False, False, 0)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        main_vbox.pack_start(self.progress_bar, False, False, 0)
        
        # Log area with scrolled window
        log_frame = Gtk.Frame(label="Installation Log")
        main_vbox.pack_start(log_frame, True, True, 0)
        
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        log_frame.add(scrolled_window)
        
        # Text view for logs
        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled_window.add(self.log_view)
        
        # Bottom info label
        self.completion_label = Gtk.Label(label="")
        main_vbox.pack_start(self.completion_label, False, False, 0)
        
        # Buttons box
        button_box = Gtk.HBox(spacing=10)
        main_vbox.pack_start(button_box, False, False, 0)
        
        self.close_button = Gtk.Button(label="Close")
        self.close_button.set_sensitive(False)  # Disabled during installation
        self.close_button.connect("clicked", self.on_close_progress)
        button_box.pack_end(self.close_button, False, False, 0)
        
        print("[DEBUG] Showing progress window")
        self.progress_window.show_all()
        
        # Run installation using threading
        print("[DEBUG] Starting installation thread")
        self.install_thread = threading.Thread(target=self.run_installation, args=(selected_plugins,))
        self.install_thread.daemon = False  # Non-daemon thread
        self.install_thread.start()
        print("[DEBUG] Installation thread started")
    
    def run_installation(self, selected_plugins):
        """Run installation process"""
        print("[DEBUG] run_installation started")
        try:
            total_steps = len(selected_plugins)
            current_step = 0
            
            print(f"[DEBUG] Starting installation of {total_steps} plugins")
            self.add_log(f"Starting installation of {total_steps} plugins...\n")
            
            for plugin_info in selected_plugins:
                name = plugin_info['name']
                category = plugin_info['category']
                
                print(f"[DEBUG] Installing {name} ({category}) - Step {current_step + 1}/{total_steps}")
                GLib.idle_add(self.update_progress, f"Installing {name}...", current_step / total_steps)
                self.add_log(f"[{current_step + 1}/{total_steps}] Installing {name} ({category})...")
                
                # Wait a bit for GTK to process
                import time
                time.sleep(0.05)
                
                # Find plugin in scanned plugins
                plugin = None
                for p in self.plugins.get(category, []):
                    if p['name'] == name:
                        plugin = p
                        break
                
                if not plugin:
                    raise Exception(f"Plugin not found: {name}")
                
                # Install based on category
                print(f"[DEBUG] Installing {category}: {name}")
                if category == 'Installer':
                    self.install_exe(plugin['path'])
                elif category == 'AEX':
                    self.install_aex(plugin['path'], plugin['type'])
                elif category == 'CEP':
                    if name == 'AddKeys.reg':
                        self.install_regedit(plugin['path'])
                    else:
                        self.install_cep(plugin['path'])
                elif category == 'Presets':
                    self.install_preset(plugin['path'])
                elif category == 'Scripts':
                    self.install_script(plugin['path'])
                
                print(f"[DEBUG] Completed: {name}")
                self.add_log(f"✓ Completed: {name}\n")
                current_step += 1
            
            print("[DEBUG] All installations complete")
            self.add_log(f"\n{'='*50}\n✓ INSTALLATION COMPLETED SUCCESSFULLY!\n{'='*50}\n")
            GLib.idle_add(self.installation_complete)
            
        except Exception as e:
            print(f"[ERROR] Installation failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.add_log(f"\n✗ ERROR: {str(e)}\n")
            GLib.idle_add(self.show_installation_error, str(e))
    
    def install_exe(self, exe_path):
        """Install .exe file using wine dengan parameter silent"""
        print(f"[DEBUG] install_exe called for: {exe_path}")
        wine_bin = os.path.join(self.config['wine_path'], 'bin', 'wine')
        wineprefix = self.config['wineprefix']
        
        if not os.path.exists(wine_bin):
            raise Exception(f"Wine binary not found: {wine_bin}")
        
        if not os.path.exists(exe_path):
            raise Exception(f"Installer file not found: {exe_path}")
        
        env = os.environ.copy()
        env['WINEPREFIX'] = wineprefix
        
        # Tambahkan parameter /verysilent /suppressmsgboxes
        exe_name = os.path.basename(exe_path).lower()
        
        # Tentukan parameter berdasarkan jenis installer
        if exe_name.startswith(('keygen', 'crack', 'patch')):
            # Untuk keygen/crack, jangan gunakan silent parameter
            args = [wine_bin, exe_path]
            self.add_log(f"  Running installer (normal mode): {exe_name}\n")
        else:
            # Untuk installer biasa, gunakan parameter silent
            args = [wine_bin, exe_path, '/verysilent', '/suppressmsgboxes']
            self.add_log(f"  Running installer (silent mode): {exe_name}\n")
        
        print(f"[DEBUG] Running: {' '.join(args)}")
        
        # Tambahkan timeout untuk mencegah hang
        try:
            result = subprocess.run(
                args,
                env=env,
                capture_output=True,
                text=True,
                timeout=300,  # Timeout 5 menit
                check=False  # Jangan raise exception otomatis
            )
            
            print(f"[DEBUG] Wine return code: {result.returncode}")
            print(f"[DEBUG] Wine stdout: {result.stdout[:200]}...")
            print(f"[DEBUG] Wine stderr: {result.stderr[:200]}...")
            
            # Log output untuk debugging
            if result.stdout:
                self.add_log(f"  Output: {result.stdout[:500]}\n")
            if result.stderr:
                self.add_log(f"  Errors: {result.stderr[:500]}\n")
            
            # Cek apakah installer berhasil (return code 0 atau 3010 umum untuk restart required)
            if result.returncode not in [0, 3010, 1641, 3011]:
                # Beberapa installer mengembalikan code khusus
                # 3010: RESTART_REQUIRED, 1641: SUCCESS_REBOOT_INITIATED
                error_msg = f"Installer returned code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr[:200]}"
                raise Exception(f"Failed to install {os.path.basename(exe_path)}: {error_msg}")
            
            # Tunggu sebentar agar installer selesai
            import time
            time.sleep(2)
            
        except subprocess.TimeoutExpired:
            self.add_log(f"  Warning: Installer timeout, mungkin masih berjalan di background\n")
            print(f"[WARNING] Installer timeout: {exe_path}")
            # Tidak raise exception, anggap berhasil
        
        except Exception as e:
            raise Exception(f"Failed to install {os.path.basename(exe_path)}: {str(e)}")
    
    def install_aex(self, aex_path, aex_type):
        """Copy AEX files/folders to aenux Plug-Ins folder"""
        print(f"[DEBUG] install_aex called for: {aex_path} (type: {aex_type})")
        aenux_plugins = os.path.join(self.config['aenux_path'], 'Plug-Ins')
        
        if not os.path.exists(aenux_plugins):
            os.makedirs(aenux_plugins, exist_ok=True)
            print(f"[DEBUG] Created Plug-Ins folder: {aenux_plugins}")
        
        if aex_type == 'file':
            # Copy file
            dest = os.path.join(aenux_plugins, os.path.basename(aex_path))
            print(f"[DEBUG] Copying file: {aex_path} -> {dest}")
            shutil.copy2(aex_path, dest)
        else:
            # Copy folder
            dest = os.path.join(aenux_plugins, os.path.basename(aex_path))
            if os.path.exists(dest):
                print(f"[DEBUG] Removing existing folder: {dest}")
                shutil.rmtree(dest)
            print(f"[DEBUG] Copying folder: {aex_path} -> {dest}")
            shutil.copytree(aex_path, dest)
    
    def install_cep(self, cep_folder):
        """Copy CEP folder to Adobe CEP extensions"""
        print(f"[DEBUG] install_cep called for: {cep_folder}")
        cep_extensions = os.path.join(
            self.config['wineprefix'],
            'drive_c',
            'Program Files (x86)',
            'Common Files',
            'Adobe',
            'CEP',
            'extensions'
        )
        
        os.makedirs(cep_extensions, exist_ok=True)
        print(f"[DEBUG] CEP extensions folder: {cep_extensions}")
        
        # Copy the entire folder
        dest = os.path.join(cep_extensions, os.path.basename(cep_folder))
        if os.path.exists(dest):
            print(f"[DEBUG] Removing existing CEP folder: {dest}")
            shutil.rmtree(dest)
        print(f"[DEBUG] Copying CEP folder: {cep_folder} -> {dest}")
        shutil.copytree(cep_folder, dest)
    
    def install_regedit(self, reg_file):
        """Add registry key using wine regedit"""
        print(f"[DEBUG] install_regedit called for: {reg_file}")
        wine_regedit = os.path.join(self.config['wine_path'], 'bin', 'regedit')
        wineprefix = self.config['wineprefix']
        
        if not os.path.exists(wine_regedit):
            raise Exception(f"Wine regedit not found: {wine_regedit}")
        
        if not os.path.exists(reg_file):
            raise Exception(f"Registry file not found: {reg_file}")
        
        env = os.environ.copy()
        env['WINEPREFIX'] = wineprefix
        
        print(f"[DEBUG] Running: {wine_regedit} {reg_file}")
        result = subprocess.run(
            [wine_regedit, reg_file],
            env=env,
            capture_output=True,
            text=True
        )
        
        print(f"[DEBUG] Regedit return code: {result.returncode}")
        if result.returncode != 0:
            raise Exception(f"Failed to add registry key: {result.stderr}")
    
    def install_preset(self, preset_folder):
        """Copy preset folder to aenux Presets"""
        print(f"[DEBUG] install_preset called for: {preset_folder}")
        presets_dir = os.path.join(self.config['aenux_path'], 'Presets')
        
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir, exist_ok=True)
            print(f"[DEBUG] Created Presets folder: {presets_dir}")
        
        # Copy the folder
        dest = os.path.join(presets_dir, os.path.basename(preset_folder))
        if os.path.exists(dest):
            print(f"[DEBUG] Removing existing preset: {dest}")
            shutil.rmtree(dest)
        print(f"[DEBUG] Copying preset: {preset_folder} -> {dest}")
        shutil.copytree(preset_folder, dest)
    
    def install_script(self, script_path):
        """Copy scripts to aenux Scripts folder"""
        print(f"[DEBUG] install_script called for: {script_path}")
        scripts_dir = os.path.join(self.config['aenux_path'], 'Scripts')
        
        if not os.path.exists(scripts_dir):
            os.makedirs(scripts_dir, exist_ok=True)
            print(f"[DEBUG] Created Scripts folder: {scripts_dir}")
        
        if os.path.isfile(script_path):
            # Copy file
            dest = os.path.join(scripts_dir, os.path.basename(script_path))
            print(f"[DEBUG] Copying script file: {script_path} -> {dest}")
            shutil.copy2(script_path, dest)
        else:
            # Copy folder
            dest = os.path.join(scripts_dir, os.path.basename(script_path))
            if os.path.exists(dest):
                print(f"[DEBUG] Removing existing script folder: {dest}")
                shutil.rmtree(dest)
            print(f"[DEBUG] Copying script folder: {script_path} -> {dest}")
            shutil.copytree(script_path, dest)
    
    def update_progress(self, message, progress):
        """Update progress bar and label"""
        print(f"[DEBUG] Progress: {message} ({progress*100:.1f}%)")
        if self.progress_label and self.progress_bar:
            self.progress_label.set_text(message)
            self.progress_bar.set_fraction(min(progress, 1.0))
            # Force GTK to update
            while Gtk.events_pending():
                Gtk.main_iteration()
        return False
    
    def add_log(self, message):
        """Add message to log view"""
        GLib.idle_add(self._add_log_idle, message)
    
    def _add_log_idle(self, message):
        """Add message to log (GTK thread safe)"""
        if self.log_buffer:
            # Append to end of buffer
            end_iter = self.log_buffer.get_end_iter()
            self.log_buffer.insert(end_iter, message)
            
            # Auto-scroll to bottom
            self.log_view.scroll_to_iter(end_iter, 0, False, 0, 0)
            
            # Process GTK events
            while Gtk.events_pending():
                Gtk.main_iteration()
        return False
    
    def installation_complete(self):
        """Show completion message"""
        print("[DEBUG] installation_complete called")
        self.progress_label.set_text("✓ Installation Completed Successfully!")
        self.progress_bar.set_fraction(1.0)
        
        # Update completion label
        if self.completion_label:
            self.completion_label.set_markup(
                '<span foreground="green" weight="bold">✓ Installation Completed Successfully!</span>\n'
                'All selected plugins have been installed.'
            )
        
        # Enable close button
        if self.close_button:
            self.close_button.set_sensitive(True)
        
        # Allow window to be closed
        self.progress_window.set_deletable(True)
        
        print("[DEBUG] installation_complete finished")
        return False
    
    def on_close_progress(self, widget):
        """Handle close button on progress window"""
        print("[DEBUG] Close button clicked")
        self.progress_window.destroy()
        print("[DEBUG] Quitting GTK")
        Gtk.main_quit()
    
    def show_installation_error(self, error_message):
        """Show error during installation"""
        print(f"[ERROR] show_installation_error called: {error_message}")
        self.progress_label.set_text(f"✗ Installation Failed: {error_message}")
        
        # Update completion label
        if self.completion_label:
            self.completion_label.set_markup(
                '<span foreground="red" weight="bold">✗ Installation Failed!</span>\n'
                f'Error: {error_message}'
            )
        
        # Enable close button
        if self.close_button:
            self.close_button.set_sensitive(True)
        
        # Allow window to be closed
        self.progress_window.set_deletable(True)
        
        return False
    
    def show_error_dialog(self, message):
        """Show error dialog"""
        print(f"[ERROR] Showing error dialog: {message}")
        dialog = Gtk.MessageDialog(
            type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            message_format="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def run(self):
        """Run the application"""
        print("[DEBUG] run() method called")
        if not self.config:
            print("[ERROR] Config is None, exiting")
            return
        
        print("[DEBUG] Calling show_plugin_list()")
        self.show_plugin_list()
        print("[DEBUG] Calling Gtk.main()")
        Gtk.main()
        print("[DEBUG] Gtk.main() exited")


if __name__ == "__main__":
    print("[DEBUG] Script started")
    try:
        app = PluginInstaller()
        print("[DEBUG] PluginInstaller created, calling run()")
        app.run()
        print("[DEBUG] app.run() completed")
    except Exception as e:
        print(f"[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()