import fcntl
import glob
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


VIDIOC_QUERYCAP = 0x80685600
V4L2_CAP_VIDEO_CAPTURE = 0x00000001
V4L2_CAP_VIDEO_CAPTURE_MPLANE = 0x00001000
V4L2_CAP_DEVICE_CAPS = 0x80000000
V4L2_CAPABILITY_STRUCT_SIZE = 104


@dataclass(frozen=True)
class AudioSource:
    name: str
    description: str
    is_monitor: bool


@dataclass(frozen=True)
class CameraDevice:
    path: str
    name: str


@dataclass(frozen=True)
class SystemCapabilities:
    session_type: str
    has_pactl: bool
    has_portal: bool
    has_gstreamer: bool
    has_ximagesrc: bool
    has_pipewiresrc: bool
    has_x264enc: bool
    has_vp8enc: bool


def session_type() -> str:
    value = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
    if value in {"x11", "wayland"}:
        return value
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return value or "unknown"


def _run(*args: str) -> str:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, check=False, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout if proc.returncode == 0 else ""


def _audio_sources_json() -> List[AudioSource]:
    output = _run("pactl", "--format=json", "list", "sources")
    if not output:
        return []
    try:
        payload = json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return []

    sources: List[AudioSource] = []
    for item in payload:
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        properties = item.get("properties") or {}
        description = (
            item.get("description")
            or properties.get("device.description")
            or properties.get("device.product.name")
            or name
        )
        monitor_of_sink = item.get("monitor_of_sink")
        is_monitor = (
            monitor_of_sink not in (None, "", False)
            or name.endswith(".monitor")
            or properties.get("device.class") == "monitor"
        )
        sources.append(
            AudioSource(
                name=name,
                description=str(description),
                is_monitor=is_monitor,
            )
        )
    return sources


def list_audio_sources() -> List[AudioSource]:
    if not shutil.which("pactl"):
        return []

    sources = _audio_sources_json()
    if sources:
        return sources

    output = _run("pactl", "list", "short", "sources")
    fallback: List[AudioSource] = []
    for line in output.splitlines():
        cols = line.split("\t")
        if len(cols) < 2:
            cols = line.split()
        if len(cols) < 2:
            continue
        name = cols[1]
        fallback.append(
            AudioSource(
                name=name,
                description=name,
                is_monitor=name.endswith(".monitor"),
            )
        )
    return fallback


def default_monitor_source(sources: List[AudioSource]) -> Optional[str]:
    if not sources:
        return None
    sink = _run("pactl", "get-default-sink").strip()
    if not sink:
        info = _run("pactl", "info")
        for line in info.splitlines():
            if line.lower().startswith("default sink:"):
                sink = line.split(":", 1)[1].strip()
                break
    if sink:
        candidate = f"{sink}.monitor"
        for source in sources:
            if source.name == candidate:
                return candidate
    for source in sources:
        if source.is_monitor:
            return source.name
    return None


def _is_video_capture_caps(capabilities: int, device_caps: int) -> bool:
    effective = (
        device_caps
        if capabilities & V4L2_CAP_DEVICE_CAPS
        else capabilities
    )
    return bool(
        effective
        & (V4L2_CAP_VIDEO_CAPTURE | V4L2_CAP_VIDEO_CAPTURE_MPLANE)
    )


def _is_capture_device(path: str) -> Optional[bool]:
    """Return True/False when V4L2 capabilities can be queried, else None.

    Querying VIDIOC_QUERYCAP does not start the camera stream or turn on its LED.
    Unknown devices remain visible for compatibility; known non-capture nodes
    (for example metadata-only UVC nodes) are filtered out.
    """
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
    except OSError:
        return None

    try:
        buffer = bytearray(V4L2_CAPABILITY_STRUCT_SIZE)
        fcntl.ioctl(fd, VIDIOC_QUERYCAP, buffer, True)
        capabilities = int.from_bytes(buffer[84:88], sys.byteorder)
        device_caps = int.from_bytes(buffer[88:92], sys.byteorder)
        return _is_video_capture_caps(capabilities, device_caps)
    except OSError:
        return None
    finally:
        os.close(fd)


def list_cameras() -> List[CameraDevice]:
    result: List[CameraDevice] = []
    for path in sorted(glob.glob("/dev/video*")):
        is_capture = _is_capture_device(path)
        if is_capture is False:
            continue

        base = Path(path).name
        name_file = Path("/sys/class/video4linux") / base / "name"
        try:
            name = name_file.read_text(encoding="utf-8").strip()
        except OSError:
            name = base
        result.append(CameraDevice(path=path, name=name))
    return result


def _gst_element_exists(name: str) -> bool:
    if not shutil.which("gst-inspect-1.0"):
        return False
    try:
        proc = subprocess.run(
            ["gst-inspect-1.0", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def portal_available() -> bool:
    return bool(os.environ.get("DBUS_SESSION_BUS_ADDRESS")) and shutil.which("gdbus") is not None


def probe_capabilities() -> SystemCapabilities:
    return SystemCapabilities(
        session_type=session_type(),
        has_pactl=shutil.which("pactl") is not None,
        has_portal=portal_available(),
        has_gstreamer=shutil.which("gst-launch-1.0") is not None,
        has_ximagesrc=_gst_element_exists("ximagesrc"),
        has_pipewiresrc=_gst_element_exists("pipewiresrc"),
        has_x264enc=_gst_element_exists("x264enc"),
        has_vp8enc=_gst_element_exists("vp8enc"),
    )
