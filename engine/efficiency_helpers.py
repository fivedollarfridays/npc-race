"""Efficiency helpers — pure computation functions for per-part efficiency.

Extracted from efficiency_engine.py to keep that module under 400 lines.
"""

from .powertrain_physics import (
    compute_rpm, torque_curve, compute_power_force, compute_mixture_torque_mult,
)
from .chassis_physics import (
    compute_downforce, compute_drag, compute_ride_height_effect,
    compute_traction_limit, apply_traction_circle,
)
from .hybrid_physics import compute_diff_effect


def compute_grip_factor(tire_mu, downforce, mass_kg, _unused,
                        speed_kmh, cl, baseline_rh=-0.3):
    """Grip relative to baseline car at same speed. Diff NOT included."""
    weight = mass_kg * 9.81
    base_rh, base_bottoming = compute_ride_height_effect(baseline_rh, speed_kmh)
    base_df = compute_downforce(speed_kmh, cl, base_rh)
    if base_bottoming:
        base_df *= 0.8
    tire_ratio = tire_mu / 1.4  # baseline tire mu
    df_ratio = (weight + downforce) / max(1, weight + base_df)
    return tire_ratio * df_ratio


def compute_gearbox_efficiency(actual_rpm, speed_kmh):
    """Wrong gear = RPM outside optimal band = less power."""
    actual_tc = torque_curve(actual_rpm)
    best_tc = 0
    for gear in range(1, 9):
        rpm = compute_rpm(speed_kmh, gear)
        tc = torque_curve(rpm)
        if tc > best_tc:
            best_tc = tc
    if best_tc <= 0:
        return 0.85
    ratio = actual_tc / best_tc
    return max(0.80, 0.70 + ratio * 0.30)


def compute_ers_waste(drive_force_with_ers, drive_force_without_ers,
                      traction_limit, lateral_g, mass_kg):
    """ERS waste ratio 0.0-1.0: fraction clipped by traction circle."""
    ers_force_added = drive_force_with_ers - drive_force_without_ers
    if ers_force_added <= 0:
        return 0.0
    net_with = apply_traction_circle(drive_force_with_ers, lateral_g, traction_limit, mass_kg)
    net_without = apply_traction_circle(drive_force_without_ers, lateral_g, traction_limit, mass_kg)
    actual_ers_benefit = net_with - net_without
    return max(0.0, 1.0 - actual_ers_benefit / ers_force_added)


def compute_brake_bias_efficiency(bias_pct, speed_kmh, grip_front, grip_rear):
    """Fixed bias = suboptimal. Optimal shifts with speed (weight transfer)."""
    total_grip = grip_front + grip_rear
    if total_grip <= 0:
        return 0.85
    optimal_pct = (grip_front / total_grip) * 100
    optimal_pct += min(8, speed_kmh / 40)
    optimal_pct = max(50, min(68, optimal_pct))
    deviation = abs(bias_pct - optimal_pct)
    return max(0.75, 1.0 - deviation * 0.030)


def compute_suspension_efficiency(ride_height, speed_kmh):
    """Effective ride height vs speed-dependent optimal. Bottoming kills downforce."""
    actual_rh, bottoming = compute_ride_height_effect(ride_height, speed_kmh)
    optimal_eff = -0.20 - min(0.58, speed_kmh / 500)
    deviation = abs(actual_rh - optimal_eff)
    if bottoming:
        return max(0.65, 0.75 - deviation * 0.3)
    return max(0.78, 1.0 - deviation * 0.4)


def compute_cooling_efficiency(cooling_effort, engine_temp, speed_kmh):
    """Balance temp management (108-118 C sweet spot) vs drag penalty."""
    if 108 <= engine_temp <= 118:
        temp_score = 1.0
    elif engine_temp > 118:
        temp_score = max(0.75, 1.0 - (engine_temp - 118) * 0.04)
    else:
        temp_score = max(0.78, 1.0 - (108 - engine_temp) * 0.020)
    drag_score = max(0.78, 1.0 - cooling_effort * 0.25)
    return max(0.70, temp_score * drag_score)


