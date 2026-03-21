"""Efficiency engine — computes per-part efficiency factors and multiplies them.

Each part's decision is evaluated against the theoretical optimum for the
current conditions (using t-1 state). The efficiency factors multiply together
to determine what fraction of theoretical max performance is realized.

This is the core of v3's game design: better code → higher efficiency → faster car.
"""

from .safe_call import _safe_call_with_timeout  # noqa: F401
from .parts_api import get_defaults
from .powertrain_physics import (
    compute_rpm, torque_curve, compute_power_force,
    compute_fuel_consumption, compute_engine_temp, compute_mixture_torque_mult,
)
from .chassis_physics import (
    compute_downforce, compute_drag, compute_ride_height_effect, compute_cooling_effect,
    compute_traction_limit, apply_traction_circle,
)
from .hybrid_physics import update_ers, compute_diff_effect

def compute_grip_factor(tire_mu, downforce, mass_kg, _unused,
                        speed_kmh, cl, baseline_rh=-0.3):
    """Compute grip relative to baseline car at the same speed.

    Compares actual grip (tire + downforce) against what the default car
    would produce at this speed. No clamping needed — the baseline
    reference eliminates speed-dependent downforce variation.
    Diff traction is NOT included — it affects acceleration, not corner speed.
    """
    weight = mass_kg * 9.81
    baseline_tire_mu = 1.4

    # Baseline downforce with default ride height at this speed
    base_rh, base_bottoming = compute_ride_height_effect(baseline_rh, speed_kmh)
    base_df = compute_downforce(speed_kmh, cl, base_rh)
    if base_bottoming:
        base_df *= 0.8

    # Ratios relative to baseline
    tire_ratio = tire_mu / baseline_tire_mu
    actual_normal = weight + downforce
    baseline_normal = max(1, weight + base_df)
    df_ratio = actual_normal / baseline_normal

    return tire_ratio * df_ratio


def compute_gearbox_efficiency(actual_rpm, speed_kmh):
    """Gearbox efficiency: how close the RPM is to the torque peak.

    Wrong gear = RPM outside optimal band = less power = lower efficiency.
    """
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
    # Narrower range: default near peak gets ~0.93, perfect = 1.0
    return max(0.80, 0.70 + ratio * 0.30)


def compute_ers_waste(drive_force_with_ers, drive_force_without_ers,
                      traction_limit, lateral_g, mass_kg):
    """Track how much ERS energy was wasted (clipped by traction circle).

    Returns waste ratio 0.0-1.0 (fraction of ERS energy that produced no speed).
    """
    ers_force_added = drive_force_with_ers - drive_force_without_ers
    if ers_force_added <= 0:
        return 0.0
    # What force actually reaches the wheels after traction circle?
    net_with = apply_traction_circle(drive_force_with_ers, lateral_g, traction_limit, mass_kg)
    net_without = apply_traction_circle(drive_force_without_ers, lateral_g, traction_limit, mass_kg)
    actual_ers_benefit = net_with - net_without
    return max(0.0, 1.0 - actual_ers_benefit / ers_force_added)


def compute_brake_bias_efficiency(bias_pct, speed_kmh, grip_front, grip_rear):
    """Brake bias efficiency: how close to optimal front/rear split.

    Optimal shifts significantly with speed (weight transfer at high speed
    pushes optimal forward). Fixed bias = always suboptimal.
    """
    total_grip = grip_front + grip_rear
    if total_grip <= 0:
        return 0.85
    optimal_pct = (grip_front / total_grip) * 100
    # Speed-dependent weight transfer: big shift at high speed
    optimal_pct += min(8, speed_kmh / 40)
    optimal_pct = max(50, min(68, optimal_pct))
    deviation = abs(bias_pct - optimal_pct)
    # Each point off costs 3% efficiency
    return max(0.75, 1.0 - deviation * 0.030)


