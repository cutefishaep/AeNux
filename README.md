# AeNux

<p align="center">
  <img src="https://github.com/cutefishaep/AeNux/blob/main/asset/logo.png" alt="AeNux Logo" width="200"/><br>
  <strong style="font-size: 100px">AeNux</strong>
</p>

<div align="center">

[![Linux Compatible](https://img.shields.io/badge/Linux-Compatible-brightgreen?style=for-the-badge&logo=linux)](https://www.linux.org)
[![Wine](https://img.shields.io/badge/Wine-Compatible-7e0202?style=for-the-badge&logo=wine)](https://www.winehq.org)

</div>

## 🚀 Overview

**AeNux** is a sophisticated Linux solution that enables seamless execution of **Adobe After Effects** through **Wine** and **Winetricks**. Designed for creative professionals who prefer Linux environments, this project bridges the gap between Windows-based creative software and Linux ecosystems.

> ⚠️ **Educational Purpose Notice**  
> This project is intended for educational and experimental use only. Please respect software licensing agreements and use responsibly. The primary objective is to explore Linux compatibility for creative applications.

## ⚠️ Known Limitations

- ❌ **Hardware Acceleration** - OpenCL support limited (NVIDIA GPUs excepted)
- 🎨 **UI Rendering** - Occasional flickering with certain plugins (e.g., Flow)
- 💥 **Memory Management** - Potential crashes under heavy RAM usage (Debian excluded)
- 🐛 **Bug Reports** - Please submit issues for any discovered anomalies

---

## 🖥️ Tested Environments

| Component | Specification |
|-----------|---------------|
| **Operating Systems** | Linux Mint 22.1 Cinnamon, Debian 12, ElementaryOS 8.0.1, Ubuntu Budgie |
| **Processor** | 11th Gen Intel® Core™ i3-1115G4 @ 3.00GHz × 2 |
| **Graphics** | Intel Corporation Tiger Lake-LP GT2 [UHD Graphics G4] |
| **Memory** | 8 GB RAM |

---

## 🛠️ Installation Guide

### Quick Installation

1. **Clone and Initialize**
   ```bash
   git clone https://github.com/cutefishaep/AeNux
   cd AeNux
   chmod +X run.sh
   ./run.sh
   ```
   *Ensure you're within the cloned repository directory*

2. **GUI Installation**
   - Click the **"Install"** button in the top-right corner
   - Enable the **"Apply AeNux Patch"** checkbox
   - Click **"Run AeNux"** to launch AeNux

### Plugin Installation

The plugin directory is located at:
```bash
/home/<your-username>/cutefishaep/AeNux/Plug-ins
```

**Free Plugin**: Install all most editor used plugins:
```bash
Run "Install Plugin on the gui"
```
[🔗 AeNux Plugin Repository](https://github.com/cutefishaep/AeNux-plugin)

### Uninstallation

1. Launch AeNux from your application menu
2. Click **"Uninstall"** in the top-right corner
3. Delete the cloned repository directory

---

## 📋 Important Notes

- **Wine Configuration**: Installation methods may vary across Linux distributions. Adjust instructions in `run_qt6.py` accordingly
- **Swap Memory**: Disabling swap is strongly recommended to preserve SSD longevity
- **Performance**: Results may vary based on hardware configuration and Linux distribution

---

## 📄 License

This project is licensed for educational and personal use exclusively. Commercial redistribution or unauthorized use is strictly prohibited.

---

## 🙏 Acknowledgments

Special gratitude to **MattKC** for making this project feasible through his pioneering work.

**MattKC Forum Reference**:  
https://forum.mattkc.com/viewtopic.php?t=337

---

## 🎯 Development Roadmap

- [❓] Enable hardware acceleration support
*Only for NVIDIA, by patching nvidia-libs. [Read this issue for more information](https://github.com/cutefishaep/AeNux/issues/5).*
- [❌] Streamline additional plugin installation
- [❌] Package as .deb file for easier distribution
- [❌] Implement "Open With AeNux" context menu integration

---

<div align="center">

**Happy Editing on Linux! 🎬🐧**

</div>
