#!/usr/bin/env python3
"""Sensitivity test — measure per-part lap time impact.

Runs Monza with default code, then changes ONE part at a time
and measures the lap time difference.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.car_loader import load_all_cars
from engine.parts_simulation import PartsRaceSim
from engine.parts_api import get_defaults
from engine import safe_call
from tracks import get_track
from engine.track_gen import interpolate_track

# Disable thread overhead for batch testing
safe_call.TIMEOUT_ENABLED = False


def _run_race(parts_override=None, car_idx=0):
    """Run 1-lap Monza and return lap time for car_idx."""
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    cars = load_all_cars("cars")

    if parts_override:
        defaults = get_defaults()
        for name, func in parts_override.items():
            defaults[name] = func
        cars[car_idx]["parts"] = defaults

    sim = PartsRaceSim(cars, pts, laps=1, seed=42, track_name="monza",
                        real_length_m=td.get("real_length_m"))
    sim.run(max_ticks=6000)

    state = sim.car_states[car_idx]
    if state.get("finish_tick"):
        return state["finish_tick"] / 30
    return 999.0


# --- Optimized part variants ---

def optimized_engine_map(rpm, throttle_demand, engine_temp):
    """Smart power delivery: full power on straights, temp-aware derating."""
    torque = throttle_demand
    fuel = throttle_demand
    # Derate when engine hot to prevent power loss from temp_penalty
    if engine_temp > 115:
        derating = max(0.8, 1.0 - (engine_temp - 115) * 0.02)
        torque *= derating
        fuel *= derating
    return (torque, fuel)


def optimized_gearbox(rpm, speed, current_gear, throttle):
    """Keep RPM in the peak torque band 10800-12500."""
    if rpm > 12200 and current_gear < 8:
        return current_gear + 1
    if rpm < 9500 and current_gear > 1:
        return current_gear - 1
    return current_gear


def optimized_ers_deploy(battery_pct, speed, lap, gap_ahead, braking):
    """Smart deploy: skip low-speed corners where traction clips the force."""
    if braking or battery_pct < 5:
        return 0
    if speed > 150:
        return 120  # full deploy on straights and medium-speed sections
    return 0        # no deploy in slow corners (force exceeds traction)


def optimized_ers_harvest(braking_force, battery_pct, battery_temp):
    """Proportional harvest: recover energy based on actual braking force."""
    if battery_pct > 98 or battery_temp > 52:
        return 0
    # Scale harvest to braking intensity (braking_force is now actual G)
    return min(120, braking_force * 25)  # 25kW per G of braking


def optimized_brake_bias(speed, deceleration_g, tire_grip_front, tire_grip_rear):
    """Grip-proportional: split braking force to match available grip per axle."""
    total = tire_grip_front + tire_grip_rear
    if total <= 0:
        return 55
    # Optimal: front percentage matches front grip fraction
    return max(50, min(65, (tire_grip_front / total) * 100))


def optimized_suspension(speed, lateral_g, bump_severity, current_ride_height):
    """Lower ride height for more downforce, staying above drag penalty zone."""
    return -0.50


def optimized_cooling(engine_temp, brake_temp, battery_temp, speed):
    """Match the efficiency optimal: minimal cooling, ramp when hot."""
    if engine_temp > 118:
        return min(1.0, 0.3 + (engine_temp - 118) * 0.1)
    if engine_temp < 105:
        return 0.1  # minimal when cool
    return 0.25


def optimized_fuel_mix(fuel_remaining_kg, laps_left, position, gap_ahead):
    """Match fuel_mix_efficiency optimal: rich when excess, lean when tight."""
    if laps_left <= 0:
        return 1.0
    rate = fuel_remaining_kg / max(1, laps_left)
    if rate > 2.5:
        return 0.92  # rich when excess fuel
    if rate < 1.5:
        return 1.08  # lean when tight
    return 1.0


def optimized_differential(corner_phase, speed, lateral_g):
    """Low lock minimizes understeer penalty for corner speed."""
    return 15


OPTIMIZED = {
    "engine_map": optimized_engine_map,
    "gearbox": optimized_gearbox,
    "ers_deploy": optimized_ers_deploy,
    "ers_harvest": optimized_ers_harvest,
    "brake_bias": optimized_brake_bias,
    "suspension": optimized_suspension,
    "cooling": optimized_cooling,
    "fuel_mix": optimized_fuel_mix,
    "differential": optimized_differential,
}


INTERACTION_PAIRS = [
    ("engine_map", "gearbox"),
    ("brake_bias", "ers_harvest"),
    ("suspension", "cooling"),
    ("ers_deploy", "differential"),
    ("engine_map", "fuel_mix"),
]


def main(output_file=None):
    from datetime import datetime

    lines = []

    def log(s=""):
        print(s)
        lines.append(s)

    log("# NPC Race — Sensitivity Test")
    log(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log("Track: Monza | Laps: 1 | Seed: 42 | Car: BrickHouse (idx 0)")
    log("")

    # Baseline
    baseline = _run_race()
    log(f"## Baseline: {baseline:.2f}s")
    log("")

    # Per-part sensitivity
    log("## Per-Part Sensitivity")
    log("")
    log(f"| {'Part':<20} | {'Default':>10} | {'Optimized':>10} | {'Gain':>10} | {'Note':>6} |")
    log(f"|{'-'*22}|{'-'*12}|{'-'*12}|{'-'*12}|{'-'*8}|")

    part_gains = {}
    total_individual = 0
    for part_name, opt_func in OPTIMIZED.items():
        optimized_time = _run_race({part_name: opt_func})
        gain = baseline - optimized_time
        part_gains[part_name] = gain
        total_individual += gain
        note = "***" if gain > 0.5 else ("BAD" if gain < -0.1 else "")
        log(f"| {part_name:<20} | {baseline:>10.2f} | {optimized_time:>10.2f} | {gain:>+10.3f}s | {note:>6} |")

    # All optimized
    all_opt_time = _run_race(OPTIMIZED)
    total_gain = baseline - all_opt_time

    log("")
    log(f"| {'ALL OPTIMIZED':<20} | {baseline:>10.2f} | {all_opt_time:>10.2f} | {total_gain:>+10.3f}s | {'':>6} |")
    log(f"| {'SUM OF PARTS':<20} | {'':>10} | {'':>10} | {total_individual:>+10.3f}s | {'':>6} |")
    log(f"| {'INTERACTION':<20} | {'':>10} | {'':>10} | {total_gain - total_individual:>+10.3f}s | {'':>6} |")
    log("")

    # Dominance check
    log("## Dominance Check")
    log("")
    if abs(total_gain) > 0.01:
        for part_name, gain in part_gains.items():
            pct = gain / total_gain * 100 if total_gain != 0 else 0
            flag = " **DOMINANT**" if abs(pct) > 25 else ""
            log(f"- {part_name}: {pct:.0f}% of total{flag}")
    else:
        log("Total gain is ~0 — dominance check N/A")
    log("")

    # Interaction pairs
    log("## Interaction Pairs")
    log("")
    log(f"| {'Pair':<30} | {'A alone':>10} | {'B alone':>10} | {'A+B':>10} | {'Expected':>10} | {'Interaction':>12} |")
    log(f"|{'-'*32}|{'-'*12}|{'-'*12}|{'-'*12}|{'-'*12}|{'-'*14}|")

    for part_a, part_b in INTERACTION_PAIRS:
        gain_a = part_gains.get(part_a, 0)
        gain_b = part_gains.get(part_b, 0)
        both_time = _run_race({part_a: OPTIMIZED[part_a], part_b: OPTIMIZED[part_b]})
        gain_ab = baseline - both_time
        expected = gain_a + gain_b
        interaction = gain_ab - expected
        log(f"| {part_a+' + '+part_b:<30} | {gain_a:>+10.3f} | {gain_b:>+10.3f} | {gain_ab:>+10.3f} | {expected:>+10.3f} | {interaction:>+12.3f} |")

    log("")

    # Summary
    log("## Summary")
    log("")
    log(f"- **Baseline:** {baseline:.2f}s")
    log(f"- **All optimized:** {all_opt_time:.2f}s")
    log(f"- **Total spread:** {total_gain:.2f}s (target: 3.0-5.0s)")
    log(f"- **Parts with > 0.3s gain:** {sum(1 for g in part_gains.values() if g > 0.3)}/9")
    log(f"- **Parts with negative gain (worse):** {sum(1 for g in part_gains.values() if g < -0.1)}/9")
    coupled = sum(1 for pa, pb in INTERACTION_PAIRS
                  if abs((baseline - _run_race({pa: OPTIMIZED[pa], pb: OPTIMIZED[pb]}))
                         - part_gains.get(pa, 0) - part_gains.get(pb, 0)) > 0.03)
    log(f"- **Coupled pairs (interaction > 0.03s):** {coupled}/{len(INTERACTION_PAIRS)}")
    log("")

    # Gate criteria (physics-emergent targets)
    log("## Gate Criteria (1-lap)")
    log("")
    spread_ok = 3.0 <= total_gain <= 5.0
    parts_above = sum(1 for g in part_gains.values() if g >= 0.3)
    parts_ok = parts_above >= 4
    ceiling_ok = all(g <= 1.2 for g in part_gains.values())
    no_dominant = all(abs(g / total_gain * 100) <= 35 for g in part_gains.values()) if abs(total_gain) > 0.01 else False
    log(f"- [{'x' if spread_ok else ' '}] 3-5s spread: {total_gain:.2f}s")
    log(f"- [{'x' if parts_ok else ' '}] ≥4 parts above 0.3s: {parts_above}/9")
    log(f"- [{'x' if ceiling_ok else ' '}] No part above 1.2s")
    log(f"- [{'x' if no_dominant else ' '}] No part > 35% of total")
    log(f"- [{'x' if coupled >= 3 else ' '}] ≥3 coupled pairs")
    log("")
    all_pass = spread_ok and parts_ok and ceiling_ok and no_dominant and coupled >= 3
    log(f"**GATE: {'PASS' if all_pass else 'FAIL'}**")

    # --- 5-LAP VERIFICATION ---
    log("")
    log("---")
    log("")
    log("# 5-Lap Race Verification")
    log("")

    def _run_race_5lap(parts_override=None, car_idx=0):
        td = get_track("monza")
        pts = interpolate_track(td["control_points"], resolution=500)
        cars = load_all_cars("cars")
        if parts_override:
            defs = get_defaults()
            for name, func in parts_override.items():
                defs[name] = func
            cars[car_idx]["parts"] = defs
        sim = PartsRaceSim(cars, pts, laps=5, seed=42, track_name="monza",
                            real_length_m=td.get("real_length_m"))
        sim.run(max_ticks=30000)
        state = sim.car_states[car_idx]
        if state.get("finish_tick"):
            return state["finish_tick"] / 30
        return 999.0

    baseline_5 = _run_race_5lap()
    log(f"## Baseline (5 laps): {baseline_5:.2f}s")
    log("")

    multi_lap_parts = ["engine_map", "brake_bias", "ers_deploy", "ers_harvest"]
    log("| Part | Default | Optimized | Gain |")
    log("|------|---------|-----------|------|")
    multi_gains = {}
    for pn in multi_lap_parts:
        opt_time = _run_race_5lap({pn: OPTIMIZED[pn]})
        gain = baseline_5 - opt_time
        multi_gains[pn] = gain
        log(f"| {pn:<15} | {baseline_5:.2f} | {opt_time:.2f} | {gain:+.2f}s |")

    all_5 = _run_race_5lap(OPTIMIZED)
    total_5 = baseline_5 - all_5
    log(f"| {'ALL OPTIMIZED':<15} | {baseline_5:.2f} | {all_5:.2f} | {total_5:+.2f}s |")
    log("")

    # 5-lap gate
    log("## Gate Criteria (5-lap)")
    log("")
    spread_5_ok = total_5 >= 15.0
    multi_parts_ok = sum(1 for g in multi_gains.values() if g >= 0.3) >= 2
    log(f"- [{'x' if spread_5_ok else ' '}] Total spread ≥ 15s: {total_5:.2f}s")
    log(f"- [{'x' if multi_parts_ok else ' '}] ≥2 multi-lap parts above 0.3s")
    for pn, g in multi_gains.items():
        flag = "✓" if g >= 0.3 else "—"
        log(f"  - {pn}: {g:+.2f}s {flag}")
    log("")
    five_pass = spread_5_ok and multi_parts_ok
    log(f"**5-LAP GATE: {'PASS' if five_pass else 'FAIL'}**")

    combined = all_pass and five_pass
    log("")
    log(f"**COMBINED GATE: {'PASS' if combined else 'FAIL'}**")

    # Write to file
    if output_file:
        with open(output_file, "w") as f:
            f.write("\n".join(lines))
        print(f"\nResults saved to {output_file}")

    return combined


if __name__ == "__main__":
    outfile = sys.argv[1] if len(sys.argv) > 1 else None
    main(output_file=outfile)
