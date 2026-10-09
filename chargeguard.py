#!/usr/bin/env python3
"""Charge Guard - minimal battery bypass control for Lenovo IdeaPad on Linux."""

import glob
import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

APP_ID = "io.github.chargeguard"
HELPER_PATHS = (
    "/usr/libexec/charge-guard-helper",
    "/usr/local/libexec/charge-guard-helper",
)
REFRESH_SECONDS = 5

PILL_WIDTH = 92
PILL_HEIGHT = 176
PILL_PAD = 5


def first(pattern):
    hits = sorted(glob.glob(pattern))
    return hits[0] if hits else None


BAT = first("/sys/class/power_supply/BAT*")
AC = first("/sys/class/power_supply/AC*") or first("/sys/class/power_supply/AD*")


def helper_path():
    for candidate in HELPER_PATHS:
        if os.path.exists(candidate):
            return candidate
    return None


def conservation_path():
    return first("/sys/bus/platform/drivers/ideapad_acpi/*/conservation_mode")


def read(path, default=""):
    if not path:
        return default
    try:
        with open(path) as handle:
            return handle.read().strip()
    except OSError:
        return default


def read_int(path, default=0):
    try:
        return int(read(path))
    except ValueError:
        return default


class Battery:
    """One snapshot of the power state."""

    def __init__(self):
        self.percent = read_int(f"{BAT}/capacity") if BAT else 0
        self.status = read(f"{BAT}/status", "Unknown") if BAT else "Unknown"
        self.plugged = read_int(f"{AC}/online") == 1 if AC else False
        self.cycles = read_int(f"{BAT}/cycle_count")
        self.watts = read_int(f"{BAT}/power_now") / 1_000_000
        self.bypass = read_int(conservation_path()) == 1

        full = read_int(f"{BAT}/energy_full")
        design = read_int(f"{BAT}/energy_full_design")
        self.health = round(full / design * 100) if design else 0

    @property
    def headline(self):
        if not self.plugged:
            return "On battery"
        if self.bypass:
            return "Adapter power - battery held"
        if self.status == "Full":
            return "Plugged in - full"
        if self.status == "Charging":
            return "Plugged in - charging"
        return "Plugged in - not charging"

    @property
    def detail(self):
        if self.watts > 0.1:
            unit = "out" if self.status == "Discharging" else "in"
            return f"{self.watts:.1f} W {unit}"
        return "No current flow"

    @property
    def tone(self):
        if self.plugged and self.bypass:
            return "bypass"
        if self.percent < 15:
            return "critical"
        if self.percent < 30:
            return "low"
        if self.percent < 45:
            return "warn"
        return "normal"


CSS = b"""
.pill {
  border-radius: 26px;
  border: 2px solid alpha(currentColor, 0.18);
  background: alpha(currentColor, 0.06);
}
.pill-cap { border-radius: 4px; background: alpha(currentColor, 0.22); }
.fill { border-radius: 21px; background: #2fc16d; }
.fill.bypass   { background: #3685e2; }
.fill.warn     { background: #ef9a1f; }
.fill.low      { background: #e2695c; }
.fill.critical { background: #e01b0c; }
.percent  { font-size: 40px; font-weight: 200; letter-spacing: -1px; }
.unit     { font-size: 15px; font-weight: 300; opacity: 0.45; }
.headline { font-size: 14px; font-weight: 700; }
.detail   { font-size: 12px; opacity: 0.55; }
.hint     { font-size: 11px; opacity: 0.5; }
"""


