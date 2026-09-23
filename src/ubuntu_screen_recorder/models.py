from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class RecordingMode(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    SCREENSHOT = "screenshot"


class CaptureSource(str, Enum):
    SCREEN = "screen"
    WINDOW = "window"
    AREA = "area"
    ACTIVE_WINDOW = "active-window"


@dataclass(frozen=True)
class QualityProfile:
    key: str
    label: str
    scale_percent: int
    video_bitrate_kbps: int
    x264_speed_preset: str


QUALITY_PROFILES = {
    "economy": QualityProfile("economy", "Economy", 75, 1800, "ultrafast"),
    "balanced": QualityProfile("balanced", "Balanced", 100, 4500, "veryfast"),
    "high": QualityProfile("high", "High", 100, 8000, "fast"),
}


@dataclass
class RecordingConfig:
    mode: RecordingMode = RecordingMode.VIDEO
    source: CaptureSource = CaptureSource.SCREEN
    quality: QualityProfile = QUALITY_PROFILES["balanced"]
    fps: int = 30
    microphone_source: Optional[str] = None
    system_audio_source: Optional[str] = None
    include_microphone: bool = False
    include_system_audio: bool = False
    include_camera: bool = False
    camera_device: Optional[str] = None
    show_pointer: bool = True
    output_dir: Path = Path.home() / "Videos"

    def validate(self) -> None:
        if self.fps not in (15, 30, 60):
            raise ValueError("FPS must be 15, 30, or 60")
        if self.include_microphone and not self.microphone_source:
            raise ValueError("Microphone recording is enabled but no microphone is selected")
        if self.include_system_audio and not self.system_audio_source:
            raise ValueError("System-audio recording is enabled but no monitor source is selected")
        if self.include_camera and not self.camera_device:
            raise ValueError("Camera overlay is enabled but no camera is selected")
        if self.mode == RecordingMode.AUDIO and not (
            self.include_microphone or self.include_system_audio
        ):
            raise ValueError("Audio-only mode needs at least one audio source")
