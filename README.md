# Charge Guard

A small GTK4 app for Ubuntu. It stops the battery charge, so the laptop runs
from the adapter.

Written for a Lenovo IdeaPad Slim 3 15IRH8 on Ubuntu 24.04, kernel 7.0. It
works on any IdeaPad whose kernel driver shows `conservation_mode`. See
[COMPATIBILITY.md](COMPATIBILITY.md) for the models, the one-line check, and
what happens on other laptops.

## What the hardware allows

The embedded controller of an IdeaPad gives one control only:
`conservation_mode`, which Lenovo calls "Long Life".

| Goal | Possible |
| --- | --- |
| Run from the battery while the cable stays in | No. IdeaPads have no force-discharge. |
| Stop the charge and run from the adapter | Yes. This app does it. |

With the mode on, the charge stops near 60 percent and the laptop takes its
power from the adapter. A battery above that level is held, never drained.

## Install

    sudo dpkg -i dist/charge-guard_1.1.0_all.deb

Or from this directory, without a package:

    sudo ./install.sh

Both put the same files in the same places:

| Path | What |
| --- | --- |
| `/usr/bin/charge-guard` | the app (`/usr/local/bin` with `install.sh`) |
| `/usr/libexec/charge-guard-helper` | root helper, 17 lines |
| `/usr/share/polkit-1/actions/io.github.chargeguard.policy` | the authentication rule |
| `/usr/share/applications/io.github.chargeguard.desktop` | menu entry |
| `/usr/share/icons/hicolor/scalable/apps/io.github.chargeguard.svg` | icon |
| `/usr/share/gnome-shell/extensions/charge-guard@io.github.chargeguard/` | top bar extension |

Remove it with `sudo apt remove charge-guard`, or `sudo ./uninstall.sh`.

## Top bar extension

The install puts a GNOME Shell extension in place as well. It carries the
same switch in the top bar, and its icon turns green while the mode is on.

GNOME enables an extension per user and loads a new one only at login, so
two short steps are left to you. [EXTENSION.md](EXTENSION.md) has them.

To install it for one user only, without sudo, use
`./gnome-extension/install.sh` instead.

## Authentication

Every change asks for authentication (`auth_admin`). A fingerprint works,
because polkit reads `common-auth` and `pam_fprintd` sits at the top of it.

To stop the prompt, set `allow_active` to `yes` in the policy file.

## Guard

Without the adapter the switch is locked off: the mode would have nothing to
do. Switching it off stays open, so a full charge can be prepared before the
cable goes in.

## Safety

The app writes one byte, `0` or `1`, to one sysfs file. The kernel parses it
with `kstrtobool()` and calls the ACPI method `SBMC` with 3 (on) or 5 (off).
The embedded controller does the rest. No charge voltage, charge current, or
hardware register is touched by this path, and the 60 percent limit belongs to
the firmware, not to software.

The setting lives in the EC. It survives a reboot and applies under Windows
too. Turn it off before a trip, so the battery charges in full.

## Run without installing

    ./chargeguard.py

## Command line

    pkexec /usr/libexec/charge-guard-helper on
    pkexec /usr/libexec/charge-guard-helper off

## Build the package

    ./packaging/build-deb.sh
