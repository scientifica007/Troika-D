# Debian Package Field Test — v0.1.0-beta.1

Date: 2026-09-24

Target environment: primary Ubuntu/Wayland field machine.

Package under test:

```text
troika-d_0.1.0~beta1-1_all.deb
```

## Overall result

**ACCEPTED WITH KNOWN LIMITATION.**

The Debian-installed edition is acceptable for the user's practical workflow and successfully covers the core recording, audio-only, and screenshot needs exercised in this field pass.

The only rejected combinations found in this pass are Window capture with Webcam overlay enabled at Balanced 15 FPS and Balanced 30 FPS. That defect is tracked separately as **PERF-002**.

## Coverage exercised

The field pass included:

- Video recording.
- Audio-only recording.
- Screenshot workflow.
- Full Screen source.
- Window source.
- Area source.
- Balanced quality.
- 15 FPS.
- 30 FPS.
- microphone capture.
- system-audio capture.
- microphone + system audio together.
- webcam overlay.
- pointer inclusion.

Not exercised in this pass:

- Economy quality.
- High quality.
- 60 FPS.

## Comparative isolation matrix

| Source | FPS | Mic | System audio | Webcam | Result |
| --- | ---: | --- | --- | --- | --- |
| Window | 15 | ON | ON | ON | **FAIL** — green corruption + severe stutter in screen stream |
| Window | 15 | ON | ON | OFF | **PASS** |
| Window | 30 | ON | ON | OFF | **PASS** |
| Window | 30 | ON | ON | ON | **FAIL** — green corruption + severe stutter in screen stream |
| Area | 30 | ON | ON | ON | **PASS** |

In the failed Window + Webcam runs:

- webcam video itself remained good;
- microphone recording remained good;
- system-audio recording remained good;
- the degraded component was the recorded Window/screen stream.

The comparison strongly isolates the defect to the interaction between the Window capture path and webcam-overlay composition on this field machine. Exact pipeline root cause is not yet proven.

## Current workaround

For this beta:

- use **Window with Webcam OFF**; or
- use **Area / Full Screen** when Webcam overlay is required.

## Release disposition

The defect is non-blocking for the current beta because:

- Window capture is acceptable with Webcam disabled;
- webcam overlay is acceptable in Area and previously accepted Full Screen workflows;
- audio paths remain functional;
- the application continues to satisfy the user's primary workflow requirements.

Do not modify the accepted current pipeline in-place. PERF-002 should be investigated on a separate improvement branch for the next release.
