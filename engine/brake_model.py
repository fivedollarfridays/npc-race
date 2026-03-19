"""Brake temperature model — heating from braking, cooling from airflow, fade effect."""

BRAKE_AMBIENT = 20.0
BRAKE_OPTIMAL_LOW = 300.0
BRAKE_OPTIMAL_HIGH = 600.0
BRAKE_FADE_START = 700.0
BRAKE_FADE_MAX = 900.0
BRAKE_MIN_EFFICIENCY = 0.6
HEAT_RATE = 0.15          # per unit braking_force * speed/300
COOL_RATE = 0.08          # per unit speed/300 * dt


def create_brake_state() -> dict:
    """Return initial brake state at ambient temperature."""
    return {"temp": BRAKE_AMBIENT}


def update_brake_temp(
    brake_state: dict, braking_force: float, speed: float, dt: float
) -> dict:
    """Update brake temperature from braking heat and airflow cooling.

    Heating is proportional to braking_force * speed/300 (kinetic energy -> heat).
    Cooling is proportional to speed (airflow) and temp delta from ambient.
    """
    temp = brake_state["temp"]

    # Heating: kinetic energy converted to heat
    heating = HEAT_RATE * braking_force * (speed / 300.0) * dt

    # Cooling: airflow proportional to speed, driven by temp delta
    delta = temp - BRAKE_AMBIENT
    cooling = COOL_RATE * (speed / 300.0) * delta * dt

    temp = temp + heating - cooling
    temp = max(temp, BRAKE_AMBIENT)

    return {"temp": temp}


def get_brake_efficiency(brake_temp: float) -> float:
    """Return braking efficiency [0.6-1.0] based on temperature.

    Below 700C: 1.0 (full efficiency).
    700-900C: linear fade from 1.0 to 0.6.
    Above 900C: clamped at 0.6 (severe fade).
    """
    if brake_temp <= BRAKE_FADE_START:
        return 1.0
    if brake_temp >= BRAKE_FADE_MAX:
        return BRAKE_MIN_EFFICIENCY
    # Linear interpolation in fade range
    fade_range = BRAKE_FADE_MAX - BRAKE_FADE_START
    fade_pct = (brake_temp - BRAKE_FADE_START) / fade_range
    return 1.0 - fade_pct * (1.0 - BRAKE_MIN_EFFICIENCY)


def get_brake_temp_from_state(brake_state: dict) -> float:
    """Return current brake temperature from state dict."""
    return brake_state["temp"]
