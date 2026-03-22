"""Top-level CLI dispatcher for NPC Race.

Entry point: ``npcrace`` via pyproject.toml console_scripts.
Uses argparse with subcommands.
"""

import argparse
import sys

from .commands import (
    cmd_init,
    cmd_list_tracks,
    cmd_run,
    cmd_season,
    cmd_tournament,
    cmd_validate,
    cmd_wizard,
)


def _add_run_parser(subs) -> None:
    """Add the 'run' subparser with race and league options."""
    run_p = subs.add_parser("run", help="Run a race")
    run_p.add_argument("--car-dir", default="cars",
                       help="Directory containing car .py files")
    run_p.add_argument("--laps", type=int, default=None, help="Number of laps")
    run_p.add_argument("--seed", type=int, default=42, help="Track generation seed")
    run_p.add_argument("--output", default="replay.json", help="Replay output file")
    run_p.add_argument("--track", default=None, help="Named track or 'random'")
    run_p.add_argument("--league", choices=["F3", "F2", "F1", "Championship"],
                       default=None, help="League tier (auto-detect if not specified)")


def _add_season_parser(subs) -> None:
    """Add the 'season' subparser."""
    season_p = subs.add_parser("season", help="Run a championship season")
    season_p.add_argument("--calendar", default="short",
                           help="Preset calendar: short, full, classic")
    season_p.add_argument("--tracks", default=None,
                           help="Custom track list (comma-separated)")
    season_p.add_argument("--laps", type=int, default=5, help="Laps per race")
    season_p.add_argument("--car-dir", default="cars", help="Car directory")
    season_p.add_argument("--output-dir", default="season_output",
                           help="Output directory for replays")


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="npcrace",
        description="NPC Race -- you build the car, we run the race",
    )
    subs = parser.add_subparsers(dest="command")
    subs.required = True

    _add_run_parser(subs)

    init_p = subs.add_parser("init", help="Create cars/ directory with template")
    init_p.add_argument("--dir", default="cars", help="Target directory (default: cars)")

    val_p = subs.add_parser("validate", help="Validate car file(s)")
    val_p.add_argument("car_files", nargs="+", help="Car .py files to validate")

    subs.add_parser("list-tracks", help="Print available tracks")
    subs.add_parser("wizard", help="Interactive car wizard (coming soon)")

    _add_tournament_parser(subs)
    _add_season_parser(subs)

    return parser


def _add_tournament_parser(subs) -> None:
    """Add the tournament subparser to the CLI."""
    tourn_p = subs.add_parser(
        "tournament", help="Run multi-race tournament with championship points",
    )
    tourn_p.add_argument(
        "--tracks", required=True,
        help="Comma-separated track names (e.g., monaco,monza,silverstone)",
    )
    tourn_p.add_argument("--races", type=int, default=1,
                         help="Races per track (default: 1)")
    tourn_p.add_argument("--laps", type=int, default=5,
                         help="Laps per race (default: 5)")
    tourn_p.add_argument("--car-dir", default="cars",
                         help="Car directory")
    tourn_p.add_argument("--data-dir", default=None,
                         help="Data directory for car persistence")
    tourn_p.add_argument("--output-dir", default="tournaments",
                         help="Output directory for replays")


_DISPATCH = {
    "run": cmd_run,
    "init": cmd_init,
    "validate": cmd_validate,
    "list-tracks": cmd_list_tracks,
    "wizard": cmd_wizard,
    "tournament": cmd_tournament,
    "season": cmd_season,
}


def main(argv: list[str] | None = None) -> None:
    """Parse args and dispatch to the appropriate command."""
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    handler = _DISPATCH[args.command]
    handler(args)
