"""Efficiency engine — per-part efficiency factors multiply into car performance.

Better code -> higher efficiency -> faster car. Uses t-1 state for stability.
"""

from .safe_call import _safe_call_with_timeout
from .parts_api import get_defaults
from .powertrain_physics import (
    compute_rpm, compute_fuel_consumption, compute_engine_temp,
)
from .chassis_physics import (
    compute_ride_height_effect, compute_cooling_effect,
    apply_traction_circle,
)
from .hybrid_physics import update_ers

# Re-export all efficiency helpers so existing imports keep working
from .efficiency_helpers import (  # noqa: F401
    compute_grip_factor,
    compute_gearbox_efficiency,
    compute_ers_waste,
    compute_brake_bias_efficiency,
    compute_suspension_efficiency,
    compute_cooling_efficiency,
    compute_diff_efficiency,
    compute_fuel_mix_efficiency,
    compute_forces_and_traction,
    compute_diff_and_grip,
)


def _apply_braking(s, physics_state, brake_bias_val, grip_f, grip_r,
                    drive_force, drag, rolling_r, product, lateral_g,
                    effective_traction, mass_kg):
    """Returns (net_force, brake_g, excess)."""
    is_braking = physics_state.get("braking", False)
    brake_g = 0.0
    excess = 0.0
    if is_braking:
        target_spd = physics_state.get("target_speed", s["speed_kmh"])
        excess = s["speed_kmh"] - target_spd
        if excess > 0:
            brake_g = min(5.5, 0.5 + excess / 40)
            total_brake = mass_kg * brake_g * 9.81
            front_demand = total_brake * brake_bias_val / 100
            rear_demand = total_brake * (100 - brake_bias_val) / 100
            front_actual = min(front_demand, grip_f)
            rear_actual = min(rear_demand, grip_r)
            raw_brake = -(front_actual + rear_actual)
            net_force = apply_traction_circle(raw_brake, lateral_g, effective_traction, mass_kg)
        else:
            raw_drive = (drive_force - drag - rolling_r) * product
            net_force = apply_traction_circle(raw_drive, lateral_g, effective_traction, mass_kg)
    else:
        raw_drive = (drive_force - drag - rolling_r) * product
        net_force = apply_traction_circle(raw_drive, lateral_g, effective_traction, mass_kg)
    return net_force, brake_g, excess


def _update_state(s, torque_pct, fuel_flow_pct, lambda_val, cooling_effort,
                  drive_force, traction, lateral_g, is_braking, brake_g,
                  excess, deploy_kw, harvest_kw, hw, dt):
    """Update fuel, temps, tire wear, ERS."""
    fuel_consumed = compute_fuel_consumption(
        fuel_flow_pct, lambda_val, hw.get("max_fuel_flow_kghr", 100), dt)
    s["fuel_remaining_kg"] = max(0, s["fuel_remaining_kg"] - fuel_consumed)
    s["engine_temp"] = compute_engine_temp(
        s["engine_temp"], torque_pct, s["rpm"], cooling_effort, dt)
    e_cool, b_cool, bat_cool = compute_cooling_effect(
        cooling_effort, s["engine_temp"], s["brake_temp"], s["battery_temp"], dt)
    s["engine_temp"] -= e_cool
    s["brake_temp"] = max(200, s["brake_temp"] - b_cool)
    s["battery_temp"] = max(25, s["battery_temp"] - bat_cool)

    # Tire wear from wheelspin
    if drive_force > traction and not is_braking:
        wheelspin = (drive_force - traction) / max(1, traction)
        s["tire_wear"] = min(1.0, s.get("tire_wear", 0) + wheelspin * 0.002 * dt)
        tire_temp = s.get("tire_temp", 85.0)
        s["tire_temp"] = tire_temp + wheelspin * 8.0 * dt
    # Cornering wear
    if lateral_g > 0.5:
        corner_wear = (lateral_g - 0.5) * 0.00009 * dt
        s["tire_wear"] = min(1.0, s.get("tire_wear", 0) + corner_wear)
    # Tire temp cools toward ambient
    tire_temp = s.get("tire_temp", 85.0)
    s["tire_temp"] = max(50, tire_temp - (tire_temp - 85.0) * 0.02 * dt)

    # ERS
    s["ers_state"], _ = update_ers(s["ers_state"], deploy_kw, harvest_kw, dt)
    s["battery_temp"] = s["ers_state"]["battery_temp"]


