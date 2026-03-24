"""Tests for qualifying simulation (T34.7).

Validates single flying lap qualifying: out-lap + flying lap,
sorted results, grid positions, and export.
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.track_gen import generate_track, interpolate_track

import pytest
pytestmark = pytest.mark.smoke


def _default_strategy(s):
    return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}


def _make_car(name, power=20, strategy=None):
    strat = strategy or _default_strategy
    return {
        "CAR_NAME": name, "CAR_COLOR": "#FF0000",
        "POWER": power, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
        "strategy": strat,
    }


def _make_track():
    control = generate_track(seed=42)
    return interpolate_track(control, resolution=500)


# ── Cycle 1: Basic qualifying results ────────────────────────────────────


class TestQualifyingBasic:
    """run_qualifying returns sorted results with grid positions."""

    def test_returns_list_of_results(self):
        from engine.qualifying import run_qualifying
        cars = [_make_car("A"), _make_car("B")]
        results = run_qualifying(cars, _make_track())
        assert isinstance(results, list)
        assert len(results) == 2

    def test_results_have_required_fields(self):
        from engine.qualifying import run_qualifying
        cars = [_make_car("A"), _make_car("B")]
        results = run_qualifying(cars, _make_track())
        for r in results:
            assert "name" in r
            assert "qualifying_time" in r
            assert "grid_position" in r

    def test_grid_positions_are_sequential(self):
        from engine.qualifying import run_qualifying
        cars = [_make_car("A"), _make_car("B"), _make_car("C")]
        results = run_qualifying(cars, _make_track())
        positions = [r["grid_position"] for r in results]
        assert positions == [1, 2, 3]

    def test_results_sorted_by_qualifying_time(self):
        from engine.qualifying import run_qualifying
        cars = [_make_car("A"), _make_car("B"), _make_car("C")]
        results = run_qualifying(cars, _make_track())
        times = [r["qualifying_time"] for r in results]
        assert times == sorted(times)


# ── Cycle 2: Performance ordering and lap count ──────────────────────────


class TestQualifyingPerformance:
    """Faster cars qualify ahead; each car gets 2 laps."""

    def test_higher_power_qualifies_ahead(self):
        from engine.qualifying import run_qualifying
        cars = [_make_car("Slow", power=15), _make_car("Fast", power=30)]
        results = run_qualifying(cars, _make_track())
        names = [r["name"] for r in results]
        assert names[0] == "Fast", f"Expected Fast P1, got {names}"

    def test_qualifying_times_are_positive(self):
        from engine.qualifying import run_qualifying
        cars = [_make_car("A"), _make_car("B")]
        results = run_qualifying(cars, _make_track())
        for r in results:
            assert r["qualifying_time"] > 0
            assert r["qualifying_time"] < 999.0

    def test_each_car_runs_two_laps(self):
        """Each car should complete 2 laps (out-lap + flying lap)."""
        from engine.simulation import RaceSim
        car = _make_car("Solo")
        track = _make_track()
        sim = RaceSim(
            cars=[car], track_points=track, laps=2, seed=42,
            fast_mode=True,
        )
        sim.run()
        timing = sim.timings["Solo"]
        assert len(timing.lap_times) >= 2, (
            f"Expected 2+ lap times, got {len(timing.lap_times)}"
        )


# ── Cycle 3: Grid export ─────────────────────────────────────────────────


class TestExportGrid:
    """export_grid writes valid JSON with all qualifying data."""

    def test_export_writes_valid_json(self):
        from engine.qualifying import export_grid
        results = [
            {"name": "A", "qualifying_time": 80.5, "grid_position": 1},
            {"name": "B", "qualifying_time": 81.2, "grid_position": 2},
        ]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            export_grid(results, path)
            with open(path) as f:
                loaded = json.load(f)
            assert len(loaded) == 2
            assert loaded[0]["name"] == "A"
            assert loaded[1]["grid_position"] == 2
        finally:
            os.unlink(path)

    def test_export_preserves_qualifying_times(self):
        from engine.qualifying import export_grid
        results = [
            {"name": "X", "qualifying_time": 75.123, "grid_position": 1},
        ]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            export_grid(results, path)
            with open(path) as f:
                loaded = json.load(f)
            assert loaded[0]["qualifying_time"] == 75.123
        finally:
            os.unlink(path)


# ── Cycle 4: Solo isolation ──────────────────────────────────────────────


class TestQualifyingSolo:
    """Each car runs alone — no traffic interference."""

    def test_single_car_qualifying(self):
        from engine.qualifying import run_qualifying
        cars = [_make_car("Solo")]
        results = run_qualifying(cars, _make_track())
        assert len(results) == 1
        assert results[0]["grid_position"] == 1
        assert results[0]["qualifying_time"] > 0

    def test_identical_cars_get_same_time(self):
        """Two identical cars with same seed should get identical times."""
        from engine.qualifying import run_qualifying
        cars = [_make_car("A"), _make_car("B")]
        results = run_qualifying(cars, _make_track(), seed=42)
        # Same car spec, same seed, solo runs => same qualifying time
        assert results[0]["qualifying_time"] == results[1]["qualifying_time"]
