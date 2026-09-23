# Milestone B — Field Test Plan

Branch: `milestone-b/capture-completeness`

The rule for this milestone is: validate what already exists before adding code.

## Test order

### Test 1 — Audio-only / external microphone

- Mode: Audio only
- Microphone: external CM108
- System audio: off
- Duration: 20–30 seconds

Pass criteria:

- recording starts without video portal dialog;
- stop completes normally;
- output file opens;
- speech is continuous and clear;
- no recurrent dropouts.

### Test 2 — Audio-only / built-in microphone

Same as Test 1 with Built-in Audio Analog Stereo.

Pass criteria focus on continuity, not fan/noise rejection.

### Test 3 — Microphone + system audio

- Mode: Video
- Source: Full screen
- Quality: Balanced
- Frame rate: 30 FPS
- Microphone: external CM108
- System audio: on
- Webcam: off
- Play a known audio source during the recording.

Pass criteria:

- voice and system playback are both audible;
- no repeated dropouts;
- no runaway level/clipping caused by the mixer;
- stop/finalization remains clean.

### Test 4 — Pause / resume

Run twice:

1. video only;
2. video + external microphone.

Procedure:

- record 10 seconds;
- Pause for about 5 seconds;
- Resume;
- record 10 more seconds;
- Stop.

Pass criteria:

- application remains responsive;
- output is readable;
- no broken timestamps;
- no permanently lost audio after Resume.

### Test 5 — Wayland window capture

- Mode: Video
- Source: Window
- Microphone/system audio/webcam: off for first attempt.
- Select one visible application window from the system portal.

Pass criteria:

- only the selected window is recorded;
- no unrelated screen content appears;
- stop/finalization succeeds;
- output is readable.

### Test 6 — Screenshots

Run each available source independently:

- Full screen
- Window
- Area
- Active window

Pass criteria:

- source selection matches the requested mode;
- image is saved to the chosen directory;
- image opens normally;
- no lingering portal session.

## Evidence to report

For each test, report only:

- PASS / FAIL
- what was selected
- observable defect, if any
- terminal error/warning only if one appears

Screenshots are useful only when they show a defect or a source-selection result.


## Field results — 2026-09-23, cycle 1

### Test 1 — Audio-only / external microphone

PASS.

Observed:
- Audio-only starts without the screen-sharing portal.
- External CM108 microphone records successfully.
- Output OGG file is created and readable.
- Audio recording path is operational.

### Test 3 — Microphone + system audio

PASS for source mixing and recording.

Observed:
- External CM108 microphone and system audio can be recorded at the same time.
- Screen video is recorded at the same time.
- Stop/finalization succeeds.

New defect discovered during this test:

- Fast/moving YouTube content in the recorded image is visibly choppy at Balanced / 30 FPS.
- This is tracked as GitHub issue #2 (PERF-001).
- Audio mixing itself is not considered the cause until measurements show otherwise.

### External GNOME stop control

Recording can be stopped using the orange GNOME screen-sharing control and the application reports:
`Saved after system stop`.

A transient duplicate-pointer artifact was observed immediately afterward:
- one pointer remains frozen near the top-bar stop location;
- one pointer remains live;
- the frozen pointer disappears after a delay.

Tracked as GitHub issue #3 (PORTAL-001).

## Next controlled tests

Before implementing new capture features:

1. Pause/resume: video only.
2. Pause/resume: video + external microphone.
3. Wayland Window capture.
4. Screenshots: full screen, window, area, active window.
5. Performance isolation for PERF-001:
   - Economy / 30 FPS
   - Balanced / 30 FPS
   - Balanced / 15 FPS
   using the same moving YouTube scene.


## Field results — 2026-09-23, cycle 2

### Performance isolation

#### Balanced / 30 FPS / full screen / no audio / no webcam

PARTIAL.

- Live YouTube playback becomes slightly heavier.
- Recorded motion contains clearly visible intermittent pauses.
- The defect is easy to see in the recorded file.

#### Balanced / 15 FPS / full screen / no audio / no webcam

