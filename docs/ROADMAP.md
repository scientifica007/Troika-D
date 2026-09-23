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
- [x] audio-only: external USB microphone
- [x] microphone + system-audio mixing
- [x] pause/resume: video only
- [ ] pause/resume: video + microphone
- [x] Wayland window capture: functional selection/capture; motion-quality hardening remains
- [x] screenshot: portal v2 interactive system workflow
- [x] screenshot: recorder hides before system screenshot UI
- [x] screenshot: portal v2 code=2 compatibility behavior
- [ ] screenshot: source-specific targets on portal v3+ (not available on current test machine)

### B2 — Complete Wayland capture modes

- [ ] harden Wayland window motion quality (startup green artifact fixed in field test)
- [x] reject Window drop-only/max-rate experiment after hard GStreamer abort
- [ ] investigate safer Window timing design without destabilizing the known-stable CFR path
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

- [ ] investigate PERF-001: choppy recorded motion; 15 FPS materially better than 30 FPS on tested machine
- [x] add videorate in/out/drop/duplicate diagnostics
- [x] label timing diagnostics with source/quality/FPS/audio/webcam context
- [x] add skip-to-first startup timing guard
- [x] remove unapplied Economy resolution-scaling claim
- [x] remove misleading Active Window video option on Wayland/ScreenCast path
- [x] screenshot portal v2 simplified interactive mode after code=2 compatibility fix
- [ ] verify portal-v2 screenshots no longer duplicate into Videos after storage-ownership fix
- [ ] investigate PORTAL-001: transient duplicate cursor after GNOME external screen-share stop
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
