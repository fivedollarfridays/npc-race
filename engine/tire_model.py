"""
Tire compound definitions and non-linear wear/grip curves.

Provides five compounds (soft, medium, hard, intermediate, wet)
with different base grip, wear rates, and cliff characteristics.
All functions are purely functional with no state mutation.
"""

COMPOUNDS: dict[str, dict[str, float]] = {
    "soft": {
        "base_grip": 1.15,
        "wear_rate": 0.000016,
        "cliff_threshold": 0.75,
        "cliff_exponent": 3.0,
    },
    "medium": {
        "base_grip": 1.00,
        "wear_rate": 0.000010,
        "cliff_threshold": 0.80,
        "cliff_exponent": 2.5,
    },
    "hard": {
        "base_grip": 0.85,
        "wear_rate": 0.000007,
        "cliff_threshold": 0.80,
        "cliff_exponent": 2.5,
    },
    "intermediate": {
        "base_grip": 1.05,
        "wear_rate": 0.000012,
        "cliff_threshold": 0.75,
        "cliff_exponent": 2.5,
    },
    "wet": {
        "base_grip": 0.95,
        "wear_rate": 0.000008,
        "cliff_threshold": 0.80,
        "cliff_exponent": 2.0,
    },
}


def get_compound(name: str | None) -> dict[str, float]:
    """Return compound dict by name, defaulting to medium if invalid."""
    if name in COMPOUNDS:
        return COMPOUNDS[name]
    return COMPOUNDS["medium"]


def get_compound_names() -> list[str]:
    """Return list of valid compound names."""
    return list(COMPOUNDS.keys())


def compute_wear(
    current_wear: float,
    compound_name: str,
    throttle: float,
    curvature: float,
) -> float:
    """Compute new wear value after one tick.

    Wear rate increases with throttle and curvature:
        rate = base_rate * (0.5 + 0.5 * throttle) * (1.0 + curvature * 5.0)

    Returns new wear capped at 1.0.
    """
    compound = get_compound(compound_name)
    base_rate = compound["wear_rate"]
    rate = base_rate * (0.5 + 0.5 * throttle) * (1.0 + curvature * 5.0)
    return min(1.0, current_wear + rate)


def compute_grip_multiplier(wear: float, compound_name: str) -> float:
    """Compute grip multiplier based on wear level.

    Before cliff: base_grip * (1.0 - wear ** 1.5 * 0.3)
    After cliff:  base_grip * max(0.3, 1.0 - ((wear - cliff) / (1 - cliff)) ** exponent)
    """
    compound = get_compound(compound_name)
    base_grip = compound["base_grip"]
    cliff = compound["cliff_threshold"]
    exponent = compound["cliff_exponent"]

    if cliff >= 1.0:
        return base_grip * 0.3

    if wear < cliff:
        return base_grip * (1.0 - wear ** 1.5 * 0.3)

    overshoot = (wear - cliff) / (1.0 - cliff)
    return base_grip * max(0.3, 1.0 - overshoot ** exponent)


def is_past_cliff(wear: float, compound_name: str) -> bool:
    """Return True if wear >= cliff_threshold for the given compound."""
    compound = get_compound(compound_name)
    return wear >= compound["cliff_threshold"]
