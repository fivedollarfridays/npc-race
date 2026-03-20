"""Parts runner — sandbox that runs your car's code every tick.

Calls all 10 part functions, feeds outputs into physics engines,
handles errors, and logs every call.
"""

from __future__ import annotations

from .parts_api import CAR_PARTS, clamp_output, get_defaults
from .powertrain_physics import (
    compute_rpm, compute_fuel_consumption,
    compute_engine_temp, compute_mixture_torque_mult, compute_power_force,
)
from .chassis_physics import (
    compute_downforce, compute_drag, compute_braking_force,
    compute_ride_height_effect, compute_cooling_effect,
)
from .hybrid_physics import update_ers, compute_diff_effect, create_ers_state


# ---------------------------------------------------------------------------
# State creation
# ---------------------------------------------------------------------------

def create_initial_state(hardware_specs: dict) -> dict:
    """Create a fresh car state for race start."""
    chassis = hardware_specs.get("chassis", {})
    fuel_cap = chassis.get("fuel_capacity_kg", 110)
    return {
        "speed_kmh": 0.0,
        "rpm": 4000.0,
        "gear": 1,
        "engine_temp": 90.0,
        "brake_temp": 200.0,
        "battery_temp": 30.0,
        "fuel_remaining_kg": fuel_cap,
        "fuel_capacity_kg": fuel_cap,
        "tire_wear": 0.0,
        "tire_grip": 1.0,
        "ers_state": create_ers_state(),
        "ride_height": -0.2,
        "lateral_g": 0.0,
        "curvature": 0.0,
        "corner_phase": "straight",
        "lap": 0,
        "laps_total": 0,
        "position": 1,
        "gap_ahead": 99.0,
        "pit_stops": 0,
        "throttle_demand": 0.0,
    }


# ---------------------------------------------------------------------------
# Safe call wrapper
# ---------------------------------------------------------------------------

