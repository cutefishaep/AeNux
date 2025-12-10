# AeNux

<p align="center">
  <img src="https://raw.githubusercontent.com/cutefishaep/AeNux/main/src/aenux.png" 
       alt="AeNux Logo" 
       width="200">
  <br>
  <strong style="font-size: 100px;">AeNux</strong>
</p>

<div align="center">

[![Linux Compatible](https://img.shields.io/badge/Linux-Compatible-brightgreen?style=for-the-badge&logo=linux)](https://www.linux.org)
[![Wine](https://img.shields.io/badge/Wine-Compatible-7e0202?style=for-the-badge&logo=wine)](https://www.winehq.org)

</div>

---

## 🚀 Overview

**AeNux** is a comprehensive installer and configuration tool that enables **Adobe After Effects** to run on **Linux** through **Wine** and **Winetricks**.
Created for creative professionals working on Linux, it provides an automated solution for installation, configuration, and plugin management.

## Features

### 🚀 AeNux Installer
- Automatic download of Wine, VC Redistributables, and dependencies
- Wine prefix creation and configuration
- After Effects installation and setup
- Registry and theme configuration
- Desktop shortcut creation

### ⚙️ AeNux Configurator
- Manage Wine prefix and runner paths
- Kill Wine processes
- Open plugin, preset, and runner folders
- Reinstall or patch runner
- Uninstall AeNux

### 🔌 Plugin Installer
- Install AEX plugins
- Install CEP extensions
- Run EXE installers via Wine
- Copy presets and scripts

### 🏃 AeNux Runner
- Run After Effects application
- Manage virtual environment (venv)
- Install/reinstall dependencies
- Easy menu-based interface
- Command-line support with flags

---

## ⚠️ Known Limitations

* ❌ **Hardware Acceleration** — Limited OpenCL support (except NVIDIA GPUs)
* 🎨 **UI Rendering** — Occasional flickering with certain plugins (e.g., Flow)
* 💥 **Memory Issues** — Potential crashes during heavy RAM usage
* 🐛 **Bugs** — Report any issues you encounter

---

## 🖥️ Tested Environments

| Component             | Specification                                                 |
| --------------------- | ------------------------------------------------------------- |
| **Operating Systems** | Linux Mint 22.1, Debian 12, ElementaryOS 8.0.1, Ubuntu Budgie |
| **Processor**         | Intel® Core™ i3-1115G4 (11th Gen)                             |
| **Graphics**          | Intel Tiger Lake-LP GT2 (UHD Graphics G4)                     |
| **Memory**            | 8 GB RAM                                                      |

---

## 📋 Dependencies

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install wget unzip cabextract zenity python3 python3-pip python3-venv
```

### Fedora

```bash
sudo dnf install wget unzip cabextract zenity python3 python3-pip
```

### Arch Linux

```bash
sudo pacman -S wget unzip cabextract zenity python python-pip
```

---

## 🛠️ Installation Guide

### 1. Clone & Initialize

```bash
git clone https://github.com/cutefishaep/AeNux
cd AeNux
chmod +x run.sh
./run.sh
```

### 2. Provide Required Microsoft Components

AeNux requires **msxml3.dll** and **msxml3r.dll**, which you must supply yourself from a Windows installation:

```
C:\Windows\System32\
```

Copy both files to whatever you want

### 3. Launch AeNux GUI

Simply run from application menu

Or use command-line flags:
```bash
./run.sh -r   # Run After Effects
./run.sh -i   # Run Installer
./run.sh -c   # Run Configurator
./run.sh -p   # Run Plugin Installer
./run.sh -h   # Show help
```

---

## 🧩 Plugin Installation

To install plugins:

1. Open the AeNux GUI: `./run.sh`
2. Select option `4` - Run Plugin Installer
3. Place your plugins in the respective folders:
   - **AEX Plugins**: `PlugIn/aex/`
   - **CEP Extensions**: `PlugIn/CEP/`
   - **Script Installers**: `PlugIn/installer/`
   - **Presets**: `PlugIn/preset-backup/`
   - **Scripts**: `PlugIn/scripts/`

4. Use the Plugin Installer GUI to select and install
---

## 📁 Project Structure

```
AeNux/
├── run.sh                       # Main entry point
├── requirements.txt             # Python dependencies
├── script/
│   ├── AeNux_Installer.py      # Installation script
│   ├── AeNux_Configurator.py   # Configuration GUI
│   ├── run.py                   # After Effects runner
│   ├── AppShortcutMake.sh       # Desktop shortcut creator
│   ├── gui.ui                   # GTK UI definition
│   └── aenux_config.json        # Configuration file
├── PlugIn/
│   ├── PlugIn.py               # Plugin installer
│   ├── aex/                     # AEX plugins
│   ├── CEP/                     # CEP extensions
│   ├── installer/               # EXE installers
│   ├── preset-backup/           # Presets
│   └── scripts/                 # Scripts
├── src/
│   └── aenux.png               # Application icon
└── venv/                        # Python virtual environment
```

---

## 🔧 Troubleshooting

### ModuleNotFoundError: No module named 'gi'
Run dependency installation:
```bash
./run.sh -d
```

### Wine not found
The wine binary will be automatically installed. If issues persist:
```bash
./run.sh -c
```
And verify the wine path in the Configurator.

### After Effects won't start
1. Try killing Wine processes:
   ```bash
   ./run.sh -c
   ```
   Then click "Kill Wine Processes" button

2. Check if configuration is correct:
   - Verify wine_path exists
   - Verify wineprefix exists
   - Verify aenux_path exists

### Desktop shortcut not working
Recreate shortcuts using Configurator:
```bash
./run.sh -c
```

---

## Uninstallation

1. Open AeNux:
   ```bash
   ./run.sh
   ```
2. Select option `2` - Run AeNux Configurator
3. Click **Uninstall**

---

## 🙏 Acknowledgments

Special thanks to **MattKC** for his pioneering work.
Forum reference: [https://forum.mattkc.com/viewtopic.php?t=337](https://forum.mattkc.com/viewtopic.php?t=337)

Huge thanks also to **@relativemodder** for creating the AeGnux fork, making installation much simpler for the community. ❤️🐧

Additional thanks to the **Wine Project** and **GTK Project** for their amazing work.

---

<div align="center">
  <strong>Happy Editing on Linux! 🎬🐧</strong>
</div>

---

## 🔗 Support & Contact

* Telegram: **@cutefishaep**
* GitHub Issues: Bug reports & feature requests
* GitHub Discussions: Questions & suggestions

---

**Last Updated**: December 2025

Made with ❤️ for the creative community on Linux
