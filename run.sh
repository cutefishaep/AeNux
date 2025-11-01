#!/bin/bash

# ===========================================
# 🎃 AeNux Halloween Edition Launcher (UV Native)
# ===========================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# -----------------------------------------------------
# Check UV installation
# -----------------------------------------------------
check_uv() {
    if ! command -v uv &> /dev/null; then
        print_error "UV is not installed."

        read -p "Do you want to install UV automatically? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Installing UV..."
            curl -LsSf https://astral.sh/uv/install.sh | sh

            if [ -d "$HOME/.local/bin" ]; then
                export PATH="$HOME/.local/bin:$PATH"
            fi

            if command -v uv &> /dev/null; then
                print_success "UV installed successfully."
            else
                print_error "UV installed but not in PATH. Restart terminal."
                exit 1
            fi
        else
            print_error "UV is required to run AeNux."
            echo "Install manually: curl -LsSf https://astral.sh/uv/install.sh | sh"
            exit 1
        fi
    fi
}

# -----------------------------------------------------
# Check PyQt6 runtime
# -----------------------------------------------------
check_pyqt6() {
    print_status "Checking PyQt6 availability..."
    if ! uv run --with PyQt6 python -c "import PyQt6" 2>/dev/null; then
        print_warning "PyQt6 not found or broken. Installing stable version..."
        uv pip install "PyQt6==6.6.1" "pyqt6-qt6==6.6.1"
    fi
}

# -----------------------------------------------------
# Fix PyQt6 ABI if broken
# -----------------------------------------------------
fix_pyqt6_if_broken() {
    LOG_FILE=".aenux_temp_log.txt"
    if grep -q "undefined symbol" "$LOG_FILE" 2>/dev/null; then
        print_error "Detected PyQt6 ABI mismatch. Fixing automatically..."
        print_status "Reinstalling PyQt6 (Qt 6.6.1 ABI)..."
        uv pip install --force-reinstall "PyQt6==6.6.1" "pyqt6-qt6==6.6.1"
        rm -f "$LOG_FILE"
        print_status "Retrying AeNux launch..."
        uv run run_qt6.py
        exit $?
    fi
}

# -----------------------------------------------------
# Run AeNux GUI
# -----------------------------------------------------
run_app() {
    print_status "Launching AeNux GUI..."

    if [ ! -f "run_qt6.py" ]; then
        print_error "run_qt6.py not found. Run this from AeNux root directory."
        exit 1
    fi

    uv run --with PyQt6 run_qt6.py 2>&1 | tee .aenux_temp_log.txt
    APP_EXIT=${PIPESTATUS[0]}

    if [ $APP_EXIT -eq 0 ]; then
        print_success "Application exited successfully."
        rm -f .aenux_temp_log.txt
    else
        print_error "Application exited with error code $APP_EXIT."
        fix_pyqt6_if_broken
    fi
}

# -----------------------------------------------------
# Welcome Message
# -----------------------------------------------------
welcome_message() {
    echo
    print_status "🎃 AeNux Halloween Edition Launcher"
    echo "================================"
    echo
}

# -----------------------------------------------------
# Cleanup on exit
# -----------------------------------------------------
cleanup() {
    echo
    print_status "Shutting down AeNux..."
    exit 0
}
trap cleanup SIGINT SIGTERM

# -----------------------------------------------------
# Main Function
# -----------------------------------------------------
main() {
    welcome_message
    check_uv
    check_pyqt6
    run_app
}

main "$@"

