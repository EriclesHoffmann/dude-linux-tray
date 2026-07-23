#!/usr/bin/env python3
"""Dock MikroTik The Dude Wine tray flag onto the GNOME panel.

Keeps the real NotifyIcon (~16x16) with an XShape mask (white = transparent),
outside the task list. Position from ~/.config/dude-flag/position.conf or a
panel fallback. Avoids remapping every tick (prevents flicker).
"""
from __future__ import annotations

import os
import re
import subprocess
import time

from PIL import Image, ImageFilter
from Xlib import X, Xatom, Xutil, display
from Xlib.ext import shape
from Xlib.protocol import event

SIZE = 16
MARGIN = 6
PANEL = 48  # Dash to Panel no monitor principal
CLOCK_WIDTH = 165
ICONS_TO_THE_RIGHT = 5
ICON_SLOT = 32
NUDGE_LEFT = 18
GAP = 4
LOCK = "/tmp/dude-dock-tray.lock"
TOL = 2
POLL = 2.5
CONFIG = os.path.expanduser("~/.config/dude-flag/position.conf")


def run(cmd: list[str]) -> str:
    return subprocess.run(cmd, text=True, capture_output=True).stdout


def primary_geom() -> tuple[int, int, int, int]:
    out = run(["xrandr", "--listmonitors"])
    for line in out.splitlines():
        if "+*" in line:
            m = re.search(r"(\d+)/\d+x(\d+)/\d+\+(\d+)\+(\d+)", line)
            if m:
                return int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
    return 1920, 1080, 0, 0


def load_saved_pos() -> tuple[int, int] | None:
    if not os.path.isfile(CONFIG):
        return None
    try:
        x = y = None
        with open(CONFIG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("x="):
                    x = int(line.split("=", 1)[1])
                elif line.startswith("y="):
                    y = int(line.split("=", 1)[1])
        if x is None or y is None:
            return None
        return x, y
    except Exception:
        return None


def corner_pos() -> tuple[int, int]:
    """Posição salva pelo ajustador, ou cálculo automático."""
    saved = load_saved_pos()
    if saved:
        return saved
    mw, mh, mx, my = primary_geom()
    x = mx + mw - CLOCK_WIDTH - ICONS_TO_THE_RIGHT * ICON_SLOT - GAP - SIZE - NUDGE_LEFT
    y = my + mh - PANEL + max(0, (PANEL - SIZE) // 2)
    return x, y


def find_tray_windows() -> list[tuple[str, int, int, int, int]]:
    out = run(["xwininfo", "-root", "-tree"])
    found: list[tuple[str, int, int, int, int]] = []
    seen: set[str] = set()
    for line in out.splitlines():
        if "explorer.exe" not in line:
            continue
        m_id = re.search(r"(0x[0-9a-fA-F]+)", line)
        m_sz = re.search(r"\b(\d+)x(\d+)\b", line)
        positions = re.findall(r"\+(\-?\d+)\+(\-?\d+)", line)
        if not m_id or not m_sz or not positions:
            continue
        wid = m_id.group(1)
        if wid in seen:
            continue
        w, h = int(m_sz.group(1)), int(m_sz.group(2))
        if w <= 2 or h <= 2:
            continue
        is_strip = 40 <= w <= 400 and 12 <= h <= 48
        is_icon = 12 <= w <= 80 and 12 <= h <= 80
        if not (is_strip or is_icon):
            continue
        ax, ay = int(positions[-1][0]), int(positions[-1][1])
        seen.add(wid)
        found.append((wid, w, h, ax, ay))
    return found


def window_alive(wid: str) -> bool:
    r = subprocess.run(["xwininfo", "-id", wid], capture_output=True, text=True)
    return r.returncode == 0 and "xwininfo:" in r.stdout


def geom_of(wid: str) -> tuple[int, int, int, int, bool] | None:
    info = run(["xwininfo", "-id", wid])
    if "xwininfo:" not in info:
        return None
    w = h = ax = ay = None
    mapped = "IsViewable" in info
    for line in info.splitlines():
        if "Absolute upper-left X:" in line:
            ax = int(line.split()[-1])
        elif "Absolute upper-left Y:" in line:
            ay = int(line.split()[-1])
        elif line.strip().startswith("Width:"):
            w = int(line.split()[-1])
        elif line.strip().startswith("Height:"):
            h = int(line.split()[-1])
    if None in (w, h, ax, ay):
        return None
    return w, h, ax, ay, mapped


def _atom(d: display.Display, name: str):
    return d.intern_atom(name)


def set_net_wm_state(d: display.Display, w, add: list[str], remove: list[str]) -> None:
    root = d.screen().root
    net_state = _atom(d, "_NET_WM_STATE")
    for name in add:
        ev = event.ClientMessage(
            window=w,
            client_type=net_state,
            data=(32, [1, _atom(d, name), 0, 0, 0]),
        )
        root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)
    for name in remove:
        ev = event.ClientMessage(
            window=w,
            client_type=net_state,
            data=(32, [0, _atom(d, name), 0, 0, 0]),
        )
        root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask)


