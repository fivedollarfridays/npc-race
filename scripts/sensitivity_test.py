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
from tracks import get_track
from engine.track_gen import interpolate_track


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
    """Max power always — full torque, full fuel. Aggressive."""
    return (min(1.0, throttle_demand * 1.05), min(1.0, throttle_demand * 1.05))


def optimized_gearbox(rpm, speed, current_gear, throttle):
    """Rev higher — shift at 13000 for more power from the top of the band."""
    if rpm > 13000 and current_gear < 8:
        return current_gear + 1
    if rpm < 6000 and current_gear > 1:
        return current_gear - 1
    return current_gear


def optimized_ers_deploy(battery_pct, speed, lap, gap_ahead, braking):
    """Deploy only on straights above 200 km/h."""
    if braking or battery_pct < 10:
        return 0
    if speed > 200:
        return 120  # max deploy on straights
    return 0


def optimized_ers_harvest(braking_force, battery_pct, battery_temp):
    """Max harvest under braking, temp-aware."""
    if battery_pct > 98 or battery_temp > 52:
        return 0
    return min(120, braking_force * 0.8)  # more aggressive harvest


def optimized_brake_bias(speed, deceleration_g, tire_grip_front, tire_grip_rear):
    """Speed-dependent — more front at high speed."""
    if speed > 250:
        return 60  # high speed: more front
    if speed < 100:
        return 54  # low speed: more balanced
    return 57


def optimized_suspension(speed, lateral_g, bump_severity, current_ride_height):
    """Speed-adaptive — low but not bottoming out."""
    if speed > 250:
        return -0.6  # low for aero but above bottoming threshold
    if speed > 100:
        return -0.4
    return -0.15  # slight lift in slow corners


def optimized_cooling(engine_temp, brake_temp, battery_temp, speed):
    """Minimal cooling until temps approach limits."""
    if engine_temp > 118 or battery_temp > 53 or brake_temp > 750:
        return 0.8
    if engine_temp > 110:
        return 0.5
    return 0.2  # minimal — save drag


def optimized_fuel_mix(fuel_remaining_kg, laps_left, position, gap_ahead):
    """Aggressive: rich on straights."""
    if laps_left <= 0:
        return 1.0
    rate = fuel_remaining_kg / laps_left
    if rate > 2.5:
        return 0.88  # very rich
    if rate < 1.4:
        return 1.12
    return 0.95  # slightly rich by default


def optimized_differential(corner_phase, speed, lateral_g):
    """Lateral-g-aware lock percentage."""
    if corner_phase == "entry":
        return 35 if lateral_g > 1.5 else 45
    if corner_phase == "mid":
        return 20 if lateral_g > 2.0 else 30
    if corner_phase == "exit":
        return 75 if speed > 150 else 65
    return 50


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
    log(f"- **Total spread:** {total_gain:.2f}s (target: 10.0s)")
    log(f"- **Parts with > 0.5s gain:** {sum(1 for g in part_gains.values() if g > 0.5)}/9")
    log(f"- **Parts with negative gain (worse):** {sum(1 for g in part_gains.values() if g < -0.1)}/9")
    coupled = sum(1 for pa, pb in INTERACTION_PAIRS
                  if abs((baseline - _run_race({pa: OPTIMIZED[pa], pb: OPTIMIZED[pb]}))
                         - part_gains.get(pa, 0) - part_gains.get(pb, 0)) > 0.05)
    log(f"- **Coupled pairs (interaction > 0.05s):** {coupled}/{len(INTERACTION_PAIRS)}")
    log("")

    # Gate criteria
    log("## Gate Criteria")
    log("")
    spread_ok = total_gain >= 10.0
    parts_ok = sum(1 for g in part_gains.values() if 0.5 <= g <= 1.5) >= 5
    no_dominant = all(abs(g / total_gain * 100) <= 25 for g in part_gains.values()) if abs(total_gain) > 0.01 else False
    log(f"- [{'x' if spread_ok else ' '}] 10s spread: {total_gain:.2f}s")
    log(f"- [{'x' if parts_ok else ' '}] ≥5 parts in 0.5-1.5s range")
    log(f"- [{'x' if no_dominant else ' '}] No part > 25% of total")
    log(f"- [{'x' if coupled >= 3 else ' '}] ≥3 coupled pairs")
    log("")
    all_pass = spread_ok and parts_ok and no_dominant and coupled >= 3
    log(f"**GATE: {'PASS' if all_pass else 'FAIL'}**")

    # Write to file
    if output_file:
        with open(output_file, "w") as f:
            f.write("\n".join(lines))
        print(f"\nResults saved to {output_file}")

    return all_pass


if __name__ == "__main__":
    outfile = sys.argv[1] if len(sys.argv) > 1 else None
    main(output_file=outfile)
