#!/usr/bin/env bash
set -euo pipefail

DEB="${1:-}"
if [[ -z "$DEB" || ! -f "$DEB" ]]; then
  echo "Usage: $0 path/to/troika-d_*.deb" >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

dpkg-deb --info "$DEB" >/dev/null
dpkg-deb --contents "$DEB" >/dev/null
dpkg-deb --extract "$DEB" "$TMP/root"

required=(
  "usr/bin/troika-d"
  "usr/lib/troika-d/ubuntu_screen_recorder/__main__.py"
  "usr/share/applications/io.github.scientifica007.TroikaD.desktop"
  "usr/share/metainfo/io.github.scientifica007.TroikaD.metainfo.xml"
  "usr/share/icons/hicolor/scalable/apps/io.github.scientifica007.TroikaD.svg"
  "usr/share/doc/troika-d/LICENSE"
  "usr/share/doc/troika-d/RESPONSIBLE_USE.md"
  "usr/share/doc/troika-d/TRADEMARKS.md"
)

for rel in "${required[@]}"; do
  test -e "$TMP/root/$rel" || {
    echo "Missing package path: $rel" >&2
    exit 1
  }
done

grep -q '^Name=Troika D$'   "$TMP/root/usr/share/applications/io.github.scientifica007.TroikaD.desktop"
grep -q '^Exec=troika-d$'   "$TMP/root/usr/share/applications/io.github.scientifica007.TroikaD.desktop"

PYTHONPATH="$TMP/root/usr/lib/troika-d"   /usr/bin/python3 -c 'import ubuntu_screen_recorder.app'

echo "Troika D .deb verification: PASS"
