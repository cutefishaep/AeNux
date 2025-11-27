# AeNux

<p align="center">
  <img src="https://github.com/cutefishaep/AeNux/blob/main/asset/logo.png" alt="AeNux Logo" width="200"/><br>
  <strong style="font-size: 100px">AeNux</strong>
</p>

<div align="center">

[![Linux Compatible](https://img.shields.io/badge/Linux-Compatible-brightgreen?style=for-the-badge\&logo=linux)](https://www.linux.org)
[![Wine](https://img.shields.io/badge/Wine-Compatible-7e0202?style=for-the-badge\&logo=wine)](https://www.winehq.org)

</div>

---

## 🚀 Overview

**AeNux** is a Linux-based solution that enables **Adobe After Effects** to run through **Wine** and **Winetricks**.
Created for creative professionals working on Linux, it bridges the gap between Windows-exclusive creative software and Linux systems.

> ⚠️ **Notice:**
> AeNux is for educational and experimental purposes only.
> Please follow all software licensing rules and use responsibly.

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

AeNux requires **msxml3.dll** and **msxml3r.dll**, which you must supply yourself from a licensed Windows installation:

```
C:\Windows\System32\
```

Copy both files into:

```
/asset/System32
```

> ⚠️ These files are **not included** in AeNux due to licensing restrictions.

### 3. Launch AeNux GUI

* Click **Install**
* Select your local AeNux `.zip` file
* Enable **Apply AeNux Patch**
* Click **Run AeNux**

---

## 🧩 Flatpak Installation (Simplified)

A simplified Flatpak-based installation is available through the fork by **@relativemodder**:

👉 **AeGnux:** [https://github.com/relativemodder/aegnux](https://github.com/relativemodder/aegnux)

---

## Plugin Installation

Plugins are **not included** due to copyright restrictions.

To install plugins:

1. Open the AeNux GUI
2. Click **Install Plugin**
3. Select your local plugin `.zip` file
4. Follow the on-screen steps

**For plugin-related inquiries:**

* Telegram: **@cutefishaep**

---

## Uninstallation

1. Open AeNux
2. Click **Uninstall**
3. Delete the project directory

---

## 🙏 Acknowledgments

Special thanks to **MattKC** for his pioneering work.
Forum reference: [https://forum.mattkc.com/viewtopic.php?t=337](https://forum.mattkc.com/viewtopic.php?t=337)

Huge thanks also to **@relativemodder** for creating the AeGnux fork, making installation much simpler for the community. ❤️🐧

---

## 💬 Developer Disclaimer

This is my first GitHub project.
While AI assistance was used during development, the code has been cleaned and refined manually.
Please submit issues if you encounter any problems, I will continue improving AeNux.

---

<div align="center">
  <strong>Happy Editing on Linux! 🎬🐧</strong>
</div>

---

## 🔧 Support

* Telegram: **@cutefishaep**
* GitHub Issues: Bug reports & feature requests

---
