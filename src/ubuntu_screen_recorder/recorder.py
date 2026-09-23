import os
from pathlib import Path
from typing import Callable, Optional

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst

from .models import CaptureSource, RecordingConfig, RecordingMode
from .pipeline import PortalStream, build_pipeline
from .portal import PortalClient
from .system_probe import SystemCapabilities


SOURCE_NAMES = (
    "screen_src",
    "mic_src",
    "system_audio_src",
    "camera_src",
)
FINALIZE_TIMEOUT_SECONDS = 8


class Recorder:
    def __init__(
        self,
        capabilities: SystemCapabilities,
        status_cb: Callable[[str], None],
    ):
        Gst.init(None)
        self.capabilities = capabilities
        self.status_cb = status_cb
        self.pipeline: Optional[Gst.Element] = None
        self.portal = PortalClient() if capabilities.has_portal else None
        self.portal_session: Optional[str] = None
        self.pipewire_fd: Optional[int] = None
        self.portal_closed_subscription = 0
        self.stop_timeout_id = 0
        self.stopping = False
        self.active_config = None
        self.active_config: Optional[RecordingConfig] = None

    @property
    def active(self) -> bool:
        return self.pipeline is not None

    def start(self, config: RecordingConfig, output_path: Path) -> None:
        if self.pipeline is not None:
            raise RuntimeError("Recorder is already active")
        config.validate()
        portal_stream = None
        self.stopping = False

        if config.mode == RecordingMode.VIDEO:
            if (
                self.capabilities.session_type == "x11"
                and config.source != CaptureSource.SCREEN
            ):
                raise RuntimeError(
                    "This foundation build records the full screen on X11. "
                    "Interactive X11 window/area picking is Milestone B."
                )
            if (
                self.capabilities.session_type == "wayland"
                and config.source == CaptureSource.AREA
            ):
                raise RuntimeError(
                    "Wayland area recording needs the portal-stream "
                    "preview/crop workflow from Milestone B."
                )

        if (
            config.mode == RecordingMode.VIDEO
            and self.capabilities.session_type == "wayland"
        ):
            if self.portal is None:
                raise RuntimeError(
                    "Wayland capture requires XDG Desktop Portal"
                )
            self.status_cb(
                "Select a screen or window in the system dialog…"
            )
            source_types = (
                1 if config.source.value in {"screen", "area"} else 2
            )
            (
                session,
                fd,
                node_id,
                pipewire_serial,
            ) = self.portal.create_screencast(
                source_types=source_types,
                cursor_mode=2 if config.show_pointer else 1,
            )
            self.portal_session = session
            self.pipewire_fd = fd
            self.portal_closed_subscription = (
                self.portal.watch_session_closed(
                    session, self._on_portal_closed
                )
            )
            portal_stream = PortalStream(
                fd=fd,
                node_id=node_id,
                pipewire_serial=pipewire_serial,
            )
            selector_kind = (
                "serial"
                if pipewire_serial is not None
                else "node-id"
            )
            selector_value = (
                pipewire_serial
                if pipewire_serial is not None
                else node_id
            )
            print(
                f"Wayland portal stream: fd={fd}, "
                f"{selector_kind}={selector_value}",
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
            raise RuntimeError(
                "GStreamer failed to start the recording pipeline"
            )

        self.active_config = config
        self.status_cb(f"Recording — {plan.encoder}")

    def pause(self) -> None:
        if self.pipeline and not self.stopping:
            self.pipeline.set_state(Gst.State.PAUSED)
            self.status_cb("Paused")

    def resume(self) -> None:
        if self.pipeline and not self.stopping:
            self.pipeline.set_state(Gst.State.PLAYING)
            self.status_cb("Recording")

    def stop(self) -> None:
        pipeline = self.pipeline
        if not pipeline or self.stopping:
            return

        self.stopping = True
        self.status_cb("Finalizing recording…")

        accepted = False
        for name in SOURCE_NAMES:
            source = pipeline.get_by_name(name)
            if source is None:
                continue
            try:
                accepted = (
                    source.send_event(Gst.Event.new_eos()) or accepted
                )
            except Exception:
                pass

        if not accepted:
            accepted = pipeline.send_event(Gst.Event.new_eos())

        if not accepted:
            self.status_cb(
                "Could not request clean EOS; stopping with "
                "recoverable MP4 state."
            )
            self._force_null_and_cleanup()
            return

        self.stop_timeout_id = GLib.timeout_add_seconds(
            FINALIZE_TIMEOUT_SECONDS,
            self._on_finalize_timeout,
        )

    def force_stop(self) -> None:
        self._log_video_timing("force-stop")
        self._force_null_and_cleanup()

    def _log_video_timing(self, reason: str) -> None:
        pipeline = self.pipeline
        if not pipeline:
            return
        rate = pipeline.get_by_name("video_rate")
        if rate is None:
            return
        try:
            values = {
                "in": rate.get_property("in"),
                "out": rate.get_property("out"),
                "drop": rate.get_property("drop"),
                "duplicate": rate.get_property("duplicate"),
            }
        except Exception:
            return
        config = self.active_config
        context = ""
        if config is not None:
            context = (
                f" source={config.source.value}"
                f" quality={config.quality.key}"
                f" fps={config.fps}"
                f" mic={int(config.include_microphone)}"
                f" system_audio={int(config.include_system_audio)}"
                f" webcam={int(config.include_camera)}"
            )
        print(
            "Video timing stats "
            f"[{reason}]:"
            f"{context} "
            f"in={values['in']} "
            f"out={values['out']} "
            f"drop={values['drop']} "
            f"duplicate={values['duplicate']}",
            flush=True,
        )

    def _on_finalize_timeout(self) -> bool:
        self.stop_timeout_id = 0
        if not self.pipeline:
            return False
        self.status_cb(
            "Finalization timeout — recording stopped. "
            "Robust MP4 headers preserve playability."
        )
        self._log_video_timing("finalize-timeout")
        self._force_null_and_cleanup()
        return False

    def _on_portal_closed(self) -> None:
        GLib.idle_add(self._handle_external_portal_close)

    def _handle_external_portal_close(self) -> bool:
        if not self.pipeline:
            return False
        self.status_cb(
            "Screen sharing was stopped by the system — "
            "closing the recording safely."
        )
        self.stopping = True
        self._log_video_timing("external-portal-stop")
        self._force_null_and_cleanup(portal_already_closed=True)
        self.status_cb("Saved after system stop")
        return False

    def _on_message(self, _bus, message) -> None:
        if message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            self._log_video_timing("error")
            if debug:
                print(debug, flush=True)

            if self.stopping:
                self.status_cb(
                    "Recording stopped during finalization; "
                    "robust MP4 recovery state retained."
                )
            else:
                self.status_cb(f"Recording error: {err.message}")
            self._force_null_and_cleanup()

        elif message.type == Gst.MessageType.EOS:
            self._log_video_timing("eos")
            pipeline = self.pipeline
            if pipeline:
                pipeline.set_state(Gst.State.NULL)
            self.status_cb("Saved")
            self._cleanup()

    def _force_null_and_cleanup(
        self,
        portal_already_closed: bool = False,
    ) -> None:
        pipeline = self.pipeline
        if pipeline:
            pipeline.set_state(Gst.State.NULL)
        self._cleanup(portal_already_closed=portal_already_closed)

    def _cleanup(
        self,
        portal_already_closed: bool = False,
    ) -> None:
        if self.stop_timeout_id:
            GLib.source_remove(self.stop_timeout_id)
            self.stop_timeout_id = 0

        if self.portal and self.portal_closed_subscription:
            self.portal.unwatch_session(
                self.portal_closed_subscription
            )
            self.portal_closed_subscription = 0

        self.pipeline = None

        if (
            not portal_already_closed
            and self.portal
            and self.portal_session
        ):
            self.portal.close_session(self.portal_session)

        self.portal_session = None

        if self.pipewire_fd is not None:
            try:
                os.close(self.pipewire_fd)
            except OSError:
                pass
            self.pipewire_fd = None

        self.stopping = False
        self.active_config = None
