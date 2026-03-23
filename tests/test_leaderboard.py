"""Tests for engine.leaderboard — persistent local standings."""

import pytest

from engine.leaderboard import (
    add_result,
    format_standings,
    load_leaderboard,
    save_leaderboard,
)


def _make_results(*cars_data):
    """Helper: build a minimal results_summary dict."""
    cars = []
    for name, position, best_lap, league in cars_data:
        cars.append({
            "name": name,
            "position": position,
            "best_lap_s": best_lap,
            "league": league,
            "reliability_score": 0.95,
        })
    return {"cars": cars}


# --- load ---


def test_load_creates_empty(tmp_path):
    """Load from nonexistent file returns empty leaderboard."""
    lb = load_leaderboard(str(tmp_path / "nope.json"))
    assert lb["version"] == "1.0"
    assert lb["entries"] == []
    assert lb["last_updated"] == ""


# --- add_result ---


def test_add_result_creates_entry():
    """Adding results creates entry with correct name and points."""
    lb = load_leaderboard("/nonexistent")
    results = _make_results(("Alice", 1, 80.5, "F2"))
    lb = add_result(lb, results)

    assert len(lb["entries"]) == 1
    assert lb["entries"][0]["name"] == "Alice"
    assert lb["entries"][0]["total_points"] == 25


def test_points_calculation():
    """P1 gets 25, P3 gets 15, P11 gets 0."""
    lb = load_leaderboard("/nonexistent")
    results = _make_results(
        ("A", 1, 80.0, "F3"),
        ("B", 3, 81.0, "F3"),
        ("C", 11, 85.0, "F3"),
    )
    lb = add_result(lb, results)
    entries = {e["name"]: e for e in lb["entries"]}

    assert entries["A"]["total_points"] == 25
    assert entries["B"]["total_points"] == 15
    assert entries["C"]["total_points"] == 0


def test_accumulates_across_races():
    """Adding two results accumulates races and points."""
    lb = load_leaderboard("/nonexistent")
    lb = add_result(lb, _make_results(("X", 1, 80.0, "F3")))
    lb = add_result(lb, _make_results(("X", 2, 79.0, "F3")))

    e = lb["entries"][0]
    assert e["races"] == 2
    assert e["total_points"] == 25 + 18  # P1 + P2


def test_wins_and_podiums():
    """P1 counts as win+podium, P3 as podium only."""
    lb = load_leaderboard("/nonexistent")
    lb = add_result(lb, _make_results(("W", 1, 80.0, "F3")))
    lb = add_result(lb, _make_results(("W", 3, 81.0, "F3")))

    e = lb["entries"][0]
    assert e["wins"] == 1
    assert e["podiums"] == 2


def test_best_lap_tracked():
    """Keeps the fastest lap across races."""
    lb = load_leaderboard("/nonexistent")
    lb = add_result(lb, _make_results(("L", 1, 82.0, "F3")))
    lb = add_result(lb, _make_results(("L", 2, 79.5, "F3")))
    lb = add_result(lb, _make_results(("L", 3, 81.0, "F3")))

    assert lb["entries"][0]["best_lap_s"] == 79.5


def test_avg_position():
    """Running average position updates correctly."""
    lb = load_leaderboard("/nonexistent")
    lb = add_result(lb, _make_results(("P", 2, 80.0, "F3")))
    lb = add_result(lb, _make_results(("P", 4, 80.0, "F3")))

    assert lb["entries"][0]["avg_position"] == pytest.approx(3.0)


def test_save_and_load_roundtrip(tmp_path):
    """Save then load returns same data."""
    lb = load_leaderboard("/nonexistent")
    lb = add_result(lb, _make_results(("RT", 1, 78.0, "F2")))

    path = str(tmp_path / "lb.json")
    save_leaderboard(lb, path)
    loaded = load_leaderboard(path)

    assert loaded["entries"][0]["name"] == "RT"
    assert loaded["entries"][0]["total_points"] == 25
    assert loaded["entries"][0]["best_lap_s"] == 78.0
    assert loaded["version"] == "1.0"


# --- format_standings ---


def test_format_standings_empty():
    """Empty leaderboard formats as message."""
    lb = {"entries": []}
    assert format_standings(lb) == "No races recorded yet."


def test_format_standings_table():
    """Non-empty leaderboard formats as table with headers."""
    lb = load_leaderboard("/nonexistent")
    lb = add_result(lb, _make_results(("Alice", 1, 80.5, "F2")))
    text = format_standings(lb)

    assert "Name" in text
    assert "Pts" in text
    assert "Alice" in text
    assert "25" in text


def test_entries_sorted_by_points():
    """Entries are sorted by total_points descending."""
    lb = load_leaderboard("/nonexistent")
    results = _make_results(
        ("Low", 5, 85.0, "F3"),
        ("High", 1, 80.0, "F3"),
        ("Mid", 3, 82.0, "F3"),
    )
    lb = add_result(lb, results)

    names = [e["name"] for e in lb["entries"]]
    assert names == ["High", "Mid", "Low"]
