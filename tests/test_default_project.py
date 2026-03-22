"""Tests for cars/default_project/ template."""

import importlib.util
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parent.parent / "cars" / "default_project"


def _load_module(name: str):
    """Import a .py file from the default_project directory."""
    path = PROJECT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# -- Cycle 1: Directory structure --

@pytest.mark.parametrize("filename", [
    "car.py", "engine_map.py", "gearbox.py", "strategy.py", "README.md",
])
def test_template_file_exists(filename):
    """All template files must exist."""
    assert (PROJECT_DIR / filename).is_file(), f"Missing {filename}"


def test_py_files_under_30_lines():
    """Each .py file should be under 30 lines."""
    for py_file in PROJECT_DIR.glob("*.py"):
        lines = py_file.read_text().strip().splitlines()
        assert len(lines) <= 30, f"{py_file.name} has {len(lines)} lines (max 30)"


# -- Cycle 2: car.py metadata --

def test_car_py_metadata():
    """car.py must define CAR_NAME, CAR_COLOR, and five stats."""
    car = _load_module("car")
    assert car.CAR_NAME == "DefaultProject"
    assert car.CAR_COLOR == "#4488cc"
    assert car.POWER == 20
    assert car.GRIP == 20
    assert car.WEIGHT == 20
    assert car.AERO == 20
    assert car.BRAKES == 20


# -- Cycle 3: engine_map.py --

def test_engine_map_signature_and_default():
    """engine_map must accept (rpm, throttle_demand, engine_temp) and return (1.0, 1.0)."""
    mod = _load_module("engine_map")
    result = mod.engine_map(10000, 0.8, 90.0)
    assert result == (1.0, 1.0)


# -- Cycle 4: gearbox.py --

def test_gearbox_upshift():
    """gearbox must upshift above 12800 rpm."""
    mod = _load_module("gearbox")
    assert mod.gearbox(13000, 200.0, 3, 1.0) == 4


def test_gearbox_downshift():
    """gearbox must downshift below 6200 rpm."""
    mod = _load_module("gearbox")
    assert mod.gearbox(6000, 80.0, 3, 0.5) == 2


def test_gearbox_hold():
    """gearbox must hold gear in normal rpm range."""
    mod = _load_module("gearbox")
    assert mod.gearbox(9000, 150.0, 4, 1.0) == 4


# -- Cycle 5: strategy.py --

def test_strategy_default_no_pit():
    """strategy returns engine_mode standard when tire_wear is low."""
    mod = _load_module("strategy")
    result = mod.strategy({"tire_wear": 0.3, "pit_stops": 0})
    assert result == {"engine_mode": "standard"}


def test_strategy_pit_request():
    """strategy requests pit when tire_wear > 0.7 and no pit stops yet."""
    mod = _load_module("strategy")
    result = mod.strategy({"tire_wear": 0.8, "pit_stops": 0})
    assert result == {"pit_request": True, "tire_compound_request": "hard"}


# -- Cycle 6: README.md --

def test_readme_under_50_lines():
    """README.md should be under 50 lines."""
    readme = PROJECT_DIR / "README.md"
    lines = readme.read_text().strip().splitlines()
    assert len(lines) <= 50, f"README has {len(lines)} lines (max 50)"


def test_only_three_part_files():
    """Template should have exactly 3 part files (engine_map, gearbox, strategy)."""
    from engine.parts_api import CAR_PARTS
    part_files = [f for f in PROJECT_DIR.glob("*.py")
                  if f.stem in CAR_PARTS]
    assert len(part_files) == 3
    part_names = sorted(f.stem for f in part_files)
    assert part_names == ["engine_map", "gearbox", "strategy"]
