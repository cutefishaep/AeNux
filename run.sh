#!/bin/bash

# AeNux Runner - Main Entry Point
# Handles venv setup, dependency installation, and script execution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
SCRIPTS_DIR="$SCRIPT_DIR/script"
PLUGIN_DIR="$SCRIPT_DIR/PlugIn"

# Functions
print_header() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check Python availability
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found. Please install Python 3.6+"
        exit 1
    fi
    print_success "Python3 found: $(python3 --version)"
}

# Create or verify venv
setup_venv() {
    if [[ ! -d "$VENV_DIR" ]]; then
        print_header "Creating Virtual Environment"
        # Create venv with --system-site-packages to access system packages like gi
        python3 -m venv --system-site-packages "$VENV_DIR"
        print_success "Virtual Environment created at: $VENV_DIR"
    else
        print_success "Virtual Environment already exists"
    fi
}

# Ask user for dependency installation
ask_install_deps() {
    echo ""
    print_info "Dependencies not installed in venv"
    echo -e "${YELLOW}Would you like to install dependencies now? (y/n)${NC}"
    read -p "> " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_dependencies
        return 0
    else
        print_warning "Dependencies not installed. Scripts may not run correctly."
        return 1
    fi
}

# Install dependencies
install_dependencies() {
    print_header "Installing Dependencies"
    
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        print_error "File requirements.txt not found"
        exit 1
    fi
    
    # Setup venv
    setup_venv

    # Install system dependencies FIRST (includes python3-gi)
    print_info "Installing system dependencies..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 cabextract
        print_success "System dependencies installed"
    else
        print_error "apt-get not found. Please install manually:"
        echo "  sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 cabextract"
        exit 1
    fi
    
    # Activate venv and upgrade pip
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip setuptools wheel > /dev/null 2>&1
    
    # Install pip requirements
    print_info "Installing Python dependencies from requirements.txt..."
    pip install -r "$REQUIREMENTS_FILE"
    
    deactivate
    print_success "All dependencies installed successfully"
}

# Check if dependencies are installed
check_dependencies() {
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        return 1
    fi
    source "$VENV_DIR/bin/activate"
    python3 -c "import requests; import gi" 2>/dev/null
    local result=$?
    deactivate
    return $result
}

# Run AeNux Installer
run_installer() {
    print_header "Running AeNux Installer"
    source "$VENV_DIR/bin/activate"
    python3 "$SCRIPTS_DIR/AeNux_Installer.py"
    deactivate
}

# Run AeNux Configurator
run_configurator() {
    print_header "Running AeNux Configurator"
    source "$VENV_DIR/bin/activate"
    python3 "$SCRIPTS_DIR/AeNux_Configurator.py"
    deactivate
}

# Run AeNux (run.py)
run_aenux() {
    print_header "Running AeNux"
    source "$VENV_DIR/bin/activate"
    python3 "$SCRIPTS_DIR/run.py"
    deactivate
}

# Run Plugin Installer
run_plugin_installer() {
    print_header "Running Plugin Installer"
    source "$VENV_DIR/bin/activate"
    python3 "$PLUGIN_DIR/PlugIn.py"
    deactivate
}

# Show menu
show_menu() {
    echo ""
    print_header "AeNux Menu"
    echo -e "${BLUE}1)${NC} Run AeNux Installer"
    echo -e "${BLUE}2)${NC} Run AeNux Configurator"
    echo -e "${BLUE}3)${NC} Run AeNux (run.py)"
    echo -e "${BLUE}4)${NC} Run Plugin Installer"
    echo -e "${BLUE}5)${NC} Install/Reinstall Dependencies"
    echo -e "${BLUE}0)${NC} Exit"
    echo ""
    echo -e "${YELLOW}Choose menu (0-5):${NC}"
}

# Handle command-line arguments
handle_args() {
    case "${1:-}" in
        -r|--run)
            # Run mode: execute run.py with venv
            run_aenux
            exit 0
            ;;
        -i|--install)
            # Install mode: run installer
            run_installer
            exit 0
            ;;
        -c|--config)
            # Config mode: run configurator
            run_configurator
            exit 0
            ;;
        -p|--plugin)
            # Plugin mode: run plugin installer
            run_plugin_installer
            exit 0
            ;;
        -d|--deps)
            # Deps mode: install dependencies
            install_dependencies
            exit 0
            ;;
        -h|--help)
            echo "AeNux Runner"
            echo ""
            echo "Usage: $0 [OPTION]"
            echo ""
            echo "Options:"
            echo "  -r, --run      Run AeNux (run.py)"
            echo "  -i, --install  Run AeNux Installer"
            echo "  -c, --config   Run AeNux Configurator"
            echo "  -p, --plugin   Run Plugin Installer"
            echo "  -d, --deps     Install/reinstall dependencies"
            echo "  -h, --help     Show this help message"
            echo ""
            echo "Without arguments will show interactive menu"
            exit 0
            ;;
        *)
            # Interactive menu mode
            return 0
            ;;
    esac
}

# Main menu loop
main_menu() {
    while true; do
        show_menu
        read -p "" choice
        
        case $choice in
            1)
                run_installer
                ;;
            2)
                run_configurator
                ;;
            3)
                run_aenux
                ;;
            4)
                run_plugin_installer
                ;;
            5)
                install_dependencies
                ;;
            0)
                print_info "Exiting..."
                exit 0
                ;;
            *)
                print_error "Invalid choice"
                ;;
        esac
    done
}

# Main execution
main() {
    print_header "AeNux Runner"
    
    # Check Python
    check_python
    
    # Handle command-line arguments that exit immediately
    handle_args "$@"

    # Setup venv
    setup_venv
    
    # Check dependencies in interactive mode
    if ! check_dependencies; then
        ask_install_deps || true
    else
        print_success "All dependencies available"
    fi
    
    # Show interactive menu
    main_menu
}

# Execute main
main "$@"
