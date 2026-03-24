"""Tests for car project detection in load_all_cars (T29.3)."""

import os
import textwrap

from engine.car_loader import load_all_cars


VALID_CAR_PY = textwrap.dedent("""\
    CAR_NAME = "SingleCar"
    CAR_COLOR = "#FF0000"
    POWER = 20
    GRIP = 20
    WEIGHT = 20
    AERO = 20
    BRAKES = 20

    def strategy(state):
        return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
""")

PROJECT_CAR_PY = textwrap.dedent("""\
    CAR_NAME = "ProjectCar"
    CAR_COLOR = "#00FF00"
    POWER = 20
    GRIP = 20
    WEIGHT = 20
    AERO = 20
    BRAKES = 20
""")


def _setup_mixed_dir(tmp_path):
    """Create a dir with one single-file car and one project subdirectory."""
    # Single-file car
    (tmp_path / "solo.py").write_text(VALID_CAR_PY)

    # Project subdirectory
    proj = tmp_path / "my_project"
    proj.mkdir()
    (proj / "car.py").write_text(PROJECT_CAR_PY)
    return tmp_path


# -- Cycle 1: load_all_cars detects both types --

def test_load_all_cars_includes_projects(tmp_path):
    """load_all_cars should load both single-file and project cars."""
    _setup_mixed_dir(tmp_path)
    cars = load_all_cars(str(tmp_path))
    names = [c["CAR_NAME"] for c in cars]
    assert "SingleCar" in names
    assert "ProjectCar" in names
    assert len(cars) == 2


def test_project_without_car_py_skipped(tmp_path):
    """Subdirectories without car.py should be silently skipped."""
    (tmp_path / "solo.py").write_text(VALID_CAR_PY)
    (tmp_path / "not_a_project").mkdir()
    cars = load_all_cars(str(tmp_path))
    assert len(cars) == 1


# -- Cycle 2: _source populated for single-file cars --

def test_source_populated_for_single_file(tmp_path):
    """Single-file cars should have _source set to file contents."""
    (tmp_path / "solo.py").write_text(VALID_CAR_PY)
    cars = load_all_cars(str(tmp_path))
    assert len(cars) == 1
    assert cars[0]["_source"] == VALID_CAR_PY


# -- Cycle 3: _source populated for project cars --

def test_source_populated_for_project(tmp_path):
    """Project cars should have _source set (from car_project_loader)."""
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "car.py").write_text(PROJECT_CAR_PY)
    cars = load_all_cars(str(tmp_path))
    assert len(cars) == 1
    assert "_source" in cars[0]
    assert "CAR_NAME" in cars[0]["_source"]


# -- Cycle 4: malicious project skipped --

def test_malicious_project_skipped(tmp_path, capsys):
    """Project that fails security scan should be skipped with warning."""
    # Good single-file car
    (tmp_path / "good.py").write_text(VALID_CAR_PY)

    # Bad project with disallowed import
    bad_proj = tmp_path / "bad_project"
    bad_proj.mkdir()
    bad_car = textwrap.dedent("""\
        import subprocess
        CAR_NAME = "BadCar"
        CAR_COLOR = "#000000"
        POWER = 20
        GRIP = 20
        WEIGHT = 20
        AERO = 20
        BRAKES = 20
    """)
    (bad_proj / "car.py").write_text(bad_car)

    cars = load_all_cars(str(tmp_path))
    names = [c["CAR_NAME"] for c in cars]
    assert "BadCar" not in names
    # Only the good single-file car should load, not the bad project
    assert len(cars) == 1
    assert cars[0]["CAR_NAME"] == "SingleCar"

    captured = capsys.readouterr()
    assert "FAILED" in captured.out or "bad_project" in captured.out


# -- Existing cars still load --

def test_existing_cars_still_load():
    """The 19 rival cars (5 seed + 14 generated) should load."""
    cars_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cars"
    )
    cars = load_all_cars(cars_dir)
    assert len(cars) >= 19
    names = [c["CAR_NAME"] for c in cars]
    assert "GlassCanon" in names
