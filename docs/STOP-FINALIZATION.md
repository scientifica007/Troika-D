# Stop/finalization design

## Problem found during Wayland field testing

Two different stop paths were observed:

1. The application's Stop recording button could leave the live
   ScreenCast session active while waiting for pipeline EOS.
2. The GNOME orange screen-sharing control destroys the portal session
   externally. A normal MP4 file can be unreadable if its muxer never
   receives EOS and therefore never writes/finalizes the moov index.

A checkerboard was observed in VLC when opening an interrupted file.
The GNOME screen-sharing indicator could also remain active after an
unclean application stop.

## Fix

### Source-level EOS

All live GStreamer sources now have stable element names:

- screen_src
- mic_src
- system_audio_src
- camera_src

The application sends EOS to each active source before waiting for the
pipeline EOS message. This follows the same principle as
gst-launch-1.0 with eos-on-shutdown for muxed files.

### Bounded finalization

The application waits up to 8 seconds for clean EOS finalization. If
that does not complete, it tears down the pipeline instead of leaving
the ScreenCast session running indefinitely.

### Explicit portal lifecycle

The application now:

- subscribes to org.freedesktop.portal.Session::Closed;
- detects the GNOME/system screen-sharing stop action;
- explicitly closes its own portal session after normal finalization;
- explicitly closes the PipeWire remote file descriptor.

### Robust MP4 headers

The H.264/MP4 path uses GstBaseQTMux robust muxing:

- reserved-max-duration: 24 hours
- reserved-moov-update-period: 1 second

This periodically updates MP4 index tables on disk. Therefore an
external interruption should lose at most the newest unindexed portion
rather than leaving an entirely unreadable MP4.

The normal in-app stop still uses EOS and remains the preferred stop
path.
