#!/usr/bin/env bash
set -e

INSTALL_DIR="/opt/anneal"
BIN_PATH="/usr/local/bin/anneal"
DATA_DIR="/var/lib/anneal"

if [[ "$EUID" -ne 0 ]]; then
    exec sudo "$0" "$@"
fi

uninstall() {
    echo "Uninstalling anneal..."
    rm -f "$BIN_PATH"
    rm -rf "$INSTALL_DIR"
    echo "Removed $BIN_PATH and $INSTALL_DIR"
    echo "Data directory $DATA_DIR was left intact."
}

if [[ "$1" == "--uninstall" ]]; then
    uninstall
    exit 0
fi

# Dependency checks
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is required but not found."
    exit 1
fi

if ! command -v mkfs.ext4 &>/dev/null; then
    echo "Error: mkfs.ext4 is required. Install e2fsprogs >= 1.45."
    exit 1
fi

MKE2FS_VERSION=$(mkfs.ext4 -V 2>&1 | grep -oP '\d+\.\d+' | head -1)
REQUIRED="1.45"
if [[ "$(printf '%s\n' "$REQUIRED" "$MKE2FS_VERSION" | sort -V | head -1)" != "$REQUIRED" ]]; then
    echo "Error: e2fsprogs >= 1.45 is required (found $MKE2FS_VERSION)."
    exit 1
fi

echo "Installing anneal..."

# Copy package
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -r src/anneal/. "$INSTALL_DIR/"

# Install entry point
cp "$INSTALL_DIR/bash/anneal.bash" "$BIN_PATH"
chmod +x "$BIN_PATH"

# Create data directory
mkdir -p "$DATA_DIR"

echo "Done. Run: anneal <command>"
