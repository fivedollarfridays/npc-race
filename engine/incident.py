"""Spin and lockup incident model."""
import random

BASE_SPIN_RISK = 0.00005
SPIN_RECOVERY_TICKS_MIN = 90   # 3 seconds at 30 tps
SPIN_RECOVERY_TICKS_MAX = 150  # 5 seconds
SPIN_TIRE_WEAR_PENALTY = 0.05
SPIN_SC_PROBABILITY = 0.20
LOCKUP_FLAT_SPOT_WEAR = 0.02
LOCKUP_SPEED_PENALTY = 5.0
LOCKUP_DURATION_TICKS = 30


def compute_spin_risk(grip_available: float, grip_demanded: float,
                      dirty_air_factor: float, tire_wear: float,
                      tire_age_laps: int) -> float:
    """Return spin probability for this tick.

    grip_available: effective grip multiplier (0-2+)
    grip_demanded: how much grip the car needs (curvature x speed proxy)
    dirty_air_factor: 0.92-1.0 (lower = more dirty air)
    tire_wear: 0.0-1.0
    tire_age_laps: laps since fresh tires (0 = just pitted, cold)
    """
    if grip_available <= 0:
        deficit = 5.0
    elif grip_demanded <= grip_available:
        deficit = 0.0
    else:
        deficit = (grip_demanded / grip_available) - 1.0
    deficit_factor = 1.0 + deficit * 10.0

    dirty_factor = 1.0 + (1.0 - dirty_air_factor) * 5.0
    tire_factor = 1.0 + tire_wear * 3.0
    cold_factor = 2.0 if tire_age_laps < 2 else 1.0

    return BASE_SPIN_RISK * deficit_factor * dirty_factor * tire_factor * cold_factor


def check_spin(spin_risk: float, rng: random.Random) -> bool:
    """Roll the dice. Returns True if car spins this tick."""
    return rng.random() < spin_risk


def create_spin_event(rng: random.Random) -> dict:
    """Create a spin event with recovery time and consequences."""
    recovery = rng.randint(SPIN_RECOVERY_TICKS_MIN, SPIN_RECOVERY_TICKS_MAX)
    trigger_sc = rng.random() < SPIN_SC_PROBABILITY
    return {
        "recovery_ticks": recovery,
        "tire_penalty": SPIN_TIRE_WEAR_PENALTY,
        "trigger_sc": trigger_sc,
    }


def compute_lockup_risk(braking_force: float, grip_available: float) -> float:
    """Return lockup probability when braking hard."""
    if grip_available <= 0 or braking_force <= 0:
        return 0.0
    excess = max(0.0, braking_force / max(0.01, grip_available) - 0.8)
    return min(0.01, excess * 0.005)


def create_lockup_event() -> dict:
    """Create a lockup event: flat spot and speed penalty."""
    return {
        "flat_spot_wear": LOCKUP_FLAT_SPOT_WEAR,
        "speed_penalty": LOCKUP_SPEED_PENALTY,
        "duration_ticks": LOCKUP_DURATION_TICKS,
    }
