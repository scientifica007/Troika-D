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
