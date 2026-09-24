# Troika D v0.1.0-beta.1 — Release Notes

Troika D is a lightweight native GTK/GStreamer screen capture application for Linux.

This is the first public beta and the first release under the **Troika D** product identity.

## What is included

Troika D can record:

- the full screen;
- a selected window;
- a selected area;
- microphone audio;
- system audio;
- microphone and system audio together;
- an optional webcam overlay;
- audio only.

It also supports interactive screenshots, Pause/Resume, selectable microphones/cameras, multiple FPS choices, and simple quality profiles.

## Wayland

The primary field-validation environment is Ubuntu on Wayland.

Screen and window sharing use XDG Desktop Portal + PipeWire. Area recording uses an authorized portal stream plus Troika D's preview/crop workflow.

The Window path includes the field-tested PERF-001 v3 ordering that materially improved motion quality on the primary low-resource test machine.

## Installation

For the first beta, the supported project-provided installation path is the reversible user-local installer:

```bash
bash scripts/install-user.sh
```

It installs only under the current user's home directory and does not require `sudo`.

Verify:

```bash
bash scripts/verify-user-install.sh
```

Remove:

```bash
bash scripts/uninstall-user.sh
```

## Licensing

Troika D is free and open-source software under **GPL-3.0-or-later**.

The repository also contains:

- `RESPONSIBLE_USE.md` — non-binding project values;
- `TRADEMARKS.md` — guidance for the Troika D name, logo, and official identity.

## Known limitation discovered in field testing

**PERF-002 — Window + Webcam overlay:** on the primary Ubuntu/Wayland low-resource machine, Window recording with Webcam enabled at Balanced 15 FPS or 30 FPS can show green corruption and severe stutter in the recorded screen stream.

Comparative field testing showed:

- Window + Webcam OFF: acceptable at 15 and 30 FPS;
- Window + Webcam ON: rejected at 15 and 30 FPS;
- Area + Webcam ON: accepted at 30 FPS;
- webcam image and microphone/system audio remained good even in the failed Window runs.

Beta workaround: disable Webcam for Window capture, or use Area/Full Screen when Webcam is required.

Tracked as **PERF-002 / GitHub issue #22**.

## Beta status

This release is intentionally marked **beta**.

The core recording workflows have been field-tested repeatedly on the primary Ubuntu/Wayland machine, but broader hardware, desktop-environment, distribution, and X11 coverage is still needed.

Please report reproducible defects with:

- Linux distribution/version;
- desktop environment;
- Wayland or X11;
- selected source, FPS, quality profile, audio/webcam options;
- terminal output where available.
