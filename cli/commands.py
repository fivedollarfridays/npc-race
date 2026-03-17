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

F1_POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}


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


def cmd_init(args) -> None:
    """Create a cars/ directory with a template car file."""
    target = args.dir
    if not os.path.isdir(target):
        os.makedirs(target, exist_ok=True)
        print(f"Created directory: {target}")
    else:
        print(f"Directory already exists: {target}")

    template_src = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "car_template.py",
    )
    dest = os.path.join(target, "car_template.py")
    if not os.path.exists(dest):
        shutil.copy2(template_src, dest)
        print(f"Copied template to: {dest}")
    else:
        print(f"Template already exists: {dest} (skipped)")


def cmd_run(args) -> None:
    """Run a race, mirroring play.py behavior (no auto-browser)."""
    if not os.path.isdir(args.car_dir):
        print(f"Car directory not found: {args.car_dir}")
        return

    track_name = _resolve_track(args)
    run_race(
        car_dir=args.car_dir,
        laps=args.laps,
        track_seed=args.seed,
        output=args.output,
        track_name=track_name,
    )


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
        points = F1_POINTS.get(pos, 0)
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