def _call_powertrain(s, car_parts, defaults, physics_state, tick, g_ctx):
    """Call engine_map, gearbox, fuel_mix. Returns (log, torque_pct, fuel_flow_pct, lambda_val, gb_eff, fuel_eff)."""
    log = []
    s["rpm"] = compute_rpm(s["speed_kmh"], s["gear"])
    entry = _safe_call_with_timeout(
        "engine_map", car_parts.get("engine_map", defaults["engine_map"]),
        (s["rpm"], s["throttle_demand"], s["engine_temp"]),
        defaults["engine_map"], tick, g_ctx)
    log.append(entry)
    torque_pct, fuel_flow_pct = (
        entry["output"] if isinstance(entry["output"], tuple)
        else (entry["output"], entry["output"]))

    entry = _safe_call_with_timeout(
        "gearbox", car_parts.get("gearbox", defaults["gearbox"]),
        (s["rpm"], s["speed_kmh"], s["gear"], s["throttle_demand"]),
        defaults["gearbox"], tick, g_ctx)
    log.append(entry)
    s["gear"] = entry["output"]
    s["rpm"] = compute_rpm(s["speed_kmh"], s["gear"])
    gb_eff = compute_gearbox_efficiency(s["rpm"], s["speed_kmh"])
    entry["efficiency"] = gb_eff

    laps_left = max(1, s.get("laps_total", 1) - s.get("lap", 0))
    entry = _safe_call_with_timeout(
        "fuel_mix", car_parts.get("fuel_mix", defaults["fuel_mix"]),
        (s["fuel_remaining_kg"], laps_left, s["position"], s["gap_ahead"]),
        defaults["fuel_mix"], tick, g_ctx)
    log.append(entry)
    lambda_val = entry["output"]
    fuel_eff = compute_fuel_mix_efficiency(lambda_val, s["fuel_remaining_kg"], laps_left)
    entry["efficiency"] = fuel_eff

    return log, torque_pct, fuel_flow_pct, lambda_val, gb_eff, fuel_eff


def _call_chassis(s, car_parts, defaults, physics_state, t1, tick, g_ctx):
    """Call suspension + cooling. Returns (log, bottoming, cooling_effort, sus_eff, cool_eff)."""
    log = []
    entry = _safe_call_with_timeout(
        "suspension", car_parts.get("suspension", defaults["suspension"]),
        (s["speed_kmh"], s["lateral_g"], physics_state.get("bump_severity", 0), s["ride_height"]),
        defaults["suspension"], tick, g_ctx)
    log.append(entry)
    ride_target = entry["output"]
    actual_rh, bottoming = compute_ride_height_effect(ride_target, s["speed_kmh"])
    s["ride_height"] = actual_rh
    sus_eff = compute_suspension_efficiency(actual_rh, s["speed_kmh"])
    entry["efficiency"] = sus_eff

    entry = _safe_call_with_timeout(
        "cooling", car_parts.get("cooling", defaults["cooling"]),
        (s["engine_temp"], s["brake_temp"], s["battery_temp"], s["speed_kmh"]),
        defaults["cooling"], tick, g_ctx)
    log.append(entry)
    cooling_effort = entry["output"]
    cool_eff = compute_cooling_efficiency(cooling_effort, t1.get("engine_temp", 90), s["speed_kmh"])
    entry["efficiency"] = cool_eff

    return log, bottoming, cooling_effort, sus_eff, cool_eff


def _track_ers_waste(s, log, forces, lateral_g, mass_kg, deploy_kw, dt):
    """Annotate ERS deploy log entry with waste tracking."""
    log[0]["efficiency"] = 1.0  # engine_map: physics handles it
    ers_waste = compute_ers_waste(
        forces["drive_force"], forces["drive_force_no_ers"],
        forces["traction"], lateral_g, mass_kg)
    log[5]["efficiency"] = 1.0
    log[5]["waste"] = ers_waste
    if deploy_kw > 0:
        s["ers_energy_wasted_mj"] = s.get("ers_energy_wasted_mj", 0) + (deploy_kw * dt / 1000 * ers_waste)
    else:
        s["ers_energy_wasted_mj"] = s.get("ers_energy_wasted_mj", 0)


