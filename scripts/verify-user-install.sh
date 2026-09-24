#!/usr/bin/env bash
set -euo pipefail

APP_ID="io.github.scientifica007.TroikaD"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"

files=(
  "$HOME/.local/bin/troika-d"
  "$DATA_HOME/applications/$APP_ID.desktop"
  "$DATA_HOME/icons/hicolor/scalable/apps/$APP_ID.svg"
  "$DATA_HOME/metainfo/$APP_ID.metainfo.xml"
  "$DATA_HOME/troika-d/app/src/ubuntu_screen_recorder/__main__.py"
)

missing=0
for path in "${files[@]}"; do
  if [[ -e "$path" ]]; then
    printf 'PASS  %s\n' "$path"
  else
    printf 'MISS  %s\n' "$path"
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "Troika D installation verification failed." >&2
  exit 1
fi

grep -q '^Name=Troika D$' "$DATA_HOME/applications/$APP_ID.desktop"
grep -q "^Exec=$HOME/.local/bin/troika-d$" "$DATA_HOME/applications/$APP_ID.desktop"
grep -q "^Icon=$APP_ID$" "$DATA_HOME/applications/$APP_ID.desktop"

echo "Troika D desktop installation verification: PASS"
