from pathlib import Path
from typing import Callable, Optional

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst

from .models import CaptureSource, RecordingConfig, RecordingMode
from .pipeline import PortalStream, build_pipeline
from .portal import PortalClient
from .system_probe import SystemCapabilities


class Recorder:
    def __init__(self, capabilities: SystemCapabilities, status_cb: Callable[[str], None]):
        Gst.init(None)
        self.capabilities = capabilities
        self.status_cb = status_cb
        self.pipeline: Optional[Gst.Element] = None
        self.portal = PortalClient() if capabilities.has_portal else None
        self.portal_session: Optional[str] = None

    @property
    def active(self) -> bool:
        return self.pipeline is not None

    def start(self, config: RecordingConfig, output_path: Path) -> None:
        if self.pipeline is not None:
            raise RuntimeError("Recorder is already active")
        config.validate()
        portal_stream = None

        if config.mode == RecordingMode.VIDEO:
            if self.capabilities.session_type == "x11" and config.source != CaptureSource.SCREEN:
                raise RuntimeError(
                    "This foundation build records the full screen on X11. "
                    "Interactive X11 window/area picking is Milestone B and is not silently emulated."
                )
            if self.capabilities.session_type == "wayland" and config.source == CaptureSource.AREA:
                raise RuntimeError(
                    "Wayland area recording needs the portal-stream preview/crop workflow from Milestone B. "
                    "Choose Full screen or Window for this build."
                )

        if config.mode == RecordingMode.VIDEO and self.capabilities.session_type == "wayland":
            if self.portal is None:
                raise RuntimeError("Wayland capture requires XDG Desktop Portal")
            self.status_cb("Select a screen or window in the system dialog…")
            source_types = 1 if config.source.value in {"screen", "area"} else 2
            session, fd, node_id, pipewire_serial = self.portal.create_screencast(
                source_types=source_types,
                cursor_mode=2 if config.show_pointer else 1,
            )
            self.portal_session = session
            portal_stream = PortalStream(
                fd=fd,
                node_id=node_id,
                pipewire_serial=pipewire_serial,
            )
            selector_kind = "serial" if pipewire_serial is not None else "node-id"
            selector_value = pipewire_serial if pipewire_serial is not None else node_id
            print(
                f"Wayland portal stream: fd={fd}, {selector_kind}={selector_value}",
                flush=True,
            )

        plan = build_pipeline(
            config,
            output_path,
            self.capabilities.session_type,
            self.capabilities.has_x264enc,
            self.capabilities.has_vp8enc,
            portal_stream,
        )

        pipeline = Gst.parse_launch(plan.description)
        self.pipeline = pipeline
        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_message)

        result = pipeline.set_state(Gst.State.PLAYING)
        if result == Gst.StateChangeReturn.FAILURE:
            pipeline.set_state(Gst.State.NULL)
            if self.pipeline is pipeline:
                self._cleanup()
            raise RuntimeError("GStreamer failed to start the recording pipeline")

        self.status_cb(f"Recording — {plan.encoder}")

    def pause(self) -> None:
        if self.pipeline:
            self.pipeline.set_state(Gst.State.PAUSED)
            self.status_cb("Paused")

    def resume(self) -> None:
        if self.pipeline:
            self.pipeline.set_state(Gst.State.PLAYING)
            self.status_cb("Recording")

    def stop(self) -> None:
        if not self.pipeline:
            return
        self.status_cb("Finalizing recording…")
        if not self.pipeline.send_event(Gst.Event.new_eos()):
            self.pipeline.set_state(Gst.State.NULL)
            self._cleanup()

    def force_stop(self) -> None:
        pipeline = self.pipeline
        if pipeline:
            pipeline.set_state(Gst.State.NULL)
        self._cleanup()

    def _on_message(self, _bus, message) -> None:
        if message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self.status_cb(f"Recording error: {err.message}")
            if debug:
                print(debug, flush=True)
            self.force_stop()
        elif message.type == Gst.MessageType.EOS:
            pipeline = self.pipeline
            if pipeline:
                pipeline.set_state(Gst.State.NULL)
            self.status_cb("Saved")
            self._cleanup()

    def _cleanup(self) -> None:
        self.pipeline = None
        if self.portal and self.portal_session:
            self.portal.close_session(self.portal_session)
        self.portal_session = None
