import unittest

from ubuntu_screen_recorder.portal_policy import (
    screenshot_request_policy,
    screenshot_result_is_app_managed,
)


class ScreenshotPolicyTests(unittest.TestCase):
    def test_v3_supported_screen_target_is_noninteractive(self):
        targeted, interactive = screenshot_request_policy(
            1, 3, 1 | 2 | 4 | 8
        )
        self.assertTrue(targeted)
        self.assertFalse(interactive)

    def test_v3_supported_window_target_is_interactive(self):
        targeted, interactive = screenshot_request_policy(
            2, 3, 1 | 2 | 4 | 8
        )
        self.assertTrue(targeted)
        self.assertTrue(interactive)

    def test_legacy_portal_uses_interactive_fallback(self):
        targeted, interactive = screenshot_request_policy(
            4, 2, 0
        )
        self.assertFalse(targeted)
        self.assertTrue(interactive)

    def test_portal_v2_storage_is_system_managed(self):
        self.assertFalse(
            screenshot_result_is_app_managed(2)
        )

    def test_portal_v3_storage_can_be_app_managed(self):
        self.assertTrue(
            screenshot_result_is_app_managed(3)
        )

    def test_unadvertised_target_uses_interactive_fallback(self):
        targeted, interactive = screenshot_request_policy(
            8, 3, 1 | 2 | 4
        )
        self.assertFalse(targeted)
        self.assertTrue(interactive)


if __name__ == "__main__":
    unittest.main()
