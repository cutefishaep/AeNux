#!/bin/bash

# Enable i386 architecture and add WineHQ repository
echo "[*] Adding i386 architecture..."
sudo dpkg --add-architecture i386

# Setup keyrings
sudo mkdir -pm755 /etc/apt/keyrings
wget -O - https://dl.winehq.org/wine-builds/winehq.key | \
  sudo gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key

clear 

# Show OS and version info
echo
echo "[*] Detecting your operating system:"
if command -v lsb_release &> /dev/null; then
  lsb_release -a
else
  cat /etc/os-release
fi

# Prompt user to select their distribution
echo
echo "Select your distribution:"
echo "1) Ubuntu 25.04 (plucky)"
echo "2) Ubuntu 24.10 (oracular)"
echo "3) Ubuntu 24.04 / Linux Mint 22 (noble)"
echo "4) Ubuntu 22.04 / Linux Mint 21.x (jammy)"
echo "5) Ubuntu 20.04 / Linux Mint 20.x (focal)"
echo "6) Debian Testing (trixie)"
echo "7) Debian 12 (bookworm)"
echo "8) Debian 11 (bullseye)"
echo

read -p "Enter the number of your distribution [1-8]: " choice

case $choice in
  1) distro="plucky"; origin="ubuntu" ;;
  2) distro="oracular"; origin="ubuntu" ;;
  3) distro="noble"; origin="ubuntu" ;;
  4) distro="jammy"; origin="ubuntu" ;;
  5) distro="focal"; origin="ubuntu" ;;
  6) distro="trixie"; origin="debian" ;;
  7) distro="bookworm"; origin="debian" ;;
  8) distro="bullseye"; origin="debian" ;;
  *) echo "Invalid option. Exiting..."; exit 1 ;;
esac

# Add the correct WineHQ source list
echo "[*] Adding WineHQ source for $distro..."
sudo wget -NP /etc/apt/sources.list.d/ \
  "https://dl.winehq.org/wine-builds/$origin/dists/$distro/winehq-$distro.sources"

# Install Wine and Winetricks
echo "[*] Updating package list and installing Wine & Winetricks..."
sudo apt update
sudo apt install --install-recommends winehq-stable winetricks -y

# Display Wine version
clear
wine --version

# Winetricks setup
echo "[*] Installing DXVK and Core Fonts..."
winetricks dxvk corefonts

echo "[*] Installing GDIPLUS and enabling font smoothing..."
winetricks gdiplus fontsmooth=rgb

# Install VC Redists
echo "[*] Installing Visual C++ Redistributables..."
wine vcr/install_all.bat

# Register MSXML3 override
echo "[*] Registering msxml3 override..."
cp -f System32/msxml3.dll System32/msxml3r.dll ~/.wine/drive_c/windows/system32/
wine reg add "HKCU\\Software\\Wine\\DllOverrides" /v msxml3 /d native,builtin /f


# Download and extract Ae2024.zip
echo "[*] Downloading Ae2024.zip..."
wget -O "2024.zip" "https://huggingface.co/cutefishae/AeNux-model/resolve/main/2024.zip"

# Make Direction
mkdir -p "Ae2024"

echo "[*] Extracting Ae2024.zip..."
unzip -o "2024.zip" -d "Ae2024" # Extract to current directory

# Clean up the zip file
rm "2024.zip"


# Create AE folders and copy files
echo "[*] Setting up Adobe AeNux directory..."
mkdir -p "$HOME/.wine/drive_c/Program Files/Adobe/Adobe After Effects 2024"
mkdir -p "$HOME/.wine/drive_c/Program Files/Adobe/Common/Plug-ins/7.0/MediaCore"

echo "[*] Copying AeNux files..."
cp -rf "Ae2024/Support Files/"* "$HOME/.wine/drive_c/Program Files/Adobe/Adobe After Effects 2024/"

# Copy some images file
echo "[*] Copying aenux.png to ~/.local/share/icons/"
sudo cp -f aenux.png ~/.local/share/icons/

# Create desktop shortcut
echo "[*] Creating desktop shortcut..."

DESKTOP_FILE="$HOME/Desktop/AfterEffects.desktop"
cat > "$DESKTOP_FILE" <<EOL
[Desktop Entry]
Name=AeNux
Comment=Run Adobe AeNux using Wine
Exec=wine "$HOME/.wine/drive_c/Program Files/Adobe/Adobe After Effects 2024/AfterFX.exe"
Type=Application
Icon=aenux
Terminal=false
Categories=Graphics;Video;
EOL

chmod +x "$DESKTOP_FILE"
echo "[✓] Shortcut created at: $DESKTOP_FILE"

# Add to application menu
echo "[*] Adding AeNux to application menu..."

APPLICATION_MENU="$HOME/.local/share/applications/AeNux.desktop"
cat > "$APPLICATION_MENU" <<EOL
[Desktop Entry]
Name=AeNux
Comment=Run Adobe AeNux using Wine
Exec=wine "$HOME/.wine/drive_c/Program Files/Adobe/Adobe After Effects 2024/AfterFX.exe"
Icon=aenux
Terminal=false
Categories=Graphics;Video;
EOL

chmod +x "$APPLICATION_MENU"
echo "[✓] AeNux added to application menu at: $APPLICATION_MENU"

echo "[✓] Setup complete! You can now run AeNux using Wine."

