"""Tests for multi-file car project loader."""

import pytest

from engine.car_project_loader import load_car_project


CAR_PY_TEMPLATE = """\
CAR_NAME = "{name}"
CAR_COLOR = "{color}"
POWER = {power}
GRIP = {grip}
WEIGHT = {weight}
AERO = {aero}
BRAKES = {brakes}
"""


def _write_car_py(project_dir, **overrides):
    """Write a minimal car.py into project_dir."""
    defaults = dict(
        name="TestCar", color="#FF0000",
        power=20, grip=20, weight=20, aero=20, brakes=20,
    )
    defaults.update(overrides)
    (project_dir / "car.py").write_text(CAR_PY_TEMPLATE.format(**defaults))


# -- Cycle 1: Missing car.py raises FileNotFoundError --

def test_missing_car_py_raises(tmp_path):
    """A project dir without car.py must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="car.py"):
        load_car_project(str(tmp_path))


# -- Cycle 2: Load metadata from car.py --

def test_loads_car_name_and_color(tmp_path):
    """car.py metadata should be extracted into the car dict."""
    _write_car_py(tmp_path, name="RedBull", color="#1E41FF")
    car = load_car_project(str(tmp_path))
    assert car["CAR_NAME"] == "RedBull"
    assert car["CAR_COLOR"] == "#1E41FF"


def test_loads_stat_fields(tmp_path):
    """All five stat fields should be loaded from car.py."""
    _write_car_py(tmp_path, power=25, grip=15, weight=20, aero=25, brakes=15)
    car = load_car_project(str(tmp_path))
    assert car["POWER"] == 25
    assert car["GRIP"] == 15
    assert car["WEIGHT"] == 20
    assert car["AERO"] == 25
    assert car["BRAKES"] == 15


# -- Cycle 3: Part loading from per-part files --

def test_loads_part_function_from_file(tmp_path):
    """A gearbox.py with def gearbox() should be loaded as parts['gearbox']."""
    _write_car_py(tmp_path)
    (tmp_path / "gearbox.py").write_text(
        "def gearbox(rpm, speed, current_gear, throttle):\n"
        "    return 3\n"
    )
    car = load_car_project(str(tmp_path))
    # The loaded function should be callable and return the custom value
    assert car["parts"]["gearbox"](0, 0, 1, 0) == 3


def test_missing_parts_use_defaults(tmp_path):
    """Parts without files should get default implementations."""
    _write_car_py(tmp_path)
    car = load_car_project(str(tmp_path))
    from engine.parts_api import get_defaults
    defaults = get_defaults()
    # All 10 parts should be present and be default callables
    for part_name, default_fn in defaults.items():
        assert part_name in car["parts"]
        assert car["parts"][part_name] is default_fn


def test_loaded_parts_tracked(tmp_path):
    """_loaded_parts should list only parts that had .py files."""
    _write_car_py(tmp_path)
    (tmp_path / "cooling.py").write_text(
        "def cooling(brake_temp, engine_temp, speed):\n"
        "    return 0.5\n"
    )
    (tmp_path / "fuel_mix.py").write_text(
        "def fuel_mix(lap, total_laps, fuel_remaining, position):\n"
        "    return 0.9\n"
    )
    car = load_car_project(str(tmp_path))
    assert sorted(car["_loaded_parts"]) == ["cooling", "fuel_mix"]


# -- Cycle 4: _source and hardware specs --

def test_source_concatenates_all_py_files(tmp_path):
    """_source should contain the source code of all .py files."""
    _write_car_py(tmp_path)
    gearbox_src = "def gearbox(rpm, speed, current_gear, throttle):\n    return 3\n"
    (tmp_path / "gearbox.py").write_text(gearbox_src)
    car = load_car_project(str(tmp_path))
    # Should contain both car.py and gearbox.py source
    assert "CAR_NAME" in car["_source"]
    assert "def gearbox" in car["_source"]


def test_hardware_specs_loaded(tmp_path):
    """Hardware specs from car.py should be extracted."""
    _write_car_py(tmp_path)
    car_py = tmp_path / "car.py"
    extra = '\nENGINE_SPEC = "v8_800hp"\nAERO_SPEC = "high_downforce"\nCHASSIS_SPEC = "lightweight"\n'
    car_py.write_text(car_py.read_text() + extra)
    car = load_car_project(str(tmp_path))
    assert car["engine_spec"] == "v8_800hp"
    assert car["aero_spec"] == "high_downforce"
    assert car["chassis_spec"] == "lightweight"


def test_hardware_specs_default_when_missing(tmp_path):
    """Hardware specs should have defaults when not specified."""
    _write_car_py(tmp_path)
    car = load_car_project(str(tmp_path))
    assert car["engine_spec"] == "v6_1000hp"
    assert car["aero_spec"] == "medium_downforce"
    assert car["chassis_spec"] == "standard"
