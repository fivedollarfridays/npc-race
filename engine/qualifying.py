"""Qualifying simulation — single flying lap qualifying.

Each car runs solo (out-lap + flying lap). Results sorted by flying lap time.
"""

from __future__ import annotations

import json

from .simulation import RaceSim


def run_qualifying(
    cars: list[dict],
    track_points: list,
    track_name: str | None = None,
    real_length_m: float | None = None,
    drs_zones: list | None = None,
    seed: int = 42,
) -> list[dict]:
    """Run single-lap qualifying for all cars.

    Each car runs alone for 2 laps (out-lap + flying lap).
    Returns list sorted by qualifying time with grid positions.
    """
    results: list[dict] = []
    for car in cars:
        sim = RaceSim(
            cars=[car],
            track_points=track_points,
            laps=2,
            seed=seed,
            track_name=track_name,
            real_length_m=real_length_m,
            drs_zones=drs_zones,
            fast_mode=True,
        )
        sim.run()

        timing = sim.timings[car["CAR_NAME"]]
        if len(timing.lap_times) >= 2:
            qualifying_time = timing.lap_times[1]
        elif timing.lap_times:
            qualifying_time = timing.lap_times[0]
        else:
            qualifying_time = 999.0

        results.append({
            "name": car["CAR_NAME"],
            "qualifying_time": qualifying_time,
        })

    results.sort(key=lambda r: r["qualifying_time"])
    for i, r in enumerate(results):
        r["grid_position"] = i + 1

    return results


def export_grid(results: list[dict], path: str) -> None:
    """Write qualifying results to grid.json."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
