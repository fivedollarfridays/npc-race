"""Local leaderboard — persistent standings across races.

Players run races locally, submit results, and track standings.
"""

import json
import os

from datetime import datetime, timezone

from engine.championship import F1_POINTS as POINTS_TABLE


def new_leaderboard() -> dict:
    """Return a fresh empty leaderboard structure."""
    return {"version": "1.0", "last_updated": "", "entries": []}


def load_leaderboard(path: str = "leaderboard.json") -> dict:
    """Load leaderboard from JSON file. Creates empty if missing."""
    if not os.path.isfile(path):
        return new_leaderboard()
    with open(path) as f:
        return json.load(f)


def add_result(leaderboard: dict, results_summary: dict) -> dict:
    """Update standings with a race's results. Returns updated leaderboard."""
    entries = {e["name"]: e for e in leaderboard.get("entries", [])}

    for car in results_summary.get("cars", []):
        name = car["name"]
        pos = car.get("position", 99)
        points = POINTS_TABLE[pos - 1] if pos <= len(POINTS_TABLE) else 0

        if name not in entries:
            entries[name] = {
                "name": name,
                "league": car.get("league", "F3"),
                "races": 0,
                "wins": 0,
                "podiums": 0,
                "best_lap_s": None,
                "avg_position": 0,
                "total_points": 0,
                "reliability_score": 1.0,
            }

        e = entries[name]
        e["races"] += 1
        if pos == 1:
            e["wins"] += 1
        if pos <= 3:
            e["podiums"] += 1
        e["total_points"] += points

        best = car.get("best_lap_s")
        if best is not None and (e["best_lap_s"] is None or best < e["best_lap_s"]):
            e["best_lap_s"] = best

        # Running average position
        prev_avg = e["avg_position"]
        prev_races = e["races"] - 1
        e["avg_position"] = (prev_avg * prev_races + pos) / e["races"]

        e["reliability_score"] = car.get("reliability_score", e["reliability_score"])
        e["league"] = car.get("league", e["league"])

    leaderboard["entries"] = sorted(
        entries.values(), key=lambda x: -x["total_points"]
    )
    leaderboard["last_updated"] = datetime.now(timezone.utc).isoformat()
    return leaderboard


def save_leaderboard(leaderboard: dict, path: str = "leaderboard.json") -> None:
    """Persist leaderboard to JSON file."""
    with open(path, "w") as f:
        json.dump(leaderboard, f, indent=2)


def format_standings(leaderboard: dict) -> str:
    """Format leaderboard as a printable table."""
    entries = leaderboard.get("entries", [])
    if not entries:
        return "No races recorded yet."

    lines = [
        f"{'#':>3}  {'Name':<20}  {'Pts':>5}  {'Races':>5}  {'Wins':>4}  "
        f"{'Avg Pos':>7}  {'Best Lap':>8}  {'League':<6}",
        "\u2500" * 75,
    ]
    for i, e in enumerate(entries, 1):
        best = f"{e['best_lap_s']:.2f}s" if e["best_lap_s"] else "\u2014"
        lines.append(
            f"{i:>3}  {e['name']:<20}  {e['total_points']:>5}  {e['races']:>5}  "
            f"{e['wins']:>4}  {e['avg_position']:>7.1f}  {best:>8}  {e['league']:<6}"
        )
    return "\n".join(lines)
