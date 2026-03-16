"""Top-level CLI dispatcher for NPC Race.

Entry point: ``npcrace`` via pyproject.toml console_scripts.
Uses argparse with subcommands.
"""

import argparse
import sys

from .commands import cmd_init, cmd_list_tracks, cmd_run, cmd_validate, cmd_wizard


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="npcrace",
        description="NPC Race — you build the car, we run the race",
    )
    subs = parser.add_subparsers(dest="command")
    subs.required = True

    # run
    run_p = subs.add_parser("run", help="Run a race")
    run_p.add_argument("--car-dir", default="cars",
                       help="Directory containing car .py files")
    run_p.add_argument("--laps", type=int, default=None,
                       help="Number of laps")
    run_p.add_argument("--seed", type=int, default=42,
                       help="Track generation seed")
    run_p.add_argument("--output", default="replay.json",
                       help="Replay output file")
    run_p.add_argument("--track", default=None,
                       help="Named track or 'random'")

    # init
    init_p = subs.add_parser("init", help="Create cars/ directory with template")
    init_p.add_argument("--dir", default="cars",
                        help="Target directory (default: cars)")

    # validate
    val_p = subs.add_parser("validate", help="Validate car file(s)")
    val_p.add_argument("car_files", nargs="+", help="Car .py files to validate")

    # list-tracks
    subs.add_parser("list-tracks", help="Print available tracks")

    # wizard (stub)
    subs.add_parser("wizard", help="Interactive car wizard (coming soon)")

    return parser


_DISPATCH = {
    "run": cmd_run,
    "init": cmd_init,
    "validate": cmd_validate,
    "list-tracks": cmd_list_tracks,
    "wizard": cmd_wizard,
}


def main(argv: list[str] | None = None) -> None:
    """Parse args and dispatch to the appropriate command."""
    parser = _build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    handler = _DISPATCH[args.command]
    handler(args)
