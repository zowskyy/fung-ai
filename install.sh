#!/usr/bin/env bash
# One-line installer for Creator (the no-code app builder), opencode-style.
#
#   curl -fsSL https://example.com/install.sh | sh
#
# Downloads the latest standalone Creator binary from GitHub Releases and
# installs it to a folder on your PATH. No Python required.

set -euo pipefail

REPO="${CREATOR_REPO:-thewi/Creator}"
INSTALL_DIR="${CREATOR_INSTALL_DIR:-$HOME/.local/bin}"

echo "Installing Creator from $REPO ..."

ASSET_NAME="Creator"
case "$(uname -s)" in
  Darwin) ASSET_NAME="Creator-macos" ;;
  Linux)  ASSET_NAME="Creator-linux" ;;
esac

RELEASE_URL="https://api.github.com/repos/$REPO/releases/latest"
ASSET_URL=$(curl -fsSL -H "Accept: application/vnd.github+json" "$RELEASE_URL" \
  | grep -o '"browser_download_url": *"[^"]*'"$ASSET_NAME"'[^"]*"' \
  | head -n1 | sed -E 's/.*"browser_download_url": *"([^"]+)".*/\1/')

if [ -z "$ASSET_URL" ]; then
  echo "Error: no $ASSET_NAME binary found in the latest release of $REPO." >&2
  echo "Build it with 'python build_exe.py' and upload it to Releases." >&2
  exit 1
fi

mkdir -p "$INSTALL_DIR"
echo "Downloading $ASSET_URL ..."
curl -fsSL "$ASSET_URL" -o "$INSTALL_DIR/Creator"
chmod +x "$INSTALL_DIR/Creator"

case ":$PATH:" in
  *":$INSTALL_DIR:"*) ;;
  *) echo "Add this to your shell profile:  export PATH=\"$INSTALL_DIR:\$PATH\"" ;;
esac

echo ""
echo "Done! Run:  Creator"