def compute_suspension_efficiency(ride_height, speed_kmh):
    """Suspension efficiency: how close EFFECTIVE ride height is to optimal.

    Accounts for speed-dependent suspension compression.
    Lower = more downforce, but bottoming (-0.8) kills downforce.
    """
    actual_rh, bottoming = compute_ride_height_effect(ride_height, speed_kmh)
    # Optimal effective height: speed-dependent, as low as possible without bottoming
    optimal_eff = -0.20 - min(0.58, speed_kmh / 500)
    deviation = abs(actual_rh - optimal_eff)
    if bottoming:
        return max(0.65, 0.75 - deviation * 0.3)
    return max(0.78, 1.0 - deviation * 0.4)


def compute_cooling_efficiency(cooling_effort, engine_temp, speed_kmh):
    """Cooling efficiency: balance temp management vs drag.

    Combines temp score (is engine in sweet spot?) with drag score (minimal cooling?).
    """
    # Temp score: engine at 108-118°C is optimal
    if 108 <= engine_temp <= 118:
        temp_score = 1.0
    elif engine_temp > 118:
        temp_score = max(0.75, 1.0 - (engine_temp - 118) * 0.04)
    else:
        temp_score = max(0.78, 1.0 - (108 - engine_temp) * 0.020)

    # Drag score: overcooling costs drag
    drag_score = max(0.78, 1.0 - cooling_effort * 0.25)

    return max(0.70, temp_score * drag_score)


def compute_diff_efficiency(lock_pct, corner_phase, lateral_g, speed_kmh):
    """Differential efficiency: optimal lock for the corner phase.

    Over-locked in mid-corner = understeer. Under-locked on exit = wheelspin.
    Even on straights, lock affects stability at high speed.
    """
    if corner_phase == "straight":
        # Even on straights, optimal is 50% — deviation costs slightly
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
    # Each point costs 0.6% in corners
    return max(0.80, 1.0 - deviation * 0.006)


def compute_fuel_mix_efficiency(lambda_val, fuel_remaining_kg, laps_left):
    """Fuel mix efficiency: how well the mixture balances power vs fuel saving.

    Rich (lambda < 1.0) = more power but wastes fuel. Optimal depends on
    remaining fuel and laps. Running rich when fuel is tight = DNF risk.
    Running lean when you have excess = leaving pace on the table.
    """
    fuel_per_lap = fuel_remaining_kg / max(1, laps_left)
    # Target consumption rate ~2.0 kg/lap
    if fuel_per_lap > 2.5:
        # Excess fuel: should run rich for power. Penalty for being lean.
        optimal_lambda = 0.92
    elif fuel_per_lap < 1.5:
        # Fuel tight: should be lean. Penalty for being rich.
        optimal_lambda = 1.08
    else:
        optimal_lambda = 1.0
    deviation = abs(lambda_val - optimal_lambda)
    return max(0.75, 1.0 - deviation * 2.0)


