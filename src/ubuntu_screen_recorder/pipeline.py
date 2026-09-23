from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .models import RecordingConfig, RecordingMode


AUDIO_BUFFER_US = 500_000
AUDIO_LATENCY_US = 20_000
AUDIO_QUEUE_NS = 3_000_000_000
AUDIO_MIXER_LATENCY_MS = 100
VIDEO_CAPTURE_QUEUE_NS = 1_000_000_000
VIDEO_MUX_QUEUE_NS = 3_000_000_000

ROBUST_MP4_MAX_DURATION_NS = 86_400_000_000_000
ROBUST_MP4_UPDATE_PERIOD_NS = 1_000_000_000


@dataclass(frozen=True)
class PortalStream:
    fd: int
    node_id: int
    pipewire_serial: Optional[int] = None


@dataclass(frozen=True)
class PipelinePlan:
    description: str
    extension: str
    encoder: str


def _q(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _queue(name: str, max_time_ns: int, leaky: Optional[str] = None) -> str:
    value = (
        f"queue name={name} max-size-buffers=0 max-size-bytes=0 "
        f"max-size-time={max_time_ns}"
    )
    if leaky:
        value += f" leaky={leaky}"
    return value


def _audio_source(device: str, queue_name: str) -> str:
    source_name = (
        "mic_src"
        if queue_name == "mic_capture_q"
        else "system_audio_src"
    )
    return (
        f"pulsesrc name={source_name} device={_q(device)} "
        f"buffer-time={AUDIO_BUFFER_US} latency-time={AUDIO_LATENCY_US} "
        "provide-clock=false slave-method=resample ! "
        "audioconvert ! audioresample ! audio/x-raw,rate=48000 ! "
        f"{_queue(queue_name, AUDIO_QUEUE_NS)}"
    )


def _enabled_audio_sources(config: RecordingConfig) -> List[Tuple[str, str]]:
    sources: List[Tuple[str, str]] = []
    if config.include_microphone:
        sources.append((config.microphone_source or "", "mic_capture_q"))
    if config.include_system_audio:
        sources.append(
            (config.system_audio_source or "", "system_capture_q")
        )
    return sources


def _audio_chain(
    config: RecordingConfig, encoder: str, sink_target: str
) -> str:
    sources = _enabled_audio_sources(config)
    if not sources:
        return ""

    mux_queue = _queue("audio_mux_q", AUDIO_QUEUE_NS)

    if len(sources) == 1:
        device, queue_name = sources[0]
        return (
            f"{_audio_source(device, queue_name)} ! "
            f"{encoder} ! {mux_queue} ! {sink_target} "
        )

    branches = " ".join(
        f"{_audio_source(device, queue_name)} ! amix."
        for device, queue_name in sources
    )
    return (
        f"{branches} "
        f"audiomixer name=amix latency={AUDIO_MIXER_LATENCY_MS} ! "
        "audioconvert ! audioresample ! audio/x-raw,rate=48000 ! "
        f"{encoder} ! {mux_queue} ! {sink_target} "
    )


def choose_video_encoder(
    has_x264: bool,
    has_vp8: bool,
    bitrate_kbps: int,
    speed: str,
):
    if has_x264:
        robust_mux = (
            "mp4mux name=mux "
            f"reserved-max-duration={ROBUST_MP4_MAX_DURATION_NS} "
            f"reserved-moov-update-period={ROBUST_MP4_UPDATE_PERIOD_NS}"
        )
        return (
            f"x264enc bitrate={bitrate_kbps} speed-preset={speed} "
            "tune=zerolatency key-int-max=60",
            "h264parse",
            robust_mux,
            "mp4",
            "x264/H.264",
        )
    if has_vp8:
        return (
            f"vp8enc target-bitrate={bitrate_kbps * 1000} "
            "deadline=1 cpu-used=8",
            "identity",
            "webmmux name=mux",
            "webm",
            "VP8",
        )
    raise RuntimeError(
        "No supported video encoder found (need x264enc or vp8enc)"
    )


def build_audio_only_pipeline(
    config: RecordingConfig, output_path: Path
) -> PipelinePlan:
    if not _enabled_audio_sources(config):
        raise ValueError(
            "Audio-only recording requires at least one source"
        )

    desc = _audio_chain(
        config,
        "opusenc bitrate=128000",
        f"oggmux ! filesink location={_q(str(output_path))}",
    )
    return PipelinePlan(desc, "ogg", "Opus")


def _wayland_video_source(stream: PortalStream) -> str:
    if stream.pipewire_serial is not None:
        selector = f"target-object={_q(str(stream.pipewire_serial))}"
    else:
        selector = f"path={_q(str(stream.node_id))}"
    return (
        f"pipewiresrc name=screen_src fd={stream.fd} "
        f"{selector} do-timestamp=true"
    )


def build_video_pipeline(
    config: RecordingConfig,
    output_path: Path,
    session_type: str,
    has_x264: bool,
    has_vp8: bool,
    portal_stream: Optional[PortalStream] = None,
) -> PipelinePlan:
    enc, parser, muxer, extension, encoder_label = choose_video_encoder(
        has_x264,
        has_vp8,
        config.quality.video_bitrate_kbps,
        config.quality.x264_speed_preset,
    )

    if session_type == "wayland":
        if portal_stream is None:
            raise ValueError(
                "Wayland video recording needs a portal PipeWire stream"
            )
        video_src = _wayland_video_source(portal_stream)
    else:
        video_src = (
            "ximagesrc name=screen_src use-damage=true "
            f"show-pointer={'true' if config.show_pointer else 'false'}"
        )

    video_chain = (
        f"{video_src} ! "
        f"{_queue('video_capture_q', VIDEO_CAPTURE_QUEUE_NS, 'downstream')} ! "
        "videoconvert ! videorate ! "
        f"video/x-raw,framerate={config.fps}/1 ! videoscale ! "
    )
    if config.quality.scale_percent != 100:
        video_chain += "videoconvert ! "

    video_mux_queue = _queue("video_mux_q", VIDEO_MUX_QUEUE_NS)

    if config.include_camera:
        screen_branch = video_chain + "queue ! comp.sink_0 "
        cam_branch = (
            f"v4l2src name=camera_src "
            f"device={_q(config.camera_device or '')} ! "
            f"{_queue('camera_capture_q', VIDEO_CAPTURE_QUEUE_NS, 'downstream')} ! "
            "videoconvert ! videoscale ! "
            "video/x-raw,width=320,height=180 ! queue ! comp.sink_1 "
        )
        main_video = (
            screen_branch
            + cam_branch
            + "compositor name=comp sink_1::xpos=20 "
            "sink_1::ypos=20 ! videoconvert ! "
            + f"{enc} ! {parser} ! {video_mux_queue} ! mux. "
        )
    else:
        main_video = (
            video_chain
            + f"{enc} ! {parser} ! {video_mux_queue} ! mux. "
        )

    audio_encoder = (
        "avenc_aac bitrate=128000"
        if extension == "mp4"
        else "opusenc bitrate=128000"
    )
    audio_chain = _audio_chain(config, audio_encoder, "mux.")

    desc = (
        f"{main_video}"
        f"{audio_chain}"
        f"{muxer} ! filesink location={_q(str(output_path))}"
    )
    return PipelinePlan(desc, extension, encoder_label)


def build_pipeline(
    config: RecordingConfig,
    output_path: Path,
    session_type: str,
    has_x264: bool,
    has_vp8: bool,
    portal_stream: Optional[PortalStream] = None,
) -> PipelinePlan:
    if config.mode == RecordingMode.AUDIO:
        return build_audio_only_pipeline(config, output_path)
    return build_video_pipeline(
        config,
        output_path,
        session_type,
        has_x264,
        has_vp8,
        portal_stream,
    )
