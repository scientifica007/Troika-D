import unittest

from ubuntu_screen_recorder.system_probe import (
    V4L2_CAP_DEVICE_CAPS,
    V4L2_CAP_VIDEO_CAPTURE,
    V4L2_CAP_VIDEO_CAPTURE_MPLANE,
    _is_video_capture_caps,
)


class CameraCapabilityTests(unittest.TestCase):
    def test_single_plane_capture_is_accepted(self):
        self.assertTrue(
            _is_video_capture_caps(V4L2_CAP_VIDEO_CAPTURE, 0)
        )

    def test_multiplane_capture_is_accepted(self):
        self.assertTrue(
            _is_video_capture_caps(V4L2_CAP_VIDEO_CAPTURE_MPLANE, 0)
        )

    def test_metadata_or_non_capture_node_is_rejected(self):
        self.assertFalse(_is_video_capture_caps(0x00800000, 0))

    def test_device_caps_take_precedence_when_advertised(self):
        capabilities = V4L2_CAP_DEVICE_CAPS | V4L2_CAP_VIDEO_CAPTURE
        self.assertFalse(_is_video_capture_caps(capabilities, 0x00800000))

    def test_device_caps_can_declare_capture(self):
        capabilities = V4L2_CAP_DEVICE_CAPS
        self.assertTrue(
            _is_video_capture_caps(
                capabilities, V4L2_CAP_VIDEO_CAPTURE
            )
        )


if __name__ == "__main__":
    unittest.main()
