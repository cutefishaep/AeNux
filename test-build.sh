#!/bin/bash
set -e

# Test script for AeNux build system
echo "🧪 Testing AeNux Build System"
echo "=============================="

# Test changelog generator
echo "📝 Testing changelog generator..."
if [ -f "scripts/generate-changelog.py" ]; then
    python3 scripts/generate-changelog.py "v1.9.0-test" "" "HEAD" > /dev/null
    echo "✅ Changelog generator works"
else
    echo "❌ Changelog generator not found"
fi

# Test build script
echo "🔨 Testing build script..."
if [ -f "build-packages.sh" ]; then
    echo "✅ Build script found"
    echo "   Run './build-packages.sh 1.9.0-test' to test locally"
else
    echo "❌ Build script not found"
fi

# Test GitHub Actions workflows
echo "⚙️ Testing GitHub Actions workflows..."
if [ -d ".github/workflows" ]; then
    echo "✅ GitHub Actions workflows found:"
    ls -la .github/workflows/
else
    echo "❌ GitHub Actions workflows not found"
fi

# Test DEB package configuration
echo "📦 Testing DEB package configuration..."
if [ -d "debian" ]; then
    echo "✅ DEB package configuration found:"
    ls -la debian/
else
    echo "❌ DEB package configuration not found"
fi

# Test AppImage configuration
echo "📦 Testing AppImage configuration..."
if [ -f "appimage.yml" ]; then
    echo "✅ AppImage configuration found"
else
    echo "❌ AppImage configuration not found"
fi

# Test main application
echo "🎬 Testing main application..."
if [ -f "run_qt6.py" ]; then
    echo "✅ Main application found"
    echo "   Run './launch_aenux.sh' to test the application"
else
    echo "❌ Main application not found"
fi

echo ""
echo "🎉 Build system test completed!"
echo "=============================="
echo ""
echo "To test the full build process:"
echo "1. Run: ./build-packages.sh 1.9.0-test"
echo "2. Check the 'dist/' directory for packages"
echo "3. Test the packages locally"
echo ""
echo "To test GitHub Actions:"
echo "1. Push changes to GitHub"
echo "2. Create a tag: git tag v1.9.0-test && git push origin v1.9.0-test"
echo "3. Check Actions tab for build progress"
