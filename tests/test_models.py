import unittest
from pathlib import Path

from ubuntu_screen_recorder.models import RecordingConfig, RecordingMode


class RecordingConfigTests(unittest.TestCase):
    def test_balanced_video_defaults_are_valid(self):
        RecordingConfig().validate()

    def test_audio_mode_requires_audio_source(self):
        config = RecordingConfig(mode=RecordingMode.AUDIO)
        with self.assertRaises(ValueError):
            config.validate()

    def test_audio_mode_accepts_microphone(self):
        config = RecordingConfig(
            mode=RecordingMode.AUDIO,
            include_microphone=True,
            microphone_source="mic.test",
            output_dir=Path("/tmp"),
        )
        config.validate()


if __name__ == "__main__":
    unittest.main()
