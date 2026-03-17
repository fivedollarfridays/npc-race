"""Balance report v2 — runs all 5 cars on 6 tracks and prints results.

Usage:
    python scripts/balance_report_v2.py
"""

import json
import os
import sys
import tempfile
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.race_runner import run_race  # noqa: E402

CAR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cars")
TRACKS = ["monaco", "monza", "silverstone", "singapore", "spa", "interlagos"]
LAPS = 2


def run_track(track_name: str) -> dict:
    """Run a race and return replay dict."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out = f.name
    try:
        run_race(car_dir=CAR_DIR, track_name=track_name, laps=LAPS, output=out)
        with open(out) as f:
            return json.load(f)
    finally:
        os.unlink(out)


def count_pit_stops(replay: dict) -> dict[str, int]:
    """Count pit ticks per car from replay frames."""
    counts: dict[str, int] = {}
    for frame in replay["frames"]:
        for car in frame:
            name = car["name"]
            if car.get("pit_status") != "racing":
                counts[name] = counts.get(name, 0) + 1
    # Convert ticks to stop count (780 ticks per stop)
    return {n: max(1, t // 780) if t > 0 else 0 for n, t in counts.items()}


def main() -> None:
    """Run balance report across all tracks."""
    print("=" * 70)
    print("NPC RACE — Balance Report v2")
    print("=" * 70)

    all_winners: list[str] = []
    all_lap_times: dict[str, list[float]] = {}

    for track in TRACKS:
        replay = run_track(track)
        tps = replay.get("ticks_per_sec", 30)
        results = replay["results"]
        pit_stops = count_pit_stops(replay)

        winner = next(r for r in results if r["position"] == 1)
        all_winners.append(winner["name"])

        print(f"\n--- {track.upper()} ({LAPS} laps) ---")
        for r in results:
            tick = r.get("finish_tick", 0)
            lap_time = (tick / tps) / LAPS if tick else 0
            name = r["name"]
            stops = pit_stops.get(name, 0)
            print(
                f"  P{r['position']}  {name:15s}  "
                f"lap~{lap_time:5.1f}s  pits={stops}"
            )
            all_lap_times.setdefault(name, []).append(lap_time)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    win_counts = Counter(all_winners)
    print("\nWins per car:")
    for car in sorted(win_counts, key=win_counts.get, reverse=True):
        pct = win_counts[car] / len(TRACKS) * 100
        print(f"  {car:15s}: {win_counts[car]} wins ({pct:.0f}%)")

    print("\nAverage lap times:")
    for car in sorted(all_lap_times):
        times = all_lap_times[car]
        avg = sum(times) / len(times)
        print(f"  {car:15s}: {avg:5.1f}s avg")


if __name__ == "__main__":
    main()
