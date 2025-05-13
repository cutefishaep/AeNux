# AeNux v1.3

<p align="center">
  <img src="https://raw.githubusercontent.com/cutefishaep/AeNux/refs/heads/main/LOGO.png" alt="AeNux Logo" width="200"/><br>
  <strong style="font-size:100px">AeNux</strong>
</p>



**AeNux** is a custom Linux command that helps you run **Ae** on Linux using **Wine** and **Winetricks**. This project aims to provide a more seamless way to launch After Effects for users who prefer Linux over Windows, especially for creative work.

> ⚠️ This project is for educational purposes only. Please do not misuse it.  
> The main goal of this project is to get familiar with using Linux for creative software.

---

## 🧰 Features

- Launch Adobe After Effects on Linux using a single command.
- Automatically configured to work with **Wine** and **Winetricks**.
- Improved plugin compatibility (see differences below).
- ✅ If you're using **Intel UHD Graphics**, the **Element 3D plugin** will detect your GPU **automatically**.
  - No need to manually replace environment files like in Windows.
- ⚡ **BCC** and **Sapphire plugins** import **significantly faster** compared to Windows, which often hangs or becomes unresponsive during import.
---

## 🐞 Known Issues

- ❌ **OpenCL / Hardware acceleration** does not work.
- ⚠️ Some UI elements (e.g., Flow Plugin) may **flicker**.
- ⚠️ **FX Console** works inconsistently — it is **recommended to install FX Console before other plugins**.
- 💥 May **crash** if After Effects consumes all available RAM.
- ❓ Please submit issue if you find some bugs!

---

## 💻 Tested On

- **OS**: Linux Mint 22.1 Cinnamon  
- **CPU**: 11th Gen Intel® Core™ i3-1115G4 @ 3.00GHz × 2  
- **GPU**: Intel Corporation Tiger Lake-LP GT2 [UHD Graphics G4]  
- **Memory**: 8 GB RAM  

> Results may vary on different hardware or distros.

---

## ⚙️ Installation & Configuration


Clone the repository and run the installer:

```bash
chmod +x install.sh && ./install.sh
```

## 📌 Note

- The method to install Wine may differ depending on your Linux distro.  
  You can modify the instructions in `./install.sh` to suit your system.
- It is **strongly recommended to disable swap memory**,  
  as using swap can reduce the lifespan of your SSD.

---

## 📜 License

This project is open for educational and personal use only. No commercial redistribution or misuse is allowed.

---

Happy Editing on Linux! 🎬🐧

