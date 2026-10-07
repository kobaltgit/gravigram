#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
FLUTTER_DIR="$ROOT_DIR/frontend_flutter"

echo "============================================="
echo " Building Antigravity Flutter Web Mini App"
echo "============================================="

if ! command -v flutter &> /dev/null; then
    echo "❌ Error: 'flutter' command not found in PATH."
    echo "Please install Flutter SDK (>=3.20) or unpack a pre-built web archive."
    exit 1
fi

cd "$FLUTTER_DIR"

echo "--> Running 'flutter pub get'..."
flutter pub get

echo "--> Building Flutter Web (release mode)..."
flutter build web --release

echo ""
echo "✅ Build completed successfully!"
echo "Web build located at: $FLUTTER_DIR/build/web"
