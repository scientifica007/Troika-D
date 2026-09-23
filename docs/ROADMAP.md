# Roadmap

## Milestone A — Native foundation

- [x] Repository architecture
- [x] GTK3 application shell
- [x] X11/Wayland session probe
- [x] microphone/system-audio discovery
- [x] camera discovery
- [x] Screenshot Portal helper
- [x] ScreenCast Portal helper
- [x] GStreamer pipeline builder
- [x] audio-only mode
- [x] webcam overlay foundation
- [x] unit tests for model/pipeline decisions
- [x] Wayland compatibility for modern pipewire-serial and legacy portal node IDs
- [x] clean GStreamer NULL-state teardown after startup failure
- [x] first real Wayland full-screen recording
- [x] first real Wayland webcam-overlay recording
- [x] automatic idle-time microphone/camera hot-plug refresh

## Milestone B — Capture completeness and field hardening

- [ ] validate audio-stability changes on internal microphone
- [ ] validate audio-stability changes on USB microphone
- [ ] validate microphone + system-audio mixing
- [ ] validate audio-only path
- [ ] X11 interactive window picker
- [ ] X11 interactive region picker
- [ ] Wayland region preview/crop workflow
- [ ] robust pause/resume and EOS finalization
- [ ] non-blocking startup/error handling
- [ ] countdown
- [ ] configurable webcam size/position
- [ ] audio level meters

## Milestone C — Performance and compatibility

- [ ] runtime encoder benchmark
- [ ] optional VA-API/NVENC hardware encoding
- [ ] low-resource preset validation
- [ ] multi-monitor validation
- [ ] fractional scaling validation
- [ ] Ubuntu 20.04 / 22.04 / 24.04 / current-LTS matrix
- [ ] X11 + Wayland QA matrix

## Milestone D — Product polish

- [ ] safe recovery of interrupted recordings
- [ ] desktop notifications
- [ ] global shortcuts where supported
- [ ] Arabic / English / French translations
- [ ] Debian package
- [ ] release workflow
