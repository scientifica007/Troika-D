# Architecture

## Core decision

Use a native GTK 3 UI with GStreamer as the media engine.

- X11 capture: GStreamer ximagesrc.
- Wayland capture: XDG Desktop Portal -> PipeWire -> GStreamer pipewiresrc.
- Audio: PulseAudio/PipeWire compatibility sources through pactl and pulsesrc.
- Camera: V4L2 through v4l2src.
- Screenshots: XDG Screenshot Portal.

## Layers

```text
GTK3 UI
  |
Application Controller
  |-- Device Discovery
  |-- XDG Portal Client
  |
Capture backend
  |-- X11 / ximagesrc
  `-- Wayland / ScreenCast Portal / PipeWire
  |
GStreamer Pipeline Builder
  |-- frame rate / conversion
  |-- optional webcam compositor
  |-- optional microphone + system audio mixer
  |-- encoder fallback
  `-- muxer / output file
```

## Why GTK 3

GTK 3 gives a lower runtime footprint than an Electron/web application and remains broadly available across Ubuntu generations. It also works under both X11 and Wayland.

## Why GStreamer

GStreamer already provides the Linux-native primitives needed here: X11 capture, PipeWire streams, PulseAudio/PipeWire audio, V4L2 cameras, compositing, encoders, muxers, and live pipeline control.

## Wayland model

Wayland intentionally blocks arbitrary screen scraping. A ScreenCast session must be created through the desktop portal; the compositor lets the user approve/select a monitor or window and exposes only that stream through PipeWire.

Area recording is therefore designed as a later portable workflow:

1. Ask the portal for a monitor stream.
2. Show a preview in the application.
3. Let the user draw a rectangle in that preview.
4. Crop the granted live stream in GStreamer.

This keeps the app compositor-independent.

## Performance strategy

Product-level settings stay simple:

| Profile | Use | Video bitrate | Encoder preset |
|---|---|---:|---|
| Economy | old CPU / long recording | 1800 kb/s | ultrafast |
| Balanced | normal use | 4500 kb/s | veryfast |
| High | detail / stronger CPU | 8000 kb/s | fast |

Frame rate is selected independently: 15, 30, or 60 FPS.

The baseline path uses software H.264 when x264enc exists and falls back to VP8/WebM. Hardware encoders are optional future adapters, never a requirement.
