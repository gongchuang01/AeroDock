import math
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "src" / "aerodock_offboard" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from avoidance_core import clearance, detour_target, sector_values


class ScanGeometryTests(unittest.TestCase):
    def test_sector_filters_angles_and_invalid_ranges(self):
        ranges = [1.0, float("nan"), 0.05, 2.0, float("inf"), 8.0, 3.0]
        values = sector_values(
            ranges, math.radians(-90), math.radians(30), 0.1, 6.0, -30, 60)
        self.assertEqual(values, [2.0])

    def test_clearance_uses_median_and_range_max_fallback(self):
        self.assertEqual(clearance([1.0, 9.0, 3.0], 30.0), 3.0)
        self.assertEqual(clearance([], 30.0), 30.0)

    def test_left_detour_with_ninety_degree_sensor_mount(self):
        north, east = detour_target(
            0.0, 0.0, 0.0, math.pi / 2, 1.5, 2.0, True)
        self.assertAlmostEqual(north, 2.0, places=6)
        self.assertAlmostEqual(east, 1.5, places=6)

    def test_right_detour_respects_vehicle_heading(self):
        north, east = detour_target(
            4.0, -2.0, math.pi / 2, 0.0, 1.0, 2.0, False)
        self.assertAlmostEqual(north, 2.0, places=6)
        self.assertAlmostEqual(east, -1.0, places=6)


if __name__ == "__main__":
    unittest.main()
