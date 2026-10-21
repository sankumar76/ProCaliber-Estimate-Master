"""Shared specific-gravity table (spec section 4.3).

This single list feeds both the Weight Calculator and the Cost Estimator.
"""

# (display name, specific gravity in g/cm3)
MATERIALS = [
    ("MS (Mild Steel)", 7.85),
    ("Steel - C15", 7.85),
    ("Steel - C35", 7.84),
    ("Steel - C60", 7.83),
    ("SS 304", 8.00),
    ("SS 316", 8.00),
    ("EN8", 7.85),
    ("EN24", 7.85),
    ("Cast Iron", 7.20),
    ("Copper", 8.96),
    ("Bronze", 8.73),
    ("Brass", 8.45),
    ("Aluminium", 2.70),
    ("Lead", 11.34),
]

CUSTOM_LABEL = "Custom..."

# Materials that come in standard rolled IS sections (steel grades).
STEEL_MATERIALS = {
    "MS (Mild Steel)", "Steel - C15", "Steel - C35", "Steel - C60",
    "SS 304", "SS 316", "EN8", "EN24",
}

_SG = dict(MATERIALS)


def material_names():
    return [name for name, _ in MATERIALS]


def specific_gravity(name):
    """Return the SG for a listed material, or None if not in the table."""
    return _SG.get(name)


def density_factor(sg):
    """Value stored in the estimate's Density column (U): SG x 1e-6 (kg/mm3)."""
    return sg * 0.000001
