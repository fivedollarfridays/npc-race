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
    compute_traction_limit, apply_traction_circle,
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
# Tick helpers — extracted from run_parts_tick
# ---------------------------------------------------------------------------

def _call_powertrain_parts(s: dict, car_parts: dict, defaults: dict, physics_state: dict, tick: int) -> list:
    """Call engine_map, gearbox, fuel_mix. Returns (log, torque_pct, fuel_flow_pct, lambda_val)."""
    log = []
    s["rpm"] = compute_rpm(s["speed_kmh"], s["gear"])

    entry = _safe_call(
        "engine_map", car_parts["engine_map"],
        (s["rpm"], s["throttle_demand"], s["engine_temp"]),
        defaults["engine_map"], tick,
    )
    log.append(entry)
    torque_pct, fuel_flow_pct = entry["output"]

    entry = _safe_call(
        "gearbox", car_parts["gearbox"],
        (s["rpm"], s["speed_kmh"], s["gear"], s["throttle_demand"]),
        defaults["gearbox"], tick,
    )
    log.append(entry)
    s["gear"] = entry["output"]

    laps_left = max(1, s.get("laps_total", 1) - s.get("lap", 0))
    entry = _safe_call(
        "fuel_mix", car_parts["fuel_mix"],
        (s["fuel_remaining_kg"], laps_left, s["position"], s["gap_ahead"]),
        defaults["fuel_mix"], tick,
    )
    log.append(entry)
    lambda_val = entry["output"]

    return log, torque_pct, fuel_flow_pct, lambda_val


def _call_chassis_parts(s: dict, car_parts: dict, defaults: dict, physics_state: dict, tick: int) -> list:
    """Call suspension + cooling. Returns (log, actual_rh, bottoming, cooling_effort)."""
    log = []
    entry = _safe_call(
        "suspension", car_parts["suspension"],
        (s["speed_kmh"], s["lateral_g"], physics_state.get("bump_severity", 0),
         s["ride_height"]),
        defaults["suspension"], tick,
    )
    log.append(entry)
    ride_target = entry["output"]
    actual_rh, bottoming = compute_ride_height_effect(ride_target, s["speed_kmh"])
    s["ride_height"] = actual_rh

    entry = _safe_call(
        "cooling", car_parts["cooling"],
        (s["engine_temp"], s["brake_temp"], s["battery_temp"], s["speed_kmh"]),
        defaults["cooling"], tick,
    )
    log.append(entry)
    cooling_effort = entry["output"]
    s["_cooling_effort"] = cooling_effort

    return log, actual_rh, bottoming, cooling_effort


def _compute_forces(s, hardware_specs, torque_pct, lambda_val, deploy_kw,
                    actual_rh, bottoming, cooling_effort, mass_kg):
    """Compute drive force, downforce, drag, traction. Returns dict of values."""
    mixture_mult = compute_mixture_torque_mult(lambda_val)
    hp = hardware_specs.get("max_hp", 1000)
    temp_penalty = max(0.7, 1.0 - max(0, s["engine_temp"] - 120) * 0.02)
    drive_force = compute_power_force(
        hp * temp_penalty, torque_pct, s["rpm"], s["speed_kmh"],
        deploy_kw, mixture_mult)
    cl = hardware_specs.get("base_cl", 4.5)
    cd = hardware_specs.get("base_cd", 0.88)
    downforce = compute_downforce(s["speed_kmh"], cl, actual_rh)
    drag = compute_drag(s["speed_kmh"], cd, cooling_effort)
    if bottoming:
        downforce *= 0.8
        drag *= 1.1
    rolling_r = mass_kg * 9.81 * 0.008
    tire_mu = 1.4 * (1.0 - s.get("tire_wear", 0) * 0.3)
    traction = compute_traction_limit(tire_mu, mass_kg, downforce)
    return {
        "drive_force": drive_force, "downforce": downforce, "drag": drag,
        "rolling_r": rolling_r, "traction": traction,
    }