PASS for practical usability on the tested machine.

- Live YouTube playback is materially smoother.
- Recorded motion is much smoother and acceptable.
- Small transient stutters correlate with periods of higher CPU/fan activity.

#### Economy / 30 FPS / full screen / no audio / no webcam

FAIL for recorded-motion quality.

- Live playback remains smooth.
- Recorded video has very frequent visible interruptions.
- Inspection of the implementation found that Economy's configured 75% scale had never actually been applied; it only added an extra conversion stage. That false internal assumption has been removed before any further Economy benchmark.

### Pause / Resume — video only

PASS.

Recording pauses when Pause is pressed and resumes when Resume is pressed.

The video + microphone variant remains to be tested.

### Wayland Window capture

FUNCTIONAL PASS / MOTION QUALITY FAIL.

- User selected a Brave window through the portal.
- Only the selected Brave window was recorded.
- Tab changes inside Brave remain visible because they are content changes inside the same selected window.
- Switching to other application windows does not change the captured source.
- At 30 FPS, scrolling and other motion produce substantial visible interruptions.
- At 15 FPS, the result is much better but still not fully clean.
- Green lines/corruption can appear at the beginning of a recording.

The code now explicitly sets videorate `skip-to-first=true` and an I420 raw-video format before encoding, then exposes videorate counters for the next field run.

### "Active Window" video mode

The field result was identical to Window because this was not a distinct ScreenCast operation.

The XDG ScreenCast portal only defines monitor, window, and virtual-monitor source types. The misleading Active Window video choice has therefore been removed from the video UI. Active Window remains meaningful for Screenshot portals that advertise screenshot target 8.

### Area video

EXPECTED FAIL / NOT IMPLEMENTED YET.

The application correctly reports that Wayland Area recording needs the Milestone B preview/crop workflow.

### Screenshot — Full screen

FAIL in the pre-fix build.

Observed:
- a screenshot is physically taken;
- the application then reports `Portal request Screenshot was cancelled or failed (code=2)`;
- the recorder UI is visible in the screenshot, which is not practical for normal screenshot use.

Fix applied for re-test:
- query Screenshot portal version and AvailableTargets;
- use target only when portal v3 advertises it;
- preserve a returned URI even if a backend returns a non-zero response;
- retry without the v3 target key when needed;
- hide the recorder window before requesting the screenshot and restore it afterward.

### Intermittent portal-stream failure

One repeated-session attempt failed with:

```text
Recording error: stream error: target not found
```

Tracked as issue #4 (PORTAL-002). It is intermittent; successful sessions occurred before and after it.

## Focused re-test after cycle-2 fixes

Only these checks are needed:

1. Window / Balanced / 15 FPS, 20–30 seconds with scrolling.
   - Report visible green startup corruption: yes/no.
   - Report overall motion quality.
   - Copy the terminal line beginning `Video timing stats`.

2. Full-screen / Balanced / 30 FPS, 20–30 seconds on the same moving content.
   - Copy the terminal line beginning `Video timing stats`.

3. Screenshot:
   - Full screen
   - Window
   - Area
   - Active window
   Confirm whether the recorder UI is absent and whether each result is saved without the code=2 error.

After those checks, proceed to implement Wayland Area video capture.


## Field results — 2026-09-23, cycle 3

### Window / Balanced / 15 FPS

- startup green corruption: FIXED in this field run;
- ordinary page motion: minor, acceptable stutter;
- YouTube motion inside the selected Brave window: still heavily choppy.

Timing counters:

```text
Video timing stats [eos]: in=1676 out=747 drop=1062 duplicate=133
```

This confirms severe drop/duplicate churn under forced constant 15 FPS.

### Full screen / Balanced / 30 FPS

PASS in this run.

- live YouTube playback: smooth;
- recorded YouTube playback: smooth;
- no visible interruption.

Timing counters:

```text
Video timing stats [eos]: in=938 out=1152 drop=26 duplicate=240
```

The known-good Full Screen CFR path is therefore left unchanged.