class Window(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Charge Guard")
        self.set_default_size(400, 650)
        self.set_resizable(False)

        self.state = Battery()
        self.muted = False
        self.busy = False

        header = Adw.HeaderBar(css_classes=["flat"])
        header.set_title_widget(Adw.WindowTitle(title="Charge Guard"))

        page = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=18,
            margin_top=4,
            margin_bottom=22,
            margin_start=20,
            margin_end=20,
        )
        page.append(self._build_gauge())
        page.append(self._build_readout())
        page.append(self._build_switch())
        page.append(self._build_facts())
        page.append(self._build_hint())

        view = Adw.ToolbarView()
        view.add_top_bar(header)
        view.set_content(page)

        self.toasts = Adw.ToastOverlay(child=view)
        self.set_content(self.toasts)

        self.refresh()
        GLib.timeout_add_seconds(REFRESH_SECONDS, self._tick)

    # UI pieces -----------------------------------------------------------

    def _build_gauge(self):
        cap = Gtk.Box(css_classes=["pill-cap"], halign=Gtk.Align.CENTER)
        cap.set_size_request(30, 7)

        # The fill is an overlay child aligned to the bottom. An expanding
        # spacer would grow the whole column, so the pill must not hold one.
        self.fill = Gtk.Box(
            css_classes=["fill"],
            valign=Gtk.Align.END,
            halign=Gtk.Align.FILL,
            margin_start=PILL_PAD,
            margin_end=PILL_PAD,
            margin_bottom=PILL_PAD,
        )
        self.fill.set_size_request(-1, 12)

        shell = Gtk.Box(css_classes=["pill"])
        shell.set_size_request(PILL_WIDTH, PILL_HEIGHT)

        gauge = Gtk.Overlay(child=shell, halign=Gtk.Align.CENTER)
        gauge.add_overlay(self.fill)

        column = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        column.set_halign(Gtk.Align.CENTER)
        column.set_margin_top(10)
        column.append(cap)
        column.append(gauge)
        return column

    def _build_readout(self):
        number = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        number.set_halign(Gtk.Align.CENTER)
        self.percent_label = Gtk.Label(css_classes=["percent"])
        number.append(self.percent_label)
        number.append(Gtk.Label(label="%", css_classes=["unit"], valign=Gtk.Align.CENTER))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_halign(Gtk.Align.CENTER)
        self.headline = Gtk.Label(css_classes=["headline"])
        self.detail = Gtk.Label(css_classes=["detail"])
        box.append(number)
        box.append(self.headline)
        box.append(self.detail)
        return box

    def _build_switch(self):
        self.switch = Adw.SwitchRow(
            title="Bypass battery",
            subtitle="Run from the adapter. Stop charging.",
        )
        self.switch.connect("notify::active", self._on_toggle)
        group = Adw.PreferencesGroup()
        group.add(self.switch)
        return group

    def _build_facts(self):
        self.mode_value = Gtk.Label(css_classes=["dim-label"])
        self.health_value = Gtk.Label(css_classes=["dim-label"])
        self.cycles_value = Gtk.Label(css_classes=["dim-label"])

        group = Adw.PreferencesGroup()
        for title, widget in (
            ("Charge mode", self.mode_value),
            ("Battery health", self.health_value),
            ("Charge cycles", self.cycles_value),
        ):
            row = Adw.ActionRow(title=title)
            row.add_suffix(widget)
            group.add(row)
        return group

    def _build_hint(self):
        return Gtk.Label(
            css_classes=["hint"],
            wrap=True,
            justify=Gtk.Justification.CENTER,
            label="Bypass stops the charge near 60 percent. The battery does not "
            "discharge while the adapter stays in.",
        )

    # State ---------------------------------------------------------------

    def _tick(self):
        self.refresh()
        return GLib.SOURCE_CONTINUE

    def refresh(self):
        self.state = Battery()

        inner = PILL_HEIGHT - 2 * PILL_PAD - 4  # minus padding and border
        self.fill.set_size_request(-1, max(12, round(inner * self.state.percent / 100)))
        for tone in ("bypass", "warn", "low", "critical"):
            self.fill.remove_css_class(tone)
        if self.state.tone != "normal":
            self.fill.add_css_class(self.state.tone)

        self.percent_label.set_label(str(self.state.percent))
        self.headline.set_label(self.state.headline)
        self.detail.set_label(self.state.detail)
        self.mode_value.set_label("Long life" if self.state.bypass else "Standard")
        self.health_value.set_label(f"{self.state.health}%")
        self.cycles_value.set_label(str(self.state.cycles) if self.state.cycles else "-")

        # Guard: without an adapter the mode cannot do anything, so it
        # cannot be switched on. Switching it off stays open, so a full
        # charge can be prepared before the cable goes in.
        self.switch.set_sensitive(self.state.plugged or self.state.bypass)
        if self.state.plugged:
            self.switch.set_subtitle("Run from the adapter. Stop charging.")
        elif self.state.bypass:
            self.switch.set_subtitle("Turn off for a full charge next time.")
        else:
            self.switch.set_subtitle("Plug in the adapter first.")

        if not self.busy:
            self.muted = True
            self.switch.set_active(self.state.bypass)
            self.muted = False

    # Actions -------------------------------------------------------------

    def _on_toggle(self, row, _param):
        if self.muted or self.busy:
            return
        self._apply(1 if row.get_active() else 0)

    def _apply(self, value):
        path = conservation_path()
        if not path:
            self._fail("This laptop has no conservation mode.")
            return

        if os.access(path, os.W_OK):
            try:
                with open(path, "w") as handle:
                    handle.write(str(value))
                self.refresh()
                return
            except OSError:
                pass

        helper = helper_path()
        if helper:
            argv, stdin = ["pkexec", helper, "on" if value else "off"], None
        else:
            # Used before install.sh runs. No shell is spawned as root:
            # pkexec runs tee, and the value arrives on stdin.
            argv, stdin = ["pkexec", "/usr/bin/tee", path], str(value)

        self.busy = True
        try:
            proc = Gio.Subprocess.new(
                argv,
                Gio.SubprocessFlags.STDIN_PIPE
                | Gio.SubprocessFlags.STDOUT_SILENCE
                | Gio.SubprocessFlags.STDERR_SILENCE,
            )
        except GLib.Error as error:
            self.busy = False
            self._fail(error.message)
            return
        proc.communicate_utf8_async(stdin, None, self._on_done)

    def _on_done(self, proc, result):
        self.busy = False
        try:
            proc.communicate_utf8_finish(result)
            changed = proc.get_successful()
        except GLib.Error:
            changed = False
        if not changed:
            self._fail("The setting did not change.")
        self.refresh()

    def _fail(self, message):
        self.toasts.add_toast(Adw.Toast(title=message, timeout=4))
        self.muted = True
        self.switch.set_active(self.state.bypass)
        self.muted = False


class App(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)

    def do_startup(self):
        Adw.Application.do_startup(self)
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def do_activate(self):
        window = self.get_active_window() or Window(self)
        window.present()


if __name__ == "__main__":
    if not BAT:
        print("No battery found.", file=sys.stderr)
        sys.exit(1)
    sys.exit(App().run(sys.argv))