def _apply_braking_or_drive(s, physics_state, car_parts, defaults, tick,
                            is_braking, forces, lateral_g,
                            effective_traction, mass_kg, log):
    """Handle brake bias call and net force computation. Appends to log."""
    drive_force = forces["drive_force"]
    drag, rolling_r = forces["drag"], forces["rolling_r"]
    if is_braking:
        entry = _safe_call(
            "brake_bias", car_parts["brake_bias"],
            (s["speed_kmh"], 1.0, s["tire_grip"], s["tire_grip"]),
            defaults["brake_bias"], tick,
        )
        log.append(entry)
        bias = entry["output"]
        ideal_bias = 57
        bias_penalty = max(0.8, 1.0 - abs(bias - ideal_bias) * 0.01)
        target_spd = physics_state.get("target_speed", s["speed_kmh"])
        excess = s["speed_kmh"] - target_spd
        if excess > 0:
            brake_g = min(5.5, 0.5 + excess / 40) * bias_penalty
            raw_brake = -mass_kg * brake_g * 9.81
            return apply_traction_circle(raw_brake, lateral_g, effective_traction, mass_kg)
        raw_drive = drive_force - drag - rolling_r
        return apply_traction_circle(raw_drive, lateral_g, effective_traction, mass_kg)
    log.append({"part": "brake_bias", "tick": tick, "inputs": {},
                 "output": 57, "status": "ok", "error": None})
    raw_drive = drive_force - drag - rolling_r
    return apply_traction_circle(raw_drive, lateral_g, effective_traction, mass_kg)


def _update_temps_and_fuel(s, torque_pct, fuel_flow_pct, lambda_val,
                           cooling_effort, hardware_specs, dt):
    """Update fuel consumption and temperatures."""
    fuel_consumed = compute_fuel_consumption(
        fuel_flow_pct, lambda_val,
        hardware_specs.get("max_fuel_flow_kghr", 100), dt,
    )
    s["fuel_remaining_kg"] = max(0, s["fuel_remaining_kg"] - fuel_consumed)
    s["engine_temp"] = compute_engine_temp(
        s["engine_temp"], torque_pct, s["rpm"], cooling_effort, dt,
    )
    e_cool, b_cool, bat_cool = compute_cooling_effect(
        cooling_effort, s["engine_temp"], s["brake_temp"], s["battery_temp"], dt,
    )
    s["engine_temp"] -= e_cool
    s["brake_temp"] = max(200, s["brake_temp"] - b_cool)
    s["battery_temp"] = max(25, s["battery_temp"] - bat_cool)


def _call_ers_harvest(s, car_parts, defaults, is_braking, downforce,
                      mass_kg, tick, log):
    """Call ERS harvest part. Appends to log. Returns harvest_kw."""
    if is_braking:
        brake_force_for_harvest = compute_braking_force(
            s["speed_kmh"], 1.0, downforce, mass_kg)
        entry = _safe_call(
            "ers_harvest", car_parts["ers_harvest"],
            (brake_force_for_harvest, s["ers_state"]["energy_mj"] / 4.0 * 100,
             s["battery_temp"]),
            defaults["ers_harvest"], tick,
        )
        log.append(entry)
        return entry["output"]
    log.append({"part": "ers_harvest", "tick": tick, "inputs": {},
                 "output": 0, "status": "ok", "error": None})
    return 0


def _sync_physics_state(s: dict, physics_state: dict) -> None:
    """Copy physics inputs into car state dict."""
    s["throttle_demand"] = physics_state.get("throttle_demand", s.get("throttle_demand", 1.0))
    s["lateral_g"] = physics_state.get("lateral_g", s.get("lateral_g", 0.0))
    s["curvature"] = physics_state.get("curvature", s.get("curvature", 0.0))
    s["corner_phase"] = physics_state.get("corner_phase", s.get("corner_phase", "straight"))


