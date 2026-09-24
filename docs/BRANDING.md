# Troika D — Product identity

## Approved identity

- Product name: **Troika D**
- Tagline: **Lightweight screen capture for Linux**
- App ID: `io.github.scientifica007.TroikaD`
- Command: `troika-d`
- Python project name: `troika-d`

## Visual system

The approved visual direction uses:

- a dark navy application tile;
- three distinct capture arcs as the core symbol;
- blue, teal, and violet for the three capture channels;
- a red recording point at the center;
- restrained, modern GTK/GNOME-compatible presentation.

The three-part mark intentionally supports the product's three primary capture domains:

1. screen;
2. audio;
3. camera.

The icon must remain recognizable at small desktop-launcher sizes and must not reuse Ubuntu/Canonical or Tux artwork.

## Implementation policy

The field-tested recording baseline is not modified directly. Rebranding is developed on `rebrand/troika-d` and must pass startup, Full Screen, Window, Area, audio, webcam, screenshot, pause/resume, cancel, and finalization regression checks before merge.

The internal Python module remains `ubuntu_screen_recorder` during the first rebrand pass to minimize runtime risk. Product-facing identity is Troika D.
