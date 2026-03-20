"""Pure physics calculations for NPC Race.

Extracted from simulation.py (T6.1) — constants and stateless math
for speed, acceleration, braking, drafting, drag, and mass.

Recalibrated (T6.2) for realistic F1 speeds (260-350 km/h)
and lap times (Monza ~80s, Monaco ~75s).
"""

# Speed constants (recalibrated for real F1 lap times)
# Track curvatures range 0.001 (straight) to ~0.16 (tight chicane)
BASE_SPEED = 250           # km/h straight-line base
POWER_SPEED_FACTOR = 90    # km/h added per unit of power
WEIGHT_SPEED_PENALTY = 20  # km/h lost per unit of weight
CURVATURE_FACTOR = 16.0    # Curvature scaling — sev=1.0 at curv=0.0625 (more braking)
GRIP_BASE_SPEED = 55       # km/h minimum corner speed (real chicane ~68 km/h)
GRIP_SPEED_RANGE = 80      # km/h range from grip (tight corners 55-135 depending on grip)
ACCEL_BASE = 40            # F1 realistic acceleration
ACCEL_POWER_FACTOR = 45    # Power advantage in acceleration
WEIGHT_MASS_FACTOR = 1.2
BRAKE_BASE = 180           # Strong F1 brakes
BRAKE_FACTOR = 120
DRAFT_BONUS_BASE = 5       # Reduced draft bonus
DRAFT_MAX_DISTANCE = 40

# Aerodynamic drag — creates natural speed limit ~330-345
DRAG_COEFFICIENT = 0.00015

# Aerodynamic downforce/grip
DOWNFORCE_GRIP_FACTOR = 0.25   # Max aero grip bonus at reference speed
DOWNFORCE_REF_SPEED = 300.0    # km/h

# Hard speed cap — safety net only, drag should limit before this
MAX_SPEED = 355.0


def compute_target_speed(power: float, grip: float, weight: float,
                         curvature: float, throttle: float,
                         tire_grip_mult: float = 1.0,
                         temp_grip_mult: float = 1.0,
                         power_mode: float = 1.0,
                         boost_active: bool = False,
                         setup: dict | None = None) -> float:
    """Calculate target speed based on car stats and track conditions.

    Combines base max speed with curvature-based corner speed.
    Setup modifies effective power if provided.
    """
    effective_power = setup.get("effective_power", power) if setup else power
    base_max_speed = (BASE_SPEED + effective_power * POWER_SPEED_FACTOR * power_mode
                      - weight * WEIGHT_SPEED_PENALTY)
    if boost_active:
        base_max_speed *= 1.25
    effective_grip = grip * tire_grip_mult * temp_grip_mult
    curv_severity = min(1.0, curvature * CURVATURE_FACTOR)
    grip_speed = GRIP_BASE_SPEED + effective_grip * GRIP_SPEED_RANGE
    target = (
        base_max_speed * (1.0 - curv_severity)
        + grip_speed * curv_severity
    ) * throttle
    return max(40, min(MAX_SPEED, target))


def apply_drag(speed: float, dt: float) -> float:
    """Apply v-squared aerodynamic drag. Returns speed after drag."""
    if speed <= 0:
        return 0.0
    drag = speed * speed * DRAG_COEFFICIENT * dt
    return max(0.0, speed - drag)


def compute_acceleration(speed: float, target_speed: float,
                         power: float, mass_factor: float,
                         dt: float) -> float:
    """Accelerate toward target speed. Returns new speed (never exceeds target)."""
    if target_speed <= speed:
        return speed
    accel_rate = (ACCEL_BASE + power * ACCEL_POWER_FACTOR) / mass_factor * dt
    return min(target_speed, speed + accel_rate)


def compute_braking(speed: float, target_speed: float,
                    brakes: float, dt: float) -> float:
    """Brake toward target speed. Returns new speed (never below target)."""
    if target_speed >= speed:
        return speed
    brake_rate = (BRAKE_BASE + brakes * BRAKE_FACTOR) * dt
    return max(target_speed, speed - brake_rate)


def compute_mass_factor(weight: float, fuel_weight: float) -> float:
    """Compute mass factor for acceleration. Higher = slower accel."""
    return 1.0 + weight * WEIGHT_MASS_FACTOR + fuel_weight


def compute_draft_bonus(aero: float, distance_ahead: float,
                        dt: float) -> float:
    """Speed bonus from drafting. Returns 0 if out of range."""
    if distance_ahead <= 5 or distance_ahead >= DRAFT_MAX_DISTANCE:
        return 0.0
    return aero * DRAFT_BONUS_BASE * (1 - distance_ahead / DRAFT_MAX_DISTANCE) * dt


def update_speed(speed: float, target_speed: float, power: float,
                 weight: float, fuel_weight: float, brakes: float,
                 dt: float) -> float:
    """Apply acceleration or braking toward target. Returns new speed.

    Drag is applied separately in simulation step. Speed cap enforced here.
    """
    mf = compute_mass_factor(weight, fuel_weight)
    if target_speed > speed:
        new_speed = compute_acceleration(speed, target_speed, power, mf, dt)
    else:
        new_speed = compute_braking(speed, target_speed, brakes, dt)
    return min(MAX_SPEED, new_speed)


def compute_aero_grip(speed: float, aero: float,
                      wing_angle: float = 0.0) -> float:
    """Speed-dependent grip bonus from aerodynamic downforce.

    Returns additional grip (0.0-0.35). Proportional to v-squared.
    At 300 km/h, aero=1.0: ~0.25. At 60 km/h: ~0.01 (negligible).
    """
    if speed <= 0:
        return 0.0
    speed_factor = (speed / DOWNFORCE_REF_SPEED) ** 2
    speed_factor = min(1.5, speed_factor)  # cap above ref speed
    wing_mult = 1.0 + wing_angle * 0.15
    return DOWNFORCE_GRIP_FACTOR * aero * speed_factor * wing_mult


def compute_lateral_push(lat_diff: float, distance: float,
                         dt: float) -> float:
    """Proximity resistance push when two cars are close laterally."""
    if abs(lat_diff) >= 0.3 or distance >= 10:
        return 0.0
    push = 0.1 * (1.0 - distance / 10) * dt
    return push if lat_diff >= 0 else -push
