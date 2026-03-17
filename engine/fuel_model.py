"""
Fuel load physics for NPC Race.

Provides fuel consumption, engine mode lookup, starting fuel
computation, and weight-from-fuel calculation. Purely functional
— no state mutation.
"""

BASE_CONSUMPTION_KG_PER_M = 0.000055  # ~0.055 g/m, ~3.5 kg/lap at 5500m
FUEL_MARGIN = 1.05  # 5% extra fuel loaded
MAX_FUEL_WEIGHT_FACTOR = 0.6  # full tank adds 0.6 normalized weight

ENGINE_MODES: dict[str, dict[str, float]] = {
    "push": {"consumption_mult": 1.25, "power_mult": 1.03},
    "standard": {"consumption_mult": 1.00, "power_mult": 1.00},
    "conserve": {"consumption_mult": 0.80, "power_mult": 0.95},
}


def get_engine_mode(name: str | None) -> dict[str, float]:
    """Return engine mode dict. Defaults to 'standard' if name is invalid."""
    if name is None or name not in ENGINE_MODES:
        return ENGINE_MODES["standard"]
    return ENGINE_MODES[name]


def get_engine_mode_names() -> list[str]:
    """Return list of valid engine mode names."""
    return list(ENGINE_MODES.keys())


def compute_starting_fuel(laps: int, track_length_m: float) -> float:
    """Compute starting fuel in kg for a race.

    Formula: laps * track_length_m * BASE_CONSUMPTION_KG_PER_M * FUEL_MARGIN
    """
    return laps * track_length_m * BASE_CONSUMPTION_KG_PER_M * FUEL_MARGIN


def compute_fuel_consumption(
    throttle: float,
    engine_mode_name: str,
    base_rate_per_tick: float,
    dt: float,
) -> float:
    """Compute fuel consumed this tick in kg.

    Args:
        throttle: 0.0-1.0 throttle input.
        engine_mode_name: Engine mode name (push/standard/conserve).
        base_rate_per_tick: Pre-calibrated base consumption per tick at
            full throttle in standard mode. Computed once at race start
            as starting_fuel / (laps * estimated_ticks_per_lap).
        dt: Time delta (typically 1.0 for per-tick calls).

    Returns:
        Fuel consumed in kg (always >= 0).
    """
    mode = get_engine_mode(engine_mode_name)
    consumed = base_rate_per_tick * throttle * mode["consumption_mult"] * dt
    return max(0.0, consumed)


def compute_weight_from_fuel(fuel_kg: float, max_fuel_kg: float) -> float:
    """Return normalized weight penalty (0-1) from current fuel load.

    Full tank yields MAX_FUEL_WEIGHT_FACTOR; empty tank yields 0.
    """
    if fuel_kg <= 0.0 or max_fuel_kg <= 0.0:
        return 0.0
    ratio = min(1.0, fuel_kg / max_fuel_kg)
    return ratio * MAX_FUEL_WEIGHT_FACTOR
