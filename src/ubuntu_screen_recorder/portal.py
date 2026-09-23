import os
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple
from urllib.parse import unquote, urlparse

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

from .portal_policy import screenshot_request_policy


BUS_NAME = "org.freedesktop.portal.Desktop"
OBJECT_PATH = "/org/freedesktop/portal/desktop"
REQUEST_IFACE = "org.freedesktop.portal.Request"
SESSION_IFACE = "org.freedesktop.portal.Session"
SCREENSHOT_IFACE = "org.freedesktop.portal.Screenshot"
SCREENCAST_IFACE = "org.freedesktop.portal.ScreenCast"
PROPERTIES_IFACE = "org.freedesktop.DBus.Properties"


class PortalError(RuntimeError):
    def __init__(
        self,
        message: str,
        code: Optional[int] = None,
        results: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.results = results or {}


def _unwrap(value):
    return value.unpack() if isinstance(value, GLib.Variant) else value


class PortalClient:
    def __init__(self) -> None:
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    def _request_path(self, token: str) -> str:
        sender = self.bus.get_unique_name().lstrip(":").replace(".", "_")
        return f"/org/freedesktop/portal/desktop/request/{sender}/{token}"

    def _request(
        self,
        interface: str,
        method: str,
        parameters: GLib.Variant,
        token: str,
    ) -> Dict[str, Any]:
        loop = GLib.MainLoop()
        response: Dict[str, Any] = {}
        request_path = self._request_path(token)

        def on_response(
            _conn, _sender, _path, _iface, _signal, params, _user_data=None
        ):
            code, results = params.unpack()
            response["code"] = int(code)
            response["results"] = results
            if loop.is_running():
                loop.quit()

        subscription = self.bus.signal_subscribe(
            BUS_NAME,
            REQUEST_IFACE,
            "Response",
            request_path,
            None,
            Gio.DBusSignalFlags.NONE,
            on_response,
        )
        try:
            returned = self.bus.call_sync(
                BUS_NAME,
                OBJECT_PATH,
                interface,
                method,
                parameters,
                GLib.VariantType.new("(o)"),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
            actual_path = returned.unpack()[0]
            if actual_path != request_path:
                self.bus.signal_unsubscribe(subscription)
                subscription = self.bus.signal_subscribe(
                    BUS_NAME,
                    REQUEST_IFACE,
                    "Response",
                    actual_path,
                    None,
                    Gio.DBusSignalFlags.NONE,
                    on_response,
                )
            loop.run()
        finally:
            self.bus.signal_unsubscribe(subscription)

        if response.get("code") != 0:
            raise PortalError(
                f"Portal request {method} was cancelled or failed "
                f"(code={response.get('code')})",
                code=response.get("code"),
                results=response.get("results", {}),
            )
        return response.get("results", {})

    def _property(
        self,
        interface: str,
        name: str,
        default: Any = None,
    ) -> Any:
        try:
            result = self.bus.call_sync(
                BUS_NAME,
                OBJECT_PATH,
                PROPERTIES_IFACE,
                "Get",
                GLib.Variant("(ss)", (interface, name)),
                GLib.VariantType.new("(v)"),
                Gio.DBusCallFlags.NONE,
                2000,
                None,
            )
        except GLib.Error:
            return default

        value = result.unpack()[0]
        return _unwrap(value)

    def screenshot_capabilities(self) -> Tuple[int, int]:
        version = int(
            self._property(SCREENSHOT_IFACE, "version", 0) or 0
        )
        targets = int(
            self._property(
                SCREENSHOT_IFACE,
                "AvailableTargets",
                0,
            )
            or 0
        )
        return version, targets

    @staticmethod
    def _screenshot_options(
        token: str,
        target: int,
        version: int,
        available_targets: int,
    ) -> Tuple[Dict[str, GLib.Variant], bool]:
        targeted, interactive = screenshot_request_policy(
            target,
            version,
            available_targets,
        )
        options: Dict[str, GLib.Variant] = {
            "handle_token": GLib.Variant("s", token),
            "interactive": GLib.Variant(
                "b", interactive
            ),
        }
        if targeted:
            options["target"] = GLib.Variant("u", target)
        return options, targeted

    def screenshot(self, target: int, destination_dir: Path) -> Path:
        version, available_targets = self.screenshot_capabilities()
        token = (
            f"shot_{os.getpid()}_{GLib.get_monotonic_time()}"
            .replace("-", "_")
        )
        options, targeted = self._screenshot_options(
            token,
            target,
            version,
            available_targets,
        )

        print(
            "Screenshot portal: "
            f"version={version}, "
            f"available-targets=0x{available_targets:x}, "
            f"requested={target}, targeted={targeted}",
            flush=True,
        )

        try:
            results = self._request(
                SCREENSHOT_IFACE,
                "Screenshot",
                GLib.Variant("(sa{sv})", ("", options)),
                token,
            )
        except PortalError as exc:
            # Some backends can still return a usable URI with a
            # non-zero response after the screenshot was actually
            # produced. Preserve that result instead of discarding it.
            if exc.results.get("uri"):
                results = exc.results
            elif targeted:
                # Compatibility fallback for older/misreporting portal
                # backends: omit the v3 target key and let the
                # interactive screenshot UI choose the target.
                retry_token = (
                    f"shot_retry_{os.getpid()}_"
                    f"{GLib.get_monotonic_time()}"
                ).replace("-", "_")
                retry_options = {
                    "handle_token": GLib.Variant(
                        "s", retry_token
                    ),
                    "interactive": GLib.Variant("b", True),
                }
                results = self._request(
                    SCREENSHOT_IFACE,
                    "Screenshot",
                    GLib.Variant(
                        "(sa{sv})", ("", retry_options)
                    ),
                    retry_token,
                )
            else:
                raise
        uri = results.get("uri")
        if not uri:
            raise PortalError("Screenshot portal returned no URI")
        parsed = urlparse(uri)
        if parsed.scheme != "file":
            raise PortalError(f"Unsupported screenshot URI: {uri}")
        source = Path(unquote(parsed.path))
        destination_dir.mkdir(parents=True, exist_ok=True)
        stamp = GLib.DateTime.new_now_local().format("%Y-%m-%d_%H-%M-%S")
        target_path = destination_dir / f"Screenshot_{stamp}.png"
        if source.resolve() != target_path.resolve():
            shutil.copy2(source, target_path)
        return target_path

    def create_screencast(
        self, source_types: int = 3, cursor_mode: int = 2
    ) -> Tuple[str, int, int, Optional[int]]:
        create_token = (
            f"create_{os.getpid()}_{GLib.get_monotonic_time()}"
            .replace("-", "_")
        )
        session_token = (
            f"session_{os.getpid()}_{GLib.get_monotonic_time()}"
            .replace("-", "_")
        )
        create_options = {
            "handle_token": GLib.Variant("s", create_token),
            "session_handle_token": GLib.Variant("s", session_token),
        }
        created = self._request(
            SCREENCAST_IFACE,
            "CreateSession",
            GLib.Variant("(a{sv})", (create_options,)),
            create_token,
        )
        session_handle = _unwrap(created.get("session_handle"))
        if not session_handle:
            raise PortalError("ScreenCast portal returned no session handle")

        select_token = (
            f"select_{os.getpid()}_{GLib.get_monotonic_time()}"
            .replace("-", "_")
        )
        select_options = {
            "handle_token": GLib.Variant("s", select_token),
            "types": GLib.Variant("u", source_types),
            "multiple": GLib.Variant("b", False),
            "cursor_mode": GLib.Variant("u", cursor_mode),
        }
        self._request(
            SCREENCAST_IFACE,
            "SelectSources",
            GLib.Variant("(oa{sv})", (session_handle, select_options)),
            select_token,
        )

        start_token = (
            f"start_{os.getpid()}_{GLib.get_monotonic_time()}"
            .replace("-", "_")
        )
        start_options = {"handle_token": GLib.Variant("s", start_token)}
        started = self._request(
            SCREENCAST_IFACE,
            "Start",
            GLib.Variant(
                "(osa{sv})", (session_handle, "", start_options)
            ),
            start_token,
        )
        streams = _unwrap(started.get("streams")) or []
        if not streams:
            raise PortalError("ScreenCast portal returned no streams")

        node_id, props = streams[0]
        node_id = int(_unwrap(node_id))
        props = _unwrap(props) or {}

        serial_value = props.get("pipewire-serial")
        serial_value = (
            _unwrap(serial_value) if serial_value is not None else None
        )
        pipewire_serial = (
            int(serial_value) if serial_value is not None else None
        )

        fd = self._open_pipewire_remote(session_handle)
        return session_handle, fd, node_id, pipewire_serial

    def _open_pipewire_remote(self, session_handle: str) -> int:
        params = GLib.Variant("(oa{sv})", (session_handle, {}))
        result, out_fds = self.bus.call_with_unix_fd_list_sync(
            BUS_NAME,
            OBJECT_PATH,
            SCREENCAST_IFACE,
            "OpenPipeWireRemote",
            params,
            GLib.VariantType.new("(h)"),
            Gio.DBusCallFlags.NONE,
            -1,
            None,
            None,
        )
        index = result.unpack()[0]
        return out_fds.get(index)

    def watch_session_closed(
        self,
        session_handle: str,
        callback: Callable[[], None],
    ) -> int:
        def on_closed(
            _conn,
            _sender,
            _path,
            _iface,
            _signal,
            _params,
            _user_data=None,
        ):
            callback()

        return self.bus.signal_subscribe(
            BUS_NAME,
            SESSION_IFACE,
            "Closed",
            session_handle,
            None,
            Gio.DBusSignalFlags.NONE,
            on_closed,
        )

    def unwatch_session(self, subscription_id: int) -> None:
        if subscription_id:
            self.bus.signal_unsubscribe(subscription_id)

    def close_session(self, session_handle: Optional[str]) -> None:
        if not session_handle:
            return
        try:
            self.bus.call_sync(
                BUS_NAME,
                session_handle,
                SESSION_IFACE,
                "Close",
                None,
                None,
                Gio.DBusCallFlags.NONE,
                2000,
                None,
            )
        except GLib.Error:
            pass
