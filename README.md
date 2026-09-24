# Troika D

**Lightweight screen capture for Linux.**

Troika D is a native GTK/GStreamer desktop recorder built to stay practical on both older and newer computers. It supports Wayland through XDG Desktop Portal + PipeWire and supports X11 capture without an Electron or browser runtime.

## Current capabilities

- Record the full screen, a selected window, or a selected area.
- Record video with optional microphone and/or system audio.
- Record audio only.
- Take interactive screenshots through the desktop portal.
- Select among available microphones and cameras.
- Optional webcam overlay.
- Pause and resume recordings.
- Choose 15/30/60 FPS and simple quality profiles.
- H.264/x264 primary encoding with VP8/WebM fallback.
- Robust stop/finalization behavior for playable output files.
- Field-tested Window-capture performance path for motion-heavy content.

## Runtime dependencies

On Ubuntu/Debian-family systems:

```bash
sudo apt update
sudo apt install -y \
  python3 python3-gi \
  gir1.2-gtk-3.0 gir1.2-gstreamer-1.0 \
  gstreamer1.0-tools gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly gstreamer1.0-libav \
  xdg-desktop-portal pulseaudio-utils
```

Wayland recording also requires a working PipeWire + desktop portal backend.

## Run from source

The repository still carries its historical development name while the Troika D rebrand is being validated:

```bash
git clone https://github.com/scientifica007/Ubuntu_Screen_Recorder.git
cd Ubuntu_Screen_Recorder
PYTHONPATH=src python3 -m ubuntu_screen_recorder
```

Or install the Python project and use the product command:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -e .
troika-d
```

## Desktop identity

- Product: **Troika D**
- App ID: `io.github.scientifica007.TroikaD`
- Command: `troika-d`
- Python project: `troika-d`

The internal Python module remains `ubuntu_screen_recorder` during the rebrand validation cycle to avoid unnecessary runtime risk. It can be migrated separately after the desktop/package identity has passed regression testing.

## Architecture

The UI does not own capture logic. Device discovery, portal handling, recording orchestration, and GStreamer pipeline construction are separate layers so the interface and backends can evolve independently.

See `docs/ARCHITECTURE.md), `docs/ROADMAP.md), and the field-test documents for the current validated state.
