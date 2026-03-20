"""Parts API — 10 car part signatures, defaults, and hardware specs.

Each function IS a car part. Players code these to build their car.
"""

from __future__ import annotations

CAR_PARTS = [
    "engine_map", "gearbox", "ers_deploy", "ers_harvest", "brake_bias",
    "suspension", "cooling", "fuel_mix", "differential", "strategy",
]


# ---------------------------------------------------------------------------
# Default implementations — one per part
# ---------------------------------------------------------------------------

def default_engine_map(rpm: float, throttle_demand: float, engine_temp: float) -> tuple[float, float]:
    """The engine's brain. Return (torque_pct: 0-1, fuel_flow_pct: 0-1)."""
    return (throttle_demand, throttle_demand)


def default_gearbox(rpm: float, speed: float, current_gear: int, throttle: float) -> int:
    """The transmission. Return target_gear (1-8)."""
    if rpm > 12000 and current_gear < 8:
        return current_gear + 1
    if rpm < 7000 and current_gear > 1:
        return current_gear - 1
    return current_gear


def default_ers_deploy(
    battery_pct: float, speed: float, lap: int, gap_ahead: float, braking: bool,
) -> float:
    """Battery deploy system. Return deploy_kw (0-120)."""
    if braking or battery_pct < 20:
        return 0
    return 80


def default_ers_harvest(
    braking_force: float, battery_pct: float, battery_temp: float,
) -> float:
    """Regeneration system. Return harvest_kw (0-120)."""
    if battery_pct > 95 or battery_temp > 50:
        return 0
    return min(120, braking_force * 0.4)


def default_brake_bias(
    speed: float, deceleration_g: float, tire_grip_front: float, tire_grip_rear: float,
) -> float:
    """Brake balance bar. Return front_pct (50-65)."""
    return 57


def default_suspension(
    speed: float, lateral_g: float, bump_severity: float, current_ride_height: float,
) -> float:
    """Ride height controller. Return ride_height_target (-1.0 to 1.0)."""
    if speed > 250:
        return -0.5
    return -0.2


def default_cooling(
    engine_temp: float, brake_temp: float, battery_temp: float, speed: float,
) -> float:
    """Cooling duct controller. Return cooling_effort (0.0-1.0)."""
    if engine_temp > 115 or battery_temp > 50:
        return 0.9
    return 0.4


def default_fuel_mix(
    fuel_remaining_kg: float, laps_left: int, position: int, gap_ahead: float,
) -> float:
    """Fuel mixture valve. Return lambda_value (0.85-1.15)."""
    if laps_left <= 0:
        return 1.0
    rate = fuel_remaining_kg / laps_left
    if rate > 2.2:
        return 0.92
    if rate < 1.6:
        return 1.10
    return 1.0


def default_differential(corner_phase: str, speed: float, lateral_g: float) -> int:
    """Diff lock controller. Return lock_pct (0-100)."""
    if corner_phase == "entry":
        return 40
    if corner_phase == "mid":
        return 25
    if corner_phase == "exit":
        return 70
    return 50


def default_strategy(state: dict) -> dict:
    """Pit wall radio. Return dict with pit/compound/mode decisions."""
    if state.get("tire_wear", 0) > 0.7 and state.get("pit_stops", 0) == 0:
        return {"pit_request": True, "tire_compound_request": "hard"}
    return {"engine_mode": "standard"}


# ---------------------------------------------------------------------------
# Output ranges — for clamping bad code
# ---------------------------------------------------------------------------

OUTPUT_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    "engine_map": {"torque_pct": (0.0, 1.0), "fuel_flow_pct": (0.0, 1.0)},
    "gearbox": {"target_gear": (1, 8)},
    "ers_deploy": {"deploy_kw": (0, 120)},
    "ers_harvest": {"harvest_kw": (0, 120)},
    "brake_bias": {"front_pct": (50, 65)},
    "suspension": {"ride_height_target": (-1.0, 1.0)},
    "cooling": {"cooling_effort": (0.0, 1.0)},
    "fuel_mix": {"lambda_value": (0.85, 1.15)},
    "differential": {"lock_pct": (0, 100)},
}


# ---------------------------------------------------------------------------
# Hardware specs — physical limits
# ---------------------------------------------------------------------------

HARDWARE_SPECS: dict[str, dict[str, dict]] = {
    "ENGINE_SPEC": {
        "v6_1000hp": {
            "max_hp": 1000, "peak_torque_rpm": 10800, "peak_power_rpm": 12500,
            "torque_nm": 300, "max_fuel_flow_kghr": 100,
        },
    },
    "AERO_SPEC": {
        "low_drag": {"base_cl": 3.5, "base_cd": 0.75, "drs_drag_reduction": 0.15},
        "medium_downforce": {"base_cl": 4.5, "base_cd": 0.88, "drs_drag_reduction": 0.12},
        "high_downforce": {"base_cl": 5.5, "base_cd": 1.00, "drs_drag_reduction": 0.10},
    },
    "CHASSIS_SPEC": {
        "standard": {"weight_kg": 798, "fuel_capacity_kg": 110},
        "lightweight": {"weight_kg": 785, "fuel_capacity_kg": 105},
    },
}


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "engine_map": default_engine_map,
    "gearbox": default_gearbox,
    "ers_deploy": default_ers_deploy,
    "ers_harvest": default_ers_harvest,
    "brake_bias": default_brake_bias,
    "suspension": default_suspension,
    "cooling": default_cooling,
    "fuel_mix": default_fuel_mix,
    "differential": default_differential,
    "strategy": default_strategy,
}


def get_defaults() -> dict[str, callable]:
    """Return dict: part_name -> default function."""
    return dict(_DEFAULTS)


def get_hardware_spec(category: str, spec_id: str) -> dict | None:
    """Look up a hardware spec dict. Returns None if not found."""
    cat = HARDWARE_SPECS.get(category)
    if cat is None:
        return None
    return cat.get(spec_id)


def clamp_output(part_name: str, output):
    """Clamp a part's output to valid range. Bad code degrades, doesn't crash."""
    ranges = OUTPUT_RANGES.get(part_name)
    if ranges is None:
        return output
    if isinstance(output, tuple):
        return _clamp_tuple(output, ranges)
    return _clamp_scalar(output, ranges)


def _clamp_tuple(output: tuple, ranges: dict) -> tuple:
    """Clamp each element of a tuple against the range dict (by order)."""
    keys = list(ranges.keys())
    result = []
    for i, val in enumerate(output):
        if i < len(keys):
            lo, hi = ranges[keys[i]]
            result.append(max(lo, min(hi, val)))
        else:
            result.append(val)
    return tuple(result)


def _clamp_scalar(output, ranges: dict):
    """Clamp a scalar against the first range in the dict."""
    lo, hi = next(iter(ranges.values()))
    return max(lo, min(hi, output))