### Screenshot portal behavior

Detected backend:

```text
version=2
available-targets=0x0
```

Therefore portal v2 does not support application-selected Full Screen / Window / Area / Active Window targets. All four prior UI choices necessarily opened the same Ubuntu interactive screenshot tool.

The recorder correctly hides before the system screenshot UI appears, but this portal/backend ends with response code 2 even after the user completes the screenshot.

Cycle-3 fix:

- portal v2 now exposes one source choice: `Interactive screenshot (system)`;
- the four source-specific choices are shown only for portal v3+ when advertised;
- response code 2 after this legacy external flow is treated as system-tool completion instead of an application error;
- the Save-to chooser is disabled for this legacy portal path because the system screenshot tool controls its own destination.

Tracked as issue #6 (SCREENSHOT-001).

### Window timing experiment applied

For Wayland Window only:

- preserve native source timestamps;
- cap maximum frame rate with `videorate max-rate`;
- use `drop-only=true`;
- do not force a constant-framerate caps filter;
- do not synthesize duplicate frames.

Full Screen keeps the previously validated constant-framerate pipeline.

## Focused re-test after cycle-3 patch

1. Window / Balanced / 15 FPS with YouTube motion.
   - report visual smoothness;
   - copy `Video timing stats [eos]`.

2. Screenshot mode.
   - confirm Source now shows one interactive system choice on this portal v2 machine;
   - confirm no error dialog appears after taking the screenshot.

If Window motion improves materially, keep the source-specific timing strategy and proceed to Wayland Area recording.


## Field results — 2026-09-23, cycle 4

### Window timing experiment

FAIL / HARD REGRESSION.

The Window-only pipeline using:

```text
videorate skip-to-first=true drop-only=true max-rate=15
```

hard-aborted twice:

```text
gst_video_rate_push_buffer: assertion failed:
(GST_BUFFER_DURATION_IS_VALID (outbuf))
Aborted (core dumped)
```

The application process terminated and left a non-playable partial file.

Decision:

- reject this experiment;
- revert immediately to the previously field-stable CFR Window path;
- track the regression as issue #7 (CRASH-001);
- do not replace the stable Window path again without an isolated safety test.

### Screenshot portal v2

PASS.

The revised application now shows:

```text
Interactive screenshot (system)
```

The recorder hides, Ubuntu's screenshot tool operates normally, and no erroneous code=2 dialog is shown.

Issue #6 (SCREENSHOT-001) is closed as completed.

## Next engineering step

Do not ask for another Window field test until a non-crashing alternative has been designed and statically/unit tested.

Proceed with the next independent Milestone B feature: Wayland Area recording, while leaving the stable Window CFR path intact.


## Field clarification — 2026-09-23, timing sample attribution

Five later `Video timing stats` lines were all produced by:

```text
Video
Full screen
Balanced
30 FPS
```

with different combinations of microphone, system audio, and webcam. Exact row-to-accessory mapping was not retained.

Therefore these samples must not be interpreted as Window measurements. They also show that a large duplicate count can coexist with an acceptable Full Screen recording, so timing counters need configuration context and must be interpreted together with perceived motion quality.

Diagnostics now print:

```text
source=<...> quality=<...> fps=<...>
mic=<0|1> system_audio=<0|1> webcam=<0|1>
in=<...> out=<...> drop=<...> duplicate=<...>
```

## Screenshot storage clarification

Portal-v2 screenshot behavior on the tested machine:

- Ubuntu saves full-screen, area, and window screenshots under
  `~/Pictures/Screenshots`.
- Area/window captures could additionally be copied by the recorder into
  `~/Videos`.
- Full-screen capture appeared only under Ubuntu's Screenshots folder.

This duplicate-copy behavior is an application bug, not a second desired save path.

Patch:
- portal v2 storage is now always treated as system-managed;
- the recorder no longer copies returned v2 screenshot URIs;
- portal v3+ keeps app-managed result handling.

Focused acceptance check after update:
take one area or window screenshot and confirm it exists only in Ubuntu's Screenshots folder.


