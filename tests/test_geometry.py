import unittest

from ubuntu_screen_recorder.geometry import (
    NormalizedCrop,
    crop_margins_for_stream,
    normalized_crop_from_selection,
)


class GeometryTests(unittest.TestCase):
    def test_selection_is_normalized(self):
        crop = normalized_crop_from_selection(
            100, 50, 400, 300, 1000, 500
        )
        self.assertAlmostEqual(crop.x, 0.1)
        self.assertAlmostEqual(crop.y, 0.1)
        self.assertAlmostEqual(crop.width, 0.4)
        self.assertAlmostEqual(crop.height, 0.6)

    def test_selection_is_clamped_to_canvas(self):
        crop = normalized_crop_from_selection(
            -50, -20, 300, 200, 1000, 500
        )
        self.assertEqual(crop.x, 0.0)
        self.assertEqual(crop.y, 0.0)
        self.assertAlmostEqual(crop.width, 0.25)
        self.assertAlmostEqual(crop.height, 0.36)

    def test_crop_margins_keep_even_output_dimensions(self):
        crop = NormalizedCrop(0.1, 0.1, 0.5, 0.5)
        left, right, top, bottom = crop_margins_for_stream(
            crop, 1366, 768
        )
        out_width = 1366 - left - right
        out_height = 768 - top - bottom
        self.assertEqual(out_width % 2, 0)
        self.assertEqual(out_height % 2, 0)
        self.assertGreater(out_width, 0)
        self.assertGreater(out_height, 0)

    def test_full_frame_crop_has_zero_margins(self):
        margins = crop_margins_for_stream(
            NormalizedCrop(0.0, 0.0, 1.0, 1.0),
            1366,
            768,
        )
        self.assertEqual(margins, (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
