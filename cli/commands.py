"""CLI command implementations for NPC Race.

Each function corresponds to a subcommand and receives the parsed
argparse namespace.
"""

import json
import os
import shutil

from engine import run_race
from security.bot_scanner import scan_car_file
from tracks import TRACKS, list_tracks
from viewer.launcher import launch_viewer

from engine.championship import F1_POINTS


def cmd_list_tracks(_args) -> None:
    """Print all available tracks with name, country, and character."""
    print(f"\n{'Name':<16} {'Country':<20} {'Character':<12}")
    print(f"{'─' * 16} {'─' * 20} {'─' * 12}")
    for key in list_tracks():
        t = TRACKS[key]
        print(f"{key:<16} {t['country']:<20} {t['character']:<12}")
    print(f"\n{len(TRACKS)} tracks available")


def cmd_validate(args) -> None:
    """Validate one or more car files using the bot scanner."""
    for path in args.car_files:
        result = scan_car_file(path)
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}: {path}")
        if not result.passed:
            for v in result.violations:
                print(f"  - {v}")


def cmd_init(args) -> int:
    """Create a project directory from the default F3 template."""
    target = args.dir
    if os.path.exists(target):
        print(f"Error: directory already exists: {target}")
        return 1

    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "cars",
        "default_project",
    )
    shutil.copytree(template_dir, target)
    print(f"Created {target}/ with 3 F3 parts. Run: npcrace run --car-dir {target}")
    return 0


def cmd_run(args) -> None:
    """Run a race and optionally open the replay viewer in a browser."""
    if not os.path.isdir(args.car_dir):
        print(f"Car directory not found: {args.car_dir}")
        return

    track_name = _resolve_track(args)
    league = getattr(args, "league", None)
    live = getattr(args, "live", False)
    fast_mode = not live
    run_race(
        car_dir=args.car_dir,
        laps=args.laps,
        track_seed=args.seed,
        output=args.output,
        track_name=track_name,
        league=league,
        fast_mode=fast_mode,
    )

    if live and not getattr(args, "no_browser", False):
        launch_viewer(args.output)


def cmd_wizard(_args) -> None:
    """Stub for the interactive car wizard (coming soon)."""
    print("Wizard is not yet implemented. Coming soon!")


def _resolve_track(args) -> str | None:
    """Resolve --track flag to a track key or None."""
    if args.track is None:
        return None
    from tracks import random_track
    if args.track == "random":
        chosen = random_track()
        print(f"Random track selected: {chosen}")
        return chosen
    name = args.track.lower()
    if name not in TRACKS:
        print(f"Unknown track: '{args.track}'")
        print(f"Available tracks: {', '.join(list_tracks())}")
        return None
    return name


def cmd_tournament(args) -> None:
    """Run multi-race tournament with F1 championship points."""
    tracks = [t.strip().lower() for t in args.tracks.split(",")]

    # Validate track names up front
    invalid = [t for t in tracks if t not in TRACKS]
    if invalid:
        print(f"Unknown track(s): {', '.join(invalid)}")
        print(f"Available tracks: {', '.join(sorted(TRACKS))}")
        return

    races_per_track = args.races
    laps = args.laps
    car_dir = args.car_dir
    data_dir = args.data_dir or os.path.join(car_dir, "data")
    output_dir = args.output_dir

    os.makedirs(output_dir, exist_ok=True)

    standings: dict[str, int] = {}
    race_num = 0

    _print_tournament_header(tracks, races_per_track, laps)

    for track_name in tracks:
        for _race_idx in range(races_per_track):
            race_num += 1
            output = os.path.join(output_dir, f"race_{race_num}_{track_name}.json")

            run_race(
                car_dir=car_dir,
                laps=laps,
                track_name=track_name,
                output=output,
                car_data_dir=data_dir,
                race_number=race_num,
            )

            try:
                with open(output) as f:
                    replay = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"  [Error reading replay for race {race_num}: {e}]")
                continue

            _award_points(standings, replay["results"], race_num, track_name)

    _print_final_standings(standings)


