# Field test — 2026-09-23

Environment observed by the application:

- Ubuntu desktop session: Wayland
- ScreenCast portal: working
- GStreamer H.264/x264 path: working
- Built-in display selection: working
- Internal microphone: detected
- External USB PnP microphone: detected when connected before startup
- HP Webcam-101: detected; multiple /dev/video* nodes exposed by the device

## Results

1. Full-screen video without audio: PASS.
2. Built-in microphone + video: records, but audio has frequent cuts/distortion.
3. External USB microphone:
   - not discovered if inserted after application startup in the original build;
   - discovered if inserted before application startup;
   - clearer than the built-in microphone;
   - intermittent cuts still observed.
4. Webcam overlay + external microphone: PASS in one run, with clearer external-mic audio.
5. Later external-microphone run: frequent audio cuts observed again.

## Interpretation

The successful video-only and webcam runs validate the Wayland Portal/PipeWire video path and the basic compositor path.

Audio cuts occur with more than one microphone and are intermittent, so they are not treated as a microphone-quality problem alone. The next build changes the capture timing/buffering strategy:

- microphone sources no longer force BaseSrc do-timestamp;
- Pulse sources do not become the pipeline master clock;
- audio source clock slaving uses resampling instead of hard pointer skew corrections;
- Pulse ring buffer is enlarged;
- raw audio is normalized to 48 kHz;
- queues are governed by time rather than byte count;
- a single audio source bypasses audiomixer;
- two-source mixing receives 100 ms of live-input tolerance;
- raw video capture uses a time-based leaky queue so an overloaded encoder drops stale video frames instead of blocking audio.

Hot-plug discovery is also added by polling devices every two seconds while idle and refreshing again immediately before recording.

These changes are hypotheses to be validated by a second field-test cycle. Audio stability is not marked PASS until the recordings are listened to.
