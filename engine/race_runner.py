"""
Race runner entry point for NPC Race.

Orchestrates car loading, track generation, simulation,
and replay export.
"""

import json

from .car_loader import load_all_cars
from .track_gen import generate_track, interpolate_track
from .simulation import RaceSim


def run_race(car_dir="cars", laps=3, track_seed=42, output="replay.json"):
    """Load cars, run race, export replay."""
    print(f"\n🏁 NPC RACE -- {laps} laps")
    print(f"{'─' * 40}")
    print(f"Loading cars from: {car_dir}/\n")

    cars = load_all_cars(car_dir)
    if len(cars) < 2:
        raise ValueError("Need at least 2 cars to race!")

    print(f"\n{len(cars)} cars on the grid")
    print(f"Track seed: {track_seed}")
    print(f"{'─' * 40}\n")

    # Generate track
    control = generate_track(seed=track_seed, num_points=12)
    track = interpolate_track(control, resolution=500)

    # Run sim
    sim = RaceSim(cars, track, laps=laps, seed=track_seed)
    results = sim.run()

    # Print results
    print("🏆 RESULTS")
    print(f"{'─' * 40}")
    for r in results:
        status = f"Tick {r['finish_tick']}" if r["finished"] else "DNF"
        print(f"  P{r['position']}  {r['name']:20s}  {status}")

    # Export replay
    replay = sim.export_replay()
    with open(output, "w") as f:
        json.dump(replay, f)
    print(f"\nReplay saved: {output}")
    print(f"Total frames: {len(replay['frames'])}")

    return results