## Field results — 2026-09-23, cycle 5

### Screenshot portal v2 storage — FINAL PASS

After commit `408d283`:

- full-screen screenshot: saved only under `~/Pictures/Screenshots`;
- area screenshot: saved only under `~/Pictures/Screenshots`;
- window screenshot: saved only under `~/Pictures/Screenshots`;
- no screenshot copy is created under `~/Videos`.

SCREENSHOT-001 (#6) is closed as completed for portal v2.

## Wayland Area recording — implementation ready for first field test

Implemented workflow:

1. Video → Area.
2. Portal asks for the monitor.
3. Recorder keeps the portal session prepared without encoding yet.
4. A translucent fullscreen GTK overlay appears on the selected monitor.
5. User drags a rectangle; Esc cancels and closes the prepared portal session.
6. Rectangle is stored as normalized geometry.
7. GStreamer starts with `videocrop name=area_crop`.
8. A pad probe reads the actual negotiated PipeWire width/height.
9. Pixel crop margins are computed and aligned to even I420/H.264 output dimensions.
10. `area_gate` stays closed until crop margins are configured, preventing a full-screen startup frame from leaking into the output.

The portal-reported monitor `position`/`size` are used only to choose the matching GTK monitor, not as the actual video pixel size.

### First Area field test

Use only:

```text
Video
Area
Balanced
15 FPS
No audio
No webcam
```

Pass criteria:

- portal lets the user select the monitor;
- translucent selector covers the selected monitor;
- drag rectangle is visible and usable;
- recording starts after mouse release;
- output contains only the selected rectangle;
- no full-screen startup frame is visible;
- Stop creates a readable MP4;
- terminal prints `Area crop configured: stream=...`.


## Field results — 2026-09-23, cycle 6

### Wayland Area / Balanced / 15 FPS / no audio

FUNCTIONAL PASS.

- monitor portal selection works;
- area selector is interactive;
- selected-area recording starts and finalizes correctly;
- output video is readable;
- selected-area crop is applied correctly;
- YouTube motion was generally smooth;
- pointer movement correlated with visible interruptions in this run.

Timing:

```text
source=area quality=balanced fps=15 mic=0 system_audio=0 webcam=0
in=294 out=650 drop=114 duplicate=470
```

### Wayland Area / Balanced / 15 FPS / system audio ON

PASS.

- selected-area video good;
- system audio good;
- scrolling/page motion acceptable;
- YouTube content good;
- clean stop/finalization.

Timing:

```text
source=area quality=balanced fps=15 mic=0 system_audio=1 webcam=0
in=1669 out=1165 drop=745 duplicate=241
```

### Selector transparency defect

The selector appeared as an opaque black fullscreen window rather than a translucent overlay.

Patch applied:
- clear backing surface to transparent with Cairo SOURCE;
- draw only a translucent dim layer;
- clear the active rectangle so the selected content remains visible;
- use whole-window opacity as a fallback where RGBA compositing is unavailable.

### Focused re-test

Only verify selector appearance:

1. Video → Area.
2. Choose the monitor.
3. Confirm the desktop remains visible under a dim translucent layer.
4. Drag a rectangle and confirm the rectangle area is visually clearer than the dimmed surroundings.
5. Esc may be used to cancel; a full recording is not required for this visual re-test.

After selector acceptance, continue with Area + microphone and Area + webcam.


## Field result — 2026-09-23, cycle 7

The second transparency fix still failed on the tested GNOME/Wayland system:
the Area selector remained fully black and the desktop was not visible.

Timing from the visual-only run:

```text
Wayland portal stream: fd=26, node-id=69, position=(0, 0), size=(1366, 768)
Area crop configured: stream=1366x768 left=1020 right=2 top=132 bottom=4
Video timing stats [eos]: source=area quality=balanced fps=30 mic=0 system_audio=0 webcam=0 in=178 out=712 drop=15 duplicate=549
```

Decision:
transparent fullscreen GTK selection is rejected for this Wayland path.

Replacement implementation:
- hide recorder UI;
- use an additional PipeWire remote in the same authorized portal session;
- grab one RGB preview frame;
- display that frame in a normal opaque fullscreen selector;
- dim the preview and show the dragged rectangle at full brightness;
- reuse the validated normalized-crop → negotiated-caps videocrop recording path.

Focused next test:
Video → Area → choose monitor.
Expected: the selector shows a snapshot of the actual desktop, not a black screen.
A full recording is not required unless the preview is correct.


## Field result — 2026-09-23, cycle 8

### Webcam startup checkerboard fix — Area acceptance

Configuration:

```text
Mode: Video
Source: Area
Quality: Balanced
Frame rate: 30 FPS
Microphone: ON — CM108
System audio: OFF
Webcam: ON
```

PASS.

Observed:

- Area monitor selection and preview workflow remained functional.
- Selected rectangle remained correct.
- Video recording completed successfully.
- External CM108 microphone recorded successfully.
- Webcam overlay recorded successfully.
- The previous checkerboard artifact did not appear at the beginning of the recorded file.
- No checkerboard artifact appeared at the end of the recorded file.
- Clean EOS finalization completed.

Terminal evidence:

```text
Wayland portal stream: fd=26, node-id=66, position=(0, 0), size=(1366, 768)
Area preview captured: 1366x768, rowstride=4100, frames=6, selected=1, rgb-range=0..255, mean=120
Area crop configured: stream=1366x768 left=0 right=2 top=126 bottom=196
EOS request: source-pads=[screen_src:1,mic_src:1,camera_src:1] pipeline-fallback=0 accepted=1
Video timing stats [eos]: source=area quality=balanced fps=30 mic=1 system_audio=0 webcam=1 in=666 out=1115 drop=54 duplicate=503
```

Interpretation:

- The compositor startup policy change removes the visible checkerboard in the tested Area + microphone + webcam path.
- No regression was observed in Area selection, crop, microphone, webcam, or finalization.
- Full-screen webcam acceptance remains the final focused check before this improvement is eligible for merge.


## Field results — 2026-09-23, cycle 9

### Webcam startup checkerboard fix — Full Screen acceptance

Configuration:

```text
Mode: Video
Source: Full screen
Quality: Balanced
Frame rate: 30 FPS
Webcam: ON
```

PASS.

Observed:

- recording completed successfully;
- the previous checkerboard artifact did not appear at the beginning;
- no checkerboard artifact appeared at the end;
- clean EOS finalization completed.

Terminal evidence:

```text
Wayland portal stream: fd=26, node-id=83, position=(0, 0), size=(1366, 768)
EOS request: source-pads=[screen_src:1,camera_src:1] pipeline-fallback=0 accepted=1
Video timing stats [eos]: source=screen quality=balanced fps=30 mic=0 system_audio=0 webcam=1 in=434 out=617 drop=35 duplicate=218
```

Decision:

- checkerboard startup/end defect is accepted as fixed for the tested Full Screen and Area webcam paths;
- protected recovery branch created after acceptance:
  `baseline/field-tested-2026-09-23-post-webcam-fix`.

## Field results — 2026-09-23, cycle 10

### Portal cancellation semantics — Full Screen and Window

A dedicated UX branch changed screen-selection cancellation from an error condition to a normal user-cancel flow.

Field acceptance:

- Full Screen: pressing Cancel in the system Share Screen dialog returns to the recorder without an error dialog and reports `Screen selection cancelled`;
- Window: same behavior;
- the recorder remains usable immediately after cancellation;
- subsequent normal Full Screen capture still starts, records, finalizes, and saves;
- subsequent normal Window capture still starts, records, finalizes, and saves.

Terminal evidence for the post-cancel normal-capture checks:

```text
Video timing stats [eos]: source=screen quality=balanced fps=15 mic=1 system_audio=0 webcam=0 in=232 out=155 drop=121 duplicate=44
Video timing stats [eos]: source=window quality=balanced fps=15 mic=1 system_audio=0 webcam=0 in=214 out=205 drop=101 duplicate=92
```

CI also passed for the change. PR #11 was merged into `milestone-b/capture-completeness`.

Canonical merge commit:

```text
675572d2216147b230acc70acf8f24c503ef9de1
```

Newest protected field-tested baseline:

```text
baseline/field-tested-2026-09-23-post-cancel-fix
```

## Field results — 2026-09-23, cycle 11

### Pause/resume — Full Screen + external CM108 microphone

Configuration:

```text
Mode: Video
Source: Full screen
Quality: Balanced
Frame rate: 15 FPS
Record microphone: ON
Microphone: CM108 Audio Controller Mono
Record system audio: OFF
Webcam overlay: OFF
```

PASS.

Observed:

- recording started normally after the screen-selection portal;
- Pause stopped recording progress and the control changed to Resume;
- Resume continued the same recording;
- Stop completed and the file was saved successfully;
- the recorder remained usable after the test.

Terminal evidence:

```text
Wayland portal stream: fd=26, node-id=81, position=(0, 0), size=(1366, 768)
EOS request: source-pads=[screen_src:1,mic_src:1] pipeline-fallback=0 accepted=1
Video timing stats [eos]: source=screen quality=balanced fps=15 mic=1 system_audio=0 webcam=0 in=217 out=277 drop=101 duplicate=161
```

Decision:

- B1 pause/resume with video + microphone is field-accepted on the tested Wayland machine;
- no implementation change is required from this test.

## Field results — 2026-09-23, cycle 12

### Audio-only — built-in microphone

Configuration:

```text
Mode: Audio only
Microphone: Built-in Audio Analog Stereo
System audio: OFF
```

FUNCTIONAL PASS / INPUT-NOISE QUALITY UNRESOLVED.

Observed:

- audio-only recording starts and records microphone input;
- Stop requests EOS cleanly from the microphone source;
- no video portal is involved;
- the recorded speech is audible;
- substantial background noise is present;
- the user cannot yet distinguish whether that noise is the built-in microphone/electrical input noise or acoustic pickup of the computer fan.

Terminal evidence:

```text
EOS request: source-pads=[mic_src:1] pipeline-fallback=0 accepted=1
```

The later `^C ... KeyboardInterrupt` occurred when the user manually terminated the still-running application after the recording test; it is not a recording-pipeline failure.

Decision:

- B1 audio-only functionality with the built-in microphone is field-accepted;
- microphone noise rejection is not part of the B1 continuity criterion and remains a separate input-quality diagnostic;
- no recorder implementation change is justified until a controlled comparison separates microphone/device noise from ambient fan noise.

## Built-in microphone noise isolation — direct ALSA confirmation

A direct ALSA recording was performed against the physical HDA capture device:

```text
card 0: MID [HDA Intel MID]
device 0: ALC270 Analog [ALC270 Analog]
```

Command:

```bash
arecord -D plughw:0,0 -f S16_LE -r 48000 -c 1 -d 20 ~/mic-test.wav
```

Result:

- the same background noise is present;
- perceived noise intensity is similar to Ubuntu Screen Recorder, Kooha, and historical Kazam recordings;
- therefore the noise is reproducible below the application/GStreamer/PipeWire layer and is not attributed to Ubuntu Screen Recorder.

Hardware capability probe:

```text
FORMAT: S16_LE S32_LE
CHANNELS: 2
RATE: [44100 192000]
```

The later `arecord --dump-hw-params` setup error was caused by the command attempting a default 8-bit sample format that this capture device does not support; it does not indicate a recorder defect.

Decision:

- built-in-microphone noise is classified as an input/hardware/acoustic quality issue, not a recorder regression;
- no noise-suppression or capture-pipeline modification is justified solely from this evidence.

## B1 field-validation status

All B1 validations that are executable on the current portal-v2 Wayland test machine are complete.

The portal-v3 source-specific screenshot target check remains unavailable on this machine and is therefore not a field failure.

Next work should proceed only on a separate improvement/development branch, preserving the protected field-tested baseline.
