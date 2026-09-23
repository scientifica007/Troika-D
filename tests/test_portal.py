import unittest

from ubuntu_screen_recorder.portal import PortalClient


class ScreenshotOptionTests(unittest.TestCase):
    def test_v3_supported_target_is_sent(self):
        options, targeted = PortalClient._screenshot_options(
            "token", 1, 3, 1 | 2 | 4 | 8
        )
        self.assertTrue(targeted)
        self.assertEqual(options["target"].unpack(), 1)
        self.assertFalse(options["interactive"].unpack())

    def test_window_target_requests_interactive_selection(self):
        options, targeted = PortalClient._screenshot_options(
            "token", 2, 3, 1 | 2 | 4 | 8
        )
        self.assertTrue(targeted)
        self.assertEqual(options["target"].unpack(), 2)
        self.assertTrue(options["interactive"].unpack())

    def test_legacy_portal_omits_v3_target_key(self):
        options, targeted = PortalClient._screenshot_options(
            "token", 4, 2, 0
        )
        self.assertFalse(targeted)
        self.assertNotIn("target", options)
        self.assertTrue(options["interactive"].unpack())

    def test_unadvertised_target_falls_back_to_interactive(self):
        options, targeted = PortalClient._screenshot_options(
            "token", 8, 3, 1 | 2 | 4
        )
        self.assertFalse(targeted)
        self.assertNotIn("target", options)
        self.assertTrue(options["interactive"].unpack())


if __name__ == "__main__":
    unittest.main()
