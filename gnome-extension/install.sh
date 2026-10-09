#!/bin/sh
# Installs the top bar extension for the current user. No sudo needed.
#   ./install.sh
set -eu

UUID=charge-guard@io.github.chargeguard
HERE=$(cd "$(dirname "$0")" && pwd)
DEST="$HOME/.local/share/gnome-shell/extensions/$UUID"

rm -rf "$DEST"
mkdir -p "$DEST"
cp -r "$HERE/metadata.json" "$HERE/extension.js" "$HERE/stylesheet.css" \
      "$HERE/icons" "$DEST/"

echo "Installed in $DEST"

if gnome-extensions enable "$UUID" 2>/dev/null; then
  echo "Enabled."
else
  echo "Could not enable it yet. Log out and back in, then run:"
  echo "  gnome-extensions enable $UUID"
fi

echo
echo "On Wayland a new extension is only loaded after you log out and in."
