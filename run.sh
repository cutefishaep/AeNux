#!/bin/bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if asset/System32 directory exists
check_system32_assets() {
    local system32_dir="$(dirname "$0")/asset/System32"
    
    if [ ! -d "$system32_dir" ]; then
        print_error "asset/System32 directory not found at: $system32_dir"
        
        # Show Zenity error popup
        zenity --error \
               --title="Missing Required Files" \
               --width=500 \
               --height=200 \
               --text="The asset/System32 directory was not found!\n\nThis directory contains essential DLL files required for AeNux to function properly.\n\nPlease copy the necessary DLL files from your Windows system.\n\nFor detailed instructions, visit:\ngithub.com/cutefishaep/AeNux\n\nAfter copying the required files, please run this script again."
        
        exit 1
    else
        print_success "asset/System32 directory found"
    fi
}

# Check UV installation
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "UV is not installed."

        read -p "Do you want to install UV automatically? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Installing UV..."
            curl -LsSf https://astral.sh/uv/install.sh | bash

            if [ -f "$HOME/.local/bin/uv" ]; then
                print_success "UV installed successfully."
                
                # Add to PATH if not already present
                if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
                    print_status "Adding ~/.local/bin to PATH..."
                    echo "export PATH=\"$HOME/.local/bin:\$PATH\"" >> ~/.bashrc
                    source ~/.bashrc
                fi
            else
                print_error "UV installation failed."
                exit 1
            fi
        else
            print_error "UV is required to run AeNux."
            echo "Install manually: curl -LsSf https://astral.sh/uv/install.sh | bash"
            exit 1
        fi
    fi
}

# Check PyQt6 runtime
check_pyqt6() {
    print_status "Checking PyQt6 availability..."
    if ! uv run --with PyQt6 python -c "import PyQt6" 2>/dev/null; then
        print_warning "PyQt6 not found. Installing stable version..."
        uv pip install "PyQt6==6.6.1" "pyqt6-qt6==6.6.1"
    fi
}

# Install missing dependencies for Qt xcb plugin
install_xcb_dependencies() {
    print_status "Checking Qt xcb platform plugin dependencies..."

    local dependencies=("libxcb1" "libxcb-cursor0" "libxcb-xinerama0" "libxcb-randr0" "libx11-xcb1" "libglu1-mesa")

    for dep in "${dependencies[@]}"; do
        if ! dpkg-query -l "$dep" &>/dev/null; then
            print_warning "$dep is missing. Installing..."
            sudo apt install -y "$dep"
        fi
    done
}

# Remove unnecessary dependencies
remove_old_dependencies() {
    print_status "Cleaning up dependencies..."

    if dpkg-query -l "xcb-cursor0" &>/dev/null; then
        print_status "Removing unnecessary 'xcb-cursor0' package..."
        sudo apt-get remove --purge -y xcb-cursor0
    fi

    sudo apt-get clean
}

# Fix PyQt6 ABI if broken
fix_pyqt6_if_broken() {
    if uv run --with PyQt6 python -c "import PyQt6" 2>/dev/null; then
        print_error "Detected PyQt6 ABI mismatch. Reinstalling..."
        uv pip install --force-reinstall "PyQt6==6.6.1" "pyqt6-qt6==6.6.1"
        print_status "Retrying AeNux launch..."
        uv run run_qt6.py
        exit $?
    fi
}

# Run AeNux GUI
run_app() {
    print_status "Launching AeNux GUI..."

    if [ ! -f "run_qt6.py" ]; then
        print_error "run_qt6.py not found. Run from AeNux root directory."
        exit 1
    fi

    export QT_QPA_PLATFORM_PLUGIN_PATH=/usr/lib/qt/plugins/platforms
    uv run --with PyQt6 run_qt6.py
    local app_exit=$?

    if [ $app_exit -eq 0 ]; then
        print_success "Application exited successfully."
    else
        print_error "Application exited with error code $app_exit."
        fix_pyqt6_if_broken
    fi
}

# Welcome message
welcome_message() {
    echo
    print_status "Don't tell Aih Don't Bee about this"
    echo "================================"
    echo
}

# Cleanup on exit
cleanup() {
    echo
    print_status "Shutting down AeNux..."
    exit 0
}

# Main function
main() {
    welcome_message
    check_system32_assets  # Check for required System32 assets first
    check_uv
    check_pyqt6
    install_xcb_dependencies
    remove_old_dependencies
    run_app
}

# Set up signal handlers and run main
trap cleanup SIGINT SIGTERM
main "$@"
