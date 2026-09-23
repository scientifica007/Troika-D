# Field test — 2026-09-23

Environment observed by the application:

- Ubuntu desktop session: Wayland
- ScreenCast portal: working
- GStreamer H.264/x264 path: working
- Built-in display selection: working
- Internal microphone: detected
- External CM108 USB microphone: detected
- HP Webcam-101: detected
- HP Webcam-101 exposes both /dev/video0 and /dev/video1

## Cycle 1 — foundation

1. Full-screen video without audio: PASS.
2. Built-in microphone + video: audio initially showed frequent cuts/distortion.
3. External USB microphone:
   - was not discovered if inserted after application startup in the original build;
   - was discovered if inserted before startup;
   - sounded clearer than the built-in microphone;
   - intermittent cuts were observed.
4. Webcam overlay + external microphone: PASS in one run.
5. A later external-microphone run again showed frequent cuts.

These observations led to the live-audio timing/buffering changes and automatic hot-plug refresh in commit 6cff3cc.

## Cycle 2 — after live-audio and hot-plug hardening

### Hot-plug

PASS.

The application was opened with only the built-in audio source visible. After the external microphone was connected while the application was already running, the list refreshed automatically and exposed:

- Built-in Audio Analog Stereo
- CM108 Audio Controller Mono

The UI also switched from raw Pulse source identifiers to human-readable device descriptions.

### External USB microphone

PASS.

The CM108 external microphone recorded clear audio without the previous dropouts.

### Built-in microphone

TIMING PASS / ACOUSTIC QUALITY DEVICE-LIMITED.

The built-in microphone no longer demonstrated the previously observed intermittent dropout pattern. Its remaining noisy/distorted character corresponds to strong laptop-fan pickup reported during the test, so this is treated as an acoustic/input-quality issue rather than a recorder timing failure.

### Webcam overlay

PASS on /dev/video0.

The HP Webcam-101 capture path on /dev/video0 records correctly alongside screen video and microphone audio.

### /dev/video1

NON-BLOCKING DEVICE-DISCOVERY ISSUE.

Selecting /dev/video1 fails with:

    Device '/dev/video1' is not a capture device.

GStreamer reports V4L2 capabilities 0x4a00000. This confirms that the original device discovery was too broad because it listed every /dev/video* node rather than only capture-capable V4L2 nodes.

The next patch queries VIDIOC_QUERYCAP and filters known non-capture nodes before they reach the UI.

## Current field verdict

Validated on the tested Wayland machine:

- full-screen recording: PASS
- H.264/x264 output: PASS
- save/finalize path: PASS
- external microphone audio continuity: PASS
- microphone hot-plug refresh: PASS
- built-in microphone timing continuity: PASS
- webcam overlay using /dev/video0: PASS
- simultaneous screen + microphone + webcam: PASS

The user reported being very satisfied with performance and judged it better than Kazam on this machine. This is a user-reported comparative observation, not a cross-machine benchmark.

Still unvalidated:

- microphone + system-audio simultaneous mixing
- audio-only mode after the latest timing changes
- window/area capture completeness
- X11 behavior
- performance across older/newer hardware classes
