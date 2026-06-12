# AeNux

AeNux is an elegant, native GTK/Vala installer and runner designed to set up and run Adobe After Effects on Linux using Wine.

## Features

- **Adobe-Style UI**: A vertical, multi-step installation wizard built with native GTK widgets.
- **Auto-Detection**: Automatically scans your `Downloads` directory for your After Effects archive (`.7z`, `.zip`, `.rar`) and the required DLL files (`msxml3.dll`, `msxml3r.dll`).
- **Optimal Prefix Setup**: Automatically initializes the Wine prefix and configures DLL overrides, dark theme registry settings, Windows 10 target version, and CEP extension debug mode.
- **Modern Wayland Support**: Correctly forwards Wayland displays to prevent XWayland fallback crashes.
- **Non-Blocking Execution**: Safe asynchronous process execution so background Wine daemons don't hang the setup process.

---

## Build & Installation

### 1. Install Dependencies
Before building, make sure you have the Vala compiler and GTK development libraries installed (on Debian/Ubuntu):
```bash
sudo apt install valac libgtk-3-dev
```

### 2. Package and Compile
Build the Debian package directly using the provided build script:
```bash
./package_deb.sh
```
This will compile the source code and generate `aenux.deb` in the root folder.

### 3. Install Package
Install the generated Debian package:
```bash
sudo dpkg -i aenux.deb
```

---

## Usage

- **Installer & Configurator**: Launch `aenux_config` from your applications menu or terminal to set up the wine prefix environment.
- **Runner**: Launch `aenux` to start After Effects through the configured environment.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
