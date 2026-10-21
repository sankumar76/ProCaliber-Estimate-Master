import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

from core import calculations as calc
from core import sections


class ShapeTests(unittest.TestCase):
    def test_round_bar_sanity_value(self):
        area, weight = calc.round_bar(100, 1000, 7.85)
        self.assertAlmostEqual(area, math.pi / 4 * 100 ** 2)
        self.assertAlmostEqual(weight, 61.65, places=2)

    def test_pipe(self):
        area, weight = calc.pipe(100, 80, 1000, 7.85)
        self.assertAlmostEqual(area, math.pi / 4 * (100 ** 2 - 80 ** 2))
        self.assertAlmostEqual(weight, area * 1000 * 7.85e-6)

    def test_box_section_and_clamp(self):
        area, _ = calc.box_section(100, 50, 5, 1000, 7.85)
        self.assertAlmostEqual(area, 100 * 50 - 90 * 40)
        area, _ = calc.box_section(20, 10, 8, 1000, 7.85)
        self.assertAlmostEqual(area, 20 * 10)  # inner size clamped to 0

    def test_plate_reports_face_area(self):
        area, weight = calc.plate(1000, 500, 10, 7.85)
        self.assertEqual(area, 500000)
        self.assertAlmostEqual(weight, 39.25)

    def test_beam_close_to_is808(self):
        h, b, tw, tf = sections.BEAMS["ISMB 200"]
        _, weight = calc.beam_or_channel(h, b, tw, tf, 1000, 7.85)
        self.assertAlmostEqual(weight, 25.4, delta=25.4 * 0.03)  # IS 808: 25.4 kg/m

    def test_angle(self):
        a, b, t = sections.ANGLES["ISA 50x50x6"]
        area, _ = calc.angle(a, b, t, 1000, 7.85)
        self.assertAlmostEqual(area, 6 * (50 + 50 - 6))

    def test_tee(self):
        area, _ = calc.tee(100, 100, 6, 6, 1000, 7.85)
        self.assertAlmostEqual(area, 100 * 6 + 94 * 6)

    def test_section_tables_parsed(self):
        self.assertEqual(sections.ANGLES["ISA 100x65x7"], (100, 65, 7))
        self.assertEqual(len(sections.EQUAL_ANGLES), 31)
        self.assertEqual(len(sections.UNEQUAL_ANGLES), 28)


class ConverterTests(unittest.TestCase):
    def test_length(self):
        self.assertAlmostEqual(calc.convert(1, "foot", "mm", calc.LENGTH_UNITS), 304.8)
        self.assertAlmostEqual(calc.convert(254, "mm", "inch", calc.LENGTH_UNITS), 10)

    def test_weight(self):
        self.assertAlmostEqual(calc.convert(1, "kg", "lb", calc.WEIGHT_UNITS), 2.2046)
        self.assertAlmostEqual(calc.convert(2.5, "tonne", "kg", calc.WEIGHT_UNITS), 2500)


if __name__ == "__main__":
    unittest.main()
