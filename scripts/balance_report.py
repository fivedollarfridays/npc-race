#!/usr/bin/env python3
"""Balance report for NPC Race seed cars.

Runs all 5 seed cars on representative tracks and prints a win matrix
showing which cars perform best on which track types.

Usage:
    python scripts/balance_report.py
"""

import json
import os
import sys
import tempfile
from collections import Counter

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine.race_runner import run_race  # noqa: E402

CAR_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cars")

TRACKS_BY_TYPE: dict[str, list[str]] = {
    "power": ["monza", "spa", "baku", "jeddah"],
    "technical": ["monaco", "singapore", "zandvoort"],
    "balanced": ["silverstone", "suzuka", "austin", "barcelona", "bahrain"],
}

ALL_TRACKS = [t for group in TRACKS_BY_TYPE.values() for t in group]
LAPS = 2


def run_single_race(track_name: str) -> list[dict]:
    """Run a race and return sorted results."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out = f.name
    try:
        run_race(
            car_dir=CAR_DIR, track_name=track_name,
            laps=LAPS, output=out,
        )
        with open(out) as f:
            replay = json.load(f)
        return replay["results"]
    finally:
        os.unlink(out)


def build_results_table() -> dict[str, list[dict]]:
    """Run all races and return {track: results}."""
    table = {}
    for track in ALL_TRACKS:
        table[track] = run_single_race(track)
    return table


def print_position_matrix(table: dict[str, list[dict]]) -> None:
    """Print a car-vs-track position matrix."""
    car_names = sorted(
        {r["name"] for results in table.values() for r in results}
    )
    col_w = 14
    header = f"{'Track':<14s}" + "".join(f"{c:<{col_w}s}" for c in car_names)
    print(header)
    print("-" * len(header))

    for track in ALL_TRACKS:
        results = table[track]
        pos_by_name = {r["name"]: r["position"] for r in results}
        row = f"{track:<14s}"
        for name in car_names:
            pos = pos_by_name.get(name, "-")
            row += f"P{pos:<{col_w - 1}}"
        print(row)


def print_win_summary(table: dict[str, list[dict]]) -> None:
    """Print win counts by car and track type."""
    print("\n--- Win Summary ---\n")

    wins_total: Counter[str] = Counter()
    wins_by_type: dict[str, Counter[str]] = {
        t: Counter() for t in TRACKS_BY_TYPE
    }

    for track_type, tracks in TRACKS_BY_TYPE.items():
        for track in tracks:
            results = table[track]
            winner = next(r["name"] for r in results if r["position"] == 1)
            wins_total[winner] += 1
            wins_by_type[track_type][winner] += 1

    print(f"{'Car':<16s}{'Total':<8s}", end="")
    for t in TRACKS_BY_TYPE:
        print(f"{t:<12s}", end="")
    print()
    print("-" * 48)

    for car in sorted(wins_total, key=wins_total.get, reverse=True):
        print(f"{car:<16s}{wins_total[car]:<8d}", end="")
        for t in TRACKS_BY_TYPE:
            print(f"{wins_by_type[t].get(car, 0):<12d}", end="")
        print()

    total_tracks = len(ALL_TRACKS)
    dominant = wins_total.most_common(1)[0]
    pct = dominant[1] / total_tracks * 100
    print(f"\nMost wins: {dominant[0]} ({dominant[1]}/{total_tracks} = {pct:.0f}%)")
    if pct > 60:
        print("WARNING: Dominance threshold exceeded (>60%)")
    else:
        print("Balance OK: no car exceeds 60% win rate")


def main() -> None:
    """Run the balance report."""
    print("NPC Race Balance Report")
    print("=" * 60)
    print(f"Tracks: {len(ALL_TRACKS)}  |  Laps per race: {LAPS}")
    print("=" * 60)
    print()

    table = build_results_table()

    print("\n--- Position Matrix ---\n")
    print_position_matrix(table)
    print_win_summary(table)


if __name__ == "__main__":
    main()
