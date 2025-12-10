#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_NAME="AeNux"
ICONS_DIR="$HOME/.local/share/icons"
APPLICATIONS_DIR="$HOME/.local/share/applications"
DESKTOP_DIR="$HOME/Desktop"

ICON_NAME="${APP_NAME}.png"
DESKTOP_FILE="${APP_NAME}.desktop"

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

check_shortcut_exists() {
    [[ -f "$APPLICATIONS_DIR/$DESKTOP_FILE" ]] || \
    [[ -f "$DESKTOP_DIR/$DESKTOP_FILE" ]] || \
    [[ -f "$ICONS_DIR/$ICON_NAME" ]]
}

remove_shortcuts() {
    [[ -f "$APPLICATIONS_DIR/$DESKTOP_FILE" ]] && rm -f "$APPLICATIONS_DIR/$DESKTOP_FILE"
    [[ -f "$DESKTOP_DIR/$DESKTOP_FILE" ]] && rm -f "$DESKTOP_DIR/$DESKTOP_FILE"
    [[ -f "$ICONS_DIR/$ICON_NAME" ]] && rm -f "$ICONS_DIR/$ICON_NAME"
    
    command -v update-desktop-database &>/dev/null && \
    update-desktop-database "$APPLICATIONS_DIR" 2>/dev/null
}

main() {
    echo "Removing AeNux shortcuts..."
    
    if ! check_shortcut_exists; then
        print_warning "No shortcuts found"
        exit 0
    fi
    
    remove_shortcuts
    print_success "Shortcuts removed"
    echo "Done!"
}

main "$@"
