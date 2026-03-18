"""
Car setup sliders for pre-race configuration.

Setup sliders are tradeoffs: high wing gives more downforce
(grip/corner bonus) but reduces top speed.
"""

DEFAULT_SETUP: dict = {
    "wing_angle":    0.0,   # -1.0 (low drag) to +1.0 (high downforce)
    "brake_bias":    0.5,   # 0.3 (rear) to 0.7 (front-heavy)
    "suspension":    0.0,   # -1.0 (soft) to +1.0 (stiff)
    "tire_pressure": 0.0,   # -1.0 (low) to +1.0 (high)
}

SETUP_BOUNDS: dict = {
    "wing_angle":    (-1.0, 1.0),
    "brake_bias":    (0.3, 0.7),
    "suspension":    (-1.0, 1.0),
    "tire_pressure": (-1.0, 1.0),
}


def validate_setup(raw: dict) -> dict:
    """Merge raw with DEFAULT_SETUP, clamp values to SETUP_BOUNDS.

    Unknown keys are dropped. Returns a clean dict.
    """
    result = dict(DEFAULT_SETUP)
    for key in DEFAULT_SETUP:
        if key in raw:
            lo, hi = SETUP_BOUNDS[key]
            result[key] = max(lo, min(hi, raw[key]))
    return result


def wing_effect(wing_angle: float) -> tuple[float, float]:
    """Return (aero_mult, power_mult) for a given wing angle.

    High wing (+1.0): aero_mult=1.15, power_mult=0.92
    Low wing (-1.0):  aero_mult=0.85, power_mult=1.08
    Neutral (0.0):    both 1.0. Linear interpolation.
    """
    aero_mult = 1.0 + wing_angle * 0.15
    power_mult = 1.0 - wing_angle * 0.08
    return aero_mult, power_mult


def brake_bias_effect(bias: float) -> float:
    """Return brakes_mult based on deviation from optimal 0.58.

    Parabolic: 1.0 - 0.5 * ((bias - 0.58) / 0.22) ** 2, clamped to 0.8 min.
    """
    deviation = (bias - 0.58) / 0.22
    mult = 1.0 - 0.5 * deviation * deviation
    return max(0.8, mult)


def suspension_effect(stiffness: float) -> float:
    """Return temp_rate_mult for tire heat generation.

    Stiff (+1.0) -> 1.25, soft (-1.0) -> 0.75. Linear: 1.0 + stiffness * 0.25.
    """
    return 1.0 + stiffness * 0.25


def tire_pressure_effect(pressure: float) -> tuple[float, float]:
    """Return (temp_offset_C, rolling_resist_mult).

    High pressure (+1.0): +10 C, 0.97 rolling resistance.
    Low pressure  (-1.0): -10 C, 1.03 rolling resistance.
    Linear interpolation.
    """
    temp_offset = pressure * 10.0
    rolling_resist_mult = 1.0 - pressure * 0.03
    return temp_offset, rolling_resist_mult


def apply_setup(car_stats: dict, setup: dict) -> dict:
    """Return adjusted stats dict. Does NOT mutate car_stats.

    car_stats keys: power, grip, weight, aero, brakes (all ints).
    setup: from validate_setup().
    """
    aero_mult, power_mult = wing_effect(setup["wing_angle"])
    brakes_mult = brake_bias_effect(setup["brake_bias"])
    temp_rate_mult = suspension_effect(setup["suspension"])
    temp_offset, _rolling = tire_pressure_effect(setup["tire_pressure"])

    return {
        "effective_power":  car_stats["power"] * power_mult,
        "effective_aero":   car_stats["aero"] * aero_mult,
        "effective_brakes": car_stats["brakes"] * brakes_mult,
        "temp_rate_mult":   temp_rate_mult,
        "temp_offset":      temp_offset,
    }
