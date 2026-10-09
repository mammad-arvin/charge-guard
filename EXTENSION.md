# Top bar extension

The package installs a GNOME Shell extension next to the app. It puts the
same switch in the top bar, so you never have to open the window.

Installing it is not enough to see it. GNOME enables an extension **per
user**, and a new extension is only loaded at login. Two steps, once.

## Step 1 - enable it

    gnome-extensions enable charge-guard@io.github.chargeguard

If that answers `doesn't exist`, the shell has not read the new folder yet.
That is normal right after an install. Do step 2 first, then run the command
again.

The Extension Manager app works too. Look for **Charge Guard** in the list
and turn it on.

## Step 2 - log out and back in

Log out of your session and log in again.

On Wayland there is no other way: the shell cannot load a new extension
while the session runs, and restarting the shell would close your windows.
On Xorg you may press `Alt+F2`, type `r`, and press Enter instead.

## What you get

A small battery icon appears in the top bar. Click it:

| Item | What it does |
| --- | --- |
| **Bypass battery** | the switch. polkit asks for your password or fingerprint |
| `83% · Not charging` | the live reading, every 5 seconds |
| **Open Charge Guard** | opens the full window |

The icon turns green while the mode is on.

Without an adapter the switch is locked off, the same guard the app uses.

## Check that it loaded

    gnome-extensions info charge-guard@io.github.chargeguard

`State: ACTIVE` means it runs. If something went wrong:

    journalctl --user -b -u gnome-shell | grep -i charge

## Requirements

GNOME Shell 45 or newer. The extension uses ESM imports, which older shells
cannot read. Check yours with `gnome-shell --version`.

It also needs `/usr/libexec/charge-guard-helper`, which the package installs.
Without it the switch reports that the helper is missing.

## Two copies

A per-user copy in `~/.local/share/gnome-shell/extensions/` wins over the
one in `/usr/share/gnome-shell/extensions/`. If you installed it by hand
before, remove the old copy so the package version is the one that runs:

    rm -rf ~/.local/share/gnome-shell/extensions/charge-guard@io.github.chargeguard

## Turn it off

    gnome-extensions disable charge-guard@io.github.chargeguard

The charge mode itself does not change. It lives in the EC, not in the
extension.
