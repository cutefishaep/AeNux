#!/usr/bin/python3
"""AeNux Configurator v2.0"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os, shutil, threading
import utils

class AeNuxConfigurator:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.ui_file = os.path.join(os.path.dirname(__file__), 'gui.ui')
        
        try:
            self.builder.add_from_file(self.ui_file)
        except Exception as e:
            utils.debug_print(f"Error loading UI: {e}")
            raise
        
        self.window = self.builder.get_object('Config')
        if not self.window:
            utils.debug_print("Error: Could not find 'Config' window in UI file")
            return

        # Load configuration
        self.config = utils.load_config()
        if not self.config:
            utils.show_error(None, "Configuration file not found. Please run AeNux Installer first.")
            return
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
        
        self.window.connect('delete-event', self.on_window_close)
        self.wineprefix_disabled = True  # Initially disabled
        
        utils.debug_print(f"Configurator initialized. Config: {self.config}")
    
    def setup_folder_buttons(self):
        """Setup folder opening buttons"""
        try:
            def find_and_connect_buttons(widget, buttons_info):
                if isinstance(widget, Gtk.Button):
                    label = widget.get_label()
                    for info in buttons_info:
                        if label == info['label']:
                            widget.connect('clicked', info['callback'])
                            utils.debug_print(f"Connected button: {label}")
                
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
            utils.debug_print(f"Error setting up folder buttons: {e}")
    
    def setup_wine_tab(self):
        """Setup Wine configuration tab"""
        try:
            wine_path = self.config.get('wine_path', '')
            wineprefix_path = self.config.get('wineprefix', '')
            
            if wine_path:
                self.select_runner.set_filename(wine_path)
            
            if wineprefix_path:
                self.select_wineprefix.set_filename(wineprefix_path)
                self.select_wineprefix.set_sensitive(False)
            
            self.select_runner.connect('selection-changed', self.on_runner_selection_changed)
            self.select_wineprefix.connect('selection-changed', self.on_wineprefix_selection_changed)
            
            kill_wine_button = self.builder.get_object('kill_wine_button')
            if kill_wine_button:
                kill_wine_button.connect('clicked', self.on_kill_wine_clicked)
            
            utils.debug_print(f"Wine tab setup - Runner: {wine_path}, Prefix: {wineprefix_path}")
        except Exception as e:
            utils.debug_print(f"Error setting up wine tab: {e}")
    
    def setup_uninstall_tab(self):
        """Setup uninstall tab"""
        try:
            self.uninstall_button = self.builder.get_object('uninstall_button')
            self.uninstall_progressbar = self.builder.get_object('uninstall_progressbar')
            self.uninstall_button.connect('clicked', self.on_uninstall_clicked)
            utils.debug_print("Uninstall tab setup complete")
        except Exception as e:
            utils.debug_print(f"Error setting up uninstall tab: {e}")
    
    def on_runner_selection_changed(self, widget):
        """Handle runner selection change"""
        runner_path = self.select_runner.get_filename()
        utils.debug_print(f"Runner selected: {runner_path}")
    
    def on_wineprefix_selection_changed(self, widget):
        """Handle wineprefix folder selection change"""
        wineprefix_path = self.select_wineprefix.get_filename()
        if wineprefix_path:
            self.config['wineprefix'] = wineprefix_path
            utils.save_config(self.config)
            utils.debug_print(f"Wineprefix updated: {wineprefix_path}")
        else:
            utils.debug_print("Wineprefix selection cleared")
    
    def on_kill_wine_clicked(self, widget):
        """Kill Wine processes"""
        wine_path = self.config.get('wine_path')
        wineprefix = self.config.get('wineprefix')

        if not wine_path or not wineprefix:
            utils.show_error(self.window, "Wine path or prefix not configured")
            return
            
        utils.kill_wine_processes(wine_path, wineprefix)
        utils.show_info(self.window, "Wine processes killed successfully")
    
    def on_aenux_clicked(self, widget):
        """Open AeNux folder"""
        aenux_path = self.config.get('aenux_path', '')
        if aenux_path and os.path.exists(aenux_path):
            self.open_folder(aenux_path)
        else:
            utils.show_error(self.window, "AeNux folder not found")
    
    def on_plugin_clicked(self, widget):
        """Open Plugins folder"""
        aenux_path = self.config.get('aenux_path', '')
        plugin_path = os.path.join(aenux_path, 'Plug-ins')
        if os.path.exists(plugin_path):
            self.open_folder(plugin_path)
        else:
            utils.show_error(self.window, "Plugins folder not found")
    
    def on_preset_clicked(self, widget):
        """Open Preset folder (Documents/Adobe)"""
        preset_path = os.path.expanduser('~/Documents/Adobe')
        if not os.path.exists(preset_path):
            os.makedirs(preset_path, exist_ok=True)
        self.open_folder(preset_path)
    
    def on_runner_clicked(self, widget):
        """Open Wine runner folder"""
        wine_path = self.config.get('wine_path', '')
        if wine_path and os.path.exists(wine_path):
            self.open_folder(wine_path)
        else:
            utils.show_error(self.window, "Wine folder not found")
    
    def on_patch_runner_clicked(self, widget):
        """Run patch runner mechanism (setup without zip extraction)"""
        utils.debug_print("Patch Runner clicked")
        
        if not self.config:
            utils.show_error(self.window, "Configuration not found")
            return
        
        widget.set_sensitive(False)
        widget.set_label("Patching...")
        
        thread = threading.Thread(target=self.patch_runner_process, daemon=True)
        thread.start()
    
    def patch_runner_process(self):
        """Patch runner installation process"""
        temp_dir = None
        try:
            wine_path = self.config.get('wine_path')
            wine_prefix = self.config.get('wineprefix')
            wine_bin = os.path.join(wine_path, 'bin', 'wine')
            winetricks = os.path.join(wine_path, 'bin', 'winetricks')
            temp_dir = os.path.join(self.config.get('user_location', ''), 'TEMP')
            
            utils.debug_print(f"Starting patch runner process - WINEPREFIX: {wine_prefix}")
            
            if not all([wine_path, wine_prefix, os.path.exists(wine_prefix)]):
                raise Exception(f"Invalid Wine configuration or prefix not found: {wine_prefix}")
            
            env = utils.get_wine_env(wine_path, wine_prefix)
            
            utils.run_command([wine_bin, 'wineboot', '--init'], env=env, check=True)
            
            gecko_file = os.path.join(temp_dir, 'wine-gecko-2.47.4-x86_64.msi')
            if os.path.exists(gecko_file):
                utils.run_command([wine_bin, 'msiexec', '/i', gecko_file], env=env, check=True)
            
            for arch in ['x64', 'x86']:
                vc_file = os.path.join(temp_dir, f'vc_redist.{arch}.exe')
                if os.path.exists(vc_file):
                    utils.run_command([wine_bin, vc_file, '/install', '/quiet', '/norestart'], env=env, check=True)
            
            for verb in ['dxvk', 'corefonts', 'gdiplus', 'fontsmooth=rgb']:
                utils.run_command([winetricks, '-q', verb], env=env, check=True)
            
            utils.set_theme_registry(wine_path, wine_prefix)
            
            GLib.idle_add(self._select_dll_files_ui)
            utils.debug_print("Patch runner process completed")
            
        except Exception as error:
            utils.debug_print(f"Patch runner error: {error}")
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    utils.debug_print(f"Error cleaning up TEMP: {e}")
            GLib.idle_add(lambda: self._show_patch_error(str(error)))
    
    def _select_dll_files_ui(self):
        """UI thread for DLL selection"""
        dll_files = {}
        
        for dll_name in ['msxml3.dll', 'msxml3r.dll']:
            dialog = Gtk.FileChooserDialog(
                title=f"Select {dll_name}",
                action=Gtk.FileChooserAction.OPEN,
                parent=self.window
            )
            dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
            
            response = dialog.run()
            filepath = dialog.get_filename()
            dialog.destroy()

            if response == Gtk.ResponseType.OK:
                if os.path.basename(filepath) != dll_name:
                    utils.show_error(self.window, f"File name mismatch! Expected {dll_name}")
                    GLib.idle_add(self._reset_patch_button)
                    return False
                dll_files[dll_name] = filepath
            else:
                GLib.idle_add(self._reset_patch_button)
                return False
        
        if len(dll_files) == 2:
            wine_prefix = self.config.get('wineprefix')
            wine_path = self.config.get('wine_path')
            wine_bin = os.path.join(wine_path, 'bin', 'wine')
            system32 = os.path.join(wine_prefix, 'drive_c', 'windows', 'system32')
            
            try:
                for name, path in dll_files.items():
                    shutil.copy2(path, os.path.join(system32, name))
                
                env = utils.get_wine_env(wine_path, wine_prefix)
                utils.run_command([
                    wine_bin, 'reg', 'add', 'HKCU\\Software\\Wine\\DllOverrides',
                    '/v', 'msxml3', '/d', 'native,builtin', '/f'
                ], env=env)
                
                GLib.idle_add(self._after_patch_success)
            except Exception as e:
                GLib.idle_add(lambda: utils.show_error(self.window, f"Error copying DLLs: {e}"))
        
        GLib.idle_add(self._reset_patch_button)
        return False
    
    def _reset_patch_button(self):
        """Reset patch button state"""
        def find_patch_button(widget):
            if isinstance(widget, Gtk.Button):
                label = widget.get_label()
                if label in ['Patch Runner', 'Patching...']:
                    widget.set_sensitive(True)
                    widget.set_label("Patch Runner")
                    return True
            if hasattr(widget, 'get_children'):
                for child in widget.get_children():
                    if find_patch_button(child):
                        return True
            return False
        find_patch_button(self.window)
    
    def _show_patch_error(self, error_msg):
        """Show patch error and reset button"""
        utils.show_error(self.window, error_msg)
        self._reset_patch_button()

    def _after_patch_success(self):
        """Called on the main thread after patch completes successfully."""
        try:
            utils.show_info(self.window, "Patch completed successfully")
            wine_path = self.config.get('wine_path')
            wineprefix = self.config.get('wineprefix')
            aenux_path = self.config.get('aenux_path')

            if wine_path and wineprefix:
                utils.create_shortcuts(wine_path, wineprefix, aenux_path)
                utils.kill_wine_processes(wine_path, wineprefix)
        finally:
            self._reset_patch_button()
    
    def on_remove_wineprefix_clicked(self, widget):
        """Remove wineprefix and allow selection"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Remove Wine Prefix?"
        )
        dialog.format_secondary_text("This will delete the Wine prefix folder. Continue?")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            try:
                wineprefix_path = self.config.get('wineprefix', '')
                if wineprefix_path and os.path.exists(wineprefix_path):
                    shutil.rmtree(wineprefix_path)
                    utils.debug_print(f"Removed wineprefix: {wineprefix_path}")
                    
                    self.config['wineprefix'] = ''
                    utils.save_config(self.config)
                    
                    self.select_wineprefix.set_sensitive(True)
                    self.select_wineprefix.unselect_all()
                    utils.show_info(self.window, "Wine prefix removed")
            except Exception as e:
                utils.show_error(self.window, f"Error removing wine prefix: {e}")
    
    def on_uninstall_clicked(self, widget):
        """Uninstall AeNux completely"""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Uninstall AeNux?"
        )
        dialog.format_secondary_text("This will delete all AeNux files. This action cannot be undone.")
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            widget.set_sensitive(False)
            thread = threading.Thread(target=self.uninstall_process, daemon=True)
            thread.start()
    
    def uninstall_process(self):
        """Uninstall process"""
        try:
            script_dir = os.path.dirname(__file__)
            remove_shortcuts_script = os.path.join(script_dir, 'AppShortcutMakeRemove.sh')
            
            if os.path.exists(remove_shortcuts_script):
                utils.run_command(['bash', remove_shortcuts_script])

            user_location = self.config.get('user_location')
            if user_location and os.path.exists(user_location):
                utils.debug_print(f"Removing: {user_location}")
                GLib.idle_add(lambda: self.uninstall_progressbar.set_fraction(0.5))
                shutil.rmtree(user_location)
                GLib.idle_add(lambda: self.uninstall_progressbar.set_fraction(1.0))
                
                config_path = os.path.join(os.path.dirname(__file__), 'aenux_config.json')
                if os.path.exists(config_path):
                    os.remove(config_path)

                GLib.idle_add(lambda: utils.show_info(self.window, "AeNux uninstalled successfully"))
                GLib.idle_add(Gtk.main_quit)
        except Exception as error:
            utils.debug_print(f"Uninstall error: {error}")
            GLib.idle_add(lambda: utils.show_error(self.window, str(error)))
            GLib.idle_add(lambda: self.uninstall_button.set_sensitive(True))
    
    def open_folder(self, path):
        """Open folder with file manager"""
        try:
            utils.run_command(['xdg-open', path])
            utils.debug_print(f"Opened folder: {path}")
        except Exception as e:
            utils.debug_print(f"Error opening folder: {e}")
            utils.show_error(self.window, f"Could not open folder: {path}")
    
    def on_window_close(self, widget, event):
        """Handle window close event"""
        Gtk.main_quit()
        return False

    def run(self):
        """Start the application"""
        if not hasattr(self, 'window') or not self.window:
            return
            
        utils.debug_print("Starting AeNux Configurator")
        self.window.show_all()
        Gtk.main()

if __name__ == '__main__':
    app = AeNuxConfigurator()
    app.run()
