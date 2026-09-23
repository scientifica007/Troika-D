import unittest
from pathlib import Path

from ubuntu_screen_recorder.models import RecordingConfig
from ubuntu_screen_recorder.pipeline import PortalStream, build_video_pipeline


class PipelineTests(unittest.TestCase):
    def test_x11_pipeline_uses_ximagesrc(self):
        config = RecordingConfig()
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn("ximagesrc", plan.description)
        self.assertIn("x264enc", plan.description)

    def test_wayland_modern_portal_uses_pipewire_serial(self):
        config = RecordingConfig()
        stream = PortalStream(fd=9, node_id=77, pipewire_serial=12345)
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "wayland", True, True, stream
        )
        self.assertIn("pipewiresrc", plan.description)
        self.assertIn("fd=9", plan.description)
        self.assertIn('target-object="12345"', plan.description)
        self.assertNotIn('path="77"', plan.description)

    def test_wayland_legacy_portal_uses_node_id_path(self):
        config = RecordingConfig()
        stream = PortalStream(fd=9, node_id=77, pipewire_serial=None)
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "wayland", True, True, stream
        )
        self.assertIn("pipewiresrc", plan.description)
        self.assertIn("fd=9", plan.description)
        self.assertIn('path="77"', plan.description)
        self.assertNotIn("target-object=", plan.description)

    def test_vp8_fallback_changes_container(self):
        config = RecordingConfig()
        plan = build_video_pipeline(
            config, Path("/tmp/a.webm"), "x11", False, True
        )
        self.assertEqual(plan.extension, "webm")
        self.assertIn("vp8enc", plan.description)

    def test_single_microphone_uses_stability_audio_path_without_mixer(self):
        config = RecordingConfig(
            include_microphone=True,
            microphone_source="test.mic",
        )
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn('pulsesrc device="test.mic"', plan.description)
        self.assertIn("buffer-time=500000", plan.description)
        self.assertIn("latency-time=20000", plan.description)
        self.assertIn("provide-clock=false", plan.description)
        self.assertIn("slave-method=resample", plan.description)
        self.assertIn("audio/x-raw,rate=48000", plan.description)
        self.assertNotIn("audiomixer name=amix", plan.description)

    def test_two_audio_sources_use_live_mixer_with_extra_latency(self):
        config = RecordingConfig(
            include_microphone=True,
            microphone_source="test.mic",
            include_system_audio=True,
            system_audio_source="test.monitor",
        )
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn("audiomixer name=amix latency=100", plan.description)
        self.assertIn('pulsesrc device="test.mic"', plan.description)
        self.assertIn('pulsesrc device="test.monitor"', plan.description)

    def test_video_capture_queue_is_time_limited_and_leaky(self):
        config = RecordingConfig()
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn(
            "queue name=video_capture_q max-size-buffers=0 "
            "max-size-bytes=0 max-size-time=1000000000 leaky=downstream",
            plan.description,
        )


if __name__ == "__main__":
    unittest.main()
