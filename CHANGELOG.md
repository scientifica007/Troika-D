# Changelog

All notable changes to Troika D are documented here.

## [0.1.0-beta.1] — 2026-09-24

First public beta.

### Added

- Full-screen video recording.
- Window recording through the Wayland ScreenCast portal.
- Selected-area recording with preview-based crop selection.
- 15, 30, and 60 FPS choices.
- Economy, Balanced, and Quality recording profiles.
- Microphone recording with selectable audio input.
- System-audio recording.
- Mixed microphone + system-audio recording.
- Optional webcam overlay with selectable camera.
- Audio-only recording.
- Interactive desktop screenshots through the system portal.
- Pause and resume.
- User-local desktop installation with application-menu launcher and icon.
- Reversible uninstall and installation verification tools.
- Troika D product identity and AppStream metadata.
- GPL-3.0-or-later licensing, Responsible Use statement, and trademark policy.

### Improved

- Wayland Window motion quality by rate-limiting before colour conversion.
- Recording finalization and playable-output reliability.
- Portal cancellation handling as a normal user flow.
- Webcam startup behavior.
- Area-selection transparency and preview workflow.
- Audio-device refresh/discovery behavior.
- Low-resource usability on the primary field-test machine.

### Known limitations

- **PERF-002:** on the primary Ubuntu/Wayland low-resource machine, Window capture with Webcam overlay enabled at Balanced 15 FPS or 30 FPS can produce green corruption and severe stutter in the recorded screen stream. The same Window configurations with Webcam disabled pass, and Area + Webcam at Balanced 30 FPS passes. Workaround for beta 1: disable Webcam in Window mode, or use Area/Full Screen when Webcam is required.

- X11 has not received the same complete field-test matrix as the primary Wayland environment.
- Screenshot behavior depends on the desktop portal implementation; on the tested Portal v2 system, Ubuntu owns the interactive target selection and saves screenshots under the system screenshot folder.
- Capture smoothness depends on hardware, compositor, selected FPS, source type, and content motion.
- Built-in microphone quality depends strongly on hardware mixer gain/boost configuration.
- The internal Python module name remains `ubuntu_screen_recorder` for compatibility; the product identity is Troika D.
