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

    print(f"\nSpeed: {min(speeds):.0f} - {max(speeds):.0f} km/h (avg {sum(speeds)/len(speeds):.0f})")
    print(f"Tire temp: {min(temps):.0f} - {max(temps):.0f} C")
    for r in replay["results"]:
        bl = f"  best: {r['best_lap_s']:.1f}s" if r.get("best_lap_s") else ""
        print(f"  P{r['position']} {r['name']:12s} total: {r.get('total_time_s', 0):.1f}s{bl}")
