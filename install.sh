#!/bin/bash

LOGFILE="$HOME/aenux-setup.log"
exec > >(tee -a "$LOGFILE") 2>&1


# Ensure zenity is installed
if ! command -v zenity &>/dev/null; then
  echo "[*] Installing zenity..."
  sudo apt update && sudo apt install zenity -y
fi



# Step 0: Check if AeNux is already installed
if [[ -f "$HOME/.local/share/applications/AeNux.desktop" ]]; then
  zenity --question \
    --title="AeNux Installation Detected" \
    --text="AeNux is already installed.\nDo you want to reinstall it?" \
    --ok-label="Reinstall" \
    --cancel-label="Quit"

  if [[ $? -ne 0 ]]; then
    echo "[*] Installation cancelled by user."
    exit 0
  else
    if [[ -f "./uninstall.sh" ]]; then
      echo "[*] Running uninstall script..."
      chmod +x ./uninstall.sh
      ./uninstall.sh
    else
      zenity --warning --title="Uninstall Script Missing" \
        --text="uninstall.sh not found. Continuing with reinstall anyway."
    fi
  fi
fi

# Error handler
handle_error() {
  zenity --error --title="Installation Failed" \
    --text="An error occurred during setup.\nCheck log at: $LOGFILE"
  exit 1
}
trap handle_error ERR

# Step 1: Check if Wine is installed
if command -v wine &>/dev/null; then
  echo "[*] Wine is already installed. Skipping Wine installation steps."
else
  echo "[*] Wine not found, preparing to install Wine..."

  # Select Distribution for Wine source
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

  echo "[*] Installing Wine and winetricks..."
  sudo dpkg --add-architecture i386
  sudo mkdir -pm755 /etc/apt/keyrings
  wget -O - https://dl.winehq.org/wine-builds/winehq.key | \
    sudo gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key
  echo "[*] Adding WineHQ source for $distro..."
  sudo wget -NP /etc/apt/sources.list.d/ \
    "https://dl.winehq.org/wine-builds/$origin/dists/$distro/winehq-$distro.sources"
  sudo apt update
  sudo apt install --install-recommends winehq-stable -y
  sudo apt install cabextract -y

  #Install winetricks manually
git clone https://github.com/Winetricks/winetricks
cd winetricks/src
chmod +x winetricks
sudo mv winetricks /usr/local/bin/
cd ../.. 
sudo rm -rf winetricks  
  
  
fi

# Step 2: Check if Winetricks is installed
if ! command -v winetricks &>/dev/null; then
  zenity --error --title="Winetricks Not Found" \
    --text="Winetricks is required for this setup but is not installed.\nPlease install Winetricks manually and rerun the script."
  exit 1
else
  echo "[*] Winetricks is already installed. Skipping Winetricks installation."
fi

# Step 3: Show Wine version
wine_version=$(wine --version)
echo "[*] Wine version: $wine_version"

# Step 4: Setup Winetricks packages
echo "[*] Installing DXVK, Core Fonts, and GDIPLUS..."
winetricks -q dxvk corefonts gdiplus fontsmooth=rgb

# Step 5: Visual C++ Redists
if [[ -f "vcr/install_all.bat" ]]; then
  echo "[*] Installing Visual C++ Redistributables..."
  wine "vcr/install_all.bat"
else
  echo "[!] Warning: vcr/install_all.bat not found. Skipping VC Redist install."
fi

# Step 6: MSXML3 override
echo "[*] Registering msxml3 override..."
cp -f System32/msxml3.dll ~/.wine/drive_c/windows/system32/
cp -f System32/msxml3.dll ~/.wine/drive_c/windows/system32/msxml3r.dll
wine reg add "HKCU\\Software\\Wine\\DllOverrides" /v msxml3 /d native,builtin /f

# Step 7: Download or Select Ae2024.zip
ACTION=$(zenity --list --title="Install AeNux" \
  --column="Action" \
  "Download from huggingface server" \
  "Manually install zip file" \
  --height=300 --width=400)

if [[ "$ACTION" == "Download from huggingface server" ]]; then
  echo "[*] Downloading AeNux"
  wget -O "2024.zip" "https://huggingface.co/cutefishae/AeNux-model/resolve/main/2024.zip"
elif [[ "$ACTION" == "Manually install zip file" ]]; then
  ZIP_FILE=$(zenity --file-selection --title="Select AeNux file" --file-filter="*.zip")
  if [[ -z "$ZIP_FILE" ]]; then
    zenity --error --text="No file selected. Exiting."
    exit 1
  fi
  cp "$ZIP_FILE" "2024.zip"
else
  zenity --error --text="No action selected. Exiting."
  exit 1
fi

# Step 8: Extract the downloaded .zip file
echo "[*] Extracting Ae2024.zip..."
unzip -o "2024.zip" -d "Ae2024"
rm "2024.zip"

# Step 9: Setup After Effects directory
ae_dir="$HOME/cutefishaep/AeNux"

echo "[*] Copying AeNux files..."
mkdir -p "$ae_dir"
cp -rf "Ae2024/Support Files/"* "$ae_dir/"
rm -rf "Ae2024"

# Step 10: Icon setup
mkdir -p "$HOME/.local/share/icons/aenux"
cp -f aenux.png "$HOME/.local/share/icons/aenux/"

# Step 12: Application menu entry
app_menu="$HOME/.local/share/applications/AeNux.desktop"
cat > "$app_menu" <<EOL
[Desktop Entry]
Name=AeNux
Comment=Run AeNux using Wine
Exec=wine "$ae_dir/AfterFX.exe"
Path=$ae_dir
Type=Application
Icon=aenux
Terminal=false
EOL

chmod +x "$app_menu"


# Step 13: Done
zenity --info --title="Installation Complete" \
  --text="AeNux has been installed successfully!\nYou can launch it from your Desktop or Applications menu."

exit 0
