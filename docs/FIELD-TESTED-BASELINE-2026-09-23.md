# Field-Tested Baseline — 2026-09-23

Repository: `scientifica007/Troika-D`

Historical repository name at the time of early development: `scientifica007/Ubuntu_Screen_Recorder`

Development branch at time of freeze:

```text
milestone-b/capture-completeness
```

Recovery snapshot:

```text
baseline/field-tested-2026-09-23
```

## Purpose

This document records the working state that was validated manually on the current Ubuntu Wayland test machine.

The recovery snapshot is intentionally treated as immutable. New experiments must happen on other branches. A new implementation is accepted only when it preserves the capabilities listed below and does not introduce a regression that is worse than the baseline for the user's real workflow.

## Accepted working capabilities

### Full-screen video

Validated successfully with the Balanced profile.

Observed successful field combinations include:

- screen only;
- external microphone;
- system audio;
- microphone + system audio;
- webcam overlay;
- microphone + webcam;
- combinations of screen/audio/webcam used in practical tests.

Both 15 FPS and 30 FPS paths have produced usable recordings. Performance varies by source/content and system load.

### Selected-area video

The Area workflow is functional on Wayland:

1. the ScreenCast portal authorizes/selects the monitor;
2. the recorder captures a PipeWire preview frame;
3. the recorder UI hides;
4. the area selector shows the real desktop image under a dim overlay;
5. the user drags the desired rectangle;
6. the selected geometry is converted to `videocrop` margins;
7. recording begins for only the selected area.

Field-validated combinations:

- Area + no audio/webcam;
- Area + system audio;
- Area + external microphone;
- Area + external microphone + webcam.

The selected output is readable and the crop is correct.

### Audio

Validated:

- external CM108 microphone;
- system audio;
- microphone + system audio mixing.

The external microphone is the preferred input on this test machine because the built-in microphone captures substantial fan noise.

### Webcam

The working webcam capture node records successfully.

Known cosmetic defect:

- a short checkerboard-like frame/region can appear at the beginning of a recording when webcam overlay is enabled.

This defect does not invalidate the rest of the recording and is now treated as an isolated improvement target.

### Pause / Resume

Video-only Pause/Resume was field-tested successfully.

Video + microphone Pause/Resume still requires a final dedicated acceptance run.

### Screenshots

On the tested Screenshot Portal v2 backend:

- the application exposes the system interactive screenshot workflow rather than pretending that source-specific app-side targets are available;
- the recorder hides while Ubuntu's screenshot UI is active;
- full-screen, area, and window screenshots are created through Ubuntu's screenshot tool;
- screenshot files are system-managed under `~/Pictures/Screenshots`;
- the recorder does not create duplicate screenshot copies under `~/Videos`.

### Stop / finalization

Successful recordings use source-level EOS finalization.

The application has also been hardened so that bounded timeout handling preserves robust/playable MP4 output when a clean EOS completion does not arrive in time.

## Performance observations on the tested machine

These are field observations for this machine, not universal benchmarks.

- Full Screen can be materially smoother than Window capture for moving content.
- Window capture can show substantial stutter with moving YouTube/video content even when ordinary pages are acceptable.
- Area capture has produced good practical results.
- 15 FPS is often a useful low-resource option.
- 30 FPS can also work well in some Full Screen/Area runs.
- `videorate` drop/duplicate counters alone do not determine perceived quality; field perception must be considered together with the diagnostic context.

## Known defects / limitations preserved for follow-up

- webcam startup checkerboard artifact;
- Window motion quality remains weaker than the strongest Full Screen/Area cases;
- transient duplicate pointer after stopping from GNOME's external orange screen-share control;
- occasional bounded finalization timeout;
- built-in microphone fan-noise susceptibility;
- X11 test matrix not yet completed;
- portal-v3 screenshot target-specific behavior cannot be validated on this portal-v2 machine.

## Development policy after this freeze

1. Do not move or overwrite `baseline/field-tested-2026-09-23`.
2. Do not rewrite stable capture paths merely for architectural elegance.
3. Isolate risky improvements on dedicated branches.
4. Preserve a working path unless a replacement is field-tested against it.
5. Treat regressions on this real test machine as release blockers for the affected feature.
6. Prefer incremental fixes with explicit rollback over broad pipeline redesign.
7. Keep known-good Full Screen and Area behavior available while improving Window/Webcam details.

## User field assessment

On this specific low-resource test machine and for the user's actual workflow, the current application is assessed as more practical than Kazam and Kooha, and more suitable than OBS on this hardware.

This statement is a machine-specific field assessment, not a general ranking of those applications across systems.
