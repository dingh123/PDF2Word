#!/usr/bin/env bash
# Build PDF2Word.app on macOS.
#
# Usage:
#   ./build_scripts/build-macos.sh
#
# Outputs:
#   dist/PDF2Word.app              — the drag-installable app bundle
#   dist/PDF2Word/                 — the equivalent unbundled folder
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "[1/4] Creating virtualenv in $VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "[2/4] Installing build dependencies"
pip install --upgrade pip >/dev/null
pip install -r requirements-build.txt

echo "[3/4] Cleaning previous build artifacts"
rm -rf build dist

echo "[4/4] Running PyInstaller"
pyinstaller pdf2word.spec --noconfirm --clean

echo
echo "✅ Build complete:"
echo "   dist/PDF2Word.app"
echo
echo "To distribute:"
echo "   hdiutil create -volname PDF2Word -srcfolder dist/PDF2Word.app -ov -format UDZO dist/PDF2Word.dmg"
