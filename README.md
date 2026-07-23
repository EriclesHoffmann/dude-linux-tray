# dude-linux-tray

Bring **MikroTik The Dude** tray flag to a modern Linux desktop (GNOME / Ubuntu) when running the Windows client under **Wine**.

On Windows, The Dude shows a small flag in the system tray (green = OK, red/yellow = problems). Under Wine on GNOME+Wayland, that icon often becomes a useless wide “Wine System Tray” strip — or disappears from the panel entirely.

This project docks the **real Wine NotifyIcon** onto your panel:

- Compact **~16×16** flag (white background masked out)
- **Live color** from The Dude (not a fake static icon)
- **Minimize → flag**, click flag → restore (Dude’s own hide-on-minimize)
- **Position adjuster** GUI so you can place it between panel icons
- Stays **out of the taskbar** / window list

> Not an official MikroTik product. No Dude server API — we reuse the client tray icon Wine already draws.

## Requirements

- Ubuntu 22.04+ / GNOME (tested with Dash to Panel; XWayland for Wine windows)
- Wine (win32 prefix recommended for The Dude)
- Packages: `python3-xlib`, `python3-pil`, `python3-gi`, `gir1.2-gtk-3.0`, `xdotool`, `wmctrl`

## Quick install

```bash
git clone https://github.com/EriclesHoffmann/dude-linux-tray.git
cd dude-linux-tray
./install.sh
```

`install.sh` installs apt deps (when possible), copies scripts to `~/bin`, icons, and desktop entries.

### Wine / The Dude

1. Create a win32 prefix and install The Dude client into it, e.g.  
   `~/.local/share/wineprefixes/dude` (override with `WINEPREFIX=...`).
2. In The Dude **Preferences**:
   - **Show tray icon** / do **not** hide tray icon  
   - **Hide on minimize** = on  
   - **Auto update** = off (recommended; self-update under Wine is fragile)
3. Launch:

```bash
~/bin/the-dude.sh
# or: WINEPREFIX=/path/to/prefix ~/bin/the-dude.sh
```

4. Align the flag on the panel:

```bash
~/bin/dude-flag-adjust.py
```

Use arrow keys (Shift = 8px). Position is saved to `~/.config/dude-flag/position.conf`.

### Black / white Dude window

The launcher sets `LIBGL_ALWAYS_SOFTWARE=1` to avoid a common black-screen glitch with The Dude under Wine.

## How it works

```text
dude.exe (Wine) → NotifyIcon → dude-dock-tray.py → flag on panel
dude-flag-adjust.py → ~/.config/dude-flag/position.conf → dock
```

- `the-dude.sh` — starts Wine + ensures the dock helper is running  
- `dude-dock-tray.py` — finds the Wine tray window, shrinks it, applies XShape, keeps it on the panel, skips taskbar  
- `dude-flag-adjust.py` — GTK tool to nudge and save position  

## Limitations

- Needs X11 tools (`xwininfo` / `xdotool`) talking to Wine’s XWayland windows — pure Wayland-native Wine tray embedding is not used.
- Panel layout varies; use the adjuster after install or after changing monitors.
- There is **no** public API for “flag status” from the Dude server; notifications must still be configured inside The Dude if you want email/syslog/etc.

## License

MIT — see [LICENSE](LICENSE).

## Portuguese

See [README.pt.md](README.pt.md).

## Forum blurb

Ready-to-paste MikroTik forum text: [FORUM_POST.md](FORUM_POST.md).
