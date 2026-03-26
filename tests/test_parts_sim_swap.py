"""Tests for T42.2 — Verify race_runner uses PartsRaceSim, not RaceSim."""

import inspect
import json
import os
from unittest.mock import patch

import pytest


def _make_minimal_cars(n=2):
    """Create minimal car dicts that work with PartsRaceSim."""
    cars = []
    for i in range(n):
        cars.append({
            "CAR_NAME": f"TestCar{i}",
            "CAR_COLOR": f"#FF000{i}",
        })
    return cars


# --- Cycle 1: import verification ---


def test_parts_sim_import():
    """race_runner imports PartsRaceSim, not RaceSim."""
    import engine.race_runner as rr
    source = inspect.getsource(rr)
    assert "PartsRaceSim" in source, "race_runner should import PartsRaceSim"
    assert "from .parts_simulation" in source or "from engine.parts_simulation" in source


def test_no_old_racesim_import():
    """race_runner no longer imports from .simulation."""
    import engine.race_runner as rr
    source = inspect.getsource(rr)
    assert "from .simulation import RaceSim" not in source, (
        "Old RaceSim import should be removed"
    )


# --- Cycle 2: run_race integration with PartsRaceSim (2 cars, fast) ---


@pytest.mark.smoke
def test_run_race_completes_with_parts_sim(tmp_path):
    """run_race() completes using PartsRaceSim with minimal cars."""
    from engine.race_runner import run_race
    output = str(tmp_path / "replay.json")
    with patch("engine.race_runner.load_all_cars", return_value=_make_minimal_cars(2)):
        results = run_race(
            car_dir="cars", track_name="monza", laps=1,
            output=output, fast_mode=True, quiet=True,
        )
    assert results is not None
    assert isinstance(results, list)
    assert len(results) == 2


@pytest.mark.smoke
def test_run_race_results_have_required_fields(tmp_path):
    """Results from PartsRaceSim have all required fields."""
    from engine.race_runner import run_race
    output = str(tmp_path / "replay.json")
    with patch("engine.race_runner.load_all_cars", return_value=_make_minimal_cars(2)):
        results = run_race(
            car_dir="cars", track_name="monza", laps=1,
            output=output, fast_mode=True, quiet=True,
        )
    required_fields = {"position", "name", "finished"}
    for r in results:
        for field in required_fields:
            assert field in r, f"Missing field '{field}' in result: {r}"


@pytest.mark.smoke
def test_run_race_all_cars_finish(tmp_path):
    """All cars should finish a 1-lap race."""
    from engine.race_runner import run_race
    output = str(tmp_path / "replay.json")
    with patch("engine.race_runner.load_all_cars", return_value=_make_minimal_cars(3)):
        results = run_race(
            car_dir="cars", track_name="monza", laps=1,
            output=output, fast_mode=True, quiet=True,
        )
    finished = [r for r in results if r.get("finished")]
    assert len(finished) == len(results), (
        f"Not all cars finished: {len(finished)}/{len(results)}"
    )


@pytest.mark.smoke
def test_run_race_writes_results_json(tmp_path):
    """Fast mode produces a results.json file."""
    from engine.race_runner import run_race
    output = str(tmp_path / "replay.json")
    with patch("engine.race_runner.load_all_cars", return_value=_make_minimal_cars(2)):
        run_race(
            car_dir="cars", track_name="monza", laps=1,
            output=output, fast_mode=True, quiet=True,
        )
    results_path = str(tmp_path / "results.json")
    assert os.path.isfile(results_path), "results.json should be written"
    with open(results_path) as f:
        data = json.load(f)
    assert "standings" in data or "results" in data or isinstance(data, dict)
