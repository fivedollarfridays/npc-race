"""T35.7 — 20-car grid integration tests.

Verify all 20 cars load, have unique names, valid stats,
and can race together without errors.
"""

import pathlib
import time

import pytest

from engine.car_loader import load_all_cars
from engine.simulation import RaceSim
from engine.track_gen import interpolate_track
from tracks import get_track

pytestmark = pytest.mark.integration

CARS_DIR = str(pathlib.Path(__file__).resolve().parent.parent / "cars")


@pytest.fixture(scope="module")
def all_cars():
    """Load all cars once for the module."""
    return load_all_cars(CARS_DIR)


@pytest.fixture(scope="module")
def monza_track():
    """Load Monza track points once for the module."""
    track_data = get_track("monza")
    points = interpolate_track(track_data["control_points"], resolution=500)
    return points, track_data


# --- Cycle 1: Loading and metadata ---


def test_load_all_cars_returns_20(all_cars):
    """load_all_cars('cars') returns exactly 20 cars."""
    assert len(all_cars) == 20


def test_all_car_names_unique(all_cars):
    """No duplicate CAR_NAME values across the grid."""
    names = [c["CAR_NAME"] for c in all_cars]
    assert len(names) == len(set(names)), f"Duplicates: {[n for n in names if names.count(n) > 1]}"


def test_all_stats_sum_to_100(all_cars):
    """Every car's 5 stats sum to exactly 100."""
    stat_fields = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]
    for car in all_cars:
        total = sum(car[s] for s in stat_fields)
        assert total == 100, f"{car['CAR_NAME']} stats sum to {total}, not 100"


# --- Cycle 2: Race simulation ---


@pytest.fixture(scope="module")
def race_results(all_cars, monza_track):
    """Run a 3-lap Monza race with all 20 cars, return (results, elapsed_s)."""
    points, track_data = monza_track
    sim = RaceSim(
        cars=all_cars,
        track_points=points,
        laps=3,
        seed=42,
        track_name="monza",
        real_length_m=track_data.get("real_length_m"),
        drs_zones=track_data.get("drs_zones", []),
    )
    start = time.monotonic()
    results = sim.run()
    elapsed = time.monotonic() - start
    return results, elapsed


def test_3_lap_race_completes(race_results):
    """3-lap Monza with 20 cars finishes without crash."""
    results, _ = race_results
    assert results is not None
    assert len(results) == 20


def test_all_positions_assigned(race_results):
    """Results have positions 1 through 20."""
    results, _ = race_results
    positions = sorted(r["position"] for r in results)
    assert positions == list(range(1, 21))


def test_performance_under_30s(race_results):
    """3-lap/20-car race completes under 30 seconds wall time."""
    _, elapsed = race_results
    assert elapsed < 30.0, f"Race took {elapsed:.1f}s, limit is 30s"
