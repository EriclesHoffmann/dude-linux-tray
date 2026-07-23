#!/usr/bin/env bash
# The Dude (Wine) launcher + Linux tray dock helper.
# Minimize → Wine flag on the panel; click the flag → restore.
# Part of: https://github.com/ (dude-linux-tray)
set -euo pipefail

export WINEPREFIX="${WINEPREFIX:-$HOME/.local/share/wineprefixes/dude}"
export WINEARCH=win32
export WINEDLLOVERRIDES="mscoree,mshtml="
export LIBGL_ALWAYS_SOFTWARE=1

DUDE_EXE='C:\Program Files\Dude\dude.exe'
DOCK="$HOME/bin/dude-dock-tray.py"

dude_running() {
  ps -u "$(id -u)" -o args= | grep -Fqx "$DUDE_EXE"
}

show_dude() {
  local wid
  wid=$(xwininfo -root -tree 2>/dev/null | awk '/The Dude/ && /dude\.exe/ {print $1; exit}')
  if [ -n "${wid:-}" ]; then
    xdotool windowmap "$wid" 2>/dev/null || true
    wmctrl -i -r "$wid" -b remove,hidden 2>/dev/null || true
    xdotool windowactivate "$wid" 2>/dev/null || true
  fi
}

ensure_dock() {
  if ps -u "$(id -u)" -o args= | grep -q '[d]ude-dock-tray\.py'; then
    return 0
  fi
  nohup python3 -u "$DOCK" >/tmp/dude-dock-tray.log 2>&1 &
}

if dude_running; then
  ensure_dock
  show_dude
  exit 0
fi

ensure_dock
exec wine "$DUDE_EXE"
