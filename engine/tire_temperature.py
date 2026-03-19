"""
Tire temperature model — thermal state affects grip.

Tires have an optimal operating window per compound. Cold tires (out-lap)
give less grip; overheated tires blister and lose grip faster.
"""

# --- Constants ---

OPTIMAL_TEMP: dict[str, float] = {"soft": 90.0, "medium": 80.0, "hard": 70.0}
TEMP_WINDOW: dict[str, float] = {"soft": 20.0, "medium": 25.0, "hard": 30.0}
AMBIENT_TEMP: float = 20.0

_MAX_TEMP: float = 150.0
_MIN_GRIP: float = 0.5


# --- Pure functions ---


def heat_generation(
    throttle: float, curvature: float, lateral: float, dt: float
) -> float:
    """Heat generated this tick (degrees C).

    Calibrated so tires reach optimal temp (~80°C) after ~30s of hard driving.
    Corners generate significantly more heat than straights.
    """
    return (throttle * 2.0 + curvature * 8.0 + abs(lateral) * 1.5) * dt


def heat_dissipation(tire_temp: float, speed: float, dt: float) -> float:
    """Passive + airflow cooling this tick (degrees C).

    Passive term dominates; speed adds minor airflow cooling.
    Calibrated for equilibrium at ~80°C under typical lap conditions.
    """
    return ((tire_temp - AMBIENT_TEMP) * 0.036 + speed * 0.00002) * dt


def update_tire_temp(tire_temp: float, heat_gen: float, heat_diss: float) -> float:
    """Apply net heat and clamp to [AMBIENT_TEMP, 150.0]."""
    new_temp = tire_temp + heat_gen - heat_diss
    return max(AMBIENT_TEMP, min(_MAX_TEMP, new_temp))


def tire_temp_grip_factor(tire_temp: float, compound: str) -> float:
    """Return grip multiplier (0.5-1.0) based on temperature and compound.

    Smooth quadratic parabola centered on optimal temperature.
    Grip peaks at 1.0 at optimal and falls off symmetrically.
    """
    optimal = OPTIMAL_TEMP[compound]
    # k calibrated so grip ≈ 0.5 at ambient temp (20°C)
    k = _MIN_GRIP / max(1.0, (optimal - AMBIENT_TEMP)) ** 2
    factor = 1.0 - k * (tire_temp - optimal) ** 2
    return max(_MIN_GRIP, min(1.0, factor))
