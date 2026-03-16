#!/usr/bin/env python3
"""
NPC Race -- play.py
==================
Drop your car file in cars/ and run:

    python play.py

Options:
    python play.py --laps 5
    python play.py --seed 123
    python play.py --car-dir my_cars/
    python play.py --track monza
    python play.py --track random
    python play.py --list-tracks
"""

import argparse
import os
import sys
import webbrowser

from engine import run_race
from tracks import list_tracks, random_track, TRACKS


def _print_tracks() -> None:
    """Print all available tracks with name, country, and character."""
    print(f"\n{'Name':<16} {'Country':<20} {'Character':<12}")
    print(f"{'─' * 16} {'─' * 20} {'─' * 12}")
    for key in list_tracks():
        t = TRACKS[key]
        print(f"{key:<16} {t['country']:<20} {t['character']:<12}")
    print(f"\n{len(TRACKS)} tracks available")


def _resolve_track(args) -> str | None:
    """Resolve --track flag. Returns track key or None for procedural."""
    if args.track is None:
        return None

    if args.track == "random":
        chosen = random_track()
        print(f"Random track selected: {chosen}")
        return chosen

    name = args.track.lower()
    if name not in TRACKS:
        print(f"Unknown track: '{args.track}'")
        print(f"Available tracks: {', '.join(list_tracks())}")
        sys.exit(1)

    return name


def main():
    parser = argparse.ArgumentParser(
        description="NPC Race -- you build the car, we run the race",
    )
    parser.add_argument("--car-dir", default="cars",
                        help="Directory containing car .py files")
    parser.add_argument("--laps", type=int, default=None,
                        help="Number of laps (default: track default or 3)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Track generation seed (default: 42)")
    parser.add_argument("--output", default="replay.json",
                        help="Replay output file")
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't auto-open viewer")
    parser.add_argument("--track", default=None,
                        help="Named track (e.g. monza) or 'random'")
    parser.add_argument("--list-tracks", action="store_true",
                        help="Print available tracks and exit")
    args = parser.parse_args()

    if args.list_tracks:
        _print_tracks()
        return

    if not os.path.isdir(args.car_dir):
        print(f"Car directory not found: {args.car_dir}")
        return

    track_name = _resolve_track(args)

    if track_name is not None and args.seed != 42:
        print("Note: --seed is ignored when --track is specified")

    run_race(
        car_dir=args.car_dir,
        laps=args.laps,
        track_seed=args.seed,
        output=args.output,
        track_name=track_name,
    )

    if not args.no_browser:
        viewer = os.path.join(os.path.dirname(__file__), "viewer.html")
        if os.path.exists(viewer):
            webbrowser.open(f"file://{os.path.abspath(viewer)}")
            print("\nOpened viewer in browser")
        else:
            print("\nviewer.html not found -- open it manually")


if __name__ == "__main__":
    main()
