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

Field-tested safety snapshot:

```text
baseline/field-tested-2026-09-23
```

This baseline is a recovery point for the known-good implementation validated on the current Wayland test machine. Experimental changes must not overwrite or move this baseline.

### B1 — Validate existing capabilities before new implementation

- [x] audio-only: built-in microphone
- [x] audio-only: external USB microphone
- [x] microphone + system-audio mixing
- [x] pause/resume: video only
- [x] pause/resume: video + microphone
- [x] Wayland window capture: functional selection/capture; motion-quality hardening remains
- [x] screenshot: portal v2 interactive system workflow
- [x] screenshot: recorder hides before system screenshot UI
- [x] screenshot: portal v2 code=2 compatibility behavior
- [ ] screenshot: source-specific targets on portal v3+ (not available on current test machine)

### B2 — Complete Wayland capture modes

- [ ] harden Wayland window motion quality (startup green artifact fixed in field test)
- [x] reject Window drop-only/max-rate experiment after hard GStreamer abort
- [ ] investigate safer Window timing design without destabilizing the known-stable CFR path
- [x] Wayland selected-area monitor preparation
- [x] selected-area rectangle interaction
- [x] GStreamer videocrop integration
- [x] reject transparent fullscreen GTK selector after repeated Wayland field failure
- [x] selected-area PipeWire-preview selector field acceptance
- [x] area recording + microphone
- [x] area recording + webcam
- [x] area recording + system audio
- [x] area stop/finalization QA
- [x] remove/avoid brief checkerboard-like startup artifact when webcam overlay is enabled

### B3 — Complete X11 capture modes

- [ ] X11 interactive window picker
- [ ] X11 interactive region picker
- [ ] X11 full-screen regression test
- [ ] X11 microphone/system-audio regression test

### B4 — Field hardening / usability

- [ ] investigate PERF-001: choppy recorded motion; 15 FPS materially better than 30 FPS on some tested capture paths
- [x] add videorate in/out/drop/duplicate diagnostics
- [x] label timing diagnostics with source/quality/FPS/audio/webcam context
- [x] add skip-to-first startup timing guard
- [x] remove unapplied Economy resolution-scaling claim
- [x] remove misleading Active Window video option on Wayland/ScreenCast path
- [x] screenshot portal v2 simplified interactive mode after code=2 compatibility fix
- [x] verify portal-v2 screenshots no longer duplicate into Videos after storage-ownership fix
- [x] portal selection cancel is treated as normal UX flow for Full Screen and Window
- [ ] investigate PORTAL-001: transient duplicate cursor after GNOME external screen-share stop
- [ ] non-blocking startup/error handling
- [ ] countdown
- [ ] configurable webcam size/position
- [ ] audio level meters
- [ ] pause/resume final field validation

### Field-tested baseline policy — 2026-09-23

The current working behavior has been accepted as a known-good baseline on the test machine.

Validated in real use:

- Full Screen recording.
- Area recording with visible PipeWire-preview area selection.
- Balanced 15 FPS and 30 FPS recording paths used successfully.
- External CM108 microphone recording.
- System-audio recording.
- microphone + system-audio recording.
- webcam overlay using the working capture node.
- webcam overlay startup/end without the previous checkerboard artifact in tested Area and Full Screen runs.
- clean portal cancellation for Full Screen and Window without an error dialog.
- Area + microphone.
- Area + system audio.
- Area + microphone + webcam.
- Pause/resume for video-only recording.
- Pause/resume with external CM108 microphone.
- Screenshot portal v2 interactive Ubuntu workflow.
- screenshot storage owned by the system under `~/Pictures/Screenshots`.
- clean selected-area crop output.
- source-level EOS finalization in successful runs.
- audio-only recording with the built-in microphone (functional pass; input-noise source still to be isolated).

Known non-blocking defects/limitations remain documented rather than erased:

- Window capture motion can be substantially worse than Full Screen/Area for moving content.
- GNOME external screen-share stop can temporarily leave a duplicate pointer artifact.
- some runs can still hit bounded finalization timeout while preserving a playable robust MP4.
- X11 coverage is not yet validated.
- portal v3 screenshot target-specific behavior is not available on the current portal-v2 test system.

The baseline branches must remain unchanged. The newest protected field baseline is `baseline/field-tested-2026-09-23-post-cancel-fix` at merge commit `675572d2216147b230acc70acf8f24c503ef9de1`. New implementation work should occur on separate development/improvement branches and be accepted only after regression comparison against this baseline.

On this specific tested low-resource machine, the user reports the current application as more practical for his workflow than Kazam, Kooha, and OBS. This is a machine-specific field assessment, not a general cross-platform benchmark.

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
