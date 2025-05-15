#!/bin/bash

LOGFILE="$HOME/aenux-uninstall.log"
exec > >(tee -a "$LOGFILE") 2>&1

# Ensure zenity is installed
if ! command -v zenity &>/dev/null; then
  echo "[*] Installing zenity..."
  sudo apt update && sudo apt install zenity -y
fi

# Error handler
handle_error() {
  zenity --error --title="Uninstallation Failed" \
    --text="An error occurred during uninstallation.\nCheck log at: $LOGFILE"
  exit 1
}
trap handle_error ERR

zenity --info --title="Uninstalling AeNux..." --text="Removing AeNux installation files..."

# Step 1: Remove AeNux-related files
echo "[*] Removing AeNux files..."
rm -rf "$HOME/cutefishaep/AeNux"
rm -f "$HOME/Desktop/AeNux.desktop"
rm -f "$HOME/.local/share/applications/AeNux.desktop"
rm -f "$HOME/.local/share/icons/aenux.png"

# Step 2: Ask if user wants to remove Wine & Winetricks completely
zenity --question --title="Remove Wine & Winetricks?" \
  --text="Do you want to completely remove Wine, Winetricks, and related configurations?\n(This may affect other Wine applications)" \
  --width=400

if [[ $? -eq 0 ]]; then
  echo "[*] Removing Wine and Winetricks..."

  # Purge Wine and Winetricks
  sudo apt-get purge --auto-remove winehq-* winetricks -y

  # Remove wine config and keys
  echo "[*] Cleaning Wine-related configs..."
  rm -rf "$HOME/.wine"
  sudo rm -rf /etc/apt/keyrings
  sudo rm -f /etc/apt/sources.list.d/winehq-*.sources

  # Optional: Remove i386 if nothing depends on it
  if ! dpkg --get-selections | grep -q ":i386"; then
    echo "[*] No i386 packages found. Removing i386 architecture..."
    sudo dpkg --remove-architecture i386
  else
    echo "[!] i386 packages still present. Skipping architecture removal."
  fi

  sudo apt-get autoremove -y
  sudo apt-get clean
fi

# Done
echo "Done uninstalling!"
exit 0