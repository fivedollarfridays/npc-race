"""Tests for midfield rival car files: ironside, crosswind, foxfire, driftking."""

import importlib.util
import os

import pytest

CARS_DIR = os.path.join(os.path.dirname(__file__), "..", "cars")

MIDFIELD_CARS = [
    ("ironside", "IronSide", "#7f8c8d", 201),
    ("crosswind", "CrossWind", "#2980b9", 202),
    ("foxfire", "FoxFire", "#e67e22", 203),
    ("driftking", "DriftKing", "#8e44ad", 204),
]

STAT_FIELDS = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]


def _load_module(filename: str):
    """Load a car module by filename."""
    filepath = os.path.join(CARS_DIR, filename + ".py")
    spec = importlib.util.spec_from_file_location(filename, filepath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(params=MIDFIELD_CARS, ids=[c[0] for c in MIDFIELD_CARS])
def car_module(request):
    """Parametrized fixture returning (module, name, color, seed)."""
    filename, name, color, seed = request.param
    mod = _load_module(filename)
    return mod, name, color, seed


def test_car_name_matches(car_module):
    """Each car file has correct CAR_NAME literal."""
    mod, expected_name, _, _ = car_module
    assert mod.CAR_NAME == expected_name


def test_car_color_matches(car_module):
    """Each car file has correct CAR_COLOR literal."""
    mod, _, expected_color, _ = car_module
    assert mod.CAR_COLOR == expected_color


def test_stats_are_literal_integers(car_module):
    """All stat fields are literal int assignments."""
    mod, _, _, _ = car_module
    for field in STAT_FIELDS:
        val = getattr(mod, field)
        assert isinstance(val, int), f"{field} should be int, got {type(val)}"


def test_stats_sum_to_100(car_module):
    """Stats must sum to exactly 100."""
    mod, _, _, _ = car_module
    total = sum(getattr(mod, f) for f in STAT_FIELDS)
    assert total == 100, f"Stats sum to {total}, expected 100"


def test_stats_match_factory(car_module):
    """Stats match what the factory generates for this seed."""
    from cars._rival_factory import generate_rival

    mod, name, color, seed = car_module
    expected = generate_rival("midfield", name, color, seed)
    for field in STAT_FIELDS:
        assert getattr(mod, field) == expected[field], (
            f"{field}: file has {getattr(mod, field)}, factory gives {expected[field]}"
        )


def test_has_strategy_function(car_module):
    """Each car has a callable strategy function."""
    mod, _, _, _ = car_module
    assert hasattr(mod, "strategy"), "Missing strategy function"
    assert callable(mod.strategy), "strategy must be callable"


def test_strategy_returns_valid_dict(car_module):
    """Strategy returns dict with required keys."""
    mod, _, _, _ = car_module
    state = {
        "tire_wear": 0.3,
        "gap_ahead_s": 5.0,
        "lap": 2,
        "total_laps": 10,
        "position": 8,
        "pit_stops": 0,
    }
    result = mod.strategy(state)
    assert isinstance(result, dict)
    assert "engine_mode" in result
    assert "tire_mode" in result


def test_strategy_push_when_gap_close(car_module):
    """Strategy uses push mode when gap ahead is small."""
    mod, _, _, _ = car_module
    state = {
        "tire_wear": 0.3,
        "gap_ahead_s": 1.0,
        "lap": 2,
        "total_laps": 10,
        "position": 8,
        "pit_stops": 0,
    }
    result = mod.strategy(state)
    assert result["engine_mode"] == "push"


def test_strategy_pits_on_high_wear(car_module):
    """Strategy requests pit when tire wear exceeds threshold."""
    mod, _, _, _ = car_module
    state = {
        "tire_wear": 0.90,
        "gap_ahead_s": 5.0,
        "lap": 5,
        "total_laps": 10,
        "position": 8,
        "pit_stops": 0,
    }
    result = mod.strategy(state)
    assert result.get("pit_request") is True
    assert result.get("tire_compound_request") == "hard"


def test_strategy_no_pit_on_low_wear(car_module):
    """Strategy does not pit when tire wear is low."""
    mod, _, _, _ = car_module
    state = {
        "tire_wear": 0.20,
        "gap_ahead_s": 5.0,
        "lap": 2,
        "total_laps": 10,
        "position": 8,
        "pit_stops": 0,
    }
    result = mod.strategy(state)
    assert not result.get("pit_request", False)


def test_pit_thresholds_vary_across_cars():
    """Each car has a slightly different pit threshold."""
    thresholds = []
    for filename, name, color, seed in MIDFIELD_CARS:
        mod = _load_module(filename)
        # Binary search for approximate threshold
        low, high = 0.5, 0.95
        for _ in range(20):
            mid = (low + high) / 2
            state = {
                "tire_wear": mid,
                "gap_ahead_s": 5.0,
                "lap": 5,
                "total_laps": 10,
                "position": 8,
                "pit_stops": 0,
            }
            result = mod.strategy(state)
            if result.get("pit_request"):
                high = mid
            else:
                low = mid
        thresholds.append(round((low + high) / 2, 2))
    # All thresholds should be distinct (different by at least 0.03)
    for i in range(len(thresholds)):
        for j in range(i + 1, len(thresholds)):
            assert abs(thresholds[i] - thresholds[j]) >= 0.03, (
                f"Thresholds too similar: {thresholds}"
            )
