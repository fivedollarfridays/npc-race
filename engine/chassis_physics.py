"""Chassis physics — aerodynamics, braking, suspension, cooling.

Your code shapes the chassis. Physics determines the consequences.
"""

AIR_DENSITY = 1.225  # kg/m^3
REFERENCE_AREA = 1.5  # m^2


# ---------------------------------------------------------------------------
# Aerodynamics
# ---------------------------------------------------------------------------


def compute_downforce(speed_kmh: float, cl: float, ride_height: float) -> float:
    """Compute downforce in Newtons. Lower ride height = more ground effect."""
    speed_ms = speed_kmh / 3.6
    # Ground effect multiplier: ride_height -1.0 = max downforce, +1.0 = minimal
    ground_mult = 1.0 + (-ride_height) * 0.3  # -1.0 -> 1.3x, +1.0 -> 0.7x
    ground_mult = max(0.5, min(1.5, ground_mult))
    return 0.5 * AIR_DENSITY * cl * REFERENCE_AREA * speed_ms**2 * ground_mult


def compute_drag(speed_kmh: float, cd: float, cooling_effort: float,
                  ride_height: float = 0.0) -> float:
    """Compute drag force in Newtons. Cooling and ride height add drag."""
    speed_ms = speed_kmh / 3.6
    cooling_drag = 1.0 + cooling_effort * 0.20  # up to +20% drag from cooling
    # Lower ride height = more aggressive floor seal = more drag
    rh_drag = 1.0 + max(0, -0.3 - ride_height) * 0.15  # 0% at -0.3, +7.5% at -0.8
    return 0.5 * AIR_DENSITY * cd * REFERENCE_AREA * speed_ms**2 * cooling_drag * rh_drag


# ---------------------------------------------------------------------------
# Braking
# ---------------------------------------------------------------------------


def compute_braking_force(
    speed_kmh: float, brake_g: float, downforce_n: float, mass_kg: float
) -> float:
    """Compute total braking force. Downforce helps braking."""
    g = 9.81
    weight_force = mass_kg * g
    total_normal = weight_force + downforce_n
    max_decel = brake_g * g  # m/s^2
    return min(total_normal * 1.5, mass_kg * max_decel)  # friction-limited


def apply_brake_bias(
    total_force: float, front_pct: float
) -> tuple[float, float]:
    """Split braking force front/rear. Returns (front_force, rear_force)."""
    front = total_force * front_pct / 100
    rear = total_force * (100 - front_pct) / 100
    return front, rear


def compute_brake_temp_change(
    current_temp: float,
    braking_force: float,
    speed_kmh: float,
    cooling_effort: float,
    dt: float,
) -> float:
    """Update brake temperature from braking heat and airflow cooling."""
    speed_ms = speed_kmh / 3.6
    # Heat from braking: KE conversion
    heat = braking_force * speed_ms * 0.0001 * dt  # simplified
    # Cooling from airflow + dedicated cooling
    cool = (
        (speed_ms / 100)
        * max(0, current_temp - 200)
        * 0.003
        * dt
        * (1 + cooling_effort * 0.5)
    )
    return max(200, current_temp + heat - cool)


# ---------------------------------------------------------------------------
# Suspension
# ---------------------------------------------------------------------------


def compute_ride_height_effect(
    ride_height_target: float, speed_kmh: float
) -> tuple[float, bool]:
    """Compute actual ride height and bottoming-out risk.

    At high speed, downforce compresses suspension — ride height drops.
    Returns (actual_ride_height, bottoming).
    """
    compression = min(0.3, (speed_kmh / 350) ** 2 * 0.3)
    actual = ride_height_target - compression
    actual = max(-1.0, min(1.0, actual))
    bottoming = actual < -0.8
    return actual, bottoming


# ---------------------------------------------------------------------------
# Cooling
# ---------------------------------------------------------------------------


def compute_cooling_effect(
    cooling_effort: float,
    engine_temp: float,
    brake_temp: float,
    battery_temp: float,
    dt: float,
) -> tuple[float, float, float]:
    """Apply cooling. Higher effort = more temp reduction but more drag.

    Returns (engine_cool, brake_cool, battery_cool) — temperature reductions.
    """
    engine_cool = cooling_effort * max(0, engine_temp - 80) * 0.03 * dt
    brake_cool = cooling_effort * max(0, brake_temp - 200) * 0.02 * dt
    battery_cool = cooling_effort * max(0, battery_temp - 25) * 0.04 * dt
    return engine_cool, brake_cool, battery_cool


def compute_traction_limit(tire_grip_mu: float, mass_kg: float,
                           downforce_n: float) -> float:
    """Maximum force tires can transmit (acceleration, braking, or cornering).

    This is the traction circle limit: F_max = mu * N where N = weight + downforce.
    """
    normal_force = mass_kg * 9.81 + downforce_n
    return tire_grip_mu * normal_force


def apply_traction_circle(longitudinal_force: float, lateral_g: float,
                          traction_limit: float, mass_kg: float) -> float:
    """Apply traction circle: available longitudinal force reduced by lateral load.

    sqrt(F_long^2 + F_lat^2) <= traction_limit
    """
    lateral_force = lateral_g * mass_kg * 9.81
    available_long_sq = max(0, traction_limit ** 2 - lateral_force ** 2)
    available_long = available_long_sq ** 0.5
    # Clamp longitudinal force
    if abs(longitudinal_force) > available_long:
        return available_long if longitudinal_force > 0 else -available_long
    return longitudinal_force