def run_efficiency_tick(car_parts, car_state, physics_state, hardware_specs,
                        dt, tick, prev_state=None):
    """Run all 10 parts with efficiency computation.

    Returns (updated_state, call_log, efficiency_product).
    """
    defaults = get_defaults()
    s = dict(car_state)
    log = []

    # Use t-1 state for dependent computations
    t1 = prev_state if prev_state else s

    engine_spec = hardware_specs
    aero_spec = hardware_specs
    mass_kg = hardware_specs.get("weight_kg", 798) + s["fuel_remaining_kg"]

    # Merge physics state into car state
    s["throttle_demand"] = physics_state.get("throttle_demand", 1.0)
    s["lateral_g"] = physics_state.get("lateral_g", 0)
    s["curvature"] = physics_state.get("curvature", 0)
    s["corner_phase"] = physics_state.get("corner_phase", "straight")

    # 1. RPM
    s["rpm"] = compute_rpm(s["speed_kmh"], s["gear"])

    # 2. Engine map
    entry = _safe_call_with_timeout(
        "engine_map", car_parts.get("engine_map", defaults["engine_map"]),
        (s["rpm"], s["throttle_demand"], s["engine_temp"]),
        defaults["engine_map"], tick)
    log.append(entry)
    torque_pct, fuel_flow_pct = entry["output"] if isinstance(entry["output"], tuple) else (entry["output"], entry["output"])

    # 3. Gearbox
    entry = _safe_call_with_timeout(
        "gearbox", car_parts.get("gearbox", defaults["gearbox"]),
        (s["rpm"], s["speed_kmh"], s["gear"], s["throttle_demand"]),
        defaults["gearbox"], tick)
    log.append(entry)
    s["gear"] = entry["output"]
    s["rpm"] = compute_rpm(s["speed_kmh"], s["gear"])
    gb_eff = compute_gearbox_efficiency(s["rpm"], s["speed_kmh"])
    entry["efficiency"] = gb_eff

    # 4. Fuel mix
    laps_left = max(1, s.get("laps_total", 1) - s.get("lap", 0))
    entry = _safe_call_with_timeout(
        "fuel_mix", car_parts.get("fuel_mix", defaults["fuel_mix"]),
        (s["fuel_remaining_kg"], laps_left, s["position"], s["gap_ahead"]),
        defaults["fuel_mix"], tick)
    log.append(entry)
    lambda_val = entry["output"]
    fuel_eff = compute_fuel_mix_efficiency(lambda_val, s["fuel_remaining_kg"], laps_left)
    entry["efficiency"] = fuel_eff

    # 5. Suspension (BEFORE speed computation — affects downforce)
    entry = _safe_call_with_timeout(
        "suspension", car_parts.get("suspension", defaults["suspension"]),
        (s["speed_kmh"], s["lateral_g"], physics_state.get("bump_severity", 0), s["ride_height"]),
        defaults["suspension"], tick)
    log.append(entry)
    ride_target = entry["output"]
    actual_rh, bottoming = compute_ride_height_effect(ride_target, s["speed_kmh"])
    s["ride_height"] = actual_rh
    sus_eff = compute_suspension_efficiency(actual_rh, s["speed_kmh"])
    entry["efficiency"] = sus_eff

    # 6. Cooling (BEFORE speed computation — affects drag)
    entry = _safe_call_with_timeout(
        "cooling", car_parts.get("cooling", defaults["cooling"]),
        (s["engine_temp"], s["brake_temp"], s["battery_temp"], s["speed_kmh"]),
        defaults["cooling"], tick)
    log.append(entry)
    cooling_effort = entry["output"]
    cool_eff = compute_cooling_efficiency(cooling_effort, t1.get("engine_temp", 90), s["speed_kmh"])
    entry["efficiency"] = cool_eff

    # 7. ERS deploy
    is_braking = physics_state.get("braking", False)
    entry = _safe_call_with_timeout(
        "ers_deploy", car_parts.get("ers_deploy", defaults["ers_deploy"]),
        (s["ers_state"]["energy_mj"] / 4.0 * 100, s["speed_kmh"],
         s["lap"], s["gap_ahead"], is_braking),
        defaults["ers_deploy"], tick)
    log.append(entry)
    deploy_kw = entry["output"] if not is_braking else 0

    # 8. COMPUTE FORCES with t-1 dependent values
    mixture_mult = compute_mixture_torque_mult(lambda_val)
    hp = engine_spec.get("max_hp", 1000)
    temp_penalty = max(0.6, 1.0 - max(0, t1.get("engine_temp", 90) - 120) * 0.04)
    cl = aero_spec.get("base_cl", 4.5)
    cd = aero_spec.get("base_cd", 0.88)

    # Drive force WITHOUT ERS (for ERS efficiency calc)
    drive_force_no_ers = compute_power_force(
        hp * temp_penalty, torque_pct, s["rpm"], s["speed_kmh"], 0, mixture_mult)
    # Drive force WITH ERS
    drive_force = compute_power_force(
        hp * temp_penalty, torque_pct, s["rpm"], s["speed_kmh"], deploy_kw, mixture_mult)

    downforce = compute_downforce(s["speed_kmh"], cl, t1.get("ride_height", -0.2))
    if bottoming:
        downforce *= 0.8
    drag = compute_drag(s["speed_kmh"], cd, cooling_effort)

    tire_mu = 1.4 * (1.0 - s.get("tire_wear", 0) * 0.3)
    # Tire temp penalty: grip degrades when overheated (>100°C optimal window)
    tire_temp = s.get("tire_temp", 85.0)
    if tire_temp > 100:
        tire_mu *= max(0.85, 1.0 - (tire_temp - 100) * 0.005)
    traction = compute_traction_limit(tire_mu, mass_kg, downforce)
    lateral_g = physics_state.get("lateral_g", 0)

    # Engine map: no prescribed efficiency — physics handles it
    log[0]["efficiency"] = 1.0

    # ERS waste tracking (replaces old speed-threshold efficiency)
    ers_waste = compute_ers_waste(drive_force, drive_force_no_ers,
                                  traction, lateral_g, mass_kg)
    log[5]["efficiency"] = 1.0  # ERS no longer an efficiency factor
    log[5]["waste"] = ers_waste
    if deploy_kw > 0:
        s["ers_energy_wasted_mj"] = s.get("ers_energy_wasted_mj", 0) + (deploy_kw * dt / 1000 * ers_waste)
    else:
        s["ers_energy_wasted_mj"] = s.get("ers_energy_wasted_mj", 0)

    # 9. Differential
    entry = _safe_call_with_timeout(
        "differential", car_parts.get("differential", defaults["differential"]),
        (s["corner_phase"], s["speed_kmh"], s["lateral_g"]),
        defaults["differential"], tick)
    log.append(entry)
    diff_lock = entry["output"]
    diff_eff = compute_diff_efficiency(diff_lock, s["corner_phase"], lateral_g, s["speed_kmh"])
    entry["efficiency"] = diff_eff
    diff_traction, _ = compute_diff_effect(diff_lock, lateral_g, s["speed_kmh"])

    # Diff understeer reduces lateral grip → slower through corners.
    # Diff traction helps acceleration (already in effective_traction), not corner speed.
    _, understeer = compute_diff_effect(diff_lock, lateral_g, s["speed_kmh"])
    understeer_penalty = max(0.80, 1.0 - understeer * 0.40)
    s["grip_factor"] = compute_grip_factor(
        tire_mu, downforce, mass_kg, 1.0,  # diff NOT in grip_factor
        s["speed_kmh"], cl) * understeer_penalty

    # 10. Brake bias — wired to front/rear force splitting.
    # Wrong bias → one axle saturates → total braking reduced.
    grip_f = tire_mu * (mass_kg * 9.81 * 0.55 + downforce * 0.45)
    grip_r = tire_mu * (mass_kg * 9.81 * 0.45 + downforce * 0.55)
    brake_bias_val = 55  # default
    brake_g = 0.0
    excess = 0.0
    if is_braking:
        entry = _safe_call_with_timeout(
            "brake_bias", car_parts.get("brake_bias", defaults["brake_bias"]),
            (s["speed_kmh"], 1.0, grip_f, grip_r),
            defaults["brake_bias"], tick)
        log.append(entry)
        brake_bias_val = entry["output"]
        entry["efficiency"] = 1.0
    else:
        log.append({"part": "brake_bias", "tick": tick, "output": 55,
                     "status": "ok", "efficiency": 1.0})

    # 11. MULTIPLY ALL EFFICIENCIES
    efficiencies = [gb_eff, sus_eff, cool_eff, diff_eff, fuel_eff]
    product = 1.0
    for eff in efficiencies:
        product *= eff

    # 12. Apply forces with efficiency product scaling
    effective_traction = traction * diff_traction
    rolling_r = mass_kg * 9.81 * 0.008

    if is_braking:
        target_spd = physics_state.get("target_speed", s["speed_kmh"])
        excess = s["speed_kmh"] - target_spd
        if excess > 0:
            brake_g = min(5.5, 0.5 + excess / 40)
            total_brake = mass_kg * brake_g * 9.81
            # Brake bias splits force front/rear — wrong split = axle lockup
            front_demand = total_brake * brake_bias_val / 100
            rear_demand = total_brake * (100 - brake_bias_val) / 100
            front_actual = min(front_demand, grip_f)
            rear_actual = min(rear_demand, grip_r)
            actual_brake = front_actual + rear_actual
            raw_brake = -actual_brake
            net_force = apply_traction_circle(raw_brake, lateral_g, effective_traction, mass_kg)
        else:
            raw_drive = (drive_force - drag - rolling_r) * product
            net_force = apply_traction_circle(raw_drive, lateral_g, effective_traction, mass_kg)
    else:
        raw_drive = (drive_force - drag - rolling_r) * product
        net_force = apply_traction_circle(raw_drive, lateral_g, effective_traction, mass_kg)

    accel = net_force / max(1, mass_kg)
    s["speed_kmh"] = max(0, s["speed_kmh"] + accel * dt * 3.6)

    # 13. Update state
    fuel_consumed = compute_fuel_consumption(
        fuel_flow_pct, lambda_val, engine_spec.get("max_fuel_flow_kghr", 100), dt)
    s["fuel_remaining_kg"] = max(0, s["fuel_remaining_kg"] - fuel_consumed)
    s["engine_temp"] = compute_engine_temp(
        s["engine_temp"], torque_pct, s["rpm"], cooling_effort, dt)
    e_cool, b_cool, bat_cool = compute_cooling_effect(
        cooling_effort, s["engine_temp"], s["brake_temp"], s["battery_temp"], dt)
    s["engine_temp"] -= e_cool
    s["brake_temp"] = max(200, s["brake_temp"] - b_cool)
    s["battery_temp"] = max(25, s["battery_temp"] - bat_cool)

    # Tire wear from excess torque (wheelspin)
    if drive_force > traction and not is_braking:
        wheelspin = (drive_force - traction) / max(1, traction)
        s["tire_wear"] = min(1.0, s.get("tire_wear", 0) + wheelspin * 0.002 * dt)
        # Wheelspin heats tires — thermal degradation reduces grip within the lap
        tire_temp = s.get("tire_temp", 85.0)
        tire_temp += wheelspin * 8.0 * dt  # aggressive heating from sliding
        s["tire_temp"] = tire_temp
    # Cornering wear (lateral force degrades tires)
    if lateral_g > 0.5:
        corner_wear = (lateral_g - 0.5) * 0.0003 * dt
        s["tire_wear"] = min(1.0, s.get("tire_wear", 0) + corner_wear)
    # Tire temp naturally cools toward ambient
    tire_temp = s.get("tire_temp", 85.0)
    tire_temp -= (tire_temp - 85.0) * 0.02 * dt  # cool toward 85°C ambient
    s["tire_temp"] = max(50, tire_temp)

    # 14. ERS harvest — pass actual braking G (not hardcoded 1.0)
    braking_g_actual = brake_g if (is_braking and excess > 0) else 0.0
    if is_braking:
        entry = _safe_call_with_timeout(
            "ers_harvest", car_parts.get("ers_harvest", defaults["ers_harvest"]),
            (braking_g_actual, s["ers_state"]["energy_mj"] / 4.0 * 100, s["battery_temp"]),
            defaults["ers_harvest"], tick)
        log.append(entry)
        harvest_kw = entry["output"]
    else:
        log.append({"part": "ers_harvest", "tick": tick, "output": 0,
                     "status": "ok", "efficiency": 1.0})
        harvest_kw = 0

    s["ers_state"], _ = update_ers(s["ers_state"], deploy_kw, harvest_kw, dt)
    s["battery_temp"] = s["ers_state"]["battery_temp"]

    # 15. Strategy
    entry = _safe_call_with_timeout(
        "strategy", car_parts.get("strategy", defaults["strategy"]),
        (s,), defaults["strategy"], tick)
    log.append(entry)

    return s, log, product