def apply_flag_shape(wid: str) -> None:
    """Máscara: pixels brancos ficam transparentes — só a bandeira aparece."""
    d = display.Display()
    w = d.create_resource_object("window", int(wid, 16))
    geo = w.get_geometry()
    if geo.width < 8 or geo.height < 8:
        d.close()
        return
    try:
        img = w.get_image(0, 0, geo.width, geo.height, X.ZPixmap, 0xFFFFFFFF)
    except Exception:
        d.close()
        return
    im = Image.frombytes("RGBA", (geo.width, geo.height), bytes(img.data), "raw", "BGRA")
    mask = Image.new("1", (geo.width, geo.height), 0)
    pix = mask.load()
    content = 0
    for yy in range(geo.height):
        for xx in range(geo.width):
            r, g, b, a = im.getpixel((xx, yy))
            if a < 200:
                continue
            if r > 245 and g > 245 and b > 245:
                continue
            pix[xx, yy] = 1
            content += 1
    if content < 4:
        d.close()
        return
    mask = (
        mask.convert("L")
        .filter(ImageFilter.MaxFilter(3))
        .point(lambda v: 255 if v > 0 else 0)
        .convert("1")
    )
    rects: list[tuple[int, int, int, int]] = []
    for yy in range(geo.height):
        xx = 0
        while xx < geo.width:
            if mask.getpixel((xx, yy)) == 0:
                xx += 1
                continue
            x0 = xx
            while xx < geo.width and mask.getpixel((xx, yy)) != 0:
                xx += 1
            rects.append((x0, yy, xx - x0, 1))
    if not rects:
        d.close()
        return
    try:
        w.shape_rectangles(shape.SO.Set, shape.SK.Bounding, X.YXBanded, 0, 0, rects)
        w.shape_rectangles(shape.SO.Set, shape.SK.Clip, X.YXBanded, 0, 0, rects)
        d.sync()
    except Exception:
        pass
    d.close()


def force_size_hints(w) -> None:
    w.set_wm_normal_hints(
        flags=Xutil.PMinSize | Xutil.PMaxSize | Xutil.PSize | Xutil.PBaseSize,
        min_width=SIZE,
        min_height=SIZE,
        max_width=SIZE,
        max_height=SIZE,
        width=SIZE,
        height=SIZE,
        base_width=SIZE,
        base_height=SIZE,
    )


def apply_stealth_once(wid: str) -> None:
    d = display.Display()
    w = d.create_resource_object("window", int(wid, 16))
    attrs = w.get_attributes()

    if not attrs.override_redirect:
        w.unmap()
        d.sync()
        time.sleep(0.05)
        w.change_attributes(override_redirect=1)
        d.sync()
        w.map()
        d.sync()

    try:
        w.set_wm_name(" ")
        w.set_wm_icon_name(" ")
    except Exception:
        pass

    motif = _atom(d, "_MOTIF_WM_HINTS")
    w.change_property(motif, motif, 32, [2, 0, 0, 0, 0])
    w.change_property(
        _atom(d, "_NET_WM_WINDOW_TYPE"),
        Xatom.ATOM,
        32,
        [_atom(d, "_NET_WM_WINDOW_TYPE_DOCK")],
    )
    set_net_wm_state(
        d,
        w,
        add=[
            "_NET_WM_STATE_SKIP_TASKBAR",
            "_NET_WM_STATE_SKIP_PAGER",
            "_NET_WM_STATE_ABOVE",
            "_NET_WM_STATE_STICKY",
        ],
        remove=["_NET_WM_STATE_DEMANDS_ATTENTION", "_NET_WM_STATE_HIDDEN"],
    )
    force_size_hints(w)
    x, y = corner_pos()
    w.configure(x=x, y=y, width=SIZE, height=SIZE)
    d.sync()
    d.close()
    time.sleep(0.15)
    apply_flag_shape(wid)


