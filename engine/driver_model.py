"""F1 Driver Model — two-mode AI that handles all driving.

Deterministic mode: optimal throttle/braking/line from pre-computed profiles.
Reactive mode: learned adjustments for disruptions (collisions, weather, wear).
"""

from .speed_profile import compute_speed_profile, get_profile_speed
from .racing_line import compute_racing_line, get_line_lateral

# Conservative defaults for reactive behavior (learned over races)
DEFAULT_REACTIVE = {
    "recovery_throttle": 0.6,      # throttle after collision (0-1)
    "overtake_aggression": 0.3,    # 0=wait for DRS, 1=dive every corner
    "tire_cliff_reduction": 0.20,  # speed reduction near tire cliff
    "wet_caution": 0.30,           # speed reduction in wet
}


def create_driver(track_points, curvatures, distances, headings,
                  track_length, car_stats: dict) -> dict:
    """Create a driver with pre-computed speed profile and racing line."""
    profile = compute_speed_profile(
        track_points, curvatures, distances, track_length, car_stats)
    line = compute_racing_line(track_points, curvatures, headings)
    return {
        "profile": profile,
        "line": line,
        "distances": distances,
        "track_length": track_length,
        "reactive": dict(DEFAULT_REACTIVE),
        "last_speed": 0.0,
        "recovery_ticks": 0,
    }


def compute_driver_inputs(driver: dict, car_state: dict,
                          tire_wear: float = 0.0, wetness: float = 0.0,
                          damage: float = 0.0) -> dict:
    """Compute optimal driving inputs for this tick.

    Returns {"throttle": float, "lateral_target": float}
    """
    distance = car_state.get("distance", 0.0)
    current_speed = car_state.get("speed", 0.0)

    # Get optimal speed from profile
    target = get_profile_speed(
        driver["profile"], distance, driver["distances"], driver["track_length"])

    # Adjust for conditions
    target = adjust_profile_for_conditions(target, tire_wear, wetness, damage)

    # Reactive: reduce throttle during recovery
    reactive = driver.get("reactive", DEFAULT_REACTIVE)
    if driver.get("recovery_ticks", 0) > 0:
        driver["recovery_ticks"] -= 1
        target *= reactive["recovery_throttle"]

    # Check for sudden speed loss (collision) — enter recovery
    if driver["last_speed"] > 0 and current_speed < driver["last_speed"] * 0.7:
        driver["recovery_ticks"] = 30  # 1 second recovery
    driver["last_speed"] = current_speed

    # Compute throttle from speed vs target
    if current_speed > target * 1.05:
        throttle = 0.0  # braking — lift completely
    elif current_speed > target * 0.95:
        throttle = 0.5  # maintenance — partial throttle
    elif current_speed > target * 0.8:
        throttle = 0.8  # approaching target
    else:
        throttle = 1.0  # accelerating — full power

    # Get lateral target from racing line
    lateral = get_line_lateral(
        driver["line"], distance, driver["distances"], driver["track_length"])

    return {"throttle": throttle, "lateral_target": lateral}


def adjust_profile_for_conditions(base_speed: float, tire_wear: float,
                                  wetness: float, damage: float) -> float:
    """Reduce target speed based on current conditions."""
    factor = 1.0
    factor -= tire_wear * 0.15       # worn tires → up to 15% slower
    factor -= wetness * 0.25         # wet → up to 25% slower
    factor -= damage * 0.10          # damage → up to 10% slower
    return base_speed * max(0.5, factor)


def compute_reactive_inputs(driver: dict, car_state: dict,
                            reactive_data: dict) -> dict:
    """Adjust driving based on reactive conditions (post-collision, tire cliff)."""
    tire_wear = car_state.get("tire_wear", 0.0)
    adjustments = {}

    # Tire cliff management
    if tire_wear > 0.7:
        cliff_reduction = reactive_data.get("tire_cliff_reduction", 0.20)
        adjustments["speed_factor"] = 1.0 - cliff_reduction

    return adjustments


def update_reactive_data(reactive_data: dict, race_events: list) -> dict:
    """Update reactive parameters based on race outcomes."""
    updated = dict(reactive_data)
    # Count successful recoveries vs failures
    spins_after_contact = sum(1 for e in race_events
                              if e.get("type") == "SPIN")
    if spins_after_contact == 0 and updated["recovery_throttle"] < 0.9:
        updated["recovery_throttle"] = min(0.9, updated["recovery_throttle"] + 0.05)
    elif spins_after_contact > 2:
        updated["recovery_throttle"] = max(0.4, updated["recovery_throttle"] - 0.05)
    return updated
