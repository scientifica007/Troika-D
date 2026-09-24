#!/usr/bin/env bash
set -euo pipefail

APP_ID="io.github.scientifica007.TroikaD"
APP_SLUG="troika-d"

DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_HOME="$HOME/.local/bin"

rm -rf "$DATA_HOME/$APP_SLUG"
rm -f "$BIN_HOME/$APP_SLUG"
rm -f "$DATA_HOME/applications/$APP_ID.desktop"
rm -f "$DATA_HOME/icons/hicolor/scalable/apps/$APP_ID.svg"
rm -f "$DATA_HOME/metainfo/$APP_ID.metainfo.xml"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DATA_HOME/applications" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1 && [[ -f "$DATA_HOME/icons/hicolor/index.theme" ]]; then
  gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Troika D user-local installation removed."
