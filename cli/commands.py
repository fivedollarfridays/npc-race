"""CLI command implementations for NPC Race.

Each function corresponds to a subcommand and receives the parsed
argparse namespace.
"""

import os
import shutil

from engine import run_race
from security.bot_scanner import scan_car_file
from tracks import TRACKS, list_tracks


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
