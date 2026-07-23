#!/usr/bin/env python3
"""Ajustar posição da bandeirinha do The Dude.

Setas / botões movem ao vivo e salvam em ~/.config/dude-flag/position.conf
O dude-dock-tray.py usa essa posição automaticamente.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk

CONFIG_DIR = Path.home() / ".config" / "dude-flag"
CONFIG = CONFIG_DIR / "position.conf"
STEP = 2
STEP_FAST = 8


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, text=True, capture_output=True).stdout


def find_flag_wid() -> str | None:
    out = run(["xwininfo", "-root", "-tree"])
    fallback = None
    for line in out.splitlines():
        if "explorer.exe" not in line:
            continue
        m_id = re.search(r"(0x[0-9a-fA-F]+)", line)
        m_sz = re.search(r"\b(\d+)x(\d+)\b", line)
        if not m_id or not m_sz:
            continue
        w, h = int(m_sz.group(1)), int(m_sz.group(2))
        if not (12 <= w <= 80 and 12 <= h <= 80):
            continue
        wid = m_id.group(1)
        info = run(["xwininfo", "-id", wid])
        if "IsViewable" in info:
            return wid
        fallback = wid
    return fallback


def geom(wid: str) -> tuple[int, int, int, int] | None:
    info = run(["xwininfo", "-id", wid])
    if "xwininfo:" not in info:
        return None
    ax = ay = w = h = None
    for line in info.splitlines():
        if "Absolute upper-left X:" in line:
            ax = int(line.split()[-1])
        elif "Absolute upper-left Y:" in line:
            ay = int(line.split()[-1])
        elif line.strip().startswith("Width:"):
            w = int(line.split()[-1])
        elif line.strip().startswith("Height:"):
            h = int(line.split()[-1])
    if None in (ax, ay, w, h):
        return None
    return ax, ay, w, h


def move_flag(wid: str, x: int, y: int) -> None:
    subprocess.run(["xdotool", "windowmove", wid, str(x), str(y)], capture_output=True)


def load_config() -> tuple[int, int] | None:
    if not CONFIG.exists():
        return None
    x = y = None
    for line in CONFIG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("x="):
            x = int(line.split("=", 1)[1])
        elif line.startswith("y="):
            y = int(line.split("=", 1)[1])
    if x is None or y is None:
        return None
    return x, y


def save_config(x: int, y: int) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(f"x={x}\ny={y}\n", encoding="utf-8")


class Adjuster(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="Ajustar bandeira — The Dude")
        self.set_border_width(14)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.connect("destroy", Gtk.main_quit)
        self.connect("key-press-event", self.on_key)

        self.wid = find_flag_wid()
        g = geom(self.wid) if self.wid else None
        saved = load_config()
        if g:
            self.x, self.y = g[0], g[1]
        elif saved:
            self.x, self.y = saved
        else:
            self.x, self.y = 3669, 1120

        self._updating = False

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        self.status = Gtk.Label()
        self.status.set_line_wrap(True)
        vbox.pack_start(self.status, False, False, 0)

        grid = Gtk.Grid(column_spacing=6, row_spacing=6, halign=Gtk.Align.CENTER)
        vbox.pack_start(grid, False, False, 0)

        def mk(label: str, dx: int, dy: int) -> Gtk.Button:
            b = Gtk.Button(label=label)
            b.set_size_request(48, 36)
            b.connect("clicked", lambda *_: self.nudge(dx, dy))
            return b

        grid.attach(mk("↑", 0, -STEP), 1, 0, 1, 1)
        grid.attach(mk("←", -STEP, 0), 0, 1, 1, 1)
        grid.attach(mk("→", STEP, 0), 2, 1, 1, 1)
        grid.attach(mk("↓", 0, STEP), 1, 2, 1, 1)

        xy = Gtk.Box(spacing=8)
        vbox.pack_start(xy, False, False, 0)
        xy.pack_start(Gtk.Label(label="X"), False, False, 0)
        self.spin_x = Gtk.SpinButton.new_with_range(-2000, 8000, 1)
        self.spin_x.set_value(self.x)
        self.spin_x.connect("value-changed", self.on_spin)
        xy.pack_start(self.spin_x, True, True, 0)
        xy.pack_start(Gtk.Label(label="Y"), False, False, 0)
        self.spin_y = Gtk.SpinButton.new_with_range(-2000, 8000, 1)
        self.spin_y.set_value(self.y)
        self.spin_y.connect("value-changed", self.on_spin)
        xy.pack_start(self.spin_y, True, True, 0)

        hint = Gtk.Label()
        hint.set_markup(
            "<small>Teclado: setas = 2px · Shift+setas = 8px\n"
            "Cada movimento já salva a posição.</small>"
        )
        hint.set_justify(Gtk.Justification.CENTER)
        vbox.pack_start(hint, False, False, 0)

        row = Gtk.Box(spacing=8)
        vbox.pack_start(row, False, False, 0)
        b_save = Gtk.Button(label="Salvar")
        b_save.get_style_context().add_class("suggested-action")
        b_save.connect("clicked", lambda *_: self.persist("Posição salva."))
        row.pack_start(b_save, True, True, 0)
        b_auto = Gtk.Button(label="Usar automático")
        b_auto.connect("clicked", self.on_clear)
        row.pack_start(b_auto, True, True, 0)
        b_find = Gtk.Button(label="Achar bandeira")
        b_find.connect("clicked", self.on_reload)
        row.pack_start(b_find, True, True, 0)

        self.refresh_status()
        if self.wid:
            move_flag(self.wid, self.x, self.y)
        GLib.timeout_add_seconds(2, self.poll_wid)

    def poll_wid(self) -> bool:
        if not self.wid or not geom(self.wid):
            self.wid = find_flag_wid()
            self.refresh_status()
        return True

    def refresh_status(self, extra: str = "") -> None:
        if self.wid:
            msg = f"Bandeira: <b>{self.wid}</b>\nPosição: <b>{self.x}, {self.y}</b>"
        else:
            msg = (
                "<span foreground='#c00'>Bandeira não encontrada.</span>\n"
                "Abra o The Dude e clique em “Achar bandeira”."
            )
        if extra:
            msg += f"\n{extra}"
        self.status.set_markup(msg)

    def persist(self, note: str = "") -> None:
        save_config(self.x, self.y)
        self.refresh_status(note or f"Salvo em {CONFIG}")

    def set_xy(self, x: int, y: int) -> None:
        self.x, self.y = int(x), int(y)
        self._updating = True
        self.spin_x.set_value(self.x)
        self.spin_y.set_value(self.y)
        self._updating = False
        if self.wid:
            move_flag(self.wid, self.x, self.y)
        self.persist()

    def nudge(self, dx: int, dy: int) -> None:
        self.set_xy(self.x + dx, self.y + dy)

    def on_spin(self, *_):
        if self._updating:
            return
        self.set_xy(int(self.spin_x.get_value()), int(self.spin_y.get_value()))

    def on_key(self, _w, event) -> bool:
        step = STEP_FAST if event.state & Gdk.ModifierType.SHIFT_MASK else STEP
        mapping = {
            Gdk.KEY_Up: (0, -step),
            Gdk.KEY_KP_Up: (0, -step),
            Gdk.KEY_Down: (0, step),
            Gdk.KEY_KP_Down: (0, step),
            Gdk.KEY_Left: (-step, 0),
            Gdk.KEY_KP_Left: (-step, 0),
            Gdk.KEY_Right: (step, 0),
            Gdk.KEY_KP_Right: (step, 0),
        }
        if event.keyval in mapping:
            dx, dy = mapping[event.keyval]
            self.nudge(dx, dy)
            return True
        return False

    def on_clear(self, *_):
        if CONFIG.exists():
            CONFIG.unlink()
        self.refresh_status("Automático: dock calcula a posição de novo.")

    def on_reload(self, *_):
        self.wid = find_flag_wid()
        g = geom(self.wid) if self.wid else None
        if g:
            self._updating = True
            self.x, self.y = g[0], g[1]
            self.spin_x.set_value(self.x)
            self.spin_y.set_value(self.y)
            self._updating = False
        self.refresh_status()


def main() -> int:
    win = Adjuster()
    win.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
