"""Tests for engine.setup_model — car setup sliders."""

import copy
import os
import tempfile

from engine.setup_model import (
    DEFAULT_SETUP,
    apply_setup,
    brake_bias_effect,
    suspension_effect,
    validate_setup,
    wing_effect,
)


# --- validate_setup ---

def test_validate_setup_returns_defaults_for_empty_dict():
    result = validate_setup({})
    assert result == DEFAULT_SETUP


def test_validate_setup_clamps_wing_angle_above_max():
    result = validate_setup({"wing_angle": 2.0})
    assert result["wing_angle"] == 1.0


def test_validate_setup_clamps_wing_angle_below_min():
    result = validate_setup({"wing_angle": -2.0})
    assert result["wing_angle"] == -1.0


def test_validate_setup_clamps_brake_bias_to_bounds():
    result = validate_setup({"brake_bias": 0.1})
    assert result["brake_bias"] == 0.3


def test_validate_setup_merges_partial_input():
    result = validate_setup({"wing_angle": 0.5})
    assert result["wing_angle"] == 0.5
    assert result["brake_bias"] == DEFAULT_SETUP["brake_bias"]
    assert result["suspension"] == DEFAULT_SETUP["suspension"]
    assert result["tire_pressure"] == DEFAULT_SETUP["tire_pressure"]


def test_validate_setup_unknown_key_ignored():
    result = validate_setup({"wing_angle": 0.0, "turbo": 9000})
    assert "turbo" not in result
    assert set(result.keys()) == set(DEFAULT_SETUP.keys())


# --- wing_effect ---

def test_wing_effect_neutral_is_identity():
    aero_mult, power_mult = wing_effect(0.0)
    assert aero_mult == 1.0
    assert power_mult == 1.0


def test_wing_effect_high_increases_aero_reduces_power():
    aero_mult, power_mult = wing_effect(1.0)
    assert aero_mult > 1.0
    assert power_mult < 1.0


def test_wing_effect_low_reduces_aero_increases_power():
    aero_mult, power_mult = wing_effect(-1.0)
    assert aero_mult < 1.0
    assert power_mult > 1.0


# --- brake_bias_effect ---

def test_brake_bias_near_optimal_returns_close_to_one():
    result = brake_bias_effect(0.58)
    assert abs(result - 1.0) < 0.01


def test_brake_bias_extremes_reduce_efficiency():
    low = brake_bias_effect(0.3)
    high = brake_bias_effect(0.7)
    assert low < 1.0
    assert high < 1.0


# --- suspension_effect ---

def test_suspension_stiff_increases_temp_rate():
    result = suspension_effect(1.0)
    assert result > 1.0


def test_suspension_soft_decreases_temp_rate():
    result = suspension_effect(-1.0)
    assert result < 1.0


# --- apply_setup ---

BASE_STATS = {"power": 20, "grip": 20, "weight": 20, "aero": 20, "brakes": 20}


def test_apply_setup_neutral_no_change_to_power_aero_brakes():
    # wing=0 and suspension=0 are neutral; brake_bias at optimal 0.58
    setup = validate_setup({"brake_bias": 0.58})
    result = apply_setup(BASE_STATS, setup)
    assert result["effective_power"] == BASE_STATS["power"]
    assert result["effective_aero"] == BASE_STATS["aero"]
    assert abs(result["effective_brakes"] - BASE_STATS["brakes"]) < 0.01


def test_apply_setup_high_wing_modifies_aero_and_power():
    setup = validate_setup({"wing_angle": 1.0})
    result = apply_setup(BASE_STATS, setup)
    assert result["effective_aero"] > BASE_STATS["aero"]
    assert result["effective_power"] < BASE_STATS["power"]


def test_apply_setup_does_not_mutate_car_stats():
    original = {"power": 20, "grip": 20, "weight": 20, "aero": 20, "brakes": 20}
    frozen = copy.deepcopy(original)
    setup = validate_setup({"wing_angle": 1.0, "brake_bias": 0.4})
    apply_setup(original, setup)
    assert original == frozen


# --- car_loader integration ---

def _make_car_module(tmpdir, name, setup_dict=None):
    """Write a minimal car .py file and return its path."""
    lines = [
        f'CAR_NAME = "{name}"',
        'CAR_COLOR = "#FF0000"',
        "POWER = 20",
        "GRIP = 20",
        "WEIGHT = 20",
        "AERO = 20",
        "BRAKES = 20",
    ]
    if setup_dict is not None:
        lines.append(f"SETUP = {setup_dict!r}")
    path = os.path.join(tmpdir, f"{name}.py")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path


def test_car_loader_reads_setup_from_module():
    from engine.car_loader import load_car

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _make_car_module(
            tmpdir, "test_setup_car", {"wing_angle": 0.8}
        )
        car = load_car(path)
        assert "setup_raw" in car
        assert car["setup_raw"]["wing_angle"] == 0.8
        assert "setup" in car


def test_car_loader_uses_defaults_when_no_setup():
    from engine.car_loader import load_car

    with tempfile.TemporaryDirectory() as tmpdir:
        path = _make_car_module(tmpdir, "test_no_setup_car")
        car = load_car(path)
        assert "setup_raw" in car
        assert car["setup_raw"] == DEFAULT_SETUP