def _call_diff_and_brake(s, car_parts, defaults, physics_state, forces,
                         lateral_g, mass_kg, is_braking, tick, g_ctx, log):
    """Call differential + brake bias. Returns (diff_traction, brake_bias_val, grip_f, grip_r)."""
    entry = _safe_call_with_timeout(
        "differential", car_parts.get("differential", defaults["differential"]),
        (s["corner_phase"], s["speed_kmh"], s["lateral_g"]),
        defaults["differential"], tick, g_ctx)
    log.append(entry)
    diff_lock = entry["output"]
    diff_traction, diff_eff, grip = compute_diff_and_grip(
        s, diff_lock, lateral_g, forces["tire_mu"], forces["downforce"],
        mass_kg, forces["cl"])
    entry["efficiency"] = diff_eff
    s["grip_factor"] = grip

    tire_mu = forces["tire_mu"]
    grip_f = tire_mu * (mass_kg * 9.81 * 0.55 + forces["downforce"] * 0.45)
    grip_r = tire_mu * (mass_kg * 9.81 * 0.45 + forces["downforce"] * 0.55)
    brake_bias_val = 55
    if is_braking:
        entry = _safe_call_with_timeout(
            "brake_bias", car_parts.get("brake_bias", defaults["brake_bias"]),
            (s["speed_kmh"], 1.0, grip_f, grip_r),
            defaults["brake_bias"], tick, g_ctx)
        log.append(entry)
        brake_bias_val = entry["output"]
        entry["efficiency"] = 1.0
    else:
        log.append({"part": "brake_bias", "tick": tick, "output": 55,
                     "status": "ok", "efficiency": 1.0})
    return diff_traction, brake_bias_val, grip_f, grip_r


def _call_ers_harvest_eff(s, car_parts, defaults, is_braking, brake_g,
                          excess, tick, g_ctx, log):
    """Call ERS harvest for efficiency tick. Appends to log. Returns harvest_kw."""
    braking_g_actual = brake_g if (is_braking and excess > 0) else 0.0
    if is_braking:
        entry = _safe_call_with_timeout(
            "ers_harvest", car_parts.get("ers_harvest", defaults["ers_harvest"]),
            (braking_g_actual, s["ers_state"]["energy_mj"] / 4.0 * 100, s["battery_temp"]),
            defaults["ers_harvest"], tick, g_ctx)
        log.append(entry)
        return entry["output"]
    log.append({"part": "ers_harvest", "tick": tick, "output": 0,
                 "status": "ok", "efficiency": 1.0})
    return 0


def _init_eff_tick(s, physics_state):
    """Sync physics inputs into car state for efficiency tick."""
    s["throttle_demand"] = physics_state.get("throttle_demand", 1.0)
    s["lateral_g"] = physics_state.get("lateral_g", 0)
    s["curvature"] = physics_state.get("curvature", 0)
    s["corner_phase"] = physics_state.get("corner_phase", "straight")


def _call_ers_deploy_eff(s, car_parts, defaults, is_braking, tick, g_ctx):
    """Call ERS deploy part. Returns (entry, deploy_kw)."""
    entry = _safe_call_with_timeout(
        "ers_deploy", car_parts.get("ers_deploy", defaults["ers_deploy"]),
        (s["ers_state"]["energy_mj"] / 4.0 * 100, s["speed_kmh"],
         s["lap"], s["gap_ahead"], is_braking),
        defaults["ers_deploy"], tick, g_ctx)
    deploy_kw = entry["output"] if not is_braking else 0
    return entry, deploy_kw


def _apply_forces_and_speed(s, physics_state, forces, diff_traction,
                            brake_bias_val, grip_f, grip_r, product,
                            lateral_g, mass_kg, dt):
    """Apply braking/driving forces and update speed. Returns (brake_g, excess)."""
    effective_traction = forces["traction"] * diff_traction
    rolling_r = mass_kg * 9.81 * 0.008
    net_force, brake_g, excess = _apply_braking(
        s, physics_state, brake_bias_val, grip_f, grip_r,
        forces["drive_force"], forces["drag"], rolling_r, product, lateral_g,
        effective_traction, mass_kg)
    s["speed_kmh"] = max(0, s["speed_kmh"] + (net_force / max(1, mass_kg)) * dt * 3.6)
    return brake_g, excess


