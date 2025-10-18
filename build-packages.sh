#!/bin/bash
set -e

# AeNux Package Builder
# Builds both DEB and AppImage packages locally

VERSION=${1:-"1.9.0"}
BUILD_DIR="build"
DIST_DIR="dist"

echo "🎬 AeNux Package Builder v${VERSION}"
echo "=================================="

# Clean and create build directories
echo "🧹 Cleaning build directories..."
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Function to build DEB package
build_deb() {
    echo "📦 Building DEB package..."
    
    # Create DEB structure
    DEB_DIR="$BUILD_DIR/aenux-deb"
    mkdir -p "$DEB_DIR/DEBIAN"
    mkdir -p "$DEB_DIR/usr/bin"
    mkdir -p "$DEB_DIR/usr/share/aenux"
    mkdir -p "$DEB_DIR/usr/share/applications"
    mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$DEB_DIR/usr/share/doc/aenux"
    
    # Copy application files
    echo "📋 Copying application files..."
    cp -r . "$DEB_DIR/usr/share/aenux/"
    rm -rf "$DEB_DIR/usr/share/aenux/.git"
    rm -rf "$DEB_DIR/usr/share/aenux/.github"
    rm -rf "$DEB_DIR/usr/share/aenux/debian"
    rm -rf "$DEB_DIR/usr/share/aenux/aenux-deb"
    rm -rf "$DEB_DIR/usr/share/aenux/aenux.AppDir"
    rm -rf "$DEB_DIR/usr/share/aenux/build"
    rm -rf "$DEB_DIR/usr/share/aenux/dist"
    chmod +x "$DEB_DIR/usr/share/aenux/launch_aenux.sh"
    
    # Create virtual environment
    echo "🐍 Creating virtual environment..."
    python3 -m venv "$DEB_DIR/usr/share/aenux/venv"
    "$DEB_DIR/usr/share/aenux/venv/bin/pip" install --upgrade pip
    "$DEB_DIR/usr/share/aenux/venv/bin/pip" install PyQt6==6.9.1 pyqt6-qt6==6.9.2 pyqt6-sip==13.10.2
    
    # Create control file
    echo "📝 Creating control file..."
    cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: aenux
Version: ${VERSION}
Section: graphics
Priority: optional
Architecture: amd64
Depends: python3, python3-venv, wine, winetricks, wget, unzip, cabextract
Recommends: python3-pyqt6
Maintainer: cutefishaep <cutefishaep@example.com>
Description: AeNux - Adobe After Effects for Linux
 AeNux is a sophisticated Linux solution that enables seamless execution
 of Adobe After Effects through Wine and Winetricks. Designed for creative
 professionals who prefer Linux environments, this project bridges the gap
 between Windows-based creative software and Linux ecosystems.
 .
 Features:
  * Easy installation and setup with modern Qt6 GUI
  * Wine integration with automatic patching
  * Plugin management system for After Effects plugins
  * Cross-distribution compatibility (Ubuntu, Debian, Elementary OS)
  * Virtual environment isolation for better compatibility
  * One-click installation and uninstallation
EOF
    
    # Create desktop entry
    echo "🖥️ Creating desktop entry..."
    cat > "$DEB_DIR/usr/share/applications/aenux.desktop" << 'EOF'
[Desktop Entry]
Name=AeNux Loader
Comment=Run Adobe After Effects using Wine on Linux
Exec=/usr/share/aenux/launch_aenux.sh
Icon=aenux
Terminal=false
Type=Application
Categories=AudioVideo;Video;Graphics;
Keywords=after;effects;adobe;wine;video;editing;
EOF
    
    # Copy icon
    if [ -f asset/logo.png ]; then
        cp asset/logo.png "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/aenux.png"
    fi
    
    # Create postinst script
    cat > "$DEB_DIR/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

# Update icon cache
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t /usr/share/icons/hicolor
fi

# Create symlink for easy access
ln -sf /usr/share/aenux/launch_aenux.sh /usr/local/bin/aenux

echo "AeNux installed successfully!"
echo "You can now find it in your applications menu or run 'aenux' from terminal."

exit 0
EOF
    chmod 755 "$DEB_DIR/DEBIAN/postinst"
    
    # Create prerm script
    cat > "$DEB_DIR/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e

# Kill any running AeNux processes
pkill -f "run_qt6.py" || true
pkill -f "AfterFX.exe" || true

# Remove symlink
rm -f /usr/local/bin/aenux

exit 0
EOF
    chmod 755 "$DEB_DIR/DEBIAN/prerm"
    
    # Build DEB package
    echo "🔨 Building DEB package..."
    dpkg-deb --build "$DEB_DIR"
    mv aenux-deb.deb "$DIST_DIR/aenux_${VERSION}_amd64.deb"
    
    echo "✅ DEB package created: $DIST_DIR/aenux_${VERSION}_amd64.deb"
}

