#!/bin/bash

# AeNux Launcher Script
# This script sets up the environment and launches AeNux

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Set Qt environment variables
export QT_QPA_PLATFORM_PLUGIN_PATH="$SCRIPT_DIR/venv/lib/python3.12/site-packages/PyQt6/Qt6/plugins"
export QT_QPA_PLATFORM="xcb"

# Run the application using the virtual environment's Python directly
./venv/bin/python run_qt6.py
