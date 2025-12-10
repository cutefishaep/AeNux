#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

APP_NAME="AeNux"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/aenux_config.json"
ICON_SRC="$SCRIPT_DIR/../src/aenux.png"

WINE_PATH=""
WINEPREFIX=""
AENUX_PATH=""
AFTERFX_EXE=""

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

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

load_config() {
    [[ ! -f "$CONFIG_FILE" ]] && print_error "Config not found" && exit 1
    
    WINE_PATH=$(grep -o '"wine_path": "[^"]*' "$CONFIG_FILE" | cut -d'"' -f4)
    WINEPREFIX=$(grep -o '"wineprefix": "[^"]*' "$CONFIG_FILE" | cut -d'"' -f4)
    AENUX_PATH=$(grep -o '"aenux_path": "[^"]*' "$CONFIG_FILE" | cut -d'"' -f4)
    
    [[ -z "$WINE_PATH" || -z "$WINEPREFIX" || -z "$AENUX_PATH" ]] && print_error "Invalid config" && exit 1
    
    AFTERFX_EXE="$AENUX_PATH/AfterFX.exe"
    print_success "Config loaded"
}

validate_inputs() {
    if [[ ! -f "$AFTERFX_EXE" ]]; then
        print_error "AfterFX.exe not found at: $AFTERFX_EXE"
        exit 1
    fi
    [[ ! -f "$ICON_SRC" ]] && print_warning "Icon not found" && ICON_SRC=""
}

remove_old_shortcuts() {
    [[ -f "$APPLICATIONS_DIR/$DESKTOP_FILE" ]] && rm -f "$APPLICATIONS_DIR/$DESKTOP_FILE"
    [[ -f "$DESKTOP_DIR/$DESKTOP_FILE" ]] && rm -f "$DESKTOP_DIR/$DESKTOP_FILE"
    [[ -f "$ICONS_DIR/$ICON_NAME" ]] && rm -f "$ICONS_DIR/$ICON_NAME" && print_success "Old shortcuts removed"
}

create_directories() {
    mkdir -p "$ICONS_DIR" "$APPLICATIONS_DIR" "$DESKTOP_DIR"
}

copy_icon() {
    [[ -z "$ICON_SRC" ]] && return 0
    [[ ! -f "$ICON_SRC" ]] && return 0
    cp "$ICON_SRC" "$ICONS_DIR/$ICON_NAME" 2>/dev/null && print_success "Icon copied to $ICONS_DIR"
}

create_menu_shortcut() {
    local ICON_LINE=""
    [[ -f "$ICONS_DIR/$ICON_NAME" ]] && ICON_LINE="Icon=$APP_NAME" || ICON_LINE="# No icon"
    
    # Get the script directory (parent of script/)
    SCRIPT_PARENT="$(dirname "$SCRIPT_DIR")"
    
    cat > "$APPLICATIONS_DIR/$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Name=$APP_NAME
Comment=Run AeNux using Wine
Exec=$SCRIPT_PARENT/run.sh -r
Path=$SCRIPT_PARENT
$ICON_LINE
Terminal=false
Type=Application
Categories=Utility;AudioVideo;Video;
StartupNotify=true
EOF
    
    chmod 755 "$APPLICATIONS_DIR/$DESKTOP_FILE"
    print_success "Menu shortcut created"
}

create_desktop_shortcut() {
    local ICON_LINE=""
    [[ -f "$ICONS_DIR/$ICON_NAME" ]] && ICON_LINE="Icon=$APP_NAME" || ICON_LINE="# No icon"
    
    # Get the script directory (parent of script/)
    SCRIPT_PARENT="$(dirname "$SCRIPT_DIR")"
    
    cat > "$DESKTOP_DIR/$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Name=$APP_NAME
Comment=Run AeNux using Wine
Exec=$SCRIPT_PARENT/run.sh -r
Path=$SCRIPT_PARENT
$ICON_LINE
Terminal=false
Type=Application
Categories=Utility;AudioVideo;Video;
StartupNotify=true
EOF
    
    chmod 755 "$DESKTOP_DIR/$DESKTOP_FILE"
    print_success "Desktop shortcut created"
}

update_desktop_database() {
    command -v update-desktop-database &>/dev/null && update-desktop-database "$APPLICATIONS_DIR" 2>/dev/null
}

main() {
    echo "Creating AeNux shortcuts..."
    load_config
    validate_inputs
    remove_old_shortcuts
    create_directories
    copy_icon
    create_menu_shortcut
    create_desktop_shortcut
    update_desktop_database
    echo "Done!"
}

main "$@"