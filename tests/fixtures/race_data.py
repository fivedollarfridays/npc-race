"""Pre-built race data for tests that don't need the real simulation.

Data structures match the formats produced by:
- engine.car_loader (SAMPLE_CARS)
- engine.replay.get_results / engine.results (SAMPLE_RESULTS, SAMPLE_RESULTS_SUMMARY)
- engine.lap_accumulator (SAMPLE_LAP_SUMMARIES)
- engine.qualifying (SAMPLE_GRID)
"""

from __future__ import annotations

SAMPLE_CARS: list[dict] = [
    {"CAR_NAME": "TestCar1", "CAR_COLOR": "#ff0000", "POWER": 25, "GRIP": 20,
     "WEIGHT": 20, "AERO": 20, "BRAKES": 15, "reliability_score": 0.95},
    {"CAR_NAME": "TestCar2", "CAR_COLOR": "#0000ff", "POWER": 20, "GRIP": 25,
     "WEIGHT": 20, "AERO": 20, "BRAKES": 15, "reliability_score": 0.90},
    {"CAR_NAME": "TestCar3", "CAR_COLOR": "#00ff00", "POWER": 22, "GRIP": 22,
     "WEIGHT": 18, "AERO": 20, "BRAKES": 18, "reliability_score": 0.88},
    {"CAR_NAME": "TestCar4", "CAR_COLOR": "#ffff00", "POWER": 18, "GRIP": 18,
     "WEIGHT": 22, "AERO": 22, "BRAKES": 20, "reliability_score": 0.85},
    {"CAR_NAME": "TestCar5", "CAR_COLOR": "#ff00ff", "POWER": 20, "GRIP": 20,
     "WEIGHT": 20, "AERO": 22, "BRAKES": 18, "reliability_score": 0.82},
    {"CAR_NAME": "TestCar6", "CAR_COLOR": "#00ffff", "POWER": 15, "GRIP": 20,
     "WEIGHT": 25, "AERO": 20, "BRAKES": 20, "reliability_score": 0.80},
]

SAMPLE_RESULTS: list[dict] = [
    {"name": "TestCar1", "position": 1, "total_time_s": 85.2,
     "best_lap_s": 85.2, "lap_times": [85.2], "finished": True,
     "reliability_score": 0.95},
    {"name": "TestCar2", "position": 2, "total_time_s": 86.5,
     "best_lap_s": 86.5, "lap_times": [86.5], "finished": True,
     "reliability_score": 0.90},
    {"name": "TestCar3", "position": 3, "total_time_s": 87.1,
     "best_lap_s": 87.1, "lap_times": [87.1], "finished": True,
     "reliability_score": 0.88},
    {"name": "TestCar4", "position": 4, "total_time_s": 88.3,
     "best_lap_s": 88.3, "lap_times": [88.3], "finished": True,
     "reliability_score": 0.85},
    {"name": "TestCar5", "position": 5, "total_time_s": 89.0,
     "best_lap_s": 89.0, "lap_times": [89.0], "finished": True,
     "reliability_score": 0.82},
    {"name": "TestCar6", "position": 6, "total_time_s": 90.2,
     "best_lap_s": 90.2, "lap_times": [90.2], "finished": True,
     "reliability_score": 0.80},
]

SAMPLE_RESULTS_SUMMARY: dict = {
    "track": "monza",
    "laps": 1,
    "league": "F3",
    "cars": [
        {"name": "TestCar1", "position": 1, "total_time_s": 85.2,
         "best_lap_s": 85.2, "reliability_score": 0.95},
        {"name": "TestCar2", "position": 2, "total_time_s": 86.5,
         "best_lap_s": 86.5, "reliability_score": 0.90},
        {"name": "TestCar3", "position": 3, "total_time_s": 87.1,
         "best_lap_s": 87.1, "reliability_score": 0.88},
        {"name": "TestCar4", "position": 4, "total_time_s": 88.3,
         "best_lap_s": 88.3, "reliability_score": 0.85},
        {"name": "TestCar5", "position": 5, "total_time_s": 89.0,
         "best_lap_s": 89.0, "reliability_score": 0.82},
        {"name": "TestCar6", "position": 6, "total_time_s": 90.2,
         "best_lap_s": 90.2, "reliability_score": 0.80},
    ],
    "integrity": "sha256:placeholder",
}

