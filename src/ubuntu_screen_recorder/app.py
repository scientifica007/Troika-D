import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk

from .models import CaptureSource, QUALITY_PROFILES, RecordingConfig, RecordingMode
from .portal import PortalClient, PortalError
from .recorder import Recorder
from .system_probe import (
    AudioSource,
    CameraDevice,
    default_monitor_source,
    list_audio_sources,
    list_cameras,
    probe_capabilities,
)


class MainWindow(Gtk.ApplicationWindow):
    DEVICE_POLL_SECONDS = 2

    def __init__(self, application: Gtk.Application):
        super().__init__(application=application, title="Ubuntu Screen Recorder")
        self.set_default_size(620, 560)
        self.set_border_width(18)

        self.cap = probe_capabilities()
        self.audio_sources = list_audio_sources()
        self.cameras = list_cameras()
        self.recorder = Recorder(self.cap, self.set_status)
        self.portal = PortalClient() if self.cap.has_portal else None
        self.paused = False

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.add(root)

        title = Gtk.Label()
        title.set_markup("<span size='x-large' weight='bold'>Ubuntu Screen Recorder</span>")
        title.set_xalign(0)
        root.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(
            label=f"Session: {self.cap.session_type.upper()}  •  Native GTK/GStreamer"
        )
        subtitle.set_xalign(0)
        root.pack_start(subtitle, False, False, 0)

        grid = Gtk.Grid(column_spacing=14, row_spacing=12)
        grid.set_hexpand(True)
        root.pack_start(grid, True, True, 0)

        self.mode = Gtk.ComboBoxText()
        for key, label in (
            ("video", "Video"),
            ("audio", "Audio only"),
            ("screenshot", "Screenshot"),
        ):
            self.mode.append(key, label)
        self.mode.set_active_id("video")
        self.mode.connect("changed", self._sync_ui)
        self._row(grid, 0, "Mode", self.mode)

        self.source = Gtk.ComboBoxText()
        for key, label in (
            ("screen", "Full screen"),
            ("window", "Window"),
            ("area", "Area"),
            ("active-window", "Active window"),
        ):
            self.source.append(key, label)
        self.source.set_active_id("screen")
        self._row(grid, 1, "Source", self.source)

        self.quality = Gtk.ComboBoxText()
        for key, profile in QUALITY_PROFILES.items():
            self.quality.append(key, profile.label)
        self.quality.set_active_id("balanced")
        self._row(grid, 2, "Quality", self.quality)

        self.fps = Gtk.ComboBoxText()
        for value in (15, 30, 60):
            self.fps.append(str(value), f"{value} FPS")
        self.fps.set_active_id("30")
        self._row(grid, 3, "Frame rate", self.fps)

        self.mic_check = Gtk.CheckButton(label="Record microphone")
        self.mic_check.connect("toggled", self._sync_ui)
        grid.attach(self.mic_check, 0, 4, 1, 1)
        self.mic = Gtk.ComboBoxText()
        self._populate_microphones()
        grid.attach(self.mic, 1, 4, 1, 1)

        self.system_check = Gtk.CheckButton(label="Record system audio")
        self.system_check.connect("toggled", self._sync_ui)
        grid.attach(self.system_check, 0, 5, 1, 1)
        self.system_audio = Gtk.ComboBoxText()
        self._populate_system_audio()
        grid.attach(self.system_audio, 1, 5, 1, 1)

        self.camera_check = Gtk.CheckButton(label="Webcam overlay")
        self.camera_check.connect("toggled", self._sync_ui)
        grid.attach(self.camera_check, 0, 6, 1, 1)
        self.camera = Gtk.ComboBoxText()
        self._populate_cameras()
        grid.attach(self.camera, 1, 6, 1, 1)

        output_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.output = Gtk.FileChooserButton(
            title="Choose output folder",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        self.output.set_filename(str(Path.home() / "Videos"))
        output_box.pack_start(self.output, True, True, 0)
        self._row(grid, 7, "Save to", output_box)

        self.pointer = Gtk.CheckButton(label="Include pointer")
        self.pointer.set_active(True)
        grid.attach(self.pointer, 1, 8, 1, 1)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        root.pack_start(buttons, False, False, 0)
        self.action = Gtk.Button(label="Start recording")
        self.action.get_style_context().add_class("suggested-action")
        self.action.connect("clicked", self._on_action)
        buttons.pack_start(self.action, True, True, 0)
        self.pause_btn = Gtk.Button(label="Pause")
        self.pause_btn.connect("clicked", self._on_pause)
        self.pause_btn.set_sensitive(False)
        buttons.pack_start(self.pause_btn, False, False, 0)

        self.status = Gtk.Label(label="Ready")
        self.status.set_xalign(0)
        self.status.set_line_wrap(True)
        root.pack_start(self.status, False, False, 0)

        self._device_signature = self._make_device_signature(
            self.audio_sources, self.cameras
        )
        self._device_poll_id = GLib.timeout_add_seconds(
            self.DEVICE_POLL_SECONDS, self._poll_devices
        )

        self._sync_ui()
        self.connect("delete-event", self._on_close)

    @staticmethod
    def _row(grid, row, label_text, widget):
        label = Gtk.Label(label=label_text)
        label.set_xalign(0)
        grid.attach(label, 0, row, 1, 1)
        grid.attach(widget, 1, row, 1, 1)

    @staticmethod
    def _make_device_signature(
        audio_sources: Sequence[AudioSource],
        cameras: Sequence[CameraDevice],
    ) -> Tuple[Tuple[Tuple[str, str, bool], ...], Tuple[Tuple[str, str], ...]]:
        audio = tuple(
            (source.name, source.description, source.is_monitor)
            for source in audio_sources
        )
        video = tuple((camera.path, camera.name) for camera in cameras)
        return audio, video

    @staticmethod
    def _replace_combo(
        combo: Gtk.ComboBoxText,
        items: Iterable[Tuple[str, str]],
        preferred_id: Optional[str],
        fallback_id: Optional[str] = None,
    ) -> None:
        values = list(items)
        combo.remove_all()
        ids = []
        for item_id, label in values:
            combo.append(item_id, label)
            ids.append(item_id)

        if preferred_id and preferred_id in ids:
            combo.set_active_id(preferred_id)
        elif fallback_id and fallback_id in ids:
            combo.set_active_id(fallback_id)
        elif ids:
            combo.set_active(0)

    def _populate_microphones(self, preferred_id: Optional[str] = None) -> None:
        microphones = (
            (source.name, source.description)
            for source in self.audio_sources
            if not source.is_monitor
        )
        self._replace_combo(self.mic, microphones, preferred_id)

    def _populate_system_audio(self, preferred_id: Optional[str] = None) -> None:
        monitors = (
            (source.name, source.description)
            for source in self.audio_sources
            if source.is_monitor
        )
        self._replace_combo(
            self.system_audio,
            monitors,
            preferred_id,
            default_monitor_source(self.audio_sources),
        )

    def _populate_cameras(self, preferred_id: Optional[str] = None) -> None:
        cameras = (
            (camera.path, f"{camera.name} ({camera.path})")
            for camera in self.cameras
        )
        self._replace_combo(self.camera, cameras, preferred_id)

    def _poll_devices(self) -> bool:
        if self.recorder.active:
            return True

        new_audio_sources = list_audio_sources()
        new_cameras = list_cameras()
        signature = self._make_device_signature(new_audio_sources, new_cameras)
        if signature == self._device_signature:
            return True

        old_mic = self.mic.get_active_id()
        old_system_audio = self.system_audio.get_active_id()
        old_camera = self.camera.get_active_id()

        self.audio_sources = new_audio_sources
        self.cameras = new_cameras
        self._device_signature = signature

        self._populate_microphones(old_mic)
        self._populate_system_audio(old_system_audio)
        self._populate_cameras(old_camera)

        if not self.cameras and self.camera_check.get_active():
            self.camera_check.set_active(False)

        self.set_status("Audio/video devices updated")
        self._sync_ui()
        return True

    def set_status(self, text: str) -> None:
        GLib.idle_add(self.status.set_text, text)
        GLib.idle_add(self._sync_ui)

    def _sync_ui(self, *_args) -> None:
        mode = self.mode.get_active_id() or "video"
        recording = self.recorder.active
        is_video = mode == "video"
        is_audio = mode == "audio"
        is_shot = mode == "screenshot"

        self.source.set_sensitive(not recording and not is_audio)
        self.quality.set_sensitive(not recording and is_video)
        self.fps.set_sensitive(not recording and is_video)
        self.mic_check.set_sensitive(not recording and not is_shot)
        self.system_check.set_sensitive(not recording and not is_shot)
        self.mic.set_sensitive(
            not recording and self.mic_check.get_active() and not is_shot
        )
        self.system_audio.set_sensitive(
            not recording and self.system_check.get_active() and not is_shot
        )
        self.camera_check.set_sensitive(
            not recording and is_video and bool(self.cameras)
        )
        self.camera.set_sensitive(
            not recording
            and is_video
            and self.camera_check.get_active()
            and bool(self.cameras)
        )
        self.pointer.set_sensitive(not recording and is_video)
        self.pause_btn.set_sensitive(recording)

        if recording:
            self.action.set_label("Stop recording")
        elif is_shot:
            self.action.set_label("Take screenshot")
        else:
            self.action.set_label("Start recording")

    def _config(self) -> RecordingConfig:
        mode = RecordingMode(self.mode.get_active_id() or "video")
        source = CaptureSource(self.source.get_active_id() or "screen")
        output = Path(
            self.output.get_filename() or str(Path.home() / "Videos")
        )
        return RecordingConfig(
            mode=mode,
            source=source,
            quality=QUALITY_PROFILES[self.quality.get_active_id() or "balanced"],
            fps=int(self.fps.get_active_id() or "30"),
            microphone_source=self.mic.get_active_id(),
            system_audio_source=self.system_audio.get_active_id(),
            include_microphone=(
                self.mic_check.get_active()
                and mode != RecordingMode.SCREENSHOT
            ),
            include_system_audio=(
                self.system_check.get_active()
                and mode != RecordingMode.SCREENSHOT
            ),
            include_camera=(
                self.camera_check.get_active()
                and mode == RecordingMode.VIDEO
            ),
            camera_device=self.camera.get_active_id(),
            show_pointer=self.pointer.get_active(),
            output_dir=output,
        )

    def _on_action(self, _button) -> None:
        if self.recorder.active:
            self.recorder.stop()
            return

        # One last refresh immediately before capture so a just-plugged device
        # does not need to wait for the periodic poll.
        self._poll_devices()

        config = self._config()
        if config.mode == RecordingMode.SCREENSHOT:
            self._take_screenshot(config)
            return
        try:
            config.validate()
            config.output_dir.mkdir(parents=True, exist_ok=True)
            stamp = GLib.DateTime.new_now_local().format("%Y-%m-%d_%H-%M-%S")
            if config.mode == RecordingMode.AUDIO:
                path = config.output_dir / f"Audio_{stamp}.ogg"
            else:
                ext = "mp4" if self.cap.has_x264enc else "webm"
                path = config.output_dir / f"Recording_{stamp}.{ext}"
            self.recorder.start(config, path)
            self.paused = False
            self.pause_btn.set_label("Pause")
        except Exception as exc:
            self._show_error(str(exc))
        self._sync_ui()

    def _take_screenshot(self, config: RecordingConfig) -> None:
        if self.portal is None:
            self._show_error("XDG Screenshot Portal is unavailable")
            return
        targets = {
            CaptureSource.SCREEN: 1,
            CaptureSource.WINDOW: 2,
            CaptureSource.AREA: 4,
            CaptureSource.ACTIVE_WINDOW: 8,
        }
        try:
            path = self.portal.screenshot(
                targets[config.source], config.output_dir
            )
            self.set_status(f"Screenshot saved: {path}")
        except (PortalError, Exception) as exc:
            self._show_error(str(exc))

    def _on_pause(self, _button) -> None:
        if not self.recorder.active:
            return
        if self.paused:
            self.recorder.resume()
            self.pause_btn.set_label("Pause")
        else:
            self.recorder.pause()
            self.pause_btn.set_label("Resume")
        self.paused = not self.paused

    def _show_error(self, text: str) -> None:
        self.set_status(text)
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Ubuntu Screen Recorder",
        )
        dialog.format_secondary_text(text)
        dialog.run()
        dialog.destroy()

    def _on_close(self, *_args):
        if getattr(self, "_device_poll_id", None):
            GLib.source_remove(self._device_poll_id)
            self._device_poll_id = None
        self.recorder.force_stop()
        return False


class ScreenRecorderApplication(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="io.github.scientifica007.UbuntuScreenRecorder"
        )

    def do_activate(self):
        window = self.props.active_window or MainWindow(self)
        window.show_all()
        window.present()


def main(argv=None) -> int:
    app = ScreenRecorderApplication()
    return app.run(argv or sys.argv)
