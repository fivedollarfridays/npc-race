"""
Race runner entry point for NPC Race.

Orchestrates car loading, track generation, simulation,
and replay export.
"""

import json
import os

from tracks import get_track
from .car_loader import load_all_cars
from .league_gates import apply_league_gates
from .results import generate_results_summary
from .track_gen import generate_track, interpolate_track
from .parts_simulation import PartsRaceSim
from .narrative import detect_events
from .commentary import format_events
from .race_report import generate_report
from .fast_export import export_lap_summary
from .race_dashboard import generate_dashboard


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


def _compute_results_path(output: str) -> str:
    """Derive the results file path from the replay output path."""
    base, ext = os.path.splitext(output)
    if os.path.basename(output) == "replay.json":
        return os.path.join(os.path.dirname(output), "results.json")
    return f"{base}_results{ext}"


def _export_results(replay: dict, cars: list[dict], league: str, output: str) -> None:
    """Generate and save a lightweight results summary alongside the replay."""
    results_path = _compute_results_path(output)
    summary = generate_results_summary(replay, cars, league=league)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Results saved to {results_path}")


def _export_fast(sim, results, output, track_name, cars, league):
    """Export results.json + lap_summary.json only (no replay.json)."""
    # Build minimal replay-like dict for generate_results_summary
    replay_stub = {
        "results": results,
        "track_name": track_name or "unknown",
        "laps": sim.laps,
    }
    _export_results(replay_stub, cars, league, output)

    # Write lap_summary.json alongside the output path
    out_dir = os.path.dirname(output) or "."
    lap_summary_path = os.path.join(out_dir, "lap_summary.json")
    export_lap_summary(sim, lap_summary_path)
    print(f"Lap summary saved to {lap_summary_path}")


def _export_replay(sim, results, output, track_name, cars, league):
    """Build narrative, export replay JSON and results, and print report."""
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

    _export_results(replay, cars, league, output)

    print(f"\n{report}")


def _load_and_filter_cars(car_dir, car_data_dir, league, *, verbose=False, tier=None):
    """Load cars from directory, apply league gates, return filtered list and league."""
    if car_data_dir:
        os.makedirs(car_data_dir, exist_ok=True)
        os.makedirs("cars/data", exist_ok=True)

    if tier and tier != "full":
        from .tiers import load_tier_cars
        cars = load_tier_cars(tier, car_dir)
    else:
        cars = load_all_cars(car_dir)
    if len(cars) < 2:
        raise ValueError("Need at least 2 cars to race!")

    cars, effective_league = apply_league_gates(cars, league, verbose=verbose)
    if len(cars) < 2:
        raise ValueError("Need at least 2 cars after league validation!")

    return cars, effective_league


def _reorder_by_grid(cars: list[dict], grid: list[dict]) -> list[dict]:
    """Reorder cars list by qualifying grid positions.

    P1 gets _grid_offset=0, P2 gets -15, P3 gets -30, etc.
    Cars not in the grid are appended at the back.
    """
    car_map = {c["CAR_NAME"]: c for c in cars}

    ordered: list[dict] = []
    for entry in sorted(grid, key=lambda g: g["grid_position"]):
        name = entry["name"]
        if name in car_map:
            car = car_map.pop(name)
            pos = entry["grid_position"]
            car["_grid_offset"] = -(pos - 1) * 15
            ordered.append(car)

    # Append any cars not in grid at the back
    next_pos = len(ordered) + 1
    for car in car_map.values():
        car["_grid_offset"] = -(next_pos - 1) * 15
        ordered.append(car)
        next_pos += 1

    return ordered


def _apply_grid_file(cars: list[dict], grid_file: str | None) -> list[dict]:
    """Load grid.json and reorder cars if grid file exists."""
    if grid_file and os.path.isfile(grid_file):
        with open(grid_file) as f:
            grid = json.load(f)
        cars = _reorder_by_grid(cars, grid)
        print("Grid order from qualifying applied")
    return cars


def _print_race_banner(
    effective_laps: int, car_dir: str, num_cars: int,
    track_name: str | None, track_seed: int,
) -> None:
    """Print the race start banner with track and car info."""
    print(f"\n🏁 NPC RACE -- {effective_laps} laps")
    print(f"{'─' * 40}")
    print(f"Loading cars from: {car_dir}/\n")


def _print_grid_info(cars, track_name, track_seed):
    """Print grid size and track info before the race starts."""
    print(f"\n{len(cars)} cars on the grid")
    if track_name:
        print(f"Track: {track_name}")
    else:
        print(f"Track seed: {track_seed}")
    print(f"{'─' * 40}\n")


def run_race(
    car_dir: str = "cars",
    laps: int | None = None,
    track_seed: int = 42,
    output: str = "replay.json",
    track_name: str | None = None,
    car_data_dir: str | None = None,
    race_number: int = 1,
    league: str | None = None,
    fast_mode: bool = False,
    grid_file: str | None = None,
    verbose: bool = False,
    quiet: bool = False,
    tier: str | None = None,
) -> list[dict]:
    """Load cars, apply league gates, run simulation, and export replay."""
    track, effective_laps, real_length_m, drs_zones = _resolve_track(
        track_name, track_seed, laps
    )

    if not quiet:
        _print_race_banner(effective_laps, car_dir, 0, track_name, track_seed)

    cars, effective_league = _load_and_filter_cars(
        car_dir, car_data_dir, league, verbose=verbose, tier=tier,
    )
    cars = _apply_grid_file(cars, grid_file)
    if not quiet:
        _print_grid_info(cars, track_name, track_seed)

    sim = PartsRaceSim(cars, track, laps=effective_laps, seed=track_seed,
                       track_name=track_name, real_length_m=real_length_m,
                       car_data_dir=car_data_dir, race_number=race_number,
                       drs_zones=drs_zones, fast_mode=fast_mode)
    results = sim.run()

    lap_sums = sim.get_lap_summaries() if fast_mode else None
    dashboard = generate_dashboard(
        results, lap_sums, track_name=track_name or "", laps=effective_laps,
    )
    print(dashboard)

    if fast_mode:
        _export_fast(sim, results, output, track_name, cars, effective_league)
    else:
        _export_replay(sim, results, output, track_name, cars, effective_league)

    return results
