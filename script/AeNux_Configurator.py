#!/usr/bin/python3
"""AeNux Configurator v2.0"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os, json, subprocess, shutil, threading, glob

DEBUG = True

def debug_print(msg):
    if DEBUG: print(f"[DEBUG] {msg}")

class AeNuxConfigurator:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.ui_file = os.path.join(os.path.dirname(__file__), 'gui.ui')
        
        try:
            self.builder.add_from_file(self.ui_file)
        except Exception as e:
            debug_print(f"Error loading UI: {e}")
            raise
        
        # Load configuration
        self.config = self.load_config()
        if not self.config:
            self.show_error_and_exit("Configuration file not found")
            return
        
        self.window = self.builder.get_object('Config')
        self.select_runner = self.builder.get_object('select_runner')
        self.select_wineprefix = self.builder.get_object('select_wineprefix_folder')
        
        # Get all buttons from Folder tab
        self.notebook = self.builder.get_object('GtkNotebook')
        
        # Setup folder buttons
        self.setup_folder_buttons()
        
        # Setup Wine tab
        self.setup_wine_tab()
        
        # Setup Uninstall tab
        self.setup_uninstall_tab()
        
        self.window.connect('delete-event', Gtk.main_quit)
        self.wineprefix_disabled = True  # Initially disabled
        
        debug_print(f"Configurator initialized. Config: {self.config}")
    
    def load_config(self):
        """Load configuration from JSON"""
        # Try to find config in parent directory and common locations
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'aenux_config.json'),
            os.path.expanduser('~/aenux_config.json'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        config = json.load(f)
                    debug_print(f"Config loaded from: {path}")
                    return config
                except Exception as e:
                    debug_print(f"Error loading config from {path}: {e}")
        
        debug_print("No valid configuration file found")
        return None
    
    def setup_folder_buttons(self):
        """Setup folder opening buttons"""
        # Get the notebook and find buttons in first tab
        try:
            # Find the grid with buttons
            container = self.builder.get_object('main_window')
            
            # We'll find buttons by their labels after building
            # This requires iterating through the UI structure
            def find_and_connect_buttons(widget, buttons_info):
                if isinstance(widget, Gtk.Button):
                    label = widget.get_label()
                    for info in buttons_info:
                        if label == info['label']:
                            widget.connect('clicked', info['callback'])
                            debug_print(f"Connected button: {label}")
                
                if hasattr(widget, 'get_children'):
                    for child in widget.get_children():
                        find_and_connect_buttons(child, buttons_info)
            
            buttons_info = [
                {'label': 'AeNux', 'callback': self.on_aenux_clicked},
                {'label': 'PlugIn', 'callback': self.on_plugin_clicked},
                {'label': 'Preset', 'callback': self.on_preset_clicked},
                {'label': 'Runner', 'callback': self.on_runner_clicked},
                {'label': 'Patch Runner', 'callback': self.on_patch_runner_clicked},
                {'label': 'Remove wineprefix', 'callback': self.on_remove_wineprefix_clicked},
            ]
            
            find_and_connect_buttons(self.window, buttons_info)
            
        except Exception as e:
            debug_print(f"Error setting up folder buttons: {e}")
    
    def setup_wine_tab(self):
        """Setup Wine configuration tab"""
        try:
            # Set default values from config
            wine_path = self.config.get('wine_path', '')
            wineprefix_path = self.config.get('wineprefix', '')
            
            if wine_path:
                self.select_runner.set_filename(wine_path)
            
            if wineprefix_path:
                self.select_wineprefix.set_filename(wineprefix_path)
                self.select_wineprefix.set_sensitive(False)
            
            # Connect selection signals
            self.select_runner.connect('selection-changed', self.on_runner_selection_changed)
            self.select_wineprefix.connect('selection-changed', self.on_wineprefix_selection_changed)
            
            # Connect kill wine button
            kill_wine_button = self.builder.get_object('kill_wine_button')
            if kill_wine_button:
                kill_wine_button.connect('clicked', self.on_kill_wine_clicked)
            
            debug_print(f"Wine tab setup - Runner: {wine_path}, Prefix: {wineprefix_path}")
        except Exception as e:
            debug_print(f"Error setting up wine tab: {e}")
    
    def setup_uninstall_tab(self):
        """Setup uninstall tab"""
        try:
            self.uninstall_button = self.builder.get_object('uninstall_button')
            self.uninstall_progressbar = self.builder.get_object('uninstall_progressbar')
            
            self.uninstall_button.connect('clicked', self.on_uninstall_clicked)
            
            debug_print("Uninstall tab setup complete")
        except Exception as e:
            debug_print(f"Error setting up uninstall tab: {e}")
    
    def on_runner_selection_changed(self, widget):
        """Handle runner selection change"""
        runner_path = self.select_runner.get_filename()
        debug_print(f"Runner selected: {runner_path}")
    
    def on_wineprefix_selection_changed(self, widget):
        """Handle wineprefix folder selection change"""
        wineprefix_path = self.select_wineprefix.get_filename()
        if wineprefix_path:
            self.config['wineprefix'] = wineprefix_path
            self.save_config()
            debug_print(f"Wineprefix updated: {wineprefix_path}")
        else:
            debug_print("Wineprefix selection cleared")
    
    def on_kill_wine_clicked(self, widget):
        """Kill Wine processes"""
        try:
            wine_path = self.config.get('wine_path', '')
            wineprefix = self.config.get('wineprefix', '')
            
            if not wine_path or not wineprefix:
                self.show_error("Wine path or prefix not configured")
                return
            
            wineserver = os.path.join(wine_path, 'bin', 'wineserver')
            
            if not os.path.exists(wineserver):
                self.show_error(f"Wineserver not found at {wineserver}")
                return
            
            debug_print(f"Killing Wine processes for {wineprefix}")
            
            env = os.environ.copy()
            env['WINEPREFIX'] = wineprefix
            
            # Kill wine processes
            subprocess.run([wineserver, '-k'], env=env, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Wait for shutdown
            subprocess.run([wineserver, '-w'], env=env, check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            debug_print("Wine processes killed")
            self.show_info("Wine processes killed successfully")
            
        except Exception as e:
            debug_print(f"Error killing wine: {e}")
            self.show_error(f"Error killing wine: {e}")
    
    def on_aenux_clicked(self, widget):
        """Open AeNux folder"""
        aenux_path = self.config.get('aenux_path', '')
        if aenux_path and os.path.exists(aenux_path):
            self.open_folder(aenux_path)
        else:
            self.show_error("AeNux folder not found")
    
    def on_plugin_clicked(self, widget):
        """Open Plugins folder"""
        aenux_path = self.config.get('aenux_path', '')
        plugin_path = os.path.join(aenux_path, 'Plug-ins')
        if os.path.exists(plugin_path):
            self.open_folder(plugin_path)
        else:
            self.show_error("Plugins folder not found")
    
    def on_preset_clicked(self, widget):
        """Open Preset folder (Documents/Adobe)"""
        preset_path = os.path.expanduser('~/Documents/Adobe')
        if os.path.exists(preset_path):
            self.open_folder(preset_path)
        else:
            # Create if doesn't exist
            os.makedirs(preset_path, exist_ok=True)
            self.open_folder(preset_path)
    
    def on_runner_clicked(self, widget):
        """Open Wine runner folder"""
        wine_path = self.config.get('wine_path', '')
        if wine_path and os.path.exists(wine_path):
            self.open_folder(wine_path)
        else:
            self.show_error("Wine folder not found")
    
    def on_patch_runner_clicked(self, widget):
        """Run patch runner mechanism (setup without zip extraction)"""
        debug_print("Patch Runner clicked")
        
        if not self.config:
            self.show_error("Configuration not found")
            return
        
        widget.set_sensitive(False)
        widget.set_label("Patching...")
        
        # Run in background thread
        thread = threading.Thread(target=self.patch_runner_process)
        thread.daemon = True
        thread.start()
    
    def patch_runner_process(self):
        """Patch runner installation process"""
        temp_dir = None
        try:
            wine_prefix = os.path.abspath(self.config.get('wineprefix', ''))
            wine_bin = os.path.join(self.config.get('wine_path', ''), 'bin', 'wine')
            winetricks = os.path.join(self.config.get('wine_path', ''), 'bin', 'winetricks')
            temp_dir = os.path.join(os.path.abspath(self.config.get('user_location', '')), 'TEMP')
            
            debug_print(f"Starting patch runner process - WINEPREFIX: {wine_prefix}")
            
            if not os.path.exists(wine_prefix):
                raise Exception(f"Wine prefix does not exist: {wine_prefix}")
            
            env = os.environ.copy()
            env['WINEPREFIX'] = wine_prefix
            
            # Initialize wine prefix if needed
            subprocess.run([wine_bin, 'wineboot', '--init'],
                         env=env, check=True)
            
            # Install dependencies
            debug_print("Installing dependencies...")
            
            # Install wine-gecko
            gecko_file = os.path.join(temp_dir, 'wine-gecko-2.47.4-x86_64.msi')
            if os.path.exists(gecko_file):
                subprocess.run([wine_bin, 'msiexec', '/i', gecko_file],
                             env=env, check=True)
            
            # Install VC Redist
            for arch in ['x64', 'x86']:
                vc_file = os.path.join(temp_dir, f'vc_redist.{arch}.exe')
                if os.path.exists(vc_file):
                    subprocess.run([wine_bin, vc_file, '/install', '/quiet', '/norestart'],
                                 env=env, check=True)
            
            # Install winetricks components
            subprocess.run([winetricks, '-q', 'dxvk', 'corefonts'],
                         env=env, check=True)
            
            subprocess.run([winetricks, '-q', 'gdiplus', 'fontsmooth=rgb'],
                         env=env, check=True)
            
            # Apply theme registry (from AeNux_Installer)
            self.set_theme_registry(wine_bin, wine_prefix)
            
            # Prompt for DLL files
            GLib.idle_add(self._select_dll_files_ui)
            
            debug_print("Patch runner process completed")
        except Exception as error:
            debug_print(f"Patch runner error: {error}")
            # Clean up TEMP folder on error
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    debug_print(f"Cleaned up TEMP folder on error: {temp_dir}")
                except Exception as cleanup_error:
                    debug_print(f"Error cleaning up TEMP: {cleanup_error}")
            GLib.idle_add(lambda error=error: self._show_patch_error(str(error)))
    
    def _select_dll_files_ui(self):
        """UI thread for DLL selection"""
        dll_files = {}
        
        for dll_name in ['msxml3.dll', 'msxml3r.dll']:
            dialog = Gtk.FileChooserDialog(
                title=f"Select {dll_name}",
                action=Gtk.FileChooserAction.OPEN
            )
            dialog.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN, Gtk.ResponseType.OK
            )
            
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                filepath = dialog.get_filename()
                filename = os.path.basename(filepath)
                
                if filename != dll_name:
                    error_dialog = Gtk.MessageDialog(
                        transient_for=self.window,
                        flags=0,
                        message_type=Gtk.MessageType.ERROR,
                        buttons=Gtk.ButtonsType.OK,
                        text="File name mismatch!"
                    )
                    error_dialog.format_secondary_text(
                        f"Expected {dll_name}, but got {filename}"
                    )
                    error_dialog.run()
                    error_dialog.destroy()
                    dialog.destroy()
                    GLib.idle_add(self._reset_patch_button)
                    return False
                
                dll_files[dll_name] = filepath
                debug_print(f"Selected {dll_name}: {filepath}")
            else:
                # User cancelled
                dialog.destroy()
                GLib.idle_add(self._reset_patch_button)
                return False
            
            dialog.destroy()
        
        if len(dll_files) == 2:
            # Copy DLLs and set registry
            wine_prefix = self.config.get('wineprefix', '')
            wine_bin = os.path.join(self.config.get('wine_path', ''), 'bin', 'wine')
            system32 = os.path.join(wine_prefix, 'drive_c', 'windows', 'system32')
            
            try:
                for dll_name, dll_path in dll_files.items():
                    dst = os.path.join(system32, dll_name)
                    shutil.copy2(dll_path, dst)
                    debug_print(f"Copied {dll_name}")
                
                env = os.environ.copy()
                env['WINEPREFIX'] = wine_prefix
                
                subprocess.run([wine_bin, 'reg', 'add',
                              'HKCU\\Software\\Wine\\DllOverrides',
                              '/v', 'msxml3', '/d', 'native,builtin', '/f'],
                             env=env, check=True)
                
                GLib.idle_add(self._after_patch_success)
            except Exception as e:
                GLib.idle_add(lambda err=str(e): self.show_error(f"Error copying DLLs: {err}"))
        
        # Re-enable patch button
        GLib.idle_add(self._reset_patch_button)
        return False
    
    def _reset_patch_button(self):
        """Reset patch button state"""
        # Find patch runner button by iterating
        def find_patch_button(widget):
            if isinstance(widget, Gtk.Button):
                label = widget.get_label()
                if label == 'Patch Runner' or label == 'Patching...':
                    widget.set_sensitive(True)
                    widget.set_label("Patch Runner")
                    debug_print("Patch button reset")
                    return True
            
            if hasattr(widget, 'get_children'):
                for child in widget.get_children():
                    if find_patch_button(child):
                        return True
            return False
        
        find_patch_button(self.window)
    
    def _show_patch_error(self, error_msg):
        """Show patch error and reset button"""
        self.show_error(error_msg)
        self._reset_patch_button()

    def _after_patch_success(self):
        """Called on the main thread after patch completes successfully."""
        try:
            self.show_info("Patch completed successfully")

            # Attempt to create shortcuts and kill Wine processes for current config
            wine_path = self.config.get('wine_path', '')
            wineprefix = self.config.get('wineprefix', '')
            if wine_path and wineprefix:
                # Create shortcuts
                env = os.environ.copy()
                env['WINEPREFIX'] = wineprefix
                wineserver = os.path.join(wine_path, 'bin', 'wineserver')
                self._create_shortcuts(env, wine_path, wineserver, wineprefix)
                
                # Kill wine processes
                self._kill_wine_processes(wine_path, wineprefix)
        finally:
            # Ensure UI button is reset
            self._reset_patch_button()

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
            aenux_path = self.config.get('aenux_path', '')
            if aenux_path and os.path.exists(aenux_path):
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
    
    def set_theme_registry(self, wine_bin, prefix):
        """Set Wine theme/colors registry (copied from AeNux_Installer)"""
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
    
    def on_remove_wineprefix_clicked(self, widget):
        """Remove wineprefix and allow selection"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Remove Wine Prefix?"
        )
        dialog.format_secondary_text(
            "This will delete the Wine prefix folder. Continue?"
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            try:
                wineprefix_path = self.config.get('wineprefix', '')
                if wineprefix_path and os.path.exists(wineprefix_path):
                    shutil.rmtree(wineprefix_path)
                    debug_print(f"Removed wineprefix: {wineprefix_path}")
                    
                    # Update config
                    self.config['wineprefix'] = ''
                    self.save_config()
                    
                    # Enable wineprefix selection and clear it
                    self.select_wineprefix.set_sensitive(True)
                    self.select_wineprefix.unselect_all()
                    
                    self.show_info("Wine prefix removed")
            except Exception as e:
                self.show_error(f"Error removing wine prefix: {e}")
    
    def on_uninstall_clicked(self, widget):
        """Uninstall AeNux completely"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Uninstall AeNux?"
        )
        dialog.format_secondary_text(
            "This will delete all AeNux files. This action cannot be undone."
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            widget.set_sensitive(False)
            
            # Run uninstall in background
            thread = threading.Thread(target=self.uninstall_process)
            thread.daemon = True
            thread.start()
    
    def uninstall_process(self):
        """Uninstall process"""
        try:
            # Run shortcut removal script first
            script_dir = os.path.dirname(__file__)
            remove_shortcuts_script = os.path.join(script_dir, 'AppShortcutMakeRemove.sh')
            
            if os.path.exists(remove_shortcuts_script):
                try:
                    debug_print("Running shortcut removal script...")
                    subprocess.run(['bash', remove_shortcuts_script], check=False,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    debug_print("Shortcuts removed")
                except Exception as e:
                    debug_print(f"Warning: Shortcut removal failed: {e}")
            
            user_location = self.config.get('user_location', '')
            
            if user_location and os.path.exists(user_location):
                debug_print(f"Removing: {user_location}")
                
                # Show progress
                GLib.idle_add(lambda: self.uninstall_progressbar.set_fraction(0.5))
                
                shutil.rmtree(user_location)
                
                GLib.idle_add(lambda: self.uninstall_progressbar.set_fraction(1.0))
                # Remove configuration file if present
                try:
                    config_path = os.path.join(os.path.dirname(__file__), 'aenux_config.json')
                    if os.path.exists(config_path):
                        os.remove(config_path)
                        debug_print(f"Removed config file: {config_path}")
                except Exception as e:
                    debug_print(f"Error removing config file: {e}")
                
                debug_print("Uninstallation completed")
                GLib.idle_add(lambda: self.show_info("AeNux uninstalled successfully"))
                
                # Close application
                GLib.idle_add(Gtk.main_quit)
        except Exception as error:
            debug_print(f"Uninstall error: {error}")
            GLib.idle_add(lambda error=error: self.show_error(str(error)))
            GLib.idle_add(lambda: self.uninstall_button.set_sensitive(True))
    
    def open_folder(self, path):
        """Open folder with file manager"""
        try:
            subprocess.run(['xdg-open', path], check=True)
            debug_print(f"Opened folder: {path}")
        except Exception as e:
            debug_print(f"Error opening folder: {e}")
            self.show_error(f"Could not open folder: {path}")
    
    def save_config(self):
        """Save configuration to JSON"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'aenux_config.json')
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            debug_print(f"Config saved to: {config_path}")
        except Exception as e:
            debug_print(f"Error saving config: {e}")
    
    def show_error(self, message):
        """Show error dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def show_info(self, message):
        """Show info dialog"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Information"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def show_error_and_exit(self, message):
        """Show error and exit"""
        dialog = Gtk.MessageDialog(
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        Gtk.main_quit()
    
    def run(self):
        """Start the application"""
        debug_print("Starting AeNux Configurator")
        self.window.show_all()
        Gtk.main()

if __name__ == '__main__':
    app = AeNuxConfigurator()
    app.run()
