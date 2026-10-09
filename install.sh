#!/bin/sh
# Installs Charge Guard from this directory. Run once:  sudo ./install.sh
# The .deb in dist/ puts the same files in the same places.
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this with sudo." >&2
  exit 1
fi

HERE=$(cd "$(dirname "$0")" && pwd)

install -D -m 0755 "$HERE/chargeguard.py"              /usr/local/bin/charge-guard
install -D -m 0755 "$HERE/charge-guard-helper"         /usr/libexec/charge-guard-helper
install -D -m 0644 "$HERE/io.github.chargeguard.policy" \
  /usr/share/polkit-1/actions/io.github.chargeguard.policy
install -D -m 0644 "$HERE/io.github.chargeguard.desktop" \
  /usr/share/applications/io.github.chargeguard.desktop
install -D -m 0644 "$HERE/io.github.chargeguard.svg" \
  /usr/share/icons/hicolor/scalable/apps/io.github.chargeguard.svg

UUID=charge-guard@io.github.chargeguard
EXT=/usr/share/gnome-shell/extensions/$UUID
install -D -m 0644 "$HERE/gnome-extension/metadata.json"  "$EXT/metadata.json"
install -D -m 0644 "$HERE/gnome-extension/extension.js"   "$EXT/extension.js"
install -D -m 0644 "$HERE/gnome-extension/stylesheet.css" "$EXT/stylesheet.css"
install -D -m 0644 "$HERE/gnome-extension/icons/io.github.chargeguard-symbolic.svg" \
  "$EXT/icons/io.github.chargeguard-symbolic.svg"

update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -qtf /usr/share/icons/hicolor 2>/dev/null || true

echo "Done. Charge Guard is in your app menu."
echo "For the top bar switch, see EXTENSION.md."
