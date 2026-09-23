#!/usr/bin/env bash
set -u

printf 'Session: %s\n' "${XDG_SESSION_TYPE:-unknown}"
for cmd in python3 gst-launch-1.0 gst-inspect-1.0 pactl gdbus; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf '[OK] %s -> %s\n' "$cmd" "$(command -v "$cmd")"
  else
    printf '[MISSING] %s\n' "$cmd"
  fi
done

for element in ximagesrc pipewiresrc x264enc vp8enc pulsesrc v4l2src; do
  if command -v gst-inspect-1.0 >/dev/null 2>&1 && gst-inspect-1.0 "$element" >/dev/null 2>&1; then
    printf '[OK] GStreamer element: %s\n' "$element"
  else
    printf '[MISSING] GStreamer element: %s\n' "$element"
  fi
done
