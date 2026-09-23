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
