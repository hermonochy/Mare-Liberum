import unittest

from tidebound.sail_geometry import (
    clamp_deployment,
    deployed_sail_dimensions,
    gaff_sail_points,
    jib_sail_points,
    lateen_sail_points,
    sail_dimensions,
    square_sail_points,
)
from tidebound.ships import SHIP_CLASSES


class SailGeometryTests(unittest.TestCase):
    def test_deployment_is_clamped(self):
        self.assertEqual(clamp_deployment(-1), 0.0)
        self.assertEqual(clamp_deployment(0.42), 0.42)
        self.assertEqual(clamp_deployment(2), 1.0)

    def test_canvas_area_tracks_sail_deployment(self):
        quarter = deployed_sail_dimensions(15, 40, 0.25)
        half = deployed_sail_dimensions(15, 40, 0.50)
        full = deployed_sail_dimensions(15, 40, 1.0)
        self.assertLess(quarter[1], half[1])
        self.assertLess(half[1], full[1])
        self.assertLess(quarter[0], full[0])

    def test_canvas_width_stays_within_rendered_hull_beam(self):
        for stats in SHIP_CLASSES.values():
            half_beam = stats["beam"] / 2
            span, depth = sail_dimensions(stats, half_beam, len(stats["masts"]), "Standard Canvas")
            actual_hull_half_width = half_beam * max(stats["hull_profile"])
            self.assertLessEqual(span, actual_hull_half_width * 0.94 + 0.001)
            self.assertGreater(depth, 0)

    def test_square_canvas_is_overhead_rectangle_not_wing_shape(self):
        points = square_sail_points(100, 60, 40, 15, 0.7)
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        self.assertGreater(max(xs) - min(xs), 30)
        self.assertLessEqual(max(xs), 100)
        self.assertAlmostEqual(max(ys) - min(ys), 30, delta=1.0)
        self.assertAlmostEqual(points[0][0], points[-1][0], delta=0.01)

    def test_distinct_rig_panels_have_valid_top_down_shapes(self):
        for points in (
            gaff_sail_points(100, 60, 35, 12, 0.4),
            lateen_sail_points(100, 60, 35, 12, 0.4),
            jib_sail_points(120, 60, 18, 7, 0.4),
        ):
            self.assertGreaterEqual(len(points), 4)
            self.assertTrue(all(len(point) == 2 for point in points))
            self.assertGreater(max(point[0] for point in points) - min(point[0] for point in points), 3)
            self.assertGreater(max(point[1] for point in points) - min(point[1] for point in points), 3)


if __name__ == "__main__":
    unittest.main()