# Function to build AppImage
build_appimage() {
    echo "📦 Building AppImage package..."
    
    # Download AppImageKit if not present
    if [ ! -f "appimagetool-x86_64.AppImage" ]; then
        echo "⬇️ Downloading AppImageKit..."
        wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
        chmod +x appimagetool-x86_64.AppImage
    fi
    
    # Create AppImage structure
    APPIMAGE_DIR="$BUILD_DIR/aenux.AppDir"
    mkdir -p "$APPIMAGE_DIR/usr/bin"
    mkdir -p "$APPIMAGE_DIR/usr/share/aenux"
    mkdir -p "$APPIMAGE_DIR/usr/share/applications"
    mkdir -p "$APPIMAGE_DIR/usr/share/icons/hicolor/256x256/apps"
    
    # Copy application files
    echo "📋 Copying application files..."
    cp -r . "$APPIMAGE_DIR/usr/share/aenux/"
    rm -rf "$APPIMAGE_DIR/usr/share/aenux/.git"
    rm -rf "$APPIMAGE_DIR/usr/share/aenux/.github"
    rm -rf "$APPIMAGE_DIR/usr/share/aenux/debian"
    rm -rf "$APPIMAGE_DIR/usr/share/aenux/aenux-deb"
    rm -rf "$APPIMAGE_DIR/usr/share/aenux/aenux.AppDir"
    rm -rf "$APPIMAGE_DIR/usr/share/aenux/build"
    rm -rf "$APPIMAGE_DIR/usr/share/aenux/dist"
    chmod +x "$APPIMAGE_DIR/usr/share/aenux/launch_aenux.sh"
    
    # Create virtual environment
    echo "🐍 Creating virtual environment..."
    python3 -m venv "$APPIMAGE_DIR/usr/share/aenux/venv"
    "$APPIMAGE_DIR/usr/share/aenux/venv/bin/pip" install --upgrade pip
    "$APPIMAGE_DIR/usr/share/aenux/venv/bin/pip" install PyQt6==6.9.1 pyqt6-qt6==6.9.2 pyqt6-sip==13.10.2
    
    # Create AppRun
    echo "🏃 Creating AppRun..."
    cat > "$APPIMAGE_DIR/AppRun" << 'EOF'
#!/bin/bash
set -e

# Get the directory where AppRun is located
APPDIR="$(dirname "$(readlink -f "${0}")")"

# Set environment variables
export QT_QPA_PLATFORM_PLUGIN_PATH="$APPDIR/usr/share/aenux/venv/lib/python3.12/site-packages/PyQt6/Qt6/plugins"
export QT_QPA_PLATFORM="xcb"
export PATH="$APPDIR/usr/bin:$PATH"

# Change to the application directory
cd "$APPDIR/usr/share/aenux"

# Run the application
exec "$APPDIR/usr/share/aenux/venv/bin/python" run_qt6.py "$@"
EOF
    chmod +x "$APPIMAGE_DIR/AppRun"
    
    # Create desktop entry
    echo "🖥️ Creating desktop entry..."
    cat > "$APPIMAGE_DIR/aenux.desktop" << 'EOF'
[Desktop Entry]
Name=AeNux Loader
Comment=Run Adobe After Effects using Wine on Linux
Exec=aenux
Icon=aenux
Terminal=false
Type=Application
Categories=AudioVideo;Video;Graphics;
Keywords=after;effects;adobe;wine;video;editing;
X-AppImage-Version=1.0.0
X-AppImage-Name=AeNux
X-AppImage-Comment=Adobe After Effects for Linux
EOF
    
    # Copy icon
    if [ -f asset/logo.png ]; then
        cp asset/logo.png "$APPIMAGE_DIR/aenux.png"
        cp asset/logo.png "$APPIMAGE_DIR/usr/share/icons/hicolor/256x256/apps/aenux.png"
    fi
    
    # Build AppImage
    echo "🔨 Building AppImage..."
    ./appimagetool-x86_64.AppImage "$APPIMAGE_DIR" "$DIST_DIR/aenux-${VERSION}-x86_64.AppImage"
    
    echo "✅ AppImage created: $DIST_DIR/aenux-${VERSION}-x86_64.AppImage"
}

# Function to generate changelog
generate_changelog() {
    echo "📝 Generating changelog..."
    if [ -f "scripts/generate-changelog.py" ]; then
        python3 scripts/generate-changelog.py "v${VERSION}" "" "HEAD"
        echo "✅ Changelog generated: CHANGELOG.md"
    else
        echo "⚠️ Changelog generator not found, skipping..."
    fi
}

# Main build process
echo "🚀 Starting build process..."

# Check dependencies
echo "🔍 Checking dependencies..."
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 is required but not installed."; exit 1; }
command -v dpkg-deb >/dev/null 2>&1 || { echo "❌ dpkg-deb is required but not installed."; exit 1; }
command -v wget >/dev/null 2>&1 || { echo "❌ wget is required but not installed."; exit 1; }

# Build packages
build_deb
build_appimage
generate_changelog

# Summary
echo ""
echo "🎉 Build completed successfully!"
echo "=================================="
echo "📦 DEB Package: $DIST_DIR/aenux_${VERSION}_amd64.deb"
echo "📦 AppImage: $DIST_DIR/aenux-${VERSION}-x86_64.AppImage"
echo "📝 Changelog: CHANGELOG.md"
echo ""
echo "📊 Package sizes:"
ls -lh "$DIST_DIR"/*.deb "$DIST_DIR"/*.AppImage 2>/dev/null || true
echo ""
echo "🚀 Ready for distribution!"
