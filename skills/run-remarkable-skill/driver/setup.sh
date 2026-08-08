#!/bin/bash
# One-time environment setup: rmapi binary, pandoc, Chrome (for HTML->PDF),
# and a python venv with the packages needed to read back annotations.
set -euo pipefail

BIN_DIR="/usr/local/bin"
VENV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/venv"

if ! command -v rmapi >/dev/null 2>&1; then
  echo "==> installing rmapi (ddvk fork, prebuilt release)"
  ARCH=$(uname -m)
  ASSET="rmapi-macos-arm64.zip"
  [ "$ARCH" = "x86_64" ] && ASSET="rmapi-macos-intel.zip"
  URL=$(curl -s https://api.github.com/repos/ddvk/rmapi/releases/latest \
    | grep browser_download_url | grep "$ASSET" | cut -d '"' -f4)
  TMP=$(mktemp -d)
  curl -sL -o "$TMP/rmapi.zip" "$URL"
  unzip -o "$TMP/rmapi.zip" -d "$TMP" >/dev/null
  sudo cp "$TMP/rmapi" "$BIN_DIR/rmapi"
  sudo chmod +x "$BIN_DIR/rmapi"
  rm -rf "$TMP"
fi
rmapi version

if ! command -v pandoc >/dev/null 2>&1; then
  echo "==> installing pandoc"
  brew install pandoc
fi

if [ ! -d "/Applications/Google Chrome.app" ]; then
  echo "!! Google Chrome not found in /Applications — required for HTML->PDF rendering." >&2
  echo "!! Install it manually: https://www.google.com/chrome/" >&2
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "==> creating python venv (needs python >=3.10, e.g. via pyenv)"
  PY="python3"
  if command -v pyenv >/dev/null 2>&1; then
    CANDIDATE=$(pyenv versions --bare | grep -E '^3\.(1[0-9]|[2-9][0-9])\.[0-9]+$' | sort -V | tail -1)
    [ -n "$CANDIDATE" ] && PY="$(pyenv root)/versions/$CANDIDATE/bin/python3"
  fi
  "$PY" -m venv "$VENV_DIR"
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$VENV_DIR/bin/pip" install -q --upgrade pip
"$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt" -r "$SCRIPT_DIR/requirements-dev.txt"

echo "==> rmapi login check (will prompt for a one-time pairing code if not yet logged in)"
echo "    Get a code at https://my.remarkable.com/device/browser/connect"
rmapi ls >/dev/null

echo "==> setup complete"
