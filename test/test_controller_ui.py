import math
import unittest

from virtual_joy.controller_ui import (
    BODY_BOUNDS,
    BODY_SHELL,
    CONTROLS,
    TOP_BOUNDS,
    TOP_SHELL,
    controller_layout,
)


def polygon_area(points):
    return abs(sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])
    )) / 2


class ControllerGeometryTest(unittest.TestCase):
    def test_control_keys_are_unique(self):
        logical_keys = []
        for geometry in CONTROLS:
            if geometry.kind == "stick":
                logical_keys.append(("button", 10 if geometry.key == "left" else 11))
            else:
                logical_keys.append((geometry.kind, geometry.key))
        self.assertEqual(len(logical_keys), len(set(logical_keys)))

    def test_all_visible_buttons_have_one_geometry(self):
        visible_buttons = {
            geometry.key
            for geometry in CONTROLS
            if geometry.kind == "button"
        }
        visible_buttons.update(
            10 if geometry.key == "left" else 11
            for geometry in CONTROLS
            if geometry.kind == "stick"
        )
        self.assertEqual(visible_buttons, set(range(12)))

    def test_shapes_are_nonempty_and_inside_canvas(self):
        for geometry in CONTROLS:
            with self.subTest(kind=geometry.kind, key=geometry.key):
                if geometry.shape == "oval":
                    self.assertIsNotNone(geometry.box)
                    x1, y1, x2, y2 = geometry.box
                    self.assertGreater(x2 - x1, 0)
                    self.assertGreater(y2 - y1, 0)
                    values = (x1, y1, x2, y2)
                else:
                    self.assertGreaterEqual(len(geometry.points), 3)
                    self.assertGreater(polygon_area(geometry.points), 20)
                    values = tuple(value for point in geometry.points for value in point)
                self.assertTrue(all(math.isfinite(value) for value in values))

        for shell in (TOP_SHELL, BODY_SHELL):
            self.assertGreater(polygon_area(shell), 1000)
            self.assertTrue(all(0 <= x <= 650 and 0 <= y <= 606 for x, y in shell))

    def test_stacked_layout_preserves_reference_scale(self):
        mode, transforms = controller_layout(650, 606)
        self.assertEqual(mode, "stacked")
        self.assertEqual(transforms["top"], transforms["body"])
        self.assertAlmostEqual(transforms["body"][0], 1.0)

    def test_wide_layout_uses_width_without_distortion(self):
        width, height = 1900, 879
        mode, transforms = controller_layout(width, height)
        self.assertEqual(mode, "wide")
        self.assertAlmostEqual(transforms["top"][0], transforms["body"][0])
        self.assertGreater(transforms["body"][0], min(width / 650, height / 606))

        for bounds, transform in ((TOP_BOUNDS, transforms["top"]), (BODY_BOUNDS, transforms["body"])):
            scale, offset_x, offset_y = transform
            left, top, right, bottom = bounds
            transformed = (
                offset_x + left * scale,
                offset_y + top * scale,
                offset_x + right * scale,
                offset_y + bottom * scale,
            )
            self.assertGreaterEqual(transformed[0], 0)
            self.assertGreaterEqual(transformed[1], 0)
            self.assertLessEqual(transformed[2], width)
            self.assertLessEqual(transformed[3], height)


if __name__ == "__main__":
    unittest.main()
