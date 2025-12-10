# AeNux

A comprehensive installer and configuration tool for running Adobe After Effects on Linux using Wine.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.6+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-lightgrey.svg)

## Overview

AeNux is a complete solution for installing and managing Adobe After Effects on Linux systems. It provides:

- **Easy Installation**: Automated setup of Wine, After Effects, and all dependencies
- **Configuration Management**: GUI-based configuration for Wine prefix and plugin management
- **Plugin Support**: Built-in plugin installer for AEX, CEP, scripts, and presets
- **Virtual Environment**: Isolated Python environment with all required dependencies

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
- Configure theme and colors
- Open plugin, preset, and runner folders
- Reinstall or patch runner
- Uninstall AeNux

### 🔌 Plugin Installer
- Install AEX plugins
- Install CEP extensions
- Run EXE installers via Wine
- Copy presets and scripts
- Registry key management

### 🏃 AeNux Runner
- Run After Effects application
- Manage virtual environment (venv)
- Install/reinstall dependencies
- Easy menu-based interface
- Command-line support with flags

## Requirements

### System Requirements
- Linux (Ubuntu 20.04+ recommended)
- Python 3.6+
- GTK3 libraries
- 50+ GB free disk space (for Wine + After Effects)

### Dependencies
- python3-gi
- python3-gi-cairo
- gir1.2-gtk-3.0
- cabextract
- Wine (will be installed automatically)

## Installation

### Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/cutefishaep/AeNux.git
cd AeNux
```

2. **Run the installer:**
```bash
./run.sh
```

3. **Follow the interactive menu:**
   - Select option `1` to run AeNux Installer
   - Select your installation location
   - Choose the After Effects ZIP file
   - Select required DLL files (msxml3.dll, msxml3r.dll)

### Installation Options

#### Option 1: Interactive Menu (Recommended)
```bash
./run.sh
```

Menu options:
- `1` - Run AeNux Installer
- `2` - Run AeNux Configurator
- `3` - Run AeNux (Execute After Effects)
- `4` - Run Plugin Installer
- `5` - Install/Reinstall Dependencies

#### Option 2: Command-Line Flags
```bash
# Run After Effects
./run.sh -r

# Run Installer
./run.sh -i

# Run Configurator
./run.sh -c

# Run Plugin Installer
./run.sh -p

# Install dependencies
./run.sh -d

# Show help
./run.sh -h
```

## First-Time Setup

### Step 1: Install Dependencies
```bash
./run.sh -d
```
or select option `5` from the menu.

This will:
- Update system packages
- Install Python GTK bindings
- Create Python virtual environment
- Install Python dependencies

### Step 2: Run Installer
```bash
./run.sh -i
```
or select option `1` from the menu.

You'll need:
- A location for installation (minimum 50GB free space)
- After Effects ZIP file
- DLL files (msxml3.dll, msxml3r.dll)

### Step 3: Configure (Optional)
```bash
./run.sh -c
```
or select option `2` from the menu.

You can:
- Verify installation paths
- Configure Wine settings
- Install plugins

### Step 4: Run After Effects
```bash
./run.sh -r
```
or select option `3` from the menu.

## Plugin Installation

### Using Plugin Installer
```bash
./run.sh -p
```
or select option `4` from the menu.

### Supported Plugin Types

1. **AEX Plugins**
   - Place .aex files in: `PlugIn/aex/`
   
2. **CEP Extensions**
   - Place CEP folders in: `PlugIn/CEP/`
   - AddKeys.reg file supported

3. **Script Installers**
   - Place .exe installers in: `PlugIn/installer/`

4. **Presets**
   - Place preset folders in: `PlugIn/preset-backup/`

5. **Scripts**
   - Place script files in: `PlugIn/scripts/`

### Example Plugin Structure
```
PlugIn/
├── aex/
│   ├── plugin1.aex
│   └── plugin_folder/
├── CEP/
│   ├── ExtensionName/
│   └── AddKeys.reg
├── installer/
│   └── installer.exe
├── preset-backup/
│   └── preset_name/
└── scripts/
    ├── script.jsx
    └── script_folder/
```

## Configuration

### Configuration File
AeNux stores configuration in `script/aenux_config.json`:

```json
{
  "version": "2.0",
  "user_location": "/path/to/installation",
  "wine_path": "/path/to/wine",
  "wineprefix": "/path/to/wineprefix",
  "aenux_path": "/path/to/AeNux"
}
```

## File Structure

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

## Troubleshooting

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

## Development

### Project Structure
- `script/` - Main application scripts
- `PlugIn/` - Plugin installer components
- `src/` - Resources (icons, UI files)
- `venv/` - Python virtual environment

### Running in Development
```bash
# Activate virtual environment
source venv/bin/activate

# Run individual scripts
python3 script/AeNux_Installer.py
python3 script/AeNux_Configurator.py
python3 PlugIn/PlugIn.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Areas for Contribution
- Bug fixes and improvements
- Plugin compatibility testing
- Documentation updates
- Feature requests and suggestions

## Credits
- **Wine Project**: https://www.winehq.org/
- **GTK Project**: https://www.gtk.org/
- **After Effects**: Adobe 

## Support

For issues, questions, or suggestions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Open an issue on GitHub
3. Check existing issues for solutions


**Last Updated**: December 2025


Made with ❤️ for the creative community on Linux
