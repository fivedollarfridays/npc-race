"""Tests for frontrunner rival cars: NightFury, Vortex, Phantom."""

import os

import pytest

from engine.car_loader import load_car

CARS_DIR = os.path.join(os.path.dirname(__file__), "..", "cars")

FRONTRUNNER_FILES = [
    ("nightfury.py", "NightFury", "#1a1a2e"),
    ("vortex.py", "Vortex", "#6c3483"),
    ("phantom.py", "Phantom", "#2c3e50"),
]

STAT_FIELDS = ["POWER", "GRIP", "WEIGHT", "AERO", "BRAKES"]


@pytest.fixture(params=FRONTRUNNER_FILES, ids=lambda x: x[1])
def loaded_car(request):
    """Load each frontrunner car via load_car."""
    filename, expected_name, expected_color = request.param
    filepath = os.path.join(CARS_DIR, filename)
    car = load_car(filepath)
    return car, expected_name, expected_color


def test_car_loads_with_name(loaded_car):
    """Car loads and has correct CAR_NAME."""
    car, expected_name, _ = loaded_car
    assert car["CAR_NAME"] == expected_name


def test_car_loads_with_color(loaded_car):
    """Car loads and has correct CAR_COLOR."""
    car, _, expected_color = loaded_car
    assert car["CAR_COLOR"] == expected_color


def test_stats_sum_to_100(loaded_car):
    """All frontrunner stat budgets sum to exactly 100."""
    car, _, _ = loaded_car
    total = sum(car[s] for s in STAT_FIELDS)
    assert total == 100, f"Stats sum to {total}, expected 100"


def test_stats_are_positive(loaded_car):
    """All stats are at least 5 (factory minimum)."""
    car, _, _ = loaded_car
    for stat in STAT_FIELDS:
        assert car[stat] >= 5, f"{stat}={car[stat]} below minimum 5"


def test_strategy_returns_dict(loaded_car):
    """Strategy function returns a dict with expected keys."""
    car, _, _ = loaded_car
    state = {
        "position": 3,
        "tire_wear": 0.4,
        "lap": 2,
        "total_laps": 5,
        "boost_available": True,
        "pit_stops": 0,
    }
    result = car["strategy"](state)
    assert isinstance(result, dict)
    assert "engine_mode" in result
    assert "tire_mode" in result


def test_strategy_requests_pit_on_high_wear(loaded_car):
    """Strategy requests pit when tire wear is high."""
    car, _, _ = loaded_car
    state = {
        "position": 3,
        "tire_wear": 0.85,
        "lap": 2,
        "total_laps": 10,
        "boost_available": False,
        "pit_stops": 0,
    }
    result = car["strategy"](state)
    assert result.get("pit_request") is True


def test_strategy_boosts_on_final_laps(loaded_car):
    """Strategy activates boost in final laps when available."""
    car, _, _ = loaded_car
    state = {
        "position": 2,
        "tire_wear": 0.3,
        "lap": 8,
        "total_laps": 9,
        "boost_available": True,
        "pit_stops": 0,
    }
    result = car["strategy"](state)
    assert result["boost"] is True


def test_distinct_stat_distributions():
    """Each frontrunner has different stats (distinct seeds)."""
    cars = []
    for filename, _, _ in FRONTRUNNER_FILES:
        filepath = os.path.join(CARS_DIR, filename)
        cars.append(load_car(filepath))
    stat_tuples = [
        tuple(c[s] for s in STAT_FIELDS) for c in cars
    ]
    assert len(set(stat_tuples)) == 3, "All 3 cars should have distinct stats"