def nudge_if_needed(wid: str) -> bool:
    """Retorna True se mexeu (aí reaplicamos a máscara)."""
    g = geom_of(wid)
    if not g:
        return False
    w, h, ax, ay, mapped = g
    x, y = corner_pos()
    changed = False
    d = display.Display()
    win = d.create_resource_object("window", int(wid, 16))
    force_size_hints(win)

    if abs(w - SIZE) > TOL or abs(h - SIZE) > TOL or abs(ax - x) > TOL or abs(ay - y) > TOL:
        win.configure(x=x, y=y, width=SIZE, height=SIZE)
        changed = True

    if not mapped:
        win.map()
        changed = True

    attrs = win.get_attributes()
    if not attrs.override_redirect:
        win.unmap()
        d.sync()
        win.change_attributes(override_redirect=1)
        d.sync()
        win.map()
        changed = True

    if changed:
        d.sync()
    d.close()
    if changed:
        time.sleep(0.1)
        apply_flag_shape(wid)
    return changed


def hide(wid: str) -> None:
    subprocess.run(["xdotool", "windowunmap", wid], capture_output=True)


def hide_tooltips() -> None:
    out = run(["xwininfo", "-root", "-tree"])
    for line in out.splitlines():
        if "onfibra@" not in line.lower():
            continue
        if "dude.exe" in line or "mutter-x11-frames" in line:
            continue
        m_id = re.search(r"(0x[0-9a-fA-F]+)", line)
        m_sz = re.search(r"\b(\d+)x(\d+)\b", line)
        if not m_id or not m_sz:
            continue
        w, h = int(m_sz.group(1)), int(m_sz.group(2))
        if h <= 40 and w <= 600:
            hide(m_id.group(1))


def pick_initial(cands: list[tuple[str, int, int, int, int]]) -> tuple[str, int, int, int, int]:
    strips = [c for c in cands if c[1] >= 40]
    if strips:
        return max(strips, key=lambda t: t[1] * t[2])
    return max(cands, key=lambda t: t[1] * t[2])


def dude_alive() -> bool:
    out = run(["ps", "-u", str(os.getuid()), "-o", "args="])
    return any(a.startswith(r"C:\Program Files\Dude\dude.exe") for a in out.splitlines())


def acquire_lock() -> bool:
    if os.path.exists(LOCK):
        try:
            old = int(open(LOCK).read().strip())
            os.kill(old, 0)
            return False
        except Exception:
            pass
        try:
            os.unlink(LOCK)
        except FileNotFoundError:
            pass
    fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    return True


def unlock() -> None:
    try:
        os.unlink(LOCK)
    except FileNotFoundError:
        pass


def main() -> None:
    if not acquire_lock():
        return
    primary: str | None = None
    stealth_done = False
    shape_ticks = 0
    try:
        t0 = time.time()
        while not dude_alive() and time.time() - t0 < 60:
            time.sleep(0.5)
        if not dude_alive():
            return

        while True:
            if not dude_alive():
                time.sleep(2)
                if not dude_alive():
                    break

            cands = find_tray_windows()
            ids = {c[0] for c in cands}

            if primary and primary not in ids and not window_alive(primary):
                primary = None
                stealth_done = False

            if primary is None and cands:
                primary = pick_initial(cands)[0]
                stealth_done = False

            if primary:
                if not stealth_done:
                    apply_stealth_once(primary)
                    stealth_done = True
                    shape_ticks = 0
                else:
                    nudge_if_needed(primary)
                    # Reaplica máscara de vez em quando (Wine redesenha branco)
                    shape_ticks += 1
                    if shape_ticks % 3 == 0:
                        apply_flag_shape(primary)

                for wid, *_ in cands:
                    if wid != primary:
                        hide(wid)

            hide_tooltips()
            time.sleep(POLL)
    finally:
        unlock()


if __name__ == "__main__":
    main()
