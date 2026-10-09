// Charge Guard - a top bar switch for the Lenovo IdeaPad conservation mode.
// It reads sysfs directly and writes through the packaged pkexec helper.

import GObject from 'gi://GObject';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import St from 'gi://St';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const DRIVER_DIR = '/sys/bus/platform/drivers/ideapad_acpi';
const POWER_DIR = '/sys/class/power_supply';
const HELPERS = [
    '/usr/libexec/charge-guard-helper',
    '/usr/local/libexec/charge-guard-helper',
];
const REFRESH_SECONDS = 5;

function listDir(path) {
    const names = [];
    try {
        const iter = Gio.File.new_for_path(path).enumerate_children(
            'standard::name', Gio.FileQueryInfoFlags.NONE, null);
        let info;
        while ((info = iter.next_file(null)) !== null)
            names.push(info.get_name());
        iter.close(null);
    } catch {
        // The directory is missing on laptops without the driver.
    }
    return names.sort();
}

function readText(path) {
    try {
        const [ok, bytes] = GLib.file_get_contents(path);
        return ok ? new TextDecoder().decode(bytes).trim() : null;
    } catch {
        return null;
    }
}

function readInt(path, fallback = 0) {
    const value = Number.parseInt(readText(path) ?? '', 10);
    return Number.isNaN(value) ? fallback : value;
}

function conservationPath() {
    for (const name of listDir(DRIVER_DIR)) {
        const path = `${DRIVER_DIR}/${name}/conservation_mode`;
        if (GLib.file_test(path, GLib.FileTest.EXISTS))
            return path;
    }
    return null;
}

function supplyPath(...prefixes) {
    for (const prefix of prefixes) {
        for (const name of listDir(POWER_DIR)) {
            if (name.startsWith(prefix))
                return `${POWER_DIR}/${name}`;
        }
    }
    return null;
}

function helperPath() {
    return HELPERS.find(path => GLib.file_test(path, GLib.FileTest.IS_EXECUTABLE)) ?? null;
}

const Indicator = GObject.registerClass(
class Indicator extends PanelMenu.Button {
    _init(extension) {
        super._init(0.5, 'Charge Guard');

        this._busy = false;
        this._timer = 0;

        this._icon = new St.Icon({
            gicon: Gio.icon_new_for_string(
                `${extension.path}/icons/io.github.chargeguard-symbolic.svg`),
            style_class: 'system-status-icon',
        });
        this.add_child(this._icon);

        this._toggle = new PopupMenu.PopupSwitchMenuItem('Bypass battery', false);
        this._toggle.connect('toggled', (item, state) => this._apply(state));
        this.menu.addMenuItem(this._toggle);

        this._reading = new PopupMenu.PopupMenuItem('', {reactive: false});
        this.menu.addMenuItem(this._reading);

        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());

        const open = new PopupMenu.PopupMenuItem('Open Charge Guard');
        open.connect('activate', () => this._launch());
        this.menu.addMenuItem(open);

        this.menu.connect('open-state-changed', (menu, isOpen) => {
            if (isOpen)
                this._refresh();
        });

        this._refresh();
        this._timer = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT, REFRESH_SECONDS, () => {
                this._refresh();
                return GLib.SOURCE_CONTINUE;
            });
    }

    _refresh() {
        const switchPath = conservationPath();
        const battery = supplyPath('BAT');
        const adapter = supplyPath('AC', 'AD');

        const bypass = switchPath ? readInt(switchPath) === 1 : false;
        const plugged = adapter ? readInt(`${adapter}/online`) === 1 : false;
        const percent = battery ? readInt(`${battery}/capacity`) : 0;
        const status = battery ? readText(`${battery}/status`) ?? 'Unknown' : 'Unknown';

        // setToggleState does not emit 'toggled', so this cannot loop.
        this._toggle.setToggleState(bypass);

        // Same guard as the app: without an adapter the mode has nothing
        // to do, so it cannot be switched on. Switching off stays open.
        this._toggle.setSensitive(!!switchPath && !this._busy && (plugged || bypass));

        if (!switchPath)
            this._reading.label.text = 'No conservation mode on this laptop';
        else
            this._reading.label.text = `${percent}%  ·  ${status}`;

        if (bypass)
            this._icon.add_style_class_name('charge-guard-active');
        else
            this._icon.remove_style_class_name('charge-guard-active');
    }

    _apply(state) {
        const helper = helperPath();
        if (!helper) {
            Main.notify('Charge Guard',
                'The helper is missing. Install the package first.');
            this._refresh();
            return;
        }

        this._busy = true;
        let proc;
        try {
            proc = Gio.Subprocess.new(
                ['pkexec', helper, state ? 'on' : 'off'],
                Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_SILENCE);
        } catch {
            this._busy = false;
            Main.notify('Charge Guard', 'pkexec could not start.');
            this._refresh();
            return;
        }

        proc.wait_check_async(null, (source, result) => {
            this._busy = false;
            try {
                source.wait_check_finish(result);
            } catch {
                Main.notify('Charge Guard', 'The setting did not change.');
            }
            this._refresh();
        });
    }

    _launch() {
        const app = Gio.DesktopAppInfo.new('io.github.chargeguard.desktop');
        if (!app) {
            Main.notify('Charge Guard', 'The app is not installed.');
            return;
        }
        app.launch([], null);
    }

    destroy() {
        if (this._timer) {
            GLib.Source.remove(this._timer);
            this._timer = 0;
        }
        super.destroy();
    }
});

export default class ChargeGuardExtension extends Extension {
    enable() {
        this._indicator = new Indicator(this);
        Main.panel.addToStatusArea(this.uuid, this._indicator);
    }

    disable() {
        this._indicator?.destroy();
        this._indicator = null;
    }
}
