#!/bin/sh
# Builds dist/charge-guard_<version>_all.deb from this working tree.
set -eu

VERSION=1.0.0
HERE=$(cd "$(dirname "$0")/.." && pwd)
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

# mktemp makes the directory 0700. That mode would land on / at install
# time, so the package root must be a normal 0755 directory.
chmod 0755 "$STAGE"

install -D -m 0755 "$HERE/chargeguard.py"      "$STAGE/usr/bin/charge-guard"
install -D -m 0755 "$HERE/charge-guard-helper" "$STAGE/usr/libexec/charge-guard-helper"
install -D -m 0644 "$HERE/io.github.chargeguard.policy" \
  "$STAGE/usr/share/polkit-1/actions/io.github.chargeguard.policy"
install -D -m 0644 "$HERE/io.github.chargeguard.desktop" \
  "$STAGE/usr/share/applications/io.github.chargeguard.desktop"
install -D -m 0644 "$HERE/io.github.chargeguard.svg" \
  "$STAGE/usr/share/icons/hicolor/scalable/apps/io.github.chargeguard.svg"
install -D -m 0644 "$HERE/README.md" \
  "$STAGE/usr/share/doc/charge-guard/README.md"
install -D -m 0644 "$HERE/COMPATIBILITY.md" \
  "$STAGE/usr/share/doc/charge-guard/COMPATIBILITY.md"

SIZE=$(du -ks "$STAGE" | cut -f1)

mkdir -p "$STAGE/DEBIAN"
cat > "$STAGE/DEBIAN/control" <<CONTROL
Package: charge-guard
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-4.0, gir1.2-adw-1, pkexec
Installed-Size: $SIZE
Maintainer: Mohammad Hadi Arvin <mammad.arvin@gmail.com>
Description: Battery charge control for Lenovo IdeaPad laptops
 Charge Guard stops the battery charge, so the laptop runs from the
 adapter. It writes the ideapad_laptop conservation mode through a
 polkit helper, the same switch Lenovo Vantage uses on Windows.
 .
 The charge then stops near 60 percent, which lowers the wear on the
 cells. The battery is never force-discharged.
CONTROL

cat > "$STAGE/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
if [ "$1" = configure ]; then
  update-desktop-database /usr/share/applications 2>/dev/null || true
  gtk-update-icon-cache -qtf /usr/share/icons/hicolor 2>/dev/null || true
fi
POSTINST

cat > "$STAGE/DEBIAN/postrm" <<'POSTRM'
#!/bin/sh
set -e
if [ "$1" = remove ] || [ "$1" = purge ]; then
  update-desktop-database /usr/share/applications 2>/dev/null || true
  gtk-update-icon-cache -qtf /usr/share/icons/hicolor 2>/dev/null || true
fi
POSTRM

chmod 0755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/postrm"

mkdir -p "$HERE/dist"
OUT="$HERE/dist/charge-guard_${VERSION}_all.deb"
dpkg-deb --root-owner-group --build "$STAGE" "$OUT" >/dev/null
echo "$OUT"
