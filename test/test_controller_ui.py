import math
import unittest

from virtual_joy.controller_ui import BODY_SHELL, CONTROLS, TOP_SHELL


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


if __name__ == "__main__":
    unittest.main()
