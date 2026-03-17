"""Tests for bot_scanner v2 — json import and path-gated open() access."""

import os
import textwrap

import pytest

from security.bot_scanner import ALLOWED_IMPORTS, scan_car_file, scan_car_source

CARS_DIR = os.path.join(os.path.dirname(__file__), "..", "cars")

# Shared valid car boilerplate
_CAR_HEADER = """\
CAR_NAME = "Test"
CAR_COLOR = "#aabbcc"
POWER = 20
GRIP = 20
WEIGHT = 20
AERO = 20
BRAKES = 20
"""

_STRATEGY_FOOTER = """\
def strategy(state):
    return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}
"""


def _make_car(body: str = "", imports: str = "") -> str:
    """Build a valid car source with optional imports and strategy body."""
    parts = []
    if imports:
        parts.append(imports)
    parts.append(_CAR_HEADER)
    if body:
        strategy = "def strategy(state):\n"
        for line in body.splitlines():
            strategy += f"    {line}\n"
        strategy += '    return {"throttle": 1.0, "boost": False, "tire_mode": "balanced"}\n'
        parts.append(strategy)
    else:
        parts.append(_STRATEGY_FOOTER)
    return textwrap.dedent("\n".join(parts))


# --- json import ---


class TestJsonImportAllowed:
    def test_import_json_passes(self):
        src = _make_car(imports="import json")
        result = scan_car_source(src)
        assert result.passed is True, f"Violations: {result.violations}"

    def test_from_json_import_passes(self):
        src = _make_car(imports="from json import loads")
        result = scan_car_source(src)
        assert result.passed is True, f"Violations: {result.violations}"

    def test_json_in_allowed_imports(self):
        assert "json" in ALLOWED_IMPORTS

    def test_import_os_still_blocked(self):
        src = _make_car(imports="import os")
        result = scan_car_source(src)
        assert result.passed is False
        assert any("os" in v for v in result.violations)


# --- open() path-gated access ---


class TestOpenSafePaths:
    def test_open_cars_data_json_passes(self):
        src = _make_car(body='f = open("cars/data/mycar.json", "r")')
        result = scan_car_source(src)
        assert result.passed is True, f"Violations: {result.violations}"

    def test_open_cars_data_json_write_passes(self):
        src = _make_car(body='f = open("cars/data/mycar.json", "w")')
        result = scan_car_source(src)
        assert result.passed is True, f"Violations: {result.violations}"

    def test_open_cars_data_json_no_mode_passes(self):
        src = _make_car(body='f = open("cars/data/stats.json")')
        result = scan_car_source(src)
        assert result.passed is True, f"Violations: {result.violations}"


class TestOpenUnsafePaths:
    def test_open_absolute_path_blocked(self):
        src = _make_car(body='open("/etc/passwd")')
        result = scan_car_source(src)
        assert result.passed is False
        assert any("open" in v.lower() for v in result.violations)

    def test_open_traversal_blocked(self):
        src = _make_car(body='open("cars/data/../../etc/passwd")')
        result = scan_car_source(src)
        assert result.passed is False
        assert any("open" in v.lower() for v in result.violations)

    def test_open_traversal_outside_cars_blocked(self):
        src = _make_car(body='open("cars/../secrets.json")')
        result = scan_car_source(src)
        assert result.passed is False
        assert any("open" in v.lower() for v in result.violations)

    def test_open_no_argument_blocked(self):
        src = _make_car(body="open()")
        result = scan_car_source(src)
        assert result.passed is False
        assert any("open" in v.lower() for v in result.violations)

    def test_open_variable_argument_blocked(self):
        src = _make_car(body="open(some_var)")
        result = scan_car_source(src)
        assert result.passed is False
        assert any("open" in v.lower() for v in result.violations)

    def test_open_subdirectory_blocked(self):
        src = _make_car(body='open("cars/data/sub/deep.json")')
        result = scan_car_source(src)
        assert result.passed is False
        assert any("open" in v.lower() for v in result.violations)

    def test_open_wrong_directory_blocked(self):
        src = _make_car(body='open("other/data/file.json")')
        result = scan_car_source(src)
        assert result.passed is False
        assert any("open" in v.lower() for v in result.violations)

    def test_open_non_json_extension_blocked(self):
        src = _make_car(body='open("cars/data/file.txt")')
        result = scan_car_source(src)
        assert result.passed is False
        assert any("open" in v.lower() for v in result.violations)


# --- Seed cars still pass ---


class TestSeedCarsStillPass:
    @pytest.mark.parametrize("filename", [
        "brickhouse.py", "glasscanon.py", "gooseloose.py",
        "silky.py", "slipstream.py",
    ])
    def test_seed_car_passes(self, filename):
        path = os.path.join(CARS_DIR, filename)
        assert os.path.exists(path), f"Seed car not found: {path}"
        result = scan_car_file(path)
        assert result.passed is True, f"{filename} failed: {result.violations}"
