#!/bin/bash

LOGFILE="$HOME/aenux-uninstall.log"
exec > >(tee -a "$LOGFILE") 2>&1

# Ensure zenity is installed
if ! command -v zenity &>/dev/null; then
  echo "[*] Installing zenity..."
  sudo apt update && sudo apt install zenity -y
fi

# Error handler with zenity dialog
handle_error() {
  zenity --error --title="Uninstallation Failed" \
    --text="An error occurred during uninstallation.\nCheck log at: $LOGFILE"
  exit 1
}

trap handle_error ERR

# Step 1: Remove AeNux files
echo "[*] Removing AeNux files..."
rm -rf "$HOME/.wine/drive_c/Program Files/Adobe/Adobe After Effects 2024"
rm -rf "$HOME/.wine/drive_c/Program Files/Adobe/Common/Plug-ins/7.0/MediaCore"
rm -rf ~/.local/share/icons/aenux.png
rm -f "$HOME/Desktop/AeNux.desktop"
rm -f "$HOME/.local/share/applications/AeNux.desktop"

# Step 2: Check if Wine is installed
echo "[*] Checking if Wine is installed..."

if ! dpkg-query -l | grep -q 'winehq'; then
  echo "[*] Wine is already uninstalled. Skipping Wine removal."
else
  # Step 3: Remove Wine and Winetricks
  echo "[*] Wine found. Proceeding to remove Wine and Winetricks..."
  sudo apt-get purge --auto-remove winehq-stable winehq-* winetricks -y
fi

# Step 4: Clean up Wine-related directories
echo "[*] Cleaning up Wine directories..."
rm -rf "$HOME/.wine"
sudo rm -rf /etc/apt/keyrings
sudo rm -f /etc/apt/sources.list.d/winehq-*.sources

# Step 5: Remove i386 architecture if no packages depend on it
echo "[*] Checking for i386 packages..."
i386_packages=$(dpkg --get-selections | grep :i386)

if [ -z "$i386_packages" ]; then
  echo "[*] No i386 packages found. Proceeding to remove i386 architecture..."
  sudo dpkg --remove-architecture i386
else
  echo "[!] Warning: Some i386 packages are still installed. Please remove them manually."
fi

# Step 6: Remove Wine repository and package list
sudo rm -f /etc/apt/sources.list.d/winehq-*.sources

# Step 7: Clean up apt cache
echo "[*] Cleaning up apt cache..."
sudo apt-get clean
sudo apt-get autoremove -y

# Step 8: Ask if user wants to remove Wine and Winetricks directories
zenity --question --title="Remove Wine and Winetricks?" \
  --text="Do you want to remove Wine, Winetricks, and their directories?" \
  --width=400

if [[ $? -eq 0 ]]; then
  # Step 9: Remove Wine and Winetricks directories
  echo "[*] Removing Wine and Winetricks directories..."
  rm -rf ~/.wine
  rm -rf /etc/apt/keyrings
fi

# Step 10: Finish uninstallation
zenity --info --title="Uninstallation Complete" \
  --text="AeNux has been removed successfully!\nWine and Winetricks have been removed.\nYou can now close this window."

# Exit the script
exit 0

