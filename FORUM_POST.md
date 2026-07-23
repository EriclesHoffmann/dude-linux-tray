# Forum post (MikroTik — The Dude)

Copy/paste into a new topic under **The Dude**.

---

**Title:** Linux/Wine: real Dude tray flag on the GNOME panel (dude-linux-tray)

**Body:**

Hi,

Running the Windows **The Dude** client under Wine on Ubuntu/GNOME, the tray flag is awkward: you either get the floating “Wine System Tray” strip, or you hide it and lose the green/red status at a glance. There is still no usable server API for “flag color” (as discussed in older threads).

I packaged a small helper that keeps the **real Wine NotifyIcon** on the panel:

* Compact ~16×16 flag (white chrome masked with XShape)
* Live green / yellow / red from the client
* Minimize → flag, click flag → restore (Dude “hide on minimize”)
* GTK position adjuster so you can park it between panel icons
* Stays out of the normal window list / taskbar

**Repo (MIT):** https://github.com/EriclesHoffmann/dude-linux-tray

```bash
git clone https://github.com/EriclesHoffmann/dude-linux-tray.git
cd dude-linux-tray
./install.sh
# Wine prefix with The Dude installed, then:
~/bin/the-dude.sh
~/bin/dude-flag-adjust.py   # align on the panel
```

**Dude prefs that work well:** tray icon visible, hide on minimize ON, auto-update OFF. Launcher sets `LIBGL_ALWAYS_SOFTWARE=1` to reduce black-screen issues under Wine.

**Limits:** needs X11 helpers for Wine/XWayland windows; panel layouts differ — use the adjuster. This does not replace Dude notifications (email/syslog/execute); it only restores the tray flag UX on Linux.

Feedback and PRs welcome.

---

*(Optional Portuguese note at the end of the topic if you want:)*  
Também há README em português no repositório (`README.pt.md`).
