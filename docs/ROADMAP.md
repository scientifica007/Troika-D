# Roadmap

## Milestone A — Native foundation — COMPLETE

Merged into `main` by PR #1.

Canonical merge commit:

```text
b9670ca189f21b3ff93d43d78c49399f51d43fe9
```

Validated on the tested Wayland machine:

- [x] Repository architecture
- [x] GTK3 application shell
- [x] X11/Wayland session probe
- [x] microphone/system-audio discovery
- [x] camera discovery
- [x] Screenshot Portal helper
- [x] ScreenCast Portal helper
- [x] GStreamer pipeline builder
- [x] audio-only mode foundation
- [x] webcam overlay foundation
- [x] unit tests for model/pipeline decisions
- [x] Wayland compatibility for modern pipewire-serial and legacy portal node IDs
- [x] clean GStreamer NULL-state teardown after startup failure
- [x] real Wayland full-screen recording
- [x] real Wayland webcam-overlay recording
- [x] automatic idle-time microphone/camera hot-plug refresh
- [x] human-readable Pulse/PipeWire device names
- [x] USB microphone live-audio stability validated
- [x] built-in microphone timing stability validated
- [x] V4L2 capture-capability filtering
- [x] clean source-level EOS finalization
- [x] bounded finalization timeout
- [x] explicit Wayland Portal/PipeWire lifecycle cleanup
- [x] robust MP4 index updates for interrupted-stop resilience
- [x] finalize active recording before application-window exit
- [x] stop/finalization field validation on Wayland

## Milestone B — Capture completeness and field hardening — ACTIVE

Development branch:

```text
milestone-b/capture-completeness
```

### B1 — Validate existing capabilities before new implementation

- [ ] audio-only: built-in microphone
- [ ] audio-only: external USB microphone
- [ ] microphone + system-audio mixing
- [ ] pause/resume: video only
- [ ] pause/resume: video + microphone
- [ ] Wayland window capture
- [ ] screenshot: full screen
- [ ] screenshot: window
- [ ] screenshot: selected area
- [ ] screenshot: active window

### B2 — Complete Wayland capture modes

- [ ] verify/fix Wayland window capture after B1 test
- [ ] Wayland selected-area preview
- [ ] selected-area rectangle interaction
- [ ] GStreamer videocrop integration
- [ ] area recording + microphone
- [ ] area recording + webcam
- [ ] area stop/finalization QA

### B3 — Complete X11 capture modes

- [ ] X11 interactive window picker
- [ ] X11 interactive region picker
- [ ] X11 full-screen regression test
- [ ] X11 microphone/system-audio regression test

### B4 — Field hardening / usability

- [ ] non-blocking startup/error handling
- [ ] countdown
- [ ] configurable webcam size/position
- [ ] audio level meters
- [ ] pause/resume final field validation

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
