import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

import gi

# Pin both GTK and GDK to the same major version before importing either
# namespace. On Ubuntu systems that also provide GTK/GDK 4, importing Gdk
# without an explicit version can load Gdk 4 first, after which Gtk 3 cannot
# require Gdk 3 and the application aborts during startup.
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

from .geometry import normalized_crop_from_selection
from .models import CaptureSource, QUALITY_PROFILES, RecordingConfig, RecordingMode
from .portal import PortalClient, PortalError
from .portal_policy import portal_request_was_cancelled
from .pipeline import PortalStream
from .recorder import Recorder
from .system_probe import (
    AudioSource,
    CameraDevice,
    default_monitor_source,
    list_audio_sources,
    list_cameras,
    probe_capabilities,
)


APP_NAME = "Troika D"
APP_ID = "io.github.scientifica007.TroikaD"
APP_ICON_NAME = APP_ID


class AreaSelectionWindow(Gtk.Window):
    MIN_SELECTION = 20

    def __init__(
        self,
        monitor_index: int,
        preview_pixbuf: GdkPixbuf.Pixbuf,
        selected_cb,
        cancelled_cb,
    ):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.preview_pixbuf = preview_pixbuf
        self.selected_cb = selected_cb
        self.cancelled_cb = cancelled_cb
        self.start_point = None
        self.current_point = None
        self.dragging = False
        self._finished = False
        self._scaled_preview = None
        self._scaled_size = (0, 0)

        self.set_title("Select recording area")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_can_focus(True)
        self.set_accept_focus(True)

        # Render the captured preview on a dedicated DrawingArea instead of
        # directly on the toplevel Gtk.Window. On the tested Ubuntu/GNOME
        # stack the window theme could repaint the toplevel after our draw
        # handler, leaving a fully white selector even though the captured
        # RGB frame contained real desktop pixels.
        self.canvas = Gtk.DrawingArea()
        self.canvas.set_can_focus(True)
        self.canvas.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
        )
        self.canvas.connect("draw", self._on_draw)
        self.canvas.connect("button-press-event", self._on_press)
        self.canvas.connect("button-release-event", self._on_release)
        self.canvas.connect("motion-notify-event", self._on_motion)
        self.add(self.canvas)

        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect("key-press-event", self._on_key)
        self.connect("delete-event", self._on_delete)

        screen = self.get_screen()
        try:
            self.fullscreen_on_monitor(screen, monitor_index)
        except Exception:
            self.fullscreen()

    def _rectangle(self):
        if self.start_point is None or self.current_point is None:
            return None
        x1, y1 = self.start_point
        x2, y2 = self.current_point
        return (
            min(x1, x2),
            min(y1, y2),
            abs(x2 - x1),
            abs(y2 - y1),
        )

    def _preview_for_allocation(self, width: int, height: int):
        size = (max(1, width), max(1, height))
        if self._scaled_preview is None or self._scaled_size != size:
            self._scaled_preview = self.preview_pixbuf.scale_simple(
                size[0],
                size[1],
                GdkPixbuf.InterpType.BILINEAR,
            )
            self._scaled_size = size
        return self._scaled_preview

    @staticmethod
    def _paint_preview(cr, pixbuf) -> None:
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
        cr.paint()

    def _on_draw(self, widget, cr):
        allocation = widget.get_allocation()
        preview = self._preview_for_allocation(
            allocation.width,
            allocation.height,
        )

        # The selector is deliberately opaque. Its background is a static
        # frame from the authorized PipeWire stream, so it does not depend
        # on compositor support for transparent fullscreen GTK windows.
        self._paint_preview(cr, preview)

        cr.set_source_rgba(0.0, 0.0, 0.0, 0.30)
        cr.rectangle(0, 0, allocation.width, allocation.height)
        cr.fill()

        rect = self._rectangle()
        if rect is not None:
            x, y, width, height = rect
            cr.save()
            cr.rectangle(x, y, width, height)
            cr.clip()
            self._paint_preview(cr, preview)
            cr.restore()

            cr.set_source_rgba(1.0, 1.0, 1.0, 0.95)
            cr.rectangle(x, y, width, height)
            cr.set_line_width(2.0)
            cr.stroke()

        cr.set_source_rgba(0.0, 0.0, 0.0, 0.66)
        cr.rectangle(18, 14, 520, 42)
        cr.fill()
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        cr.select_font_face("Sans", 0, 1)
        cr.set_font_size(20)
        cr.move_to(30, 42)
        cr.show_text(
            "Drag to select the recording area — Esc to cancel"
        )
        return False

    def _on_press(self, _widget, event):
        if event.button != 1:
            return False
        self.start_point = (event.x, event.y)
        self.current_point = self.start_point
        self.dragging = True
        self.canvas.queue_draw()
        return True

    def _on_motion(self, _widget, event):
        if not self.dragging:
            return False
        self.current_point = (event.x, event.y)
        self.canvas.queue_draw()
        return True

    def _on_release(self, _widget, event):
        if event.button != 1 or not self.dragging:
            return False
        self.current_point = (event.x, event.y)
        self.dragging = False
        rect = self._rectangle()
        self.canvas.queue_draw()
        if rect is None:
            return True

        x, y, width, height = rect
        if width < self.MIN_SELECTION or height < self.MIN_SELECTION:
            return True

        allocation = self.canvas.get_allocation()
        self._finished = True
        self.hide()
        self.destroy()
        self.selected_cb(
            x,
            y,
            width,
            height,
            allocation.width,
            allocation.height,
        )
        return True

    def _cancel(self):
        if self._finished:
            return
        self._finished = True
        self.hide()
        self.destroy()
        self.cancelled_cb()

    def _on_key(self, _widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self._cancel()
            return True
        return False

    def _on_delete(self, *_args):
        self._cancel()
        return True

class MainWindow(Gtk.ApplicationWindow):
    DEVICE_POLL_SECONDS = 2

    def __init__(self, application: Gtk.Application):
        super().__init__(application=application, title=APP_NAME)
        self.set_default_size(620, 560)
        self.set_icon_name(APP_ICON_NAME)
        self.set_border_width(18)

        self.cap = probe_capabilities()
        self.audio_sources = list_audio_sources()
        self.cameras = list_cameras()
        self.recorder = Recorder(self.cap, self.set_status)
        self.portal = PortalClient() if self.cap.has_portal else None
        if self.portal is not None:
            (
                self.screenshot_portal_version,
                self.screenshot_available_targets,
            ) = self.portal.screenshot_capabilities()
        else:
            self.screenshot_portal_version = 0
            self.screenshot_available_targets = 0
        self.paused = False
        self._closing_after_recording = False
        self._area_selecting = False
        self._area_selector = None
        self._pending_area_config = None

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.add(root)

        title = Gtk.Label()
        title.set_markup(f"<span size='x-large' weight='bold'>{APP_NAME}</span>")
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
        self.mode.connect("changed", self._on_mode_changed)
        self._row(grid, 0, "Mode", self.mode)

        self.source = Gtk.ComboBoxText()
        self._populate_sources("video")
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

    def _populate_sources(
        self,
        mode: str,
        preferred_id: Optional[str] = None,
    ) -> None:
        if mode == "screenshot":
            if (
                self.screenshot_portal_version >= 3
                and self.screenshot_available_targets
            ):
                candidates = (
                    ("screen", "Full screen", 1),
                    ("window", "Window", 2),
                    ("area", "Area", 4),
                    ("active-window", "Active window", 8),
                )
                items = tuple(
                    (key, label)
                    for key, label, bit in candidates
                    if self.screenshot_available_targets & bit
                )
            else:
                items = (
                    (
                        "screen",
                        "Interactive screenshot (system)",
                    ),
                )
        elif mode == "video":
            # ScreenCast portal exposes monitor/window/virtual,
            # not a distinct active-window source. Do not present
            # Active window as if it were semantically different.
            items = (
                ("screen", "Full screen"),
                ("window", "Window"),
                ("area", "Area"),
            )
        else:
            items = (("screen", "Full screen"),)

        self._replace_combo(
            self.source,
            items,
            preferred_id,
            "screen",
        )

    def _on_mode_changed(self, *_args) -> None:
        mode = self.mode.get_active_id() or "video"
        preferred = self.source.get_active_id()
        self._populate_sources(mode, preferred)
        self._sync_ui()

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
        preparing_area = (
            self._area_selecting or self.recorder.preparing
        )
        locked = recording or preparing_area
        is_video = mode == "video"
        is_audio = mode == "audio"
        is_shot = mode == "screenshot"

        self.source.set_sensitive(not locked and not is_audio)
        self.quality.set_sensitive(not locked and is_video)
        self.fps.set_sensitive(not locked and is_video)
        self.mic_check.set_sensitive(not locked and not is_shot)
        self.system_check.set_sensitive(not locked and not is_shot)
        self.mic.set_sensitive(
            not locked and self.mic_check.get_active() and not is_shot
        )
        self.system_audio.set_sensitive(
            not locked and self.system_check.get_active() and not is_shot
        )
        self.camera_check.set_sensitive(
            not locked and is_video and bool(self.cameras)
        )
        self.camera.set_sensitive(
            not locked
            and is_video
            and self.camera_check.get_active()
            and bool(self.cameras)
        )
        self.pointer.set_sensitive(not locked and is_video)
        legacy_screenshot = (
            is_shot
            and self.screenshot_portal_version < 3
        )
        self.output.set_sensitive(
            not locked and not legacy_screenshot
        )
        self.pause_btn.set_sensitive(recording)
        self.action.set_sensitive(not preparing_area or recording)

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

        if (
            config.mode == RecordingMode.VIDEO
            and config.source == CaptureSource.AREA
            and self.cap.session_type == "wayland"
        ):
            self._begin_area_capture(config)
            return

        try:
            config.validate()
            path = self._recording_output_path(config)
            self.recorder.start(config, path)
            self.paused = False
            self.pause_btn.set_label("Pause")
        except Exception as exc:
            if (
                isinstance(exc, PortalError)
                and portal_request_was_cancelled(exc.code)
            ):
                self.set_status("Screen selection cancelled")
            else:
                self._show_error(str(exc))
        self._sync_ui()

    def _recording_output_path(
        self,
        config: RecordingConfig,
    ) -> Path:
        config.output_dir.mkdir(parents=True, exist_ok=True)
        stamp = GLib.DateTime.new_now_local().format(
            "%Y-%m-%d_%H-%M-%S"
        )
        if config.mode == RecordingMode.AUDIO:
            return config.output_dir / f"Audio_{stamp}.ogg"
        ext = "mp4" if self.cap.has_x264enc else "webm"
        return config.output_dir / f"Recording_{stamp}.{ext}"

    def _monitor_for_stream(
        self,
        stream: PortalStream,
    ) -> int:
        screen = self.get_screen()
        count = screen.get_n_monitors()
        if count <= 1:
            return 0

        if stream.position is not None:
            px, py = stream.position
            if stream.size is not None:
                sw, sh = stream.size
                px += sw // 2
                py += sh // 2

            for index in range(count):
                geometry = screen.get_monitor_geometry(index)
                if (
                    geometry.x <= px < geometry.x + geometry.width
                    and geometry.y <= py < geometry.y + geometry.height
                ):
                    return index

        window = self.get_window()
        if window is not None:
            try:
                return screen.get_monitor_at_window(window)
            except Exception:
                pass

        primary = screen.get_primary_monitor()
        return primary if primary >= 0 else 0

    def _begin_area_capture(
        self,
        config: RecordingConfig,
    ) -> None:
        self._area_selecting = True
        self._pending_area_config = config
        self._sync_ui()
        try:
            config.validate()
            stream = self.recorder.prepare_area_capture(config)
            monitor = self._monitor_for_stream(stream)
            self.set_status("Preparing area preview…")
            self.hide()
            # Let the compositor remove this window from the monitor before
            # grabbing the static preview frame.
            GLib.timeout_add(
                300,
                self._show_area_selector,
                stream,
                monitor,
            )
        except Exception as exc:
            self._area_selecting = False
            self._pending_area_config = None
            self._area_selector = None
            if self.recorder.preparing:
                self.recorder.cancel_prepared_capture()
            self.show_all()
            self.present()
            if (
                isinstance(exc, PortalError)
                and portal_request_was_cancelled(exc.code)
            ):
                self.set_status("Screen selection cancelled")
            else:
                self._show_error(str(exc))
            self._sync_ui()

    def _show_area_selector(
        self,
        stream: PortalStream,
        monitor: int,
    ) -> bool:
        try:
            frame = self.recorder.capture_area_preview(stream)
            bytes_value = GLib.Bytes.new(frame.data)
            pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
                bytes_value,
                GdkPixbuf.Colorspace.RGB,
                False,
                8,
                frame.width,
                frame.height,
                frame.rowstride,
            )
            self.set_status(
                "Drag to select the recording area — Esc cancels"
            )
            selector = AreaSelectionWindow(
                monitor,
                pixbuf,
                self._on_area_selected,
                self._on_area_cancelled,
            )
            self._area_selector = selector
            selector.show_all()
            selector.present()
            selector.canvas.grab_focus()
        except Exception as exc:
            self._area_selecting = False
            self._pending_area_config = None
            self._area_selector = None
            if self.recorder.preparing:
                self.recorder.cancel_prepared_capture()
            self.show_all()
            self.present()
            self._show_error(str(exc))
            self._sync_ui()
        return False

    def _on_area_selected(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        canvas_width: int,
        canvas_height: int,
    ) -> None:
        config = self._pending_area_config
        self._area_selector = None
        if config is None:
            self._area_selecting = False
            if self.recorder.preparing:
                self.recorder.cancel_prepared_capture()
            self.show_all()
            self.present()
            return

        try:
            config.crop = normalized_crop_from_selection(
                x,
                y,
                width,
                height,
                canvas_width,
                canvas_height,
            )
            path = self._recording_output_path(config)
            self._area_selecting = False
            self._pending_area_config = None
            self.recorder.start(config, path)
            self.paused = False
            self.pause_btn.set_label("Pause")
            self.show_all()
            self.present()
        except Exception as exc:
            self._area_selecting = False
            self._pending_area_config = None
            if self.recorder.preparing:
                self.recorder.cancel_prepared_capture()
            self.show_all()
            self.present()
            self._show_error(str(exc))
        self._sync_ui()

    def _on_area_cancelled(self) -> None:
        self._area_selector = None
        self._area_selecting = False
        self._pending_area_config = None
        if self.recorder.preparing:
            self.recorder.cancel_prepared_capture()
        self.show_all()
        self.present()
        self.set_status("Area selection cancelled")
        self._sync_ui()

    def _take_screenshot(self, config: RecordingConfig) -> None:
        if self.portal is None:
            self._show_error("XDG Screenshot Portal is unavailable")
            return

        # Hide the recorder itself before asking the compositor for a
        # screenshot. This makes full-screen screenshots practical and
        # prevents our own UI from being forced into the captured image.
        self.set_status("Preparing screenshot…")
        self.hide()
        GLib.timeout_add(
            400,
            self._perform_screenshot,
            config,
        )

    def _perform_screenshot(
        self,
        config: RecordingConfig,
    ) -> bool:
        targets = {
            CaptureSource.SCREEN: 1,
            CaptureSource.WINDOW: 2,
            CaptureSource.AREA: 4,
            CaptureSource.ACTIVE_WINDOW: 8,
        }
        path = None
        error = None
        try:
            config.output_dir.mkdir(
                parents=True,
                exist_ok=True,
            )
            path = self.portal.screenshot(
                targets[config.source],
                config.output_dir,
            )
        except Exception as exc:
            error = exc
        finally:
            self.show_all()
            self.present()

        if error is not None:
            self._show_error(str(error))
        elif path is not None:
            self.set_status(
                f"Screenshot saved: {path}"
            )
        else:
            self.set_status(
                "Screenshot handled by the system tool"
            )
        return False

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
            text=APP_NAME,
        )
        dialog.format_secondary_text(text)
        dialog.run()
        dialog.destroy()

    def _remove_device_poll(self) -> None:
        if getattr(self, "_device_poll_id", None):
            GLib.source_remove(self._device_poll_id)
            self._device_poll_id = None

    def _finish_close_when_inactive(self) -> bool:
        if self.recorder.active:
            return True
        self._remove_device_poll()
        self._closing_after_recording = False
        self.destroy()
        return False

    def _on_close(self, *_args):
        if self.recorder.active:
            if not self._closing_after_recording:
                self._closing_after_recording = True
                self.set_status(
                    "Finalizing recording before exit…"
                )
                self.recorder.stop()
                GLib.timeout_add(
                    100,
                    self._finish_close_when_inactive,
                )
            return True

        self._remove_device_poll()
        return False


class ScreenRecorderApplication(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID
        )

    def do_activate(self):
        window = self.props.active_window or MainWindow(self)
        window.show_all()
        window.present()


def main(argv=None) -> int:
    app = ScreenRecorderApplication()
    return app.run(argv or sys.argv)
