"""
Race runner entry point for NPC Race.

Orchestrates car loading, track generation, simulation,
and replay export.
"""

import json
import os

from tracks import get_track
from .car_loader import load_all_cars
from .league_system import (
    LEAGUE_TIERS,
    determine_league,
    generate_quality_report,
    validate_car_for_league,
)
from .track_gen import generate_track, interpolate_track
from .simulation import RaceSim
from .narrative import detect_events
from .commentary import format_events
from .race_report import generate_report


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
    """Print race results to stdout with formatted times."""
    print("🏆 RESULTS")
    print(f"{'─' * 50}")
    leader_time = None
    for r in results:
        if not r["finished"]:
            print(f"  P{r['position']}  {r['name']:12s}  DNF")
            continue
        total = r.get("total_time_s") or 0
        mins, secs = int(total // 60), total % 60
        time_str = f"{mins}:{secs:06.3f}"
        best = r.get("best_lap_s")
        best_str = ""
        if best:
            bm, bs = int(best // 60), best % 60
            best_str = f"  (best: {bm}:{bs:06.3f})"
        if r["position"] == 1:
            leader_time = total
            gap = ""
        else:
            gap = f"  +{total - (leader_time or total):.3f}s"
        print(f"  P{r['position']}  {r['name']:12s}  {time_str}{gap}{best_str}")


def _apply_league_gates(
    cars: list[dict], league: str | None,
) -> tuple[list[dict], str]:
    """Detect/validate league, print quality reports, filter rejected cars.

    Returns (filtered_cars, effective_league).
    """
    # Determine effective league
    if league is None:
        per_car = [determine_league(c) for c in cars]
        effective = max(per_car, key=lambda t: LEAGUE_TIERS.index(t))
        label = f"{effective} (auto-detected)"
    else:
        effective = league
        label = effective

    print(f"\n=== League: {label} ===")

    filtered: list[dict] = []
    for car in cars:
        car["league"] = effective
        name = car.get("name", "Unknown")
        parts = car.get("_loaded_parts", [])

        # Validate parts against league
        if league is not None:
            vr = validate_car_for_league(car, effective)
            if not vr.passed:
                reasons = "; ".join(vr.violations)
                print(f"  {name}: REJECTED -- {reasons}")
                continue

        # Quality report (only enforce gates when league is explicitly specified)
        qr = generate_quality_report(car, effective)
        _print_car_league_status(name, parts, qr, effective)

        if league is not None and not qr.passed:
            violations = "; ".join(qr.blocking_violations)
            print(f"  {name}: REJECTED -- {violations}")
            continue

        filtered.append(car)

    return filtered, effective


def _print_car_league_status(
    name: str, parts: list[str], qr, league: str,
) -> None:
    """Print one car's league status line."""
    n_parts = len(parts)
    if n_parts == 0:
        print(f"  {name}: 0 custom parts -> using defaults ({league} allowed)")
    else:
        part_list = ", ".join(sorted(parts))
        print(f"  {name}: {n_parts} custom parts [{part_list}]")

    # Quality details
    if qr.advisory_messages:
        for msg in qr.advisory_messages:
            print(f"    Advisory: {msg}")
    if qr.passed and not qr.blocking_violations:
        status = "Advisory: clean code" if league in ("F3", "F2") else f"Passed {league} gate"
        print(
            f"    Quality: reliability {qr.reliability_score:.2f} | "
            f"CC avg n/a | {status}"
        )


def _export_replay(sim, results, output, track_name):
    """Build narrative, export replay JSON, and print report."""
    replay = sim.export_replay()

    events = detect_events(replay["frames"], replay.get("ticks_per_sec", 30), results)
    commentary = format_events(events)
    report = generate_report(
        results, events, commentary, track_name=track_name or "Unknown",
    )
    replay["events"] = [
        {"type": e.type, "tick": e.tick, "cars": e.cars, "data": e.data}
        for e in events
    ]
    replay["commentary"] = commentary
    replay["race_report"] = report

    with open(output, "w", encoding="utf-8") as f:
        json.dump(replay, f)
    print(f"\nReplay saved: {output}")
    print(f"Total frames: {len(replay['frames'])}")
    print(f"\n{report}")


def _load_and_filter_cars(car_dir, car_data_dir, league):
    """Load cars from directory, apply league gates, return filtered list."""
    if car_data_dir:
        os.makedirs(car_data_dir, exist_ok=True)
        os.makedirs("cars/data", exist_ok=True)

    cars = load_all_cars(car_dir)
    if len(cars) < 2:
        raise ValueError("Need at least 2 cars to race!")

    cars, _effective_league = _apply_league_gates(cars, league)
    if len(cars) < 2:
        raise ValueError("Need at least 2 cars after league validation!")

    return cars


def run_race(
    car_dir: str = "cars",
    laps: int | None = None,
    track_seed: int = 42,
    output: str = "replay.json",
    track_name: str | None = None,
    car_data_dir: str | None = None,
    race_number: int = 1,
    league: str | None = None,
) -> list[dict]:
    """Load cars, apply league gates, run simulation, and export replay."""
    track, effective_laps, real_length_m, drs_zones = _resolve_track(
        track_name, track_seed, laps
    )

    print(f"\n🏁 NPC RACE -- {effective_laps} laps")
    print(f"{'─' * 40}")
    print(f"Loading cars from: {car_dir}/\n")

    cars = _load_and_filter_cars(car_dir, car_data_dir, league)

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
    _export_replay(sim, results, output, track_name)

    return results
