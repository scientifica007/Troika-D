from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .models import RecordingConfig, RecordingMode


@dataclass(frozen=True)
class PortalStream:
    fd: int
    target_object: str


@dataclass(frozen=True)
class PipelinePlan:
    description: str
    extension: str
    encoder: str


def _q(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def choose_video_encoder(has_x264: bool, has_vp8: bool, bitrate_kbps: int, speed: str):
    if has_x264:
        return (
            f"x264enc bitrate={bitrate_kbps} speed-preset={speed} tune=zerolatency key-int-max=60",
            "h264parse",
            "mp4mux name=mux faststart=true",
            "mp4",
            "x264/H.264",
        )
    if has_vp8:
        return (
            f"vp8enc target-bitrate={bitrate_kbps * 1000} deadline=1 cpu-used=8",
            "identity",
            "webmmux name=mux",
            "webm",
            "VP8",
        )
    raise RuntimeError("No supported video encoder found (need x264enc or vp8enc)")


def build_audio_only_pipeline(config: RecordingConfig, output_path: Path) -> PipelinePlan:
    branches = []
    if config.include_microphone:
        branches.append(
            f"pulsesrc device={_q(config.microphone_source or '')} do-timestamp=true ! "
            "audioconvert ! audioresample ! queue ! amix."
        )
    if config.include_system_audio:
        branches.append(
            f"pulsesrc device={_q(config.system_audio_source or '')} do-timestamp=true ! "
            "audioconvert ! audioresample ! queue ! amix."
        )
    if not branches:
        raise ValueError("Audio-only recording requires at least one source")
    desc = " ".join(branches) + (
        " audiomixer name=amix ! audioconvert ! audioresample ! "
        f"opusenc bitrate=128000 ! oggmux ! filesink location={_q(str(output_path))}"
    )
    return PipelinePlan(desc, "ogg", "Opus")


def build_video_pipeline(
    config: RecordingConfig,
    output_path: Path,
    session_type: str,
    has_x264: bool,
    has_vp8: bool,
    portal_stream: Optional[PortalStream] = None,
) -> PipelinePlan:
    enc, parser, muxer, extension, encoder_label = choose_video_encoder(
        has_x264, has_vp8, config.quality.video_bitrate_kbps, config.quality.x264_speed_preset
    )

    if session_type == "wayland":
        if portal_stream is None:
            raise ValueError("Wayland video recording needs a portal PipeWire stream")
        video_src = (
            f"pipewiresrc fd={portal_stream.fd} target-object={_q(portal_stream.target_object)} "
            "do-timestamp=true"
        )
    else:
        video_src = f"ximagesrc use-damage=true show-pointer={'true' if config.show_pointer else 'false'}"

    video_chain = (
        f"{video_src} ! queue ! videoconvert ! videorate ! "
        f"video/x-raw,framerate={config.fps}/1 ! videoscale ! "
    )
    if config.quality.scale_percent != 100:
        video_chain += "videoconvert ! "

    if config.include_camera:
        screen_branch = video_chain + "queue ! comp.sink_0 "
        cam_branch = (
            f"v4l2src device={_q(config.camera_device or '')} ! queue ! videoconvert ! videoscale ! "
            "video/x-raw,width=320,height=180 ! queue ! comp.sink_1 "
        )
        main_video = (
            screen_branch
            + cam_branch
            + "compositor name=comp sink_1::xpos=20 sink_1::ypos=20 ! videoconvert ! "
            + f"{enc} ! {parser} ! queue ! mux. "
        )
    else:
        main_video = video_chain + f"{enc} ! {parser} ! queue ! mux. "

    audio_branches = []
    if config.include_microphone:
        audio_branches.append(
            f"pulsesrc device={_q(config.microphone_source or '')} do-timestamp=true ! "
            "audioconvert ! audioresample ! queue ! amix. "
        )
    if config.include_system_audio:
        audio_branches.append(
            f"pulsesrc device={_q(config.system_audio_source or '')} do-timestamp=true ! "
            "audioconvert ! audioresample ! queue ! amix. "
        )

    audio_chain = ""
    if audio_branches:
        audio_encoder = "avenc_aac bitrate=128000" if extension == "mp4" else "opusenc bitrate=128000"
        audio_chain = (
            "".join(audio_branches)
            + "audiomixer name=amix ! audioconvert ! audioresample ! "
            + f"{audio_encoder} ! queue ! mux. "
        )

    desc = f"{main_video}{audio_chain}{muxer} ! filesink location={_q(str(output_path))}"
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
