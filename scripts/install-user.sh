#!/usr/bin/env bash
set -euo pipefail

APP_ID="io.github.scientifica007.TroikaD"
APP_SLUG="troika-d"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_HOME="$HOME/.local/bin"
APP_HOME="$DATA_HOME/$APP_SLUG"
APP_DIR="$APP_HOME/app"
DESKTOP_DIR="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/scalable/apps"
METAINFO_DIR="$DATA_HOME/metainfo"
WRAPPER="$BIN_HOME/$APP_SLUG"
DESKTOP_FILE="$DESKTOP_DIR/$APP_ID.desktop"
ICON_FILE="$ICON_DIR/$APP_ID.svg"
METAINFO_FILE="$METAINFO_DIR/$APP_ID.metainfo.xml"

if [[ ! -d "$ROOT_DIR/src/ubuntu_screen_recorder" ]]; then
  echo "Troika D source tree not found under: $ROOT_DIR/src" >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required." >&2
  exit 1
fi

python3 - <<'PY'
try:
    import gi
    gi.require_version("Gtk", "3.0")
    gi.require_version("Gst", "1.0")
    from gi.repository import Gtk, Gst  # noqa: F401
except Exception as exc:
    raise SystemExit(
        "Troika D runtime dependencies are incomplete. "
        "Install python3-gi, GTK 3 and GStreamer GI packages first.\n"
        f"Details: {exc}"
    )
PY

mkdir -p "$APP_HOME" "$BIN_HOME" "$DESKTOP_DIR" "$ICON_DIR" "$METAINFO_DIR"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"

cp -a "$ROOT_DIR/src" "$APP_DIR/"
cp -a "$ROOT_DIR/pyproject.toml" "$APP_DIR/"

install -m 0644   "$ROOT_DIR/data/icons/hicolor/scalable/apps/$APP_ID.svg"   "$ICON_FILE"

install -m 0644   "$ROOT_DIR/data/$APP_ID.metainfo.xml"   "$METAINFO_FILE"

cat > "$WRAPPER" <<EOF
#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$APP_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
exec /usr/bin/python3 -m ubuntu_screen_recorder "$@"
EOF
chmod 0755 "$WRAPPER"

sed   -e "s|^Exec=.*$|Exec=$WRAPPER|"   "$ROOT_DIR/data/$APP_ID.desktop" > "$DESKTOP_FILE"
chmod 0644 "$DESKTOP_FILE"

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$DESKTOP_DIR" >/dev/null 2>&1 || true
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1 && [[ -f "$DATA_HOME/icons/hicolor/index.theme" ]]; then
  gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true
fi

echo "Troika D installed for user: $USER"
echo "Launcher: $DESKTOP_FILE"
echo "Command:  $WRAPPER"
echo
echo "Open the application menu and search for: Troika D"
