#!/usr/bin/env bash
# Install dude-linux-tray helpers into ~/bin and desktop entries.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOME_DIR="${HOME}"
BIN_DIR="${HOME_DIR}/bin"
APP_DIR="${HOME_DIR}/.local/share/applications"
ICON_DIR="${HOME_DIR}/.local/share/icons/hicolor/32x32/apps"

echo "==> Installing dependencies (apt)…"
if command -v apt-get >/dev/null 2>&1; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-xlib python3-pil python3-gi gir1.2-gtk-3.0 \
    xdotool wmctrl x11-utils 2>/dev/null \
    || echo "WARN: apt install failed or needs confirmation — install deps manually."
else
  echo "WARN: apt not found. Install: python3-xlib python3-pil python3-gi gir1.2-gtk-3.0 xdotool wmctrl"
fi

echo "==> Copying scripts to ${BIN_DIR}"
mkdir -p "${BIN_DIR}"
install -m 0755 "${ROOT}/bin/the-dude.sh" "${BIN_DIR}/the-dude.sh"
install -m 0755 "${ROOT}/bin/dude-dock-tray.py" "${BIN_DIR}/dude-dock-tray.py"
install -m 0755 "${ROOT}/bin/dude-flag-adjust.py" "${BIN_DIR}/dude-flag-adjust.py"

echo "==> Installing icons"
mkdir -p "${ICON_DIR}"
cp -f "${ROOT}/icons/"the-dude-flag-*.png "${ICON_DIR}/"
if [[ -f "${ROOT}/icons/the-dude.png" ]]; then
  mkdir -p "${HOME_DIR}/.local/share/icons/hicolor/256x256/apps"
  cp -f "${ROOT}/icons/the-dude.png" \
    "${HOME_DIR}/.local/share/icons/hicolor/256x256/apps/the-dude.png" 2>/dev/null || true
fi
gtk-update-icon-cache -f -t "${HOME_DIR}/.local/share/icons/hicolor" 2>/dev/null || true

echo "==> Desktop entries"
mkdir -p "${APP_DIR}"
sed "s|@HOME@|${HOME_DIR}|g" "${ROOT}/desktop/the-dude.desktop.in" \
  > "${APP_DIR}/the-dude.desktop"
sed "s|@HOME@|${HOME_DIR}|g" "${ROOT}/desktop/dude-flag-adjust.desktop.in" \
  > "${APP_DIR}/dude-flag-adjust.desktop"
chmod 0644 "${APP_DIR}/the-dude.desktop" "${APP_DIR}/dude-flag-adjust.desktop"
update-desktop-database "${APP_DIR}" 2>/dev/null || true

echo
echo "Done."
echo
echo "Next steps:"
echo "  1. Install The Dude client into a Wine prefix (win32 recommended)."
echo "     Default expected: ~/.local/share/wineprefixes/dude"
echo "  2. In The Dude: Preferences → enable tray icon, enable hide on minimize,"
echo "     disable auto-update (optional but recommended)."
echo "  3. Launch:  ${BIN_DIR}/the-dude.sh"
echo "     or open \"The Dude\" from the app menu."
echo "  4. Align the flag: open \"Adjust Dude Flag\" and use arrow keys."
echo
echo "Env overrides:"
echo "  WINEPREFIX=...  ${BIN_DIR}/the-dude.sh"
