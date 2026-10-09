#!/bin/sh
# Removes what install.sh put in place.  sudo ./uninstall.sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this with sudo." >&2
  exit 1
fi

rm -f /usr/local/bin/charge-guard \
      /usr/libexec/charge-guard-helper \
      /usr/share/polkit-1/actions/io.github.chargeguard.policy \
      /usr/share/applications/io.github.chargeguard.desktop \
      /usr/share/icons/hicolor/scalable/apps/io.github.chargeguard.svg

update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -qtf /usr/share/icons/hicolor 2>/dev/null || true

echo "Removed. The charge mode itself is unchanged."
