# Compatibility

Charge Guard has no model name in its code. Every path is resolved with a
glob at run time, so the app adapts to whatever the kernel exposes.

| What the code looks for | Pattern |
| --- | --- |
| Battery | `/sys/class/power_supply/BAT*` |
| Adapter | `/sys/class/power_supply/AC*`, then `AD*` |
| Charge switch | `/sys/bus/platform/drivers/ideapad_acpi/*/conservation_mode` |

## The one requirement

The laptop must expose `conservation_mode` through the in-tree
`ideapad_laptop` kernel driver. Check it with one command:

    ls /sys/bus/platform/drivers/ideapad_acpi/*/conservation_mode

A path means the app works. "No such file" means the switch will not work;
see [Other laptops](#other-laptops) below.

The driver binds to the ACPI device `VPC2004`. To see whether your machine
has it:

    ls /sys/bus/platform/drivers/ideapad_acpi/
    lsmod | grep ideapad

## Supported hardware

Most Lenovo **IdeaPad**, **Yoga** and **Legion** laptops carry `VPC2004` and
therefore support conservation mode. Lenovo calls the same feature
"Conservation Mode" in Vantage on Windows, and "Long Life" in the kernel's
`charge_types` attribute.

The embedded controller fixes the limit near 55-60 percent. No software can
move it, and the app does not try.

## Verified hardware

| Item | Value |
| --- | --- |
| Model | Lenovo IdeaPad Slim 3 15IRH8, type 83EM |
| BIOS | LTCN31WW |
| ACPI device | `VPC2004:00` |
| Battery | BYD L22B3PF2, 47 Wh |
| Adapter | 65 W |
| OS | Ubuntu 24.04.5 LTS |
| Kernel | 7.0.0-38-generic |

## Software requirements

| Component | Minimum | Why |
| --- | --- | --- |
| Linux kernel | 4.14 | `conservation_mode` first appeared here |
| Python | 3.8 | f-strings and `glob` only |
| GTK | 4.0 | the toolkit |
| libadwaita | 1.4 | `Adw.SwitchRow` |
| polkit | any | `pkexec` runs the helper |

Tested with Python 3.12.3, GTK 4.14.5 and libadwaita 1.5.0.

The Debian package declares these as `python3`, `python3-gi`,
`gir1.2-gtk-4.0`, `gir1.2-adw-1` and `pkexec`.

## Other laptops

The app still opens and reads the battery correctly. The gauge, the
percentage, the health and the cycle count all work. Only the switch fails:
it reports "This laptop has no conservation mode."

| Family | Interface it uses instead |
| --- | --- |
| Lenovo ThinkPad | `charge_control_start_threshold` and `charge_control_end_threshold` on the battery |
| Asus | `charge_control_end_threshold` |
| Dell, HP | vendor tools, or `charge_control_end_threshold` on newer kernels |

Those interfaces take a number, not a switch, so they can hold any level you
pick. Supporting them means reading and writing
`/sys/class/power_supply/BAT*/charge_control_end_threshold` as a fallback.
That work is not done, because an IdeaPad does not have that file.

## What the app never does

It writes one byte, `0` or `1`, to one file. It does not set charge voltage
or current, does not touch the embedded controller directly, and does not
read or change BIOS settings. The 60 percent limit belongs to the firmware.

The setting lives in the EC, so it survives a reboot and applies under
Windows too.
