import unittest
from pathlib import Path

from ubuntu_screen_recorder.geometry import NormalizedCrop
from ubuntu_screen_recorder.models import CaptureSource, RecordingConfig
from ubuntu_screen_recorder.pipeline import (
    PortalStream,
    ROBUST_MP4_MAX_DURATION_NS,
    ROBUST_MP4_UPDATE_PERIOD_NS,
    build_video_pipeline,
)


class PipelineTests(unittest.TestCase):
    def test_x11_pipeline_uses_named_ximagesrc(self):
        config = RecordingConfig()
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn("ximagesrc name=screen_src", plan.description)
        self.assertIn("x264enc", plan.description)

    def test_wayland_modern_portal_uses_pipewire_serial(self):
        config = RecordingConfig()
        stream = PortalStream(
            fd=9, node_id=77, pipewire_serial=12345
        )
        plan = build_video_pipeline(
            config,
            Path("/tmp/a.mp4"),
            "wayland",
            True,
            True,
            stream,
        )
        self.assertIn(
            "pipewiresrc name=screen_src", plan.description
        )
        self.assertIn("fd=9", plan.description)
        self.assertIn(
            'target-object="12345"', plan.description
        )
        self.assertNotIn('path="77"', plan.description)

    def test_wayland_legacy_portal_uses_node_id_path(self):
        config = RecordingConfig()
        stream = PortalStream(
            fd=9, node_id=77, pipewire_serial=None
        )
        plan = build_video_pipeline(
            config,
            Path("/tmp/a.mp4"),
            "wayland",
            True,
            True,
            stream,
        )
        self.assertIn(
            "pipewiresrc name=screen_src", plan.description
        )
        self.assertIn("fd=9", plan.description)
        self.assertIn('path="77"', plan.description)
        self.assertNotIn("target-object=", plan.description)

    def test_mp4_uses_robust_periodic_moov_updates(self):
        config = RecordingConfig()
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn(
            "reserved-max-duration="
            f"{ROBUST_MP4_MAX_DURATION_NS}",
            plan.description,
        )
        self.assertIn(
            "reserved-moov-update-period="
            f"{ROBUST_MP4_UPDATE_PERIOD_NS}",
            plan.description,
        )
        self.assertNotIn("faststart=true", plan.description)

    def test_vp8_fallback_changes_container(self):
        config = RecordingConfig()
        plan = build_video_pipeline(
            config, Path("/tmp/a.webm"), "x11", False, True
        )
        self.assertEqual(plan.extension, "webm")
        self.assertIn("vp8enc", plan.description)

    def test_single_microphone_uses_named_stable_audio_source(self):
        config = RecordingConfig(
            include_microphone=True,
            microphone_source="test.mic",
        )
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn(
            'pulsesrc name=mic_src device="test.mic"',
            plan.description,
        )
        self.assertIn("buffer-time=500000", plan.description)
        self.assertIn("latency-time=20000", plan.description)
        self.assertIn("provide-clock=false", plan.description)
        self.assertIn("slave-method=resample", plan.description)
        self.assertIn(
            "audio/x-raw,rate=48000", plan.description
        )
        self.assertNotIn(
            "audiomixer name=amix", plan.description
        )

    def test_two_audio_sources_are_named_and_mixed(self):
        config = RecordingConfig(
            include_microphone=True,
            microphone_source="test.mic",
            include_system_audio=True,
            system_audio_source="test.monitor",
        )
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn(
            "audiomixer name=amix latency=100",
            plan.description,
        )
        self.assertIn(
            'pulsesrc name=mic_src device="test.mic"',
            plan.description,
        )
        self.assertIn(
            'pulsesrc name=system_audio_src '
            'device="test.monitor"',
            plan.description,
        )

    def test_camera_source_is_named_for_clean_eos(self):
        config = RecordingConfig(
            include_camera=True,
            camera_device="/dev/video0",
        )
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn(
            "v4l2src name=camera_src", plan.description
        )

    def test_camera_compositor_avoids_checkerboard_startup(self):
        config = RecordingConfig(
            include_camera=True,
            camera_device="/dev/video0",
        )
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn(
            "compositor name=comp background=black "
            "start-time-selection=first",
            plan.description,
        )

    def test_video_chain_starts_from_first_real_frame(self):
        config = RecordingConfig()
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn(
            "video/x-raw,format=I420 ! "
            "videorate name=video_rate skip-to-first=true",
            plan.description,
        )

    def test_wayland_window_requests_upstream_rate_without_videorate(self):
        config = RecordingConfig(
            source=CaptureSource.WINDOW,
            fps=15,
        )
        stream = PortalStream(
            fd=9, node_id=77, pipewire_serial=None
        )
        plan = build_video_pipeline(
            config,
            Path("/tmp/a.mp4"),
            "wayland",
            True,
            True,
            stream,
        )
        self.assertIn(
            "video/x-raw,format=I420,framerate=15/1",
            plan.description,
        )
        self.assertNotIn(
            "videorate name=video_rate",
            plan.description,
        )

    def test_wayland_active_window_uses_same_native_window_path(self):
        config = RecordingConfig(
            source=CaptureSource.ACTIVE_WINDOW,
            fps=30,
        )
        stream = PortalStream(
            fd=9, node_id=77, pipewire_serial=None
        )
        plan = build_video_pipeline(
            config,
            Path("/tmp/a.mp4"),
            "wayland",
            True,
            True,
            stream,
        )
        self.assertIn(
            "video/x-raw,format=I420,framerate=30/1",
            plan.description,
        )
        self.assertNotIn(
            "videorate name=video_rate",
            plan.description,
        )

    def test_wayland_keeps_constant_framerate_path(self):
        config = RecordingConfig(fps=30)
        stream = PortalStream(
            fd=9, node_id=77, pipewire_serial=None
        )
        plan = build_video_pipeline(
            config,
            Path("/tmp/a.mp4"),
            "wayland",
            True,
            True,
            stream,
        )
        self.assertIn(
            "videorate name=video_rate skip-to-first=true ! "
            "video/x-raw,framerate=30/1",
            plan.description,
        )


    def test_area_pipeline_has_gated_crop_stage(self):
        config = RecordingConfig(
            source=CaptureSource.AREA,
            crop=NormalizedCrop(0.1, 0.1, 0.5, 0.5),
        )
        stream = PortalStream(
            fd=9, node_id=77, pipewire_serial=None
        )
        plan = build_video_pipeline(
            config,
            Path("/tmp/a.mp4"),
            "wayland",
            True,
            True,
            stream,
        )
        self.assertIn(
            "videocrop name=area_crop ! "
            "valve name=area_gate drop=true",
            plan.description,
        )

    def test_area_pipeline_rejects_missing_crop(self):
        config = RecordingConfig(source=CaptureSource.AREA)
        stream = PortalStream(
            fd=9, node_id=77, pipewire_serial=None
        )
        with self.assertRaises(ValueError):
            build_video_pipeline(
                config,
                Path("/tmp/a.mp4"),
                "wayland",
                True,
                True,
                stream,
            )

    def test_video_capture_queue_is_time_limited_and_leaky(self):
        config = RecordingConfig()
        plan = build_video_pipeline(
            config, Path("/tmp/a.mp4"), "x11", True, True
        )
        self.assertIn(
            "queue name=video_capture_q "
            "max-size-buffers=0 "
            "max-size-bytes=0 "
            "max-size-time=1000000000 "
            "leaky=downstream",
            plan.description,
        )


if __name__ == "__main__":
    unittest.main()
