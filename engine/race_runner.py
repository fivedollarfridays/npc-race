"""
Race runner entry point for NPC Race.

Orchestrates car loading, track generation, simulation,
and replay export.
"""

import json
import os

from tracks import get_track
from .car_loader import load_all_cars
from .track_gen import generate_track, interpolate_track
from .simulation import RaceSim


def _resolve_track(track_name, track_seed, laps):
    """Return (track_points, effective_laps, real_length_m, drs_zones) for a race."""
    if track_name is not None:
        track_data = get_track(track_name)
        control = track_data["control_points"]
        effective_laps = laps if laps is not None else track_data["laps_default"]
        real_length_m = track_data.get("real_length_m")
        drs_zones = track_data.get("drs_zones", [])
    else:
        control = generate_track(seed=track_seed, num_points=12)
        effective_laps = laps if laps is not None else 3
        real_length_m = None
        drs_zones = []
    track = interpolate_track(control, resolution=500)
    return track, effective_laps, real_length_m, drs_zones


def _print_results(results):
    """Print race results to stdout."""
    print("🏆 RESULTS")
    print(f"{'─' * 40}")
    for r in results:
        status = f"Tick {r['finish_tick']}" if r["finished"] else "DNF"
        print(f"  P{r['position']}  {r['name']:20s}  {status}")


def run_race(
    car_dir: str = "cars",
    laps: int | None = None,
    track_seed: int = 42,
    output: str = "replay.json",
    track_name: str | None = None,
    car_data_dir: str | None = None,
    race_number: int = 1,
) -> list[dict]:
    """Load cars, run race, export replay.

    Parameters
    ----------
    car_dir : str
        Directory containing car Python files.
    track_name : str | None
        Named track preset key (e.g. "monza").  ``None`` generates a random track.
    laps : int | None
        Number of laps.  ``None`` means "use track default" (or 3).
    car_data_dir : str | None
        Directory for cross-race learning JSON files.  ``None`` disables learning.
    race_number : int
        Sequential race number within a tournament (passed to car strategies).
    """
    track, effective_laps, real_length_m, drs_zones = _resolve_track(
        track_name, track_seed, laps
    )

    print(f"\n🏁 NPC RACE -- {effective_laps} laps")
    print(f"{'─' * 40}")
    print(f"Loading cars from: {car_dir}/\n")

    if car_data_dir:
        os.makedirs(car_data_dir, exist_ok=True)
        # Seed cars write to this hardcoded path (required by bot_scanner security model)
        os.makedirs("cars/data", exist_ok=True)

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
                  track_name=track_name, real_length_m=real_length_m,
                  car_data_dir=car_data_dir, race_number=race_number,
                  drs_zones=drs_zones)
    results = sim.run()

    _print_results(results)

    replay = sim.export_replay()
    with open(output, "w", encoding="utf-8") as f:
        json.dump(replay, f)
    print(f"\nReplay saved: {output}")
    print(f"Total frames: {len(replay['frames'])}")

    return results
