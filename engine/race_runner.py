"""
Race runner entry point for NPC Race.

Orchestrates car loading, track generation, simulation,
and replay export.
"""

import json

from tracks import get_track
from .car_loader import load_all_cars
from .track_gen import generate_track, interpolate_track
from .simulation import RaceSim


def _resolve_track(track_name, track_seed, laps):
    """Return (track_points, effective_laps, real_length_m) for a race."""
    if track_name is not None:
        track_data = get_track(track_name)
        control = track_data["control_points"]
        effective_laps = laps if laps is not None else track_data["laps_default"]
        real_length_m = track_data.get("real_length_m")
    else:
        control = generate_track(seed=track_seed, num_points=12)
        effective_laps = laps if laps is not None else 3
        real_length_m = None
    track = interpolate_track(control, resolution=500)
    return track, effective_laps, real_length_m


def _print_results(results):
    """Print race results to stdout."""
    print("🏆 RESULTS")
    print(f"{'─' * 40}")
    for r in results:
        status = f"Tick {r['finish_tick']}" if r["finished"] else "DNF"
        print(f"  P{r['position']}  {r['name']:20s}  {status}")


def run_race(car_dir="cars", laps=None, track_seed=42, output="replay.json",
             track_name=None):
    """Load cars, run race, export replay.

    Parameters
    ----------
    track_name : str | None
        Named track preset key (e.g. "monza").
    laps : int | None
        Number of laps.  ``None`` means "use track default" (or 3).
    """
    track, effective_laps, real_length_m = _resolve_track(
        track_name, track_seed, laps
    )

    print(f"\n🏁 NPC RACE -- {effective_laps} laps")
    print(f"{'─' * 40}")
    print(f"Loading cars from: {car_dir}/\n")

    cars = load_all_cars(car_dir)
    if len(cars) < 2:
        raise ValueError("Need at least 2 cars to race!")

    print(f"\n{len(cars)} cars on the grid")
    if track_name:
        print(f"Track: {track_name}")
    else:
        print(f"Track seed: {track_seed}")
    print(f"{'─' * 40}\n")

    sim = RaceSim(cars, track, laps=effective_laps, seed=track_seed,
                  track_name=track_name, real_length_m=real_length_m)
    results = sim.run()

    _print_results(results)

    replay = sim.export_replay()
    with open(output, "w", encoding="utf-8") as f:
        json.dump(replay, f)
    print(f"\nReplay saved: {output}")
    print(f"Total frames: {len(replay['frames'])}")

    return results
