"""CLI commands for qualifying and race pipeline.

Provides cmd_qualify and cmd_race for the npcrace CLI.
"""

import os

from engine.car_loader import load_all_cars
from engine.qualifying import export_grid, run_qualifying
from engine.race_runner import run_race
from tracks import TRACKS


def _resolve_track_for_qualifying(track_name: str) -> dict:
    """Resolve a track name to track data dict.

    Returns dict with keys: track_points, real_length_m, drs_zones, laps_default.
    """
    from tracks import get_track
    from engine.track_gen import interpolate_track

    track_data = get_track(track_name)
    control = track_data["control_points"]
    track_points = interpolate_track(control, resolution=500)
    return {
        "track_points": track_points,
        "real_length_m": track_data.get("real_length_m"),
        "drs_zones": track_data.get("drs_zones", []),
        "laps_default": track_data.get("laps_default", 5),
    }


def _print_qualifying_results(results: list[dict]) -> None:
    """Print qualifying results to stdout."""
    print("\nQUALIFYING RESULTS")
    print(f"{'─' * 40}")
    for r in results:
        pos = r["grid_position"]
        name = r["name"]
        time_s = r["qualifying_time"]
        mins, secs = int(time_s // 60), time_s % 60
        print(f"  P{pos}  {name:<20s}  {mins}:{secs:06.3f}")


def cmd_qualify(args) -> None:
    """Run qualifying session and export grid.json."""
    if not os.path.isdir(args.car_dir):
        print(f"Car directory not found: {args.car_dir}")
        return

    track_name = args.track.lower()
    if track_name not in TRACKS:
        print(f"Unknown track: '{args.track}'")
        return

    cars = load_all_cars(args.car_dir)
    if not cars:
        print("No cars found")
        return

    td = _resolve_track_for_qualifying(track_name)
    results = run_qualifying(
        cars,
        track_points=td["track_points"],
        track_name=track_name,
        real_length_m=td["real_length_m"],
        drs_zones=td["drs_zones"],
    )

    export_grid(results, args.output)
    _print_qualifying_results(results)
    print(f"\nGrid exported to {args.output}")


def cmd_race(args) -> None:
    """Run a race, optionally with qualifying first."""
    if not os.path.isdir(args.car_dir):
        print(f"Car directory not found: {args.car_dir}")
        return

    grid_file = None

    if args.qualify:
        track_name = args.track.lower() if args.track else None
        if track_name and track_name not in TRACKS:
            print(f"Unknown track: '{args.track}'")
            return

        cars = load_all_cars(args.car_dir)
        if not cars:
            print("No cars found")
            return

        td = _resolve_track_for_qualifying(track_name)
        q_results = run_qualifying(
            cars,
            track_points=td["track_points"],
            track_name=track_name,
            real_length_m=td["real_length_m"],
            drs_zones=td["drs_zones"],
        )

        grid_path = os.path.join(
            os.path.dirname(args.output) or ".", "grid.json",
        )
        export_grid(q_results, grid_path)
        _print_qualifying_results(q_results)
        grid_file = grid_path

    live = getattr(args, "live", False)
    fast_mode = not live
    track_name_arg = args.track if args.track else None

    run_race(
        car_dir=args.car_dir,
        laps=args.laps,
        track_seed=getattr(args, "seed", 42),
        output=args.output,
        track_name=track_name_arg,
        league=getattr(args, "league", None),
        fast_mode=fast_mode,
        grid_file=grid_file,
    )
