"""Top-level CLI dispatcher for NPC Race.

Entry point: ``npcrace`` via pyproject.toml console_scripts.
Uses argparse with subcommands.
"""

import argparse
import sys

from .commands import (
    cmd_init,
    cmd_leaderboard,
    cmd_list_tracks,
    cmd_run,
    cmd_season,
    cmd_submit,
    cmd_tournament,
    cmd_validate,
)
from .trial_command import cmd_trial
from .race_commands import cmd_qualify, cmd_race


def _add_run_parser(subs) -> None:
    """Add the 'run' subparser with race and league options."""
    run_p = subs.add_parser("run", help="Run a single race (default: fast mode)")
    run_p.add_argument("--car-dir", default="cars",
                       help="Directory containing car .py files")
    run_p.add_argument("--laps", type=int, default=None, help="Number of laps")
    run_p.add_argument("--seed", type=int, default=42, help="Track generation seed")
    run_p.add_argument("--output", default="replay.json", help="Replay output file")
    run_p.add_argument("--track", default=None, help="Named track or 'random'")
    run_p.add_argument("--league", choices=["F3", "F2", "F1", "Championship"],
                       default=None, help="League tier (auto-detect if not specified)")
    run_p.add_argument("--no-browser", action="store_true",
                       help="Don't auto-open the viewer in a browser")
    run_p.add_argument("--live", action="store_true", default=False,
                       help="Enable live replay mode (full replay.json export)")
    run_p.add_argument("--verbose", "-v", action="store_true", default=False,
                       help="Show per-car league validation details")


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

    init_p = subs.add_parser("init", help="Create a project from the F3 template")
    init_p.add_argument("dir", nargs="?", default="cars",
                        help="Target directory (default: cars)")

    val_p = subs.add_parser("validate", help="Validate car file(s)")
    val_p.add_argument("car_files", nargs="+", help="Car .py files to validate")

    subs.add_parser("list-tracks", help="Print available tracks")
    submit_p = subs.add_parser(
        "submit", help="Validate and prepare results for submission",
    )
    submit_p.add_argument("results_file", help="Path to results.json")

    _add_tournament_parser(subs)
    _add_season_parser(subs)
    _add_leaderboard_parser(subs)
    _add_qualify_parser(subs)
    _add_race_parser(subs)
    _add_trial_parser(subs)

    return parser


def _add_leaderboard_parser(subs) -> None:
    """Add the 'leaderboard' subparser."""
    lb_p = subs.add_parser("leaderboard", help="View or update leaderboard")
    lb_p.add_argument("--add", default=None,
                       help="Path to results.json to add")
    lb_p.add_argument("--reset", action="store_true",
                       help="Reset the leaderboard")
    lb_p.add_argument("--file", default="leaderboard.json",
                       help="Leaderboard file path")


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


def _add_trial_parser(subs) -> None:
    """Add the 'trial' subparser for quick solo time trials."""
    trial_p = subs.add_parser("trial", help="Run a quick time trial (solo, no rivals)")
    trial_p.add_argument(
        "--track", default="monza", help="Track name (default: monza)",
    )
    trial_p.add_argument(
        "--car-dir", default=None,
        help="Car project directory (auto-detect if not set)",
    )


def _add_qualify_parser(subs) -> None:
    """Add the 'qualify' subparser."""
    q_p = subs.add_parser("qualify", help="Run qualifying session")
    q_p.add_argument("--car-dir", default="cars",
                     help="Directory containing car .py files")
    q_p.add_argument("--track", required=True, help="Named track")
    q_p.add_argument("--output", default="grid.json",
                     help="Grid output file (default: grid.json)")


def _add_race_parser(subs) -> None:
    """Add the 'race' subparser for qualify+race pipeline."""
    r_p = subs.add_parser(
        "race",
        help="Run a full race weekend (qualifying + race + leaderboard)",
    )
    r_p.add_argument("--car-dir", default="cars",
                     help="Directory containing car .py files")
    r_p.add_argument("--track", default=None, help="Named track")
    r_p.add_argument("--laps", type=int, default=None, help="Number of laps")
    r_p.add_argument("--qualify", action="store_true",
                     help="Run qualifying before the race")
    r_p.add_argument("--output", default="replay.json",
                     help="Replay output file")
    r_p.add_argument("--no-browser", action="store_true",
                     help="Don't auto-open the viewer")
    r_p.add_argument("--seed", type=int, default=42, help="Track seed")
    r_p.add_argument("--league", default=None, help="League tier")
    r_p.add_argument("--live", action="store_true", default=False,
                     help="Enable live replay mode")
    r_p.add_argument("--verbose", "-v", action="store_true", default=False,
                     help="Show per-car league validation details")


_DISPATCH = {
    "run": cmd_run,
    "init": cmd_init,
    "validate": cmd_validate,
    "list-tracks": cmd_list_tracks,
    "tournament": cmd_tournament,
    "season": cmd_season,
    "submit": cmd_submit,
    "leaderboard": cmd_leaderboard,
    "qualify": cmd_qualify,
    "race": cmd_race,
    "trial": cmd_trial,
}


def main(argv: list[str] | None = None) -> None:
    """Parse args and dispatch to the appropriate command."""
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    handler = _DISPATCH[args.command]
    result = handler(args)
    if result is not None and result != 0:
        sys.exit(result)
