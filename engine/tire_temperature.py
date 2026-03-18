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
    """Heat generated this tick (degrees C)."""
    return (throttle * 0.4 + curvature * 1.5 + abs(lateral) * 0.3) * dt


def heat_dissipation(tire_temp: float, speed: float, dt: float) -> float:
    """Passive + airflow cooling this tick (degrees C)."""
    return ((tire_temp - AMBIENT_TEMP) * 0.015 + speed * 0.002) * dt


def update_tire_temp(tire_temp: float, heat_gen: float, heat_diss: float) -> float:
    """Apply net heat and clamp to [AMBIENT_TEMP, 150.0]."""
    new_temp = tire_temp + heat_gen - heat_diss
    return max(AMBIENT_TEMP, min(_MAX_TEMP, new_temp))


def tire_temp_grip_factor(tire_temp: float, compound: str) -> float:
    """Return grip multiplier (0.5-1.0) based on temperature and compound.

    - Below window low edge: linear from 0.5 (at AMBIENT_TEMP) to 1.0 (at low edge)
    - Inside window: 1.0
    - Above window high edge: linear from 1.0 (at high edge) to 0.5 (at 150 C)
    """
    optimal = OPTIMAL_TEMP[compound]
    window = TEMP_WINDOW[compound]
    low_edge = optimal - window
    high_edge = optimal + window

    if tire_temp < low_edge:
        # Linear from 0.5 at AMBIENT_TEMP to 1.0 at low_edge
        span = low_edge - AMBIENT_TEMP
        if span <= 0:
            return 1.0
        t = (tire_temp - AMBIENT_TEMP) / span
        t = max(0.0, min(1.0, t))
        return _MIN_GRIP + (_MIN_GRIP * t)  # 0.5 + 0.5*t => 0.5..1.0

    if tire_temp > high_edge:
        # Linear from 1.0 at high_edge to 0.5 at 150
        span = _MAX_TEMP - high_edge
        if span <= 0:
            return 1.0
        t = (tire_temp - high_edge) / span
        t = max(0.0, min(1.0, t))
        return 1.0 - (_MIN_GRIP * t)  # 1.0..0.5

    # Inside the window
    return 1.0
