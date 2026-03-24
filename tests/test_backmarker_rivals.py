"""Tests for backmarker rival cars: Tortoise, RustBucket, PaperWeight, SteamRoller."""

import importlib
import types

import pytest

from security.bot_scanner import scan_car_source

BACKMARKER_MODULES = [
    ("cars.tortoise", "Tortoise", "#27ae60"),
    ("cars.rustbucket", "RustBucket", "#d35400"),
    ("cars.paperweight", "PaperWeight", "#95a5a6"),
    ("cars.steamroller", "SteamRoller", "#c0392b"),
]

STAT_KEYS = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]


@pytest.fixture(params=BACKMARKER_MODULES, ids=[m[0] for m in BACKMARKER_MODULES])
def car_module(request) -> tuple[types.ModuleType, str, str]:
    """Load each backmarker car module and return (module, expected_name, expected_color)."""
    mod_name, name, color = request.param
    mod = importlib.import_module(mod_name)
    return mod, name, color


def test_car_name_and_color(car_module: tuple) -> None:
    mod, expected_name, expected_color = car_module
    assert mod.CAR_NAME == expected_name
    assert mod.CAR_COLOR == expected_color


def test_stats_sum_to_100(car_module: tuple) -> None:
    mod, _, _ = car_module
    total = sum(getattr(mod, k) for k in STAT_KEYS)
    assert total == 100, f"Stats sum to {total}, expected 100"


def test_stats_at_least_5(car_module: tuple) -> None:
    mod, _, _ = car_module
    for key in STAT_KEYS:
        val = getattr(mod, key)
        assert val >= 5, f"{key}={val} is below minimum 5"


def test_has_strategy_function(car_module: tuple) -> None:
    mod, _, _ = car_module
    assert callable(mod.strategy), "strategy must be callable"


def test_strategy_returns_valid_dict(car_module: tuple) -> None:
    mod, _, _ = car_module
    state = {
        "tire_wear": 0.3,
        "pit_stops": 0,
        "lap": 2,
        "total_laps": 5,
        "boost_available": False,
        "position": 15,
    }
    result = mod.strategy(state)
    assert isinstance(result, dict)
    assert "engine_mode" in result
    assert "tire_mode" in result


def test_strategy_conservative_engine(car_module: tuple) -> None:
    """Backmarkers use conserve engine mode."""
    mod, _, _ = car_module
    state = {
        "tire_wear": 0.3,
        "pit_stops": 0,
        "lap": 2,
        "total_laps": 5,
        "boost_available": False,
        "position": 15,
    }
    result = mod.strategy(state)
    assert result["engine_mode"] == "conserve"


def test_strategy_conservative_tire(car_module: tuple) -> None:
    """Backmarkers use conserve tire mode."""
    mod, _, _ = car_module
    state = {
        "tire_wear": 0.3,
        "pit_stops": 0,
        "lap": 2,
        "total_laps": 5,
        "boost_available": False,
        "position": 15,
    }
    result = mod.strategy(state)
    assert result["tire_mode"] == "conserve"


def test_strategy_pits_on_high_wear(car_module: tuple) -> None:
    """Backmarkers pit when tire wear exceeds 0.80."""
    mod, _, _ = car_module
    state = {
        "tire_wear": 0.85,
        "pit_stops": 0,
        "lap": 3,
        "total_laps": 5,
        "boost_available": False,
        "position": 18,
    }
    result = mod.strategy(state)
    assert result.get("pit_request") is True
    assert result.get("tire_compound_request") == "hard"


def test_strategy_no_pit_low_wear(car_module: tuple) -> None:
    """Backmarkers do NOT pit when tire wear is low."""
    mod, _, _ = car_module
    state = {
        "tire_wear": 0.3,
        "pit_stops": 0,
        "lap": 2,
        "total_laps": 5,
        "boost_available": False,
        "position": 15,
    }
    result = mod.strategy(state)
    assert not result.get("pit_request", False)


def test_strategy_no_boost(car_module: tuple) -> None:
    """Backmarkers never boost."""
    mod, _, _ = car_module
    state = {
        "tire_wear": 0.2,
        "pit_stops": 0,
        "lap": 4,
        "total_laps": 5,
        "boost_available": True,
        "position": 15,
    }
    result = mod.strategy(state)
    assert result.get("boost") is False


def _read_source(mod_name: str) -> str:
    """Read source file for a module."""
    path = mod_name.replace(".", "/") + ".py"
    with open(path) as f:
        return f.read()


@pytest.mark.parametrize("mod_name", [m[0] for m in BACKMARKER_MODULES])
def test_bot_scanner_passes(mod_name: str) -> None:
    """Each backmarker car passes the bot scanner."""
    source = _read_source(mod_name)
    result = scan_car_source(source)
    assert result.passed, f"Bot scanner failed: {result.violations}"