def _print_tournament_header(tracks, races_per_track, laps):
    """Print the tournament banner and configuration."""
    print("=" * 60)
    print("NPC RACE -- CHAMPIONSHIP TOURNAMENT")
    print("=" * 60)
    print(f"Tracks: {', '.join(tracks)}")
    print(f"Races per track: {races_per_track}")
    print(f"Laps per race: {laps}")
    print()


def _award_points(standings, results, race_num, track_name):
    """Award F1 points from a single race and print race summary."""
    print(f"\n--- Race {race_num}: {track_name.upper()} ---")
    for result in results:
        name = result["name"]
        pos = result["position"]
        points = F1_POINTS[pos - 1] if pos <= len(F1_POINTS) else 0
        standings[name] = standings.get(name, 0) + points
        print(f"  P{pos}  {name:20s}  +{points} pts")

    print(f"\n  Championship after Race {race_num}:")
    for rank, (name, pts) in enumerate(
        sorted(standings.items(), key=lambda x: -x[1]), 1,
    ):
        print(f"    {rank}. {name:20s}  {pts} pts")


def _print_final_standings(standings):
    """Print the final championship standings table."""
    print()
    print("=" * 60)
    print("FINAL CHAMPIONSHIP STANDINGS")
    print("=" * 60)
    for rank, (name, pts) in enumerate(
        sorted(standings.items(), key=lambda x: -x[1]), 1,
    ):
        marker = " CHAMPION" if rank == 1 else ""
        print(f"  {rank}. {name:20s}  {pts} pts{marker}")


def cmd_submit(args) -> int:
    """Validate a results file and print submission summary."""
    path = args.results_file
    if not os.path.isfile(path):
        print(f"Error: File not found: {path}")
        return 1

    try:
        with open(path) as f:
            results = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}")
        return 1

    from engine.results import verify_integrity

    if not verify_integrity(results):
        print("Integrity check FAILED -- results may have been tampered with")
        return 1

    _print_submit_summary(results)
    return 0


def _print_submit_summary(results: dict) -> None:
    """Print a human-readable submission summary."""
    print("Results verified")
    print(f"  Track: {results.get('track', 'unknown')}")
    print(f"  Laps: {results.get('laps', '?')}")
    print(f"  League: {results.get('league', '?')}")
    print()
    for car in results.get("cars", []):
        print(
            f"  P{car['position']}  {car['name']:<20}  "
            f"{car['total_time_s']:.2f}s  "
            f"(best: {car.get('best_lap_s', 0):.2f}s)  "
            f"reliability: {car.get('reliability_score', 1.0):.2f}"
        )
    print()
    print(f"  Hash: {results.get('integrity', 'none')}")
    print("  Ready for leaderboard submission.")


def cmd_season(args) -> None:
    """Run a championship season."""
    from engine.season_runner import run_season
    custom = [t.strip() for t in args.tracks.split(",")] if args.tracks else None
    run_season(
        car_dir=args.car_dir,
        season_name=args.calendar,
        custom_tracks=custom,
        laps=args.laps,
        output_dir=args.output_dir,
    )


def cmd_leaderboard(args) -> int:
    """View, update, or reset the local leaderboard."""
    from engine.leaderboard import (
        add_result,
        format_standings,
        load_leaderboard,
        new_leaderboard,
        save_leaderboard,
    )

    lb_path = args.file

    if args.reset:
        save_leaderboard(new_leaderboard(), lb_path)
        print("Leaderboard reset.")
        return 0

    if args.add:
        if not os.path.isfile(args.add):
            print(f"Error: results file not found: {args.add}")
            return 1

        try:
            with open(args.add) as f:
                results = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {args.add}: {e}")
            return 1

        from engine.results import verify_integrity

        if not verify_integrity(results):
            print("Error: integrity check failed -- results may be tampered")
            return 1

        lb = load_leaderboard(lb_path)
        lb = add_result(lb, results)
        save_leaderboard(lb, lb_path)

        num_cars = len(results.get("cars", []))
        print(f"Added {num_cars} cars to leaderboard")
        print(format_standings(lb))
        return 0

    # Default: show standings
    lb = load_leaderboard(lb_path)
    print(format_standings(lb))
    return 0
