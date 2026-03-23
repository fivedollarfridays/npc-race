"""Tests for wildcard rival car files (gambler, chameleon, berserker)."""

import importlib
import pytest

from security.bot_scanner import scan_car_file


# --- Module-level metadata ---


CAR_SPECS = {
    "gambler": {
        "CAR_NAME": "Gambler",
        "CAR_COLOR": "#f1c40f",
        "POWER": 29, "GRIP": 21, "WEIGHT": 18, "AERO": 18, "BRAKES": 14,
    },
    "chameleon": {
        "CAR_NAME": "Chameleon",
        "CAR_COLOR": "#1abc9c",
        "POWER": 34, "GRIP": 20, "WEIGHT": 14, "AERO": 21, "BRAKES": 11,
    },
    "berserker": {
        "CAR_NAME": "Berserker",
        "CAR_COLOR": "#e74c3c",
        "POWER": 30, "GRIP": 22, "WEIGHT": 16, "AERO": 15, "BRAKES": 17,
    },
}

STAT_KEYS = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]


@pytest.fixture(params=["gambler", "chameleon", "berserker"])
def car_module(request):
    """Load a wildcard car module."""
    return importlib.import_module(f"cars.{request.param}")


@pytest.fixture(params=["gambler", "chameleon", "berserker"])
def car_name_and_module(request):
    """Load a wildcard car module with its name."""
    mod = importlib.import_module(f"cars.{request.param}")
    return request.param, mod


def test_car_name_and_color(car_name_and_module):
    name, mod = car_name_and_module
    spec = CAR_SPECS[name]
    assert mod.CAR_NAME == spec["CAR_NAME"]
    assert mod.CAR_COLOR == spec["CAR_COLOR"]


def test_stats_match_factory(car_name_and_module):
    name, mod = car_name_and_module
    spec = CAR_SPECS[name]
    for key in STAT_KEYS:
        assert getattr(mod, key) == spec[key], f"{name}.{key}"


def test_stats_sum_to_100(car_module):
    total = sum(getattr(car_module, k) for k in STAT_KEYS)
    assert total == 100


def test_has_strategy_function(car_module):
    assert callable(car_module.strategy)


def test_bot_scanner_passes():
    for name in ("gambler", "chameleon", "berserker"):
        result = scan_car_file(f"cars/{name}.py")
        assert result.passed, f"{name}: {result.violations}"


# --- Strategy behavior: Gambler ---


def _gambler():
    return importlib.import_module("cars.gambler")


def test_gambler_push_on_mod3_lap():
    mod = _gambler()
    d = mod.strategy({"lap": 3, "position": 10})
    assert d["engine_mode"] == "push"


def test_gambler_standard_off_mod3():
    mod = _gambler()
    d = mod.strategy({"lap": 4, "position": 10})
    assert d["engine_mode"] == "standard"


def test_gambler_pit_on_lap_15():
    mod = _gambler()
    d = mod.strategy({"lap": 15, "position": 10})
    assert d.get("pit_request") is True
    assert d["tire_compound_request"] == "medium"


def test_gambler_no_pit_lap_7():
    mod = _gambler()
    d = mod.strategy({"lap": 7, "position": 10})
    assert d.get("pit_request") is not True


def test_gambler_boost_top3():
    mod = _gambler()
    d = mod.strategy({"lap": 1, "position": 2})
    assert d["boost"] is True


def test_gambler_no_boost_when_behind():
    mod = _gambler()
    d = mod.strategy({"lap": 1, "position": 8})
    assert d["boost"] is False


# --- Strategy behavior: Chameleon ---


def _chameleon():
    return importlib.import_module("cars.chameleon")


def test_chameleon_push_when_far_behind():
    mod = _chameleon()
    d = mod.strategy({"position": 15, "tire_wear": 0})
    assert d["engine_mode"] == "push"
    assert d["tire_mode"] == "push"


def test_chameleon_conserve_when_leading():
    mod = _chameleon()
    d = mod.strategy({"position": 2, "tire_wear": 0})
    assert d["engine_mode"] == "conserve"
    assert d["tire_mode"] == "conserve"


def test_chameleon_standard_midfield():
    mod = _chameleon()
    d = mod.strategy({"position": 7, "tire_wear": 0})
    assert d["engine_mode"] == "standard"
    assert d["tire_mode"] == "balanced"


def test_chameleon_pit_high_wear():
    mod = _chameleon()
    d = mod.strategy({"position": 7, "tire_wear": 0.75})
    assert d.get("pit_request") is True


def test_chameleon_no_pit_low_wear():
    mod = _chameleon()
    d = mod.strategy({"position": 7, "tire_wear": 0.50})
    assert d.get("pit_request") is not True


# --- Strategy behavior: Berserker ---


def _berserker():
    return importlib.import_module("cars.berserker")


def test_berserker_always_push():
    mod = _berserker()
    d = mod.strategy({"tire_wear": 0, "position": 10})
    assert d["engine_mode"] == "push"
    assert d["tire_mode"] == "push"


def test_berserker_always_boost():
    mod = _berserker()
    d = mod.strategy({"tire_wear": 0, "position": 10})
    assert d["boost"] is True


def test_berserker_pit_early():
    mod = _berserker()
    d = mod.strategy({"tire_wear": 0.60, "position": 10})
    assert d.get("pit_request") is True
    assert d["tire_compound_request"] == "soft"


def test_berserker_no_pit_low_wear():
    mod = _berserker()
    d = mod.strategy({"tire_wear": 0.40, "position": 10})
    assert d.get("pit_request") is not True
