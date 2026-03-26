"""Ultra-fast single-car time trial. No rivals, no replay, direct calls."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from engine import safe_call
from engine.car_project_loader import load_car_project
from engine.parts_simulation import PartsRaceSim
from engine.track_gen import interpolate_track
from tracks import get_track


@dataclass
class TrialResult:
    """Result of a single-car time trial."""

    lap_time: float
    sector_times: list[float] = field(default_factory=list)
    efficiency: dict[str, float] = field(default_factory=dict)
    car_name: str = ""
    track_name: str = ""


def run_time_trial(car_dir: str, track_name: str = "monza") -> TrialResult:
    """Run a 1-lap time trial for a single car. Returns in < 2 seconds."""
    car = load_car_project(car_dir)

    td = get_track(track_name)
    pts = interpolate_track(td["control_points"], resolution=500)
    real_length = td.get("real_length_m")

    # Disable safe_call threading for speed
    old_timeout = safe_call.TIMEOUT_ENABLED
    safe_call.TIMEOUT_ENABLED = False

    try:
        sim = PartsRaceSim(
            cars=[car],
            track_points=pts,
            laps=1,
            seed=42,
            track_name=track_name,
            real_length_m=real_length,
            fast_mode=True,
        )
        sim.run()
    finally:
        safe_call.TIMEOUT_ENABLED = old_timeout

    results = sim.get_results()
    lap_time = results[0]["total_time_s"] if results else 0.0

    efficiency = _extract_efficiency(sim.call_logs, car["CAR_NAME"])

    ct = sim.timings.get(car["CAR_NAME"])
    sector_times: list[float] = []
    if ct and ct.sector_times:
        sector_times = ct.sector_times[0] if ct.sector_times else []

    return TrialResult(
        lap_time=lap_time,
        sector_times=sector_times,
        efficiency=efficiency,
        car_name=car["CAR_NAME"],
        track_name=track_name,
    )


def _extract_efficiency(call_logs: list, car_name: str) -> dict[str, float]:
    """Average per-part efficiency from call logs."""
    part_sums: dict[str, list[float]] = {}
    for tick_log in call_logs:
        for entry in tick_log:
            if entry.get("car_name") == car_name or len(tick_log) <= 10:
                part = entry.get("part", "")
                eff = entry.get("efficiency", 1.0)
                if part:
                    part_sums.setdefault(part, []).append(eff)

    return {
        part: sum(vals) / len(vals)
        for part, vals in part_sums.items()
        if vals
    }


def find_player_car(cars_dir: str = "cars") -> str | None:
    """Find the first player car project directory."""
    if not os.path.isdir(cars_dir):
        return None
    for name in sorted(os.listdir(cars_dir)):
        full = os.path.join(cars_dir, name)
        if (
            os.path.isdir(full)
            and name != "default_project"
            and not name.startswith("_")
            and name != "data"
            and os.path.isfile(os.path.join(full, "car.py"))
        ):
            return full
    return None
