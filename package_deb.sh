#!/bin/bash
# package_deb.sh
# Build script to generate the Debian package (aenux.deb) for AeNux.

set -e

echo "=== Packaging AeNux as a Debian Package ==="

# 1. Compile clean sources
# Check for valac
if ! command -v valac &> /dev/null; then
    echo "Error: valac (Vala compiler) is not installed."
    echo "Please install it using: sudo apt install valac"
    exit 1
fi

# Check for GTK+ 3.0 development files
if ! pkg-config --exists gtk+-3.0; then
    echo "Error: GTK+ 3.0 development packages are not installed."
    echo "Please install them using: sudo apt install libgtk-3-dev"
    exit 1
fi

# Create build directory if it doesn't exist
mkdir -p build

echo "Compiling aenux runner..."
valac --pkg gio-2.0 --pkg gio-unix-2.0 --pkg gtk+-3.0 src/RunnerApp.vala src/RunnerWindow.vala src/Utils.vala -o build/aenux

echo "Compiling config manager..."
valac --pkg gio-2.0 --pkg gio-unix-2.0 --pkg gtk+-3.0 src/ConfigApp.vala src/InstallerWindow.vala src/ConfiguratorWindow.vala src/Utils.vala -o build/aenux_config

cp src/style.css build/style.css

# 2. Setup build directory
BUILD_DIR="build/deb"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/opt/aenux"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps"

# 3. Copy binaries & styles
cp build/aenux "$BUILD_DIR/opt/aenux/aenux"
cp build/aenux_config "$BUILD_DIR/opt/aenux/aenux_config"
cp src/style.css "$BUILD_DIR/opt/aenux/style.css"

# 4. Create binary symlinks
ln -sf /opt/aenux/aenux "$BUILD_DIR/usr/bin/aenux"
ln -sf /opt/aenux/aenux_config "$BUILD_DIR/usr/bin/aenux_config"

# 5. Copy icons
cp asset/aenux.svg "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/aenux.svg"
cp asset/config.svg "$BUILD_DIR/usr/share/icons/hicolor/scalable/apps/aenux-config.svg"

# 6. Write Desktop Entry (Installer by default)
cat <<EOF > "$BUILD_DIR/usr/share/applications/aenux.desktop"
[Desktop Entry]
Name=Installer
Comment=Install After Effects on Linux
Exec=aenux_config
Icon=aenux-config
Type=Application
Terminal=false
Categories=Graphics;
Actions=CleanUninstall;

[Desktop Action CleanUninstall]
Name=Clean Uninstall AeNux
Exec=aenux_config --remove
EOF

# 7. Write DEBIAN control file
cat <<EOF > "$BUILD_DIR/DEBIAN/control"
Package: aenux
Version: 2.0.0
Section: utils
Priority: optional
Architecture: amd64
Depends: libgtk-3-0, unzip, tar, curl, coreutils, p7zip-full, cabextract
Maintainer: cutefishaep <cutefishaep@github.com>
Description: AeNux is an After Effects manager for Linux with custom Wine prefixes.
EOF

# 8. Write post-install hook
cat <<EOF > "$BUILD_DIR/DEBIAN/postinst"
#!/bin/sh
set -e
chmod +x /opt/aenux/aenux
chmod +x /opt/aenux/aenux_config
chmod 777 /opt/aenux
update-desktop-database -q
gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# 9. Write post-remove hook
cat <<EOF > "$BUILD_DIR/DEBIAN/postrm"
#!/bin/sh
set -e
update-desktop-database -q
gtk-update-icon-cache -f -t /usr/share/icons/hicolor || true
EOF
chmod 755 "$BUILD_DIR/DEBIAN/postrm"

# 10. Build Debian Package
echo "Building deb package..."
dpkg-deb --build "$BUILD_DIR" aenux.deb

# 11. Cleanup temporary files
rm -rf "$BUILD_DIR"

echo "=== Package aenux.deb created successfully! ==="
echo "You can install it with:"
echo "  sudo dpkg -i aenux.deb"
