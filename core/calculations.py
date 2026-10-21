"""Weight / area formulas for Module A (spec section 4.2).

Every shape function returns (cross_section_area_mm2, weight_kg). All
dimensions are in mm and specific gravity in g/cm3.
"""

import math


def weight_from_area(area_mm2, length_mm, sg):
    return area_mm2 * length_mm * sg * 1e-6


def round_bar(diameter, length, sg):
    area = math.pi / 4 * diameter ** 2
    return area, weight_from_area(area, length, sg)


def pipe(outer_diameter, inner_diameter, length, sg):
    area = math.pi / 4 * (outer_diameter ** 2 - inner_diameter ** 2)
    return area, weight_from_area(area, length, sg)


def box_section(outer_length, outer_width, thickness, total_length, sg):
    inner_length = max(outer_length - 2 * thickness, 0)
    inner_width = max(outer_width - 2 * thickness, 0)
    area = outer_length * outer_width - inner_length * inner_width
    return area, weight_from_area(area, total_length, sg)


def plate(length, width, thickness, sg):
    """Area reported for a plate is the face area (length x width)."""
    face_area = length * width
    return face_area, length * width * thickness * sg * 1e-6


def beam_or_channel(h, b, tw, tf, length, sg):
    web_height = max(h - 2 * tf, 0)
    area = 2 * (b * tf) + web_height * tw
    return area, weight_from_area(area, length, sg)


def angle(leg_a, leg_b, thickness, length, sg):
    area = thickness * (leg_a + leg_b - thickness)
    return area, weight_from_area(area, length, sg)


def tee(h, b, tw, tf, length, sg):
    web_height = max(h - tf, 0)
    area = b * tf + web_height * tw
    return area, weight_from_area(area, length, sg)


# ---- Unit converter (spec section 4.5) -------------------------------------

# Factor that converts one unit into the base unit (mm / kg).
LENGTH_UNITS = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "inch": 25.4, "foot": 304.8}
WEIGHT_UNITS = {"kg": 1.0, "g": 0.001, "tonne": 1000.0, "lb": 1 / 2.2046}


def convert(value, from_unit, to_unit, table):
    return value * table[from_unit] / table[to_unit]