SAMPLE_LAP_SUMMARIES: dict[str, list[dict]] = {
    "TestCar1": [
        {"lap": 1, "time_s": 85.2, "position": 1, "tire_compound": "medium",
         "tire_wear": 0.05, "pit_stop": False, "fuel_remaining_pct": 0.95},
    ],
    "TestCar2": [
        {"lap": 1, "time_s": 86.5, "position": 2, "tire_compound": "medium",
         "tire_wear": 0.06, "pit_stop": False, "fuel_remaining_pct": 0.94},
    ],
    "TestCar3": [
        {"lap": 1, "time_s": 87.1, "position": 3, "tire_compound": "medium",
         "tire_wear": 0.07, "pit_stop": False, "fuel_remaining_pct": 0.93},
    ],
    "TestCar4": [
        {"lap": 1, "time_s": 88.3, "position": 4, "tire_compound": "medium",
         "tire_wear": 0.08, "pit_stop": False, "fuel_remaining_pct": 0.92},
    ],
    "TestCar5": [
        {"lap": 1, "time_s": 89.0, "position": 5, "tire_compound": "medium",
         "tire_wear": 0.09, "pit_stop": False, "fuel_remaining_pct": 0.91},
    ],
    "TestCar6": [
        {"lap": 1, "time_s": 90.2, "position": 6, "tire_compound": "medium",
         "tire_wear": 0.10, "pit_stop": False, "fuel_remaining_pct": 0.90},
    ],
}

SAMPLE_GRID: list[dict] = [
    {"name": "TestCar1", "qualifying_time": 82.1, "grid_position": 1},
    {"name": "TestCar2", "qualifying_time": 83.4, "grid_position": 2},
    {"name": "TestCar3", "qualifying_time": 83.9, "grid_position": 3},
    {"name": "TestCar4", "qualifying_time": 84.5, "grid_position": 4},
    {"name": "TestCar5", "qualifying_time": 85.0, "grid_position": 5},
    {"name": "TestCar6", "qualifying_time": 85.8, "grid_position": 6},
]


def make_results(n_cars: int = 6, n_laps: int = 3) -> list[dict]:
    """Factory for custom-sized race results."""
    results = []
    for i in range(n_cars):
        lap_times = [80.0 + i * 2.0 + j * 0.1 for j in range(n_laps)]
        results.append({
            "name": f"Car_{i + 1}",
            "position": i + 1,
            "total_time_s": sum(lap_times),
            "best_lap_s": min(lap_times),
            "lap_times": lap_times,
            "finished": True,
            "reliability_score": max(0.7, 1.0 - i * 0.03),
        })
    return results


def make_lap_summaries(
    n_cars: int = 6, n_laps: int = 3,
) -> dict[str, list[dict]]:
    """Factory for custom-sized lap summaries."""
    summaries: dict[str, list[dict]] = {}
    for i in range(n_cars):
        summaries[f"Car_{i + 1}"] = [
            {
                "lap": lap + 1,
                "time_s": 80.0 + i * 2.0 + lap * 0.1,
                "position": i + 1,
                "tire_compound": "medium" if lap < n_laps // 2 else "hard",
                "tire_wear": 0.05 * (lap + 1),
                "pit_stop": lap == n_laps // 2,
                "fuel_remaining_pct": max(0.1, 1.0 - lap * (0.8 / n_laps)),
            }
            for lap in range(n_laps)
        ]
    return summaries
