# AeNux

<p align="center">
  <img src="asset/aenux.svg" 
       alt="AeNux Logo" 
       width="140">
</p>

AeNux is an elegant, native GTK/Vala installer, runner, and configuration manager designed to set up and run Adobe After Effects on Linux using Wine.

## Features

### 🚀 AeNux Installer
- **Adobe-Style UI**: A vertical, multi-step wizard built with native GTK widgets.
- **Auto-Detection**: Automatically scans your `Downloads` directory for After Effects archives (`.7z`, `.zip`, `.rar`) and required DLL files (`msxml3.dll`, `msxml3r.dll`).
- **Optimal Prefix Setup**: Automatically initializes the Wine prefix and configures DLL overrides, dark theme registry settings, Windows 10 target version, and CEP extension debug mode.

### ⚙️ AeNux Configurator & Plugin Manager
- **Wine Prefix Utilities**: Easily launch `winecfg`, `regedit`, or force-terminate (*kill*) hung Wine prefix processes.
- **Plugin Installer**: Install `.aex` plugins, import `.zxp` CEP extensions, or run Windows `.exe` installers inside the Prefix.

### 🏃 AeNux Runner
- **Modern Wayland Support**: Correctly forwards Wayland displays to prevent XWayland fallback crashes.
- **Non-Blocking Execution**: Safe asynchronous process execution so background Wine daemons don't hang the UI.

---

## 📋 Prerequisites

AeNux requires **msxml3.dll** and **msxml3r.dll** to run After Effects. You must supply these files yourself (normally retrieved from a Windows installation at `C:\Windows\System32\`).

Place both DLL files in your `~/Downloads` folder before launching the installer, and it will auto-detect them.

---

## 🛠️ Build & Installation

### 1. Install Build Dependencies
Before compiling, install the Vala compiler and GTK+ 3 development libraries:

**Debian / Ubuntu:**
```bash
sudo apt update
sudo apt install valac libgtk-3-dev
```

### 2. Package and Compile
Build the Debian package directly using the provided build script:
```bash
./package_deb.sh
```
This will compile the source code and generate `aenux.deb` in the root folder.

### 3. Install Package
Install the generated Debian package on your system:
```bash
sudo dpkg -i aenux.deb
```

---

## 🖥️ Usage

- **AeNux Config / Installer**: Launch **AeNux Config** from your applications menu (or run `aenux_config` in your terminal) to set up and manage your Wine environment and plugins.
- **AeNux Runner**: Launch **AeNux** from your applications menu (or run `aenux` in your terminal) to start After Effects.

---

## ⚠️ Known Limitations

* 🔌 **Hardware Acceleration**: OpenCL support is limited, except on NVIDIA GPUs.
* 🎨 **UI Rendering**: Occasional flickering might occur with certain heavy UI plugins (e.g., *Flow*).
* 💥 **Memory**: High RAM usage during heavy composition rendering may cause instability.

---

## 🔧 Troubleshooting

### Too many annoying Wine plugin icons in your menu?
Wine may auto-generate desktop shortcuts for plugin installers. You can clean them up by deleting the corresponding desktop files under:
```bash
rm -rf ~/.local/share/applications/wine/
```

---

## 🙏 Acknowledgments

- Special thanks to **MattKC** for his pioneering research on running After Effects on Wine ([Forum Thread](https://forum.mattkc.com/viewtopic.php?t=337)).
- Huge thanks to **@relativemodder** for creating the AeGnux fork.
- Additional thanks to the **Wine Project** and the **GTK Project** for their runtime framework and libraries.

---

## 🔗 Support & Contact

* Telegram: **@cutefishaep**
* GitHub Issues: Bug reports & feature requests