def _safe_call(
    part_name: str, func, args: tuple, default_func, tick: int,
) -> dict:
    """Call player's part function. If it crashes, use default."""
    try:
        result = func(*args)
        clamped = clamp_output(part_name, result)
        status = "clamped" if clamped != result else "ok"
        return {
            "part": part_name, "tick": tick,
            "inputs": {f"arg{i}": a for i, a in enumerate(args)},
            "output": clamped, "status": status,
            "error": None,
        }
    except Exception as e:
        result = default_func(*args)
        clamped = clamp_output(part_name, result)
        return {
            "part": part_name, "tick": tick,
            "inputs": {f"arg{i}": a for i, a in enumerate(args)},
            "output": clamped, "status": "error",
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Part function extraction
# ---------------------------------------------------------------------------

def get_part_functions(car_module, defaults: dict) -> dict:
    """Extract part functions from a car module. Use defaults for missing."""
    parts = {}
    for name in CAR_PARTS:
        func = getattr(car_module, name, None) if car_module else None
        parts[name] = func if callable(func) else defaults[name]
    return parts


# ---------------------------------------------------------------------------
# Main tick runner
# ---------------------------------------------------------------------------

def run_parts_tick(
    car_parts: dict, car_state: dict, physics_state: dict,
    hardware_specs: dict, dt: float, tick: int = 0,
) -> tuple[dict, list[dict]]:
    """Run all 10 part functions for one tick.

    Returns (updated_state, call_log).
    """
    s = dict(car_state)  # shallow copy
    log: list[dict] = []
    defaults = get_defaults()
    # Hardware specs can be flat (merged) or nested — handle both
    engine_spec = hardware_specs
    aero_spec = hardware_specs
    mass_kg = hardware_specs.get("weight_kg", 798) + s["fuel_remaining_kg"]
    # Throttle demand comes from driver/physics, not car state
    s["throttle_demand"] = physics_state.get("throttle_demand", s.get("throttle_demand", 1.0))
    s["lateral_g"] = physics_state.get("lateral_g", s.get("lateral_g", 0.0))
    s["curvature"] = physics_state.get("curvature", s.get("curvature", 0.0))
    s["corner_phase"] = physics_state.get("corner_phase", s.get("corner_phase", "straight"))

    # 1. Compute RPM from current speed + gear
    s["rpm"] = compute_rpm(s["speed_kmh"], s["gear"])

    # 2. engine_map
    entry = _safe_call(
        "engine_map", car_parts["engine_map"],
        (s["rpm"], s["throttle_demand"], s["engine_temp"]),
        defaults["engine_map"], tick,
    )
    log.append(entry)
    torque_pct, fuel_flow_pct = entry["output"]

    # 3. gearbox
    entry = _safe_call(
        "gearbox", car_parts["gearbox"],
        (s["rpm"], s["speed_kmh"], s["gear"], s["throttle_demand"]),
        defaults["gearbox"], tick,
    )
    log.append(entry)
    s["gear"] = entry["output"]

    # 4. fuel_mix
    laps_left = max(1, s.get("laps_total", 1) - s.get("lap", 0))
    entry = _safe_call(
        "fuel_mix", car_parts["fuel_mix"],
        (s["fuel_remaining_kg"], laps_left, s["position"], s["gap_ahead"]),
        defaults["fuel_mix"], tick,
    )
    log.append(entry)
    lambda_val = entry["output"]

    # 5. Apply powertrain physics — power-based model (F = P/v)
    mixture_mult = compute_mixture_torque_mult(lambda_val)
    hp = engine_spec.get("max_hp", 1000)
    drive_force = compute_power_force(
        hp, torque_pct, s["rpm"], s["speed_kmh"], 0, mixture_mult)
    cooling_eff = s.get("_cooling_effort", 0.4)
    drag = compute_drag(s["speed_kmh"], aero_spec.get("base_cd", 0.88), cooling_eff)
    rolling_r = mass_kg * 9.81 * 0.008  # rolling resistance ~0.8%
    if physics_state.get("braking"):
        target_spd = physics_state.get("target_speed", s["speed_kmh"])
        excess = s["speed_kmh"] - target_spd
        if excess > 0:
            brake_g = min(5.5, 0.5 + excess / 40)  # proportional 0.5-5.5G
            net_force = -mass_kg * brake_g * 9.81
        else:
            net_force = drive_force - drag - rolling_r
    else:
        net_force = drive_force - drag - rolling_r
    accel = net_force / max(1, mass_kg)
    s["speed_kmh"] = max(0, s["speed_kmh"] + accel * dt * 3.6)

    fuel_consumed = compute_fuel_consumption(
        fuel_flow_pct, lambda_val,
        engine_spec.get("max_fuel_flow_kghr", 100), dt,
    )
    s["fuel_remaining_kg"] = max(0, s["fuel_remaining_kg"] - fuel_consumed)

    s["engine_temp"] = compute_engine_temp(
        s["engine_temp"], torque_pct, s["rpm"], 0.4, dt,
    )

    # 6. suspension
    entry = _safe_call(
        "suspension", car_parts["suspension"],
        (s["speed_kmh"], s["lateral_g"], physics_state.get("bump_severity", 0),
         s["ride_height"]),
        defaults["suspension"], tick,
    )
    log.append(entry)
    ride_target = entry["output"]

    # 7. cooling
    entry = _safe_call(
        "cooling", car_parts["cooling"],
        (s["engine_temp"], s["brake_temp"], s["battery_temp"], s["speed_kmh"]),
        defaults["cooling"], tick,
    )
    log.append(entry)
    cooling_effort = entry["output"]

    # 8. Apply chassis physics
    actual_rh, _bottoming = compute_ride_height_effect(ride_target, s["speed_kmh"])
    s["ride_height"] = actual_rh
    downforce = compute_downforce(
        s["speed_kmh"], aero_spec.get("base_cl", 4.5), actual_rh,
    )
    e_cool, b_cool, bat_cool = compute_cooling_effect(
        cooling_effort, s["engine_temp"], s["brake_temp"], s["battery_temp"], dt,
    )
    s["engine_temp"] -= e_cool
    s["brake_temp"] = max(200, s["brake_temp"] - b_cool)
    s["battery_temp"] = max(25, s["battery_temp"] - bat_cool)

    # 9. brake_bias (only if braking)
    is_braking = s["throttle_demand"] < 0.1 and s["speed_kmh"] > 10
    if is_braking:
        entry = _safe_call(
            "brake_bias", car_parts["brake_bias"],
            (s["speed_kmh"], 1.0, s["tire_grip"], s["tire_grip"]),
            defaults["brake_bias"], tick,
        )
        log.append(entry)
    else:
        log.append({
            "part": "brake_bias", "tick": tick,
            "inputs": {}, "output": 57, "status": "ok", "error": None,
        })

    # 10. ers_deploy
    entry = _safe_call(
        "ers_deploy", car_parts["ers_deploy"],
        (s["ers_state"]["energy_mj"] / 4.0 * 100, s["speed_kmh"],
         s["lap"], s["gap_ahead"], is_braking),
        defaults["ers_deploy"], tick,
    )
    log.append(entry)
    deploy_kw = entry["output"]

    # 11. ers_harvest (only if braking)
    if is_braking:
        brake_force = compute_braking_force(
            s["speed_kmh"], 1.0, downforce, mass_kg,
        )
        entry = _safe_call(
            "ers_harvest", car_parts["ers_harvest"],
            (brake_force, s["ers_state"]["energy_mj"] / 4.0 * 100,
             s["battery_temp"]),
            defaults["ers_harvest"], tick,
        )
        log.append(entry)
        harvest_kw = entry["output"]
    else:
        log.append({
            "part": "ers_harvest", "tick": tick,
            "inputs": {}, "output": 0, "status": "ok", "error": None,
        })
        harvest_kw = 0

    # 12. differential
    entry = _safe_call(
        "differential", car_parts["differential"],
        (s["corner_phase"], s["speed_kmh"], s["lateral_g"]),
        defaults["differential"], tick,
    )
    log.append(entry)

    # 13. Apply hybrid physics
    s["ers_state"], _actual_deploy = update_ers(
        s["ers_state"], deploy_kw, harvest_kw, dt,
    )
    s["battery_temp"] = s["ers_state"]["battery_temp"]

    traction_mult, _understeer = compute_diff_effect(
        entry["output"], s["lateral_g"], s["speed_kmh"],
    )

    # 14. strategy
    entry = _safe_call(
        "strategy", car_parts["strategy"],
        (s,),
        defaults["strategy"], tick,
    )
    log.append(entry)

    return s, log
