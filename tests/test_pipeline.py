import unittest
from pathlib import Path

from ubuntu_screen_recorder.models import RecordingConfig
from ubuntu_screen_recorder.pipeline import PortalStream, build_video_pipeline


class PipelineTests(unittest.TestCase):
    def test_x11_pipeline_uses_ximagesrc(self):
        config = RecordingConfig()
        plan = build_video_pipeline(config, Path("/tmp/a.mp4"), "x11", True, True)
        self.assertIn("ximagesrc", plan.description)
        self.assertIn("x264enc", plan.description)

    def test_wayland_modern_portal_uses_pipewire_serial(self):
        config = RecordingConfig()
        stream = PortalStream(fd=9, node_id=77, pipewire_serial=12345)
        plan = build_video_pipeline(config, Path("/tmp/a.mp4"), "wayland", True, True, stream)
        self.assertIn("pipewiresrc", plan.description)
        self.assertIn("fd=9", plan.description)
        self.assertIn('target-object="12345"', plan.description)
        self.assertNotIn('path="77"', plan.description)

    def test_wayland_legacy_portal_uses_node_id_path(self):
        config = RecordingConfig()
        stream = PortalStream(fd=9, node_id=77, pipewire_serial=None)
        plan = build_video_pipeline(config, Path("/tmp/a.mp4"), "wayland", True, True, stream)
        self.assertIn("pipewiresrc", plan.description)
        self.assertIn("fd=9", plan.description)
        self.assertIn('path="77"', plan.description)
        self.assertNotIn("target-object=", plan.description)

    def test_vp8_fallback_changes_container(self):
        config = RecordingConfig()
        plan = build_video_pipeline(config, Path("/tmp/a.webm"), "x11", False, True)
        self.assertEqual(plan.extension, "webm")
        self.assertIn("vp8enc", plan.description)


if __name__ == "__main__":
    unittest.main()
