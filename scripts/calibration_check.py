#!/usr/bin/env python3
"""Calibration check -- run races and verify realism metrics."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import run_race

CARS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cars")

tracks = ["monza", "monaco", "silverstone"]
for track in tracks:
    output = f"/tmp/calibration_{track}.json"
    print(f"\n{'=' * 60}")
    print(f"Track: {track}")
    run_race(track_name=track, laps=3, output=output, car_dir=CARS_DIR)

    with open(output) as f:
        replay = json.load(f)

    speeds = [c["speed"] for tick in replay["frames"] for c in tick if not c["finished"]]
    temps = [c["tire_temp"] for tick in replay["frames"] for c in tick if not c["finished"]]
    dirty = sum(1 for tick in replay["frames"] for c in tick if c.get("in_dirty_air"))
    total = sum(1 for tick in replay["frames"] for c in tick if not c["finished"])
    dirty_pct = dirty / total * 100 if total > 0 else 0

    print(f"\nSpeed: {min(speeds):.0f} - {max(speeds):.0f} km/h (avg {sum(speeds)/len(speeds):.0f})")
    print(f"Tire temp: {min(temps):.0f} - {max(temps):.0f} C")
    print(f"Dirty air: {dirty_pct:.1f}% of frames ({dirty}/{total})")
    for r in replay["results"]:
        bl = f"  best: {r['best_lap_s']:.1f}s" if r.get("best_lap_s") else ""
        print(f"  P{r['position']} {r['name']:12s} total: {r.get('total_time_s', 0):.1f}s{bl}")

    print("\n--- Incident Stats ---")
    spin_count = sum(1 for frame in replay["frames"] for car in frame if car.get("in_spin"))
    damage_count = sum(1 for frame in replay["frames"] for car in frame if car.get("damage", 0) > 0)
    sc_frames = sum(1 for frame in replay["frames"] if any(car.get("safety_car") for car in frame))
    dnf_count = sum(1 for r in replay["results"] if not r["finished"])
    print(f"  Spin frames: {spin_count}")
    print(f"  Damage frames: {damage_count}")
    print(f"  Safety car frames: {sc_frames}")
    print(f"  DNFs: {dnf_count}")
