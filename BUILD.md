# AeNux Build System

This document describes how to build AeNux packages locally and how the automated build system works.

## 🏗️ Build System Overview

AeNux uses a comprehensive build system that creates both DEB and AppImage packages with automated changelog generation.

### Package Formats

- **DEB Package**: Native Debian/Ubuntu package with proper dependencies
- **AppImage**: Portable application that runs on any Linux distribution

## 🚀 Quick Start

### Local Building

```bash
# Build both packages with default version
./build-packages.sh

# Build with specific version
./build-packages.sh 1.9.0
```

### GitHub Actions

The build system automatically triggers on:
- Git tags (e.g., `v1.9.0`)
- Manual workflow dispatch

## 📦 Package Details

### DEB Package

**Features:**
- Proper dependency management
- Desktop integration
- System-wide installation
- Automatic desktop database updates
- Icon cache updates

**Dependencies:**
- `python3`, `python3-venv`
- `wine`, `winetricks`
- `wget`, `unzip`, `cabextract`
- `python3-pyqt6` (recommended)

**Installation:**
```bash
sudo dpkg -i aenux_1.9.0_amd64.deb
sudo apt-get install -f  # Install dependencies if needed
```

**Uninstallation:**
```bash
sudo dpkg -r aenux
```

### AppImage Package

**Features:**
- Portable, no installation required
- Self-contained with all dependencies
- Runs on any Linux distribution
- No root privileges required

**Usage:**
```bash
chmod +x aenux-1.9.0-x86_64.AppImage
./aenux-1.9.0-x86_64.AppImage
```

## 🔧 Build System Components

### 1. GitHub Actions Workflows

#### `build-packages.yml`
- Builds DEB and AppImage packages
- Runs on Ubuntu latest
- Creates build artifacts
- Handles dependencies and environment setup

#### `release.yml`
- Generates fancy changelogs
- Creates GitHub releases
- Downloads and attaches build artifacts
- Provides release notifications

### 2. Local Build Script

#### `build-packages.sh`
- Comprehensive local build script
- Creates both package formats
- Handles virtual environment setup
- Generates changelogs
- Provides build verification

### 3. Changelog Generator

#### `scripts/generate-changelog.py`
- Fancy changelog generation
- Conventional commit parsing
- Emoji categorization
- Beautiful markdown formatting
- Statistics and metadata

### 4. DEB Package Configuration

#### `debian/` directory
- `control`: Package metadata and dependencies
- `rules`: Build rules and installation logic
- `postinst`: Post-installation scripts
- `prerm`: Pre-removal scripts
- `postrm`: Post-removal cleanup

## 🎨 Changelog Features

The changelog generator creates beautiful, comprehensive release notes with:

- **Emoji Categories**: Visual categorization of changes
- **Conventional Commits**: Automatic parsing of commit messages
- **Statistics**: Commit counts, contributors, file changes
- **Package Information**: Installation instructions for both formats
- **System Requirements**: Hardware and software requirements
- **Known Issues**: Current limitations and workarounds

### Changelog Categories

- ✨ **Features**: New features and enhancements
- 🐛 **Bug Fixes**: Bug fixes and corrections
- ⚡ **Performance**: Performance improvements
- ♻️ **Refactoring**: Code refactoring and cleanup
- 📚 **Documentation**: Documentation updates
- 💄 **Styling**: Code style and formatting changes
- 🧪 **Testing**: Test additions and improvements
- 🔨 **Build System**: Build system and CI/CD changes
- 👷 **CI/CD**: Continuous integration changes
- 🔧 **Chores**: Maintenance and housekeeping
- 🔒 **Security**: Security improvements
- 💥 **Breaking Changes**: Breaking changes that require attention

## 🛠️ Development Workflow

### 1. Making Changes

```bash
# Make your changes
git add .
git commit -m "feat: add new feature"
git push
```

### 2. Creating a Release

```bash
# Create and push a tag
git tag v1.9.0
git push origin v1.9.0

# GitHub Actions will automatically:
# 1. Build both packages
# 2. Generate changelog
# 3. Create GitHub release
# 4. Upload artifacts
```

### 3. Manual Release

You can also trigger a manual release through the GitHub Actions interface:

1. Go to Actions → Create Release
2. Click "Run workflow"
3. Enter version (e.g., `v1.9.0`)
4. Click "Run workflow"

## 🔍 Build Verification

### Local Testing

```bash
# Test DEB package
sudo dpkg -i dist/aenux_1.9.0_amd64.deb
aenux  # Should launch the application

# Test AppImage
chmod +x dist/aenux-1.9.0-x86_64.AppImage
./dist/aenux-1.9.0-x86_64.AppImage  # Should launch the application
```

### Build Artifacts

After a successful build, you'll find:

```
dist/
├── aenux_1.9.0_amd64.deb          # DEB package
├── aenux-1.9.0-x86_64.AppImage    # AppImage package
└── CHANGELOG.md                    # Generated changelog
```

## 🐛 Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-venv dpkg-dev wget
   ```

2. **Permission Issues**
   ```bash
   chmod +x build-packages.sh
   chmod +x scripts/generate-changelog.py
   ```

3. **Virtual Environment Issues**
   ```bash
   python3 -m venv --clear venv
   source venv/bin/activate
   pip install --upgrade pip
   ```

### Build Logs

Check GitHub Actions logs for detailed build information:
- Go to Actions tab in your repository
- Click on the latest workflow run
- Check individual job logs for errors

## 📋 Requirements

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.8+
- **Tools**: `dpkg-deb`, `wget`, `git`
- **Dependencies**: `python3-venv`, `build-essential`

### GitHub Actions Requirements

- Repository with Actions enabled
- `GITHUB_TOKEN` (automatically provided)
- Proper branch protection (optional)

## 🎯 Future Improvements

- [ ] Multi-architecture support (ARM64)
- [ ] Snap package support
- [ ] Flatpak package support
- [ ] Automated testing in CI
- [ ] Code signing for packages
- [ ] Automated dependency updates

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [AppImage Documentation](https://docs.appimage.org/)
- [Debian Packaging Guide](https://www.debian.org/doc/manuals/debian-reference/ch02.en.html)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Happy Building! 🎬🐧**