def compute_diff_efficiency(lock_pct, corner_phase, lateral_g, speed_kmh):
    """Over-locked = understeer. Under-locked = wheelspin. Phase-dependent."""
    if corner_phase == "straight":
        deviation = abs(lock_pct - 50)
        return max(0.90, 1.0 - deviation * 0.003)
    if corner_phase == "entry":
        optimal = 35 + lateral_g * 8
    elif corner_phase == "mid":
        optimal = 18 + lateral_g * 5
    elif corner_phase == "exit":
        optimal = 65 + min(15, speed_kmh / 25)
    else:
        optimal = 50
    optimal = max(0, min(100, optimal))
    deviation = abs(lock_pct - optimal)
    return max(0.80, 1.0 - deviation * 0.006)


def compute_fuel_mix_efficiency(lambda_val, fuel_remaining_kg, laps_left):
    """Rich = power but wastes fuel. Lean = saves fuel but slower."""
    fuel_per_lap = fuel_remaining_kg / max(1, laps_left)
    if fuel_per_lap > 2.5:
        optimal_lambda = 0.92
    elif fuel_per_lap < 1.5:
        optimal_lambda = 1.08
    else:
        optimal_lambda = 1.0
    deviation = abs(lambda_val - optimal_lambda)
    return max(0.75, 1.0 - deviation * 2.0)


def compute_forces_and_traction(s, hardware_specs, t1, torque_pct,
                                lambda_val, deploy_kw, bottoming,
                                cooling_effort, mass_kg):
    """Compute drive forces, downforce, drag, tire mu, traction. Returns dict."""
    mixture_mult = compute_mixture_torque_mult(lambda_val)
    hp = hardware_specs.get("max_hp", 1000)
    temp_penalty = max(0.6, 1.0 - max(0, t1.get("engine_temp", 90) - 120) * 0.04)
    cl = hardware_specs.get("base_cl", 4.5)
    cd = hardware_specs.get("base_cd", 0.88)
    eff_hp = hp * temp_penalty
    drive_force_no_ers = compute_power_force(
        eff_hp, torque_pct, s["rpm"], s["speed_kmh"], 0, mixture_mult)
    drive_force = compute_power_force(
        eff_hp, torque_pct, s["rpm"], s["speed_kmh"], deploy_kw, mixture_mult)
    downforce = compute_downforce(s["speed_kmh"], cl, t1.get("ride_height", -0.2))
    if bottoming:
        downforce *= 0.8
    drag = compute_drag(s["speed_kmh"], cd, cooling_effort, s["ride_height"])
    tire_mu = 1.4 * (1.0 - s.get("tire_wear", 0) * 0.3)
    tire_temp = s.get("tire_temp", 85.0)
    if tire_temp > 100:
        tire_mu *= max(0.85, 1.0 - (tire_temp - 100) * 0.005)
    traction = compute_traction_limit(tire_mu, mass_kg, downforce)
    return {
        "drive_force": drive_force, "drive_force_no_ers": drive_force_no_ers,
        "downforce": downforce, "drag": drag, "tire_mu": tire_mu,
        "traction": traction, "cl": cl,
    }


def compute_diff_and_grip(s, diff_lock, lateral_g, tire_mu, downforce,
                          mass_kg, cl):
    """Compute diff effect + grip factor. Returns (diff_traction, diff_eff, grip_factor)."""
    diff_eff = compute_diff_efficiency(
        diff_lock, s["corner_phase"], lateral_g, s["speed_kmh"])
    diff_traction, _ = compute_diff_effect(diff_lock, lateral_g, s["speed_kmh"])
    _, understeer = compute_diff_effect(diff_lock, lateral_g, s["speed_kmh"])
    understeer_penalty = max(0.90, 1.0 - understeer * 0.10)
    grip = compute_grip_factor(
        tire_mu, downforce, mass_kg, 1.0, s["speed_kmh"], cl) * understeer_penalty
    return diff_traction, diff_eff, grip