def _call_ers_deploy(s: dict, car_parts: dict, defaults: dict, is_braking: bool, tick: int) -> list:
    """Call ERS deploy part. Returns (entry, deploy_kw)."""
    entry = _safe_call(
        "ers_deploy", car_parts["ers_deploy"],
        (s["ers_state"]["energy_mj"] / 4.0 * 100, s["speed_kmh"],
         s["lap"], s["gap_ahead"], is_braking),
        defaults["ers_deploy"], tick,
    )
    deploy_kw = entry["output"] if not is_braking else 0
    return entry, deploy_kw


def _call_diff_and_resolve_forces(s, car_parts, defaults, physics_state,
                                  tick, is_braking, forces, mass_kg, log):
    """Call differential + brake_bias, resolve net force. Appends to log."""
    lateral_g = physics_state.get("lateral_g", 0)
    entry = _safe_call(
        "differential", car_parts["differential"],
        (s["corner_phase"], s["speed_kmh"], s["lateral_g"]),
        defaults["differential"], tick,
    )
    log.append(entry)
    diff_lock = entry["output"]
    diff_traction, _ = compute_diff_effect(diff_lock, lateral_g, s["speed_kmh"])
    effective_traction = forces["traction"] * diff_traction
    net_force = _apply_braking_or_drive(
        s, physics_state, car_parts, defaults, tick, is_braking,
        forces, lateral_g, effective_traction, mass_kg, log)
    return net_force, entry


def _finalize_hybrid(s, car_parts, defaults, is_braking, forces,
                     mass_kg, deploy_kw, diff_entry, tick, dt, log):
    """Handle ERS harvest + hybrid update + strategy. Appends to log."""
    harvest_kw = _call_ers_harvest(
        s, car_parts, defaults, is_braking, forces["downforce"],
        mass_kg, tick, log)
    s["ers_state"], _actual_deploy = update_ers(
        s["ers_state"], deploy_kw, harvest_kw, dt,
    )
    s["battery_temp"] = s["ers_state"]["battery_temp"]
    # Diff re-evaluation (original code does this)
    compute_diff_effect(diff_entry["output"], s["lateral_g"], s["speed_kmh"])
    entry = _safe_call(
        "strategy", car_parts["strategy"], (s,),
        defaults["strategy"], tick,
    )
    log.append(entry)


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
    defaults = get_defaults()
    mass_kg = hardware_specs.get("weight_kg", 798) + s["fuel_remaining_kg"]
    _sync_physics_state(s, physics_state)

    # 1-4. Powertrain parts
    log, torque_pct, fuel_flow_pct, lambda_val = _call_powertrain_parts(
        s, car_parts, defaults, physics_state, tick)

    # 5-6. Chassis parts
    chassis_log, actual_rh, bottoming, cooling_effort = _call_chassis_parts(
        s, car_parts, defaults, physics_state, tick)
    log.extend(chassis_log)

    # 7. ERS deploy
    is_braking = physics_state.get("braking", False)
    entry, deploy_kw = _call_ers_deploy(s, car_parts, defaults, is_braking, tick)
    log.append(entry)

    # 8. Forces + 9. Diff + 10. Brake bias
    forces = _compute_forces(
        s, hardware_specs, torque_pct, lambda_val, deploy_kw,
        actual_rh, bottoming, cooling_effort, mass_kg)
    net_force, diff_entry = _call_diff_and_resolve_forces(
        s, car_parts, defaults, physics_state, tick, is_braking,
        forces, mass_kg, log)

    # 11. Apply acceleration
    accel = net_force / max(1, mass_kg)
    s["speed_kmh"] = max(0, s["speed_kmh"] + accel * dt * 3.6)

    # 12-13. Fuel + temps
    _update_temps_and_fuel(
        s, torque_pct, fuel_flow_pct, lambda_val, cooling_effort,
        hardware_specs, dt)

    # 14-15. ERS harvest + hybrid + strategy
    _finalize_hybrid(
        s, car_parts, defaults, is_braking, forces,
        mass_kg, deploy_kw, diff_entry, tick, dt, log)

    return s, log
