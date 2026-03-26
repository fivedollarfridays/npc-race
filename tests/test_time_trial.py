"""Tests for engine.time_trial — ultra-fast single-car time trial."""

import os
import shutil

import pytest


TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "cars", "default_project"
)


@pytest.fixture
def car_dir(tmp_path):
    """Copy default_project to a temp directory."""
    dest = str(tmp_path / "test_car")
    shutil.copytree(TEMPLATE_DIR, dest)
    return dest


# -- Cycle 1: basic trial returns TrialResult with lap_time > 0 --

@pytest.mark.smoke
def test_trial_returns_result(car_dir):
    """Time trial returns TrialResult with positive lap_time."""
    from engine.time_trial import run_time_trial

    result = run_time_trial(car_dir, "monza")
    assert result.lap_time > 0
    assert result.car_name == "DefaultProject"
    assert result.track_name == "monza"


def test_trial_has_sector_times(car_dir):
    """TrialResult includes sector times list."""
    from engine.time_trial import run_time_trial

    result = run_time_trial(car_dir, "monza")
    assert isinstance(result.sector_times, list)


# -- Cycle 2: efficiency extraction --

def test_trial_has_efficiency(car_dir):
    """TrialResult includes per-part efficiency with valid values."""
    from engine.time_trial import run_time_trial

    result = run_time_trial(car_dir, "monza")
    assert isinstance(result.efficiency, dict)
    assert len(result.efficiency) > 0
    for part, eff in result.efficiency.items():
        assert isinstance(part, str)
        assert 0.0 <= eff <= 1.5, f"{part} efficiency {eff} out of range"


# -- Cycle 3: find_player_car helper --

def test_find_player_car_returns_none_empty(tmp_path):
    """find_player_car returns None when no player cars exist."""
    from engine.time_trial import find_player_car

    assert find_player_car(str(tmp_path)) is None


def test_find_player_car_skips_default(tmp_path):
    """find_player_car skips default_project."""
    from engine.time_trial import find_player_car

    dp = tmp_path / "default_project"
    dp.mkdir()
    (dp / "car.py").write_text("CAR_NAME = 'Default'")
    assert find_player_car(str(tmp_path)) is None


def test_find_player_car_finds_player(tmp_path):
    """find_player_car returns player car directory."""
    from engine.time_trial import find_player_car

    pc = tmp_path / "my_car"
    pc.mkdir()
    (pc / "car.py").write_text("CAR_NAME = 'MyCar'")
    result = find_player_car(str(tmp_path))
    assert result == str(pc)


def test_find_player_car_skips_underscore(tmp_path):
    """find_player_car skips directories starting with underscore."""
    from engine.time_trial import find_player_car

    hidden = tmp_path / "_hidden"
    hidden.mkdir()
    (hidden / "car.py").write_text("CAR_NAME = 'Hidden'")
    assert find_player_car(str(tmp_path)) is None


# -- Cycle 4: performance --

def test_trial_under_5_seconds(car_dir):
    """Time trial completes in < 5 seconds wall time."""
    import time

    from engine.time_trial import run_time_trial

    start = time.monotonic()
    result = run_time_trial(car_dir, "monza")
    elapsed = time.monotonic() - start
    assert elapsed < 5.0, f"Trial took {elapsed:.1f}s (limit 5s)"
    assert result.lap_time > 0