def _finalize_eff_tick(s, car_parts, defaults, forces, physics_state,
                       is_braking, brake_g, excess, deploy_kw, harvest_kw,
                       torque_pct, fuel_flow_pct, lambda_val, cooling_effort,
                       lateral_g, hardware_specs, dt, tick, g_ctx, log):
    """Update state + call strategy. Appends to log."""
    _update_state(s, torque_pct, fuel_flow_pct, lambda_val, cooling_effort,
                  forces["drive_force"], forces["traction"], lateral_g, is_braking,
                  brake_g, excess, deploy_kw, harvest_kw, hardware_specs, dt)
    entry = _safe_call_with_timeout(
        "strategy", car_parts.get("strategy", defaults["strategy"]),
        (s,), defaults["strategy"], tick, g_ctx)
    log.append(entry)


def run_efficiency_tick(car_parts, car_state, physics_state, hardware_specs,
                        dt, tick, prev_state=None, glitch_engine=None,
                        reliability=1.0, car_idx=0, glitch_rng=None):
    """Run all 10 parts. Returns (state, log, efficiency_product)."""
    defaults = get_defaults()
    s = dict(car_state)
    g_ctx = ({"engine": glitch_engine, "reliability": reliability,
              "car_idx": car_idx, "rng": glitch_rng} if glitch_engine else None)
    t1 = prev_state if prev_state else s
    mass_kg = hardware_specs.get("weight_kg", 798) + s["fuel_remaining_kg"]
    _init_eff_tick(s, physics_state)

    # 1-4. Powertrain
    log, torque_pct, fuel_flow_pct, lambda_val, gb_eff, fuel_eff = _call_powertrain(
        s, car_parts, defaults, physics_state, tick, g_ctx)
    # 5-6. Chassis
    ch_log, bottoming, cooling_effort, sus_eff, cool_eff = _call_chassis(
        s, car_parts, defaults, physics_state, t1, tick, g_ctx)
    log.extend(ch_log)
    # 7. ERS deploy
    is_braking = physics_state.get("braking", False)
    entry, deploy_kw = _call_ers_deploy_eff(s, car_parts, defaults, is_braking, tick, g_ctx)
    log.append(entry)
    # 8. Forces + ERS waste
    forces = compute_forces_and_traction(
        s, hardware_specs, t1, torque_pct, lambda_val, deploy_kw,
        bottoming, cooling_effort, mass_kg)
    lateral_g = physics_state.get("lateral_g", 0)
    _track_ers_waste(s, log, forces, lateral_g, mass_kg, deploy_kw, dt)
    # 9-10. Diff + brake bias
    diff_traction, brake_bias_val, grip_f, grip_r = _call_diff_and_brake(
        s, car_parts, defaults, physics_state, forces, lateral_g,
        mass_kg, is_braking, tick, g_ctx, log)
    # 11-12. Efficiency product + forces
    product = gb_eff * cool_eff * fuel_eff
    brake_g, excess = _apply_forces_and_speed(
        s, physics_state, forces, diff_traction, brake_bias_val,
        grip_f, grip_r, product, lateral_g, mass_kg, dt)
    # 13. ERS harvest
    harvest_kw = _call_ers_harvest_eff(
        s, car_parts, defaults, is_braking, brake_g, excess, tick, g_ctx, log)
    # 14-15. Update state + strategy
    _finalize_eff_tick(
        s, car_parts, defaults, forces, physics_state, is_braking,
        brake_g, excess, deploy_kw, harvest_kw, torque_pct, fuel_flow_pct,
        lambda_val, cooling_effort, lateral_g, hardware_specs, dt, tick, g_ctx, log)
    s["gearbox_efficiency"], s["cooling_efficiency"] = gb_eff, cool_eff
    if glitch_engine:
        glitch_engine.tick_glitches(car_idx)
    return s, log, product
