# Ubuntu Screen Recorder

A lightweight native Ubuntu screen recorder designed for both older and newer computers.

The project deliberately avoids Electron and browser runtimes. The UI uses GTK 3, capture/encoding uses GStreamer, X11 capture uses ximagesrc, and Wayland capture uses the XDG Desktop Portal + PipeWire permission flow.

## Product goals

- Record a full screen, selected window, or selected area.
- Record video with optional microphone and/or system audio.
- Record audio only.
- Take screenshots of a screen, window, active window, or selected area.
- Select among multiple microphones and cameras.
- Optional webcam overlay.
- Choose quality and frame rate without codec jargon by default.
- Work on X11 and Wayland.
- Stay usable on low-spec hardware.

## Current status: v0.1 foundation

Implemented foundations:

- GTK 3 application shell.
- X11/Wayland session detection.
- Microphone and system-audio source discovery with pactl.
- Camera discovery via /dev/video*.
- GStreamer capability probing.
- Quality profiles and 15/30/60 FPS selection.
- XDG Screenshot Portal integration.
- XDG ScreenCast Portal helper.
- GStreamer pipeline builder for X11 and Portal/PipeWire.
- Audio-only mode.
- Optional microphone + system-audio mixing.
- Optional webcam overlay foundation.
- H.264/x264 primary encoding with VP8/WebM fallback.

The app does not silently fake incomplete source modes: X11 window/area video picking and Wayland area-video cropping are Milestone B work.

## Install runtime dependencies

On a modern Ubuntu desktop:

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

For Wayland screen recording, a working PipeWire + desktop portal backend is also required. Ubuntu 22.04/24.04 and newer desktops normally provide the required stack. Older PulseAudio-based systems remain supported for audio discovery.

## Run from source

```bash
git clone https://github.com/scientifica007/Ubuntu_Screen_Recorder.git
cd Ubuntu_Screen_Recorder
PYTHONPATH=src python3 -m ubuntu_screen_recorder
```

Or:

```bash
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -e .
ubuntu-screen-recorder
```

## Design principle

The UI does not own capture logic. Capture, device discovery, portal handling, and GStreamer pipeline construction are separate layers. This makes it possible to redesign the interface or replace an encoder/backend without rebuilding the whole application.

See docs/ARCHITECTURE.md and docs/ROADMAP.md.
