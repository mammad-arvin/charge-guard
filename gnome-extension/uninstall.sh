#!/bin/sh
set -eu
UUID=charge-guard@io.github.chargeguard
gnome-extensions disable "$UUID" 2>/dev/null || true
rm -rf "$HOME/.local/share/gnome-shell/extensions/$UUID"
echo "Removed."
