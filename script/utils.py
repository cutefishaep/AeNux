#!/usr/bin/python3
"""AeNux Utils v2.0"""

import os
import json
import subprocess
import shutil
import glob
from gi.repository import Gtk

DEBUG = True

def debug_print(msg):
    """Prints a debug message if DEBUG is True."""
    if DEBUG:
        print(f"[DEBUG] {msg}")

def run_command(command, env=None, cwd=None, check=False):
    """Runs a command and logs its output."""
    debug_print(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        if result.stdout:
            debug_print(f"STDOUT: {result.stdout.strip()}")
        if result.stderr:
            debug_print(f"STDERR: {result.stderr.strip()}")
        return result
    except FileNotFoundError:
        debug_print(f"Error: Command not found: {command[0]}")
        return None
    except Exception as e:
        debug_print(f"An unexpected error occurred: {e}")
        return None

def get_wine_env(wine_path, wineprefix):
    """Creates a suitable environment for running Wine commands."""
    env = os.environ.copy()
    env['WINEPREFIX'] = wineprefix

    # Add Wine's bin directory to the PATH
    wine_bin_path = os.path.join(wine_path, 'bin')
    if 'PATH' in env:
        env['PATH'] = f"{wine_bin_path}{os.pathsep}{env['PATH']}"
    else:
        env['PATH'] = wine_bin_path

    return env

def kill_wine_processes(wine_path, wineprefix):
    """Kills all wineserver processes for a given Wine prefix."""
    wineserver = os.path.join(wine_path, 'bin', 'wineserver')
    if not os.path.exists(wineserver):
        debug_print(f"Wineserver not found at {wineserver}")
        return

    env = get_wine_env(wine_path, wineprefix)
    run_command([wineserver, '-k'], env=env)
    run_command([wineserver, '-w'], env=env)
    debug_print("Wine processes stopped.")

def set_theme_registry(wine_path, wineprefix):
    """Sets the dark theme registry keys for the Wine prefix."""
    wine_bin = os.path.join(wine_path, 'bin', 'wine')
    if not os.path.exists(wine_bin):
        debug_print(f"Wine executable not found at {wine_bin}")
        return

    colors = {
        "ActiveBorder": "49 54 58", "ActiveTitle": "49 54 58",
        "AppWorkSpace": "60 64 72", "Background": "49 54 58",
        "ButtonAlternativeFace": "60 64 72", "ButtonDkShadow": "30 33 36",
        "ButtonFace": "49 54 58", "ButtonHilight": "119 126 140",
        "ButtonLight": "60 64 72", "ButtonShadow": "40 43 47",
        "ButtonText": "219 220 222", "GradientActiveTitle": "49 54 58",
        "GradientInactiveTitle": "49 54 58", "GrayText": "100 104 110",
        "Hilight": "119 126 140", "HilightText": "255 255 255",
        "InactiveBorder": "49 54 58", "InactiveTitle": "49 54 58",
        "InactiveTitleText": "219 220 222", "InfoText": "180 185 190",
        "InfoWindow": "49 54 58", "Menu": "40 43 47", "MenuBar": "40 43 47",
        "MenuHilight": "119 126 140", "MenuText": "219 220 222",
        "Scrollbar": "60 64 72", "TitleText": "219 220 222",
        "Window": "35 38 41", "WindowFrame": "49 54 58",
        "WindowText": "219 220 222",
    }

    env = get_wine_env(wine_path, wineprefix)
    for key, value in colors.items():
        run_command([
            wine_bin, 'reg', 'add', 'HKCU\\Control Panel\\Colors',
            '/v', key, '/d', value, '/f'
        ], env=env)
    debug_print("Theme registry keys set.")

def create_shortcuts(wine_path, wineprefix, aenux_path):
    """Creates symbolic links to user directories within the Wine prefix."""
    debug_print("Creating shortcuts...")
    try:
        wine_drive_c = os.path.join(wineprefix, "drive_c")
        fav_dir_pattern = os.path.join(wine_drive_c, "users", "*", "Favorites")
        fav_paths = glob.glob(fav_dir_pattern)

        if not fav_paths:
            debug_print("Favorites directory not found, skipping shortcut creation.")
            return

        target_fav_dir = fav_paths[0]
        home_dir = os.path.expanduser("~")

        folders = ["Documents", "Downloads", "Pictures", "Videos", "Music"]
        for folder in folders:
            link_path = os.path.join(target_fav_dir, folder)
            if os.path.lexists(link_path):
                os.remove(link_path)

            linux_path = os.path.join(home_dir, folder)
            if os.path.exists(linux_path):
                os.symlink(linux_path, link_path)
                debug_print(f"Created shortcut for {folder}")

        # Create AeNux shortcut
        if aenux_path and os.path.exists(aenux_path):
            aenux_link = os.path.join(target_fav_dir, "AeNux")
            if os.path.lexists(aenux_link):
                os.remove(aenux_link)
            os.symlink(aenux_path, aenux_link)
            debug_print("Created AeNux shortcut.")

        kill_wine_processes(wine_path, wineprefix)
    except Exception as e:
        debug_print(f"Shortcut creation failed: {e}")

def show_dialog(parent_window, message_type, title, message):
    """Displays a GTK message dialog."""
    dialog = Gtk.MessageDialog(
        transient_for=parent_window,
        flags=0,
        message_type=message_type,
        buttons=Gtk.ButtonsType.OK,
        text=title
    )
    dialog.format_secondary_text(message)
    dialog.run()
    dialog.destroy()

def show_error(parent_window, message):
    """Shows a GTK error dialog."""
    show_dialog(parent_window, Gtk.MessageType.ERROR, "Error", message)

def show_info(parent_window, message):
    """Shows a GTK info dialog."""
    show_dialog(parent_window, Gtk.MessageType.INFO, "Information", message)

def load_config():
    """Loads the aenux_config.json file."""
    config_path = os.path.join(os.path.dirname(__file__), 'aenux_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            debug_print(f"Error loading config: {e}")
            return None
    return None

def save_config(config):
    """Saves the configuration to aenux_config.json."""
    config_path = os.path.join(os.path.dirname(__file__), 'aenux_config.json')
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        debug_print("Configuration saved.")
        return True
    except IOError as e:
        debug_print(f"Error saving config: {e}")
        return False
