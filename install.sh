#!/bin/bash

LOGFILE="$HOME/aenux-setup.log"
exec > >(tee -a "$LOGFILE") 2>&1

# Ensure zenity is installed
if ! command -v zenity &>/dev/null; then
  echo "[*] Installing zenity..."
  sudo apt update && sudo apt install zenity -y
fi

# Error handler
handle_error() {
  zenity --error --title="Installation Failed" \
    --text="An error occurred during setup.\nCheck log at: $LOGFILE"
  exit 1
}

trap handle_error ERR

# Step 1: Select Distribution
DISTRO=$(zenity --list --title="Select Your Distribution" \
  --column="ID" --column="Distribution" \
  1 "Ubuntu 25.04 (plucky)" \
  2 "Ubuntu 24.10 (oracular)" \
  3 "Ubuntu 24.04 / Mint 22 (noble)" \
  4 "Ubuntu 22.04 / Mint 21.x (jammy)" \
  5 "Ubuntu 20.04 / Mint 20.x (focal)" \
  6 "Debian Testing (trixie)" \
  7 "Debian 12 (bookworm)" \
  8 "Debian 11 (bullseye)" \
  --height=400 --width=400)

[ -z "$DISTRO" ] && zenity --error --text="No distribution selected. Exiting." && exit 1

case $DISTRO in
  1) distro="plucky"; origin="ubuntu" ;;
  2) distro="oracular"; origin="ubuntu" ;;
  3) distro="noble"; origin="ubuntu" ;;
  4) distro="jammy"; origin="ubuntu" ;;
  5) distro="focal"; origin="ubuntu" ;;
  6) distro="trixie"; origin="debian" ;;
  7) distro="bookworm"; origin="debian" ;;
  8) distro="bullseye"; origin="debian" ;;
  *) handle_error ;;
esac

# Step 2: Setup Wine repo
echo "[*] Adding i386 architecture..."
sudo dpkg --add-architecture i386

sudo mkdir -pm755 /etc/apt/keyrings
wget -O - https://dl.winehq.org/wine-builds/winehq.key | \
  sudo gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key

echo "[*] Adding WineHQ source for $distro..."
sudo wget -NP /etc/apt/sources.list.d/ \
  "https://dl.winehq.org/wine-builds/$origin/dists/$distro/winehq-$distro.sources"

# Step 3: Install packages
echo "[*] Installing Wine and dependencies..."
sudo apt update
sudo apt install --install-recommends winehq-stable winetricks unzip wget zenity -y

# Step 4: Show wine version
wine_version=$(wine --version)
echo "[*] Wine version: $wine_version"

# Step 5: Setup Winetricks packages
echo "[*] Installing DXVK, Core Fonts, and GDIPLUS..."
winetricks -q dxvk corefonts gdiplus fontsmooth=rgb

# Step 6: Visual C++ Redists
if [[ -f "vcr/install_all.bat" ]]; then
  echo "[*] Installing Visual C++ Redistributables..."
  wine "vcr/install_all.bat"
else
  echo "[!] Warning: vcr/install_all.bat not found. Skipping VC Redist install."
fi

# Step 7: MSXML3 override
echo "[*] Registering msxml3 override..."
cp -f System32/msxml3.dll ~/.wine/drive_c/windows/system32/
cp -f System32/msxml3.dll ~/.wine/drive_c/windows/system32/msxml3r.dll
wine reg add "HKCU\\Software\\Wine\\DllOverrides" /v msxml3 /d native,builtin /f

# Step 8: Download and extract Ae2024
echo "[*] Downloading Ae2024..."
wget -O "2024.zip" "https://huggingface.co/cutefishae/AeNux-model/resolve/main/2024.zip"

unzip -o "2024.zip" -d "Ae2024"
rm "2024.zip"

# Step 9: Setup After Effects directory
ae_dir="$HOME/.wine/drive_c/Program Files/Adobe/Adobe After Effects 2024"
plugin_dir="$HOME/.wine/drive_c/Program Files/Adobe/Common/Plug-ins/7.0/MediaCore"

echo "[*] Copying AeNux files..."
mkdir -p "$ae_dir" "$plugin_dir"
cp -rf "Ae2024/Support Files/"* "$ae_dir/"
rm -rf "Ae2024"

# Step 10: Icon setup
mkdir -p ~/.local/share/icons/
cp -f aenux.png ~/.local/share/icons/

# Step 11: Create desktop shortcut
desktop_file="$HOME/Desktop/AeNux.desktop"
cat > "$desktop_file" <<EOL
[Desktop Entry]
Name=AeNux
Comment=Run Adobe AeNux using Wine
Exec=wine "$ae_dir/AfterFX.exe"
Path=$ae_dir
Type=Application
Icon=aenux
Terminal=false
EOL

chmod +x "$desktop_file"

# Step 12: Application menu
app_menu="$HOME/.local/share/applications/AeNux.desktop"
cp "$desktop_file" "$app_menu"
chmod +x "$app_menu"

# Step 13: Done
zenity --info --title="Installation Complete" \
  --text="AeNux has been installed successfully!\nYou can launch it from your Desktop or Applications menu."

exit 0
