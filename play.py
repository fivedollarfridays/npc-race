#!/usr/bin/env python3
"""
NPC Race — play.py
==================
Drop your car file in cars/ and run:

    python play.py

Options:
    python play.py --laps 5
    python play.py --seed 123
    python play.py --car-dir my_cars/

The replay opens in your browser automatically.
"""

import argparse
import os
import webbrowser
from engine import run_race


def main():
    parser = argparse.ArgumentParser(description="NPC Race — you build the car, we run the race")
    parser.add_argument("--car-dir", default="cars", help="Directory containing car .py files")
    parser.add_argument("--laps", type=int, default=3, help="Number of laps (default: 3)")
    parser.add_argument("--seed", type=int, default=42, help="Track generation seed (default: 42)")
    parser.add_argument("--output", default="replay.json", help="Replay output file")
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open viewer")
    args = parser.parse_args()

    if not os.path.isdir(args.car_dir):
        print(f"Car directory not found: {args.car_dir}")
        return

    results = run_race(
        car_dir=args.car_dir,
        laps=args.laps,
        track_seed=args.seed,
        output=args.output,
    )

    if not args.no_browser:
        viewer = os.path.join(os.path.dirname(__file__), "viewer.html")
        if os.path.exists(viewer):
            webbrowser.open(f"file://{os.path.abspath(viewer)}")
            print(f"\nOpened viewer in browser")
        else:
            print(f"\nviewer.html not found — open it manually")


if __name__ == "__main__":
    main()
