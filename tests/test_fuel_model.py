"""Tests for engine/fuel_model.py — fuel consumption, engine modes, weight."""

from engine.fuel_model import (
    get_engine_mode,
    get_engine_mode_names,
    compute_starting_fuel,
    compute_fuel_consumption,
    compute_weight_from_fuel,
    BASE_CONSUMPTION_KG_PER_M,
    FUEL_MARGIN,
    FUEL_LAP_TIME_SENSITIVITY,
    MAX_FUEL_WEIGHT_FACTOR,
    ENGINE_MODES,
)


# --- Cycle 1: Engine mode lookup ---


class TestGetEngineMode:
    def test_standard_mode_returns_dict(self):
        mode = get_engine_mode("standard")
        assert mode["consumption_mult"] == 1.00
        assert mode["power_mult"] == 1.00

    def test_push_mode(self):
        mode = get_engine_mode("push")
        assert mode["consumption_mult"] == 1.25
        assert mode["power_mult"] == 1.03

    def test_conserve_mode(self):
        mode = get_engine_mode("conserve")
        assert mode["consumption_mult"] == 0.80
        assert mode["power_mult"] == 0.95

    def test_invalid_mode_defaults_to_standard(self):
        mode = get_engine_mode("turbo")
        assert mode == get_engine_mode("standard")

    def test_none_defaults_to_standard(self):
        mode = get_engine_mode(None)
        assert mode == get_engine_mode("standard")


class TestGetEngineModeNames:
    def test_returns_list(self):
        names = get_engine_mode_names()
        assert isinstance(names, list)

    def test_contains_all_modes(self):
        names = get_engine_mode_names()
        assert "push" in names
        assert "standard" in names
        assert "conserve" in names

    def test_length_matches_engine_modes(self):
        assert len(get_engine_mode_names()) == len(ENGINE_MODES)


# --- Cycle 2: Starting fuel ---


class TestComputeStartingFuel:
    def test_proportional_to_laps(self):
        fuel_10 = compute_starting_fuel(10, 5000)
        fuel_20 = compute_starting_fuel(20, 5000)
        assert abs(fuel_20 - 2 * fuel_10) < 0.001

    def test_proportional_to_track_length(self):
        fuel_short = compute_starting_fuel(10, 3000)
        fuel_long = compute_starting_fuel(10, 6000)
        assert abs(fuel_long - 2 * fuel_short) < 0.001

    def test_monza_53_laps_reasonable(self):
        """Monza 53 laps: ~85-110 kg expected (real F1 ~1.6 kg/lap)."""
        fuel = compute_starting_fuel(53, 5793)
        assert 70.0 < fuel < 120.0

    def test_includes_margin(self):
        """Starting fuel includes FUEL_MARGIN multiplier."""
        raw = 10 * 5000 * BASE_CONSUMPTION_KG_PER_M
        with_margin = compute_starting_fuel(10, 5000)
        assert abs(with_margin - raw * FUEL_MARGIN) < 0.001

    def test_zero_laps_returns_zero(self):
        assert compute_starting_fuel(0, 5000) == 0.0


# --- Cycle 3: Fuel consumption per tick ---


class TestComputeFuelConsumption:
    def test_zero_throttle_zero_consumption(self):
        result = compute_fuel_consumption(
            throttle=0.0, engine_mode_name="standard",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        assert result == 0.0

    def test_push_consumes_more_than_standard(self):
        standard = compute_fuel_consumption(
            throttle=1.0, engine_mode_name="standard",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        push = compute_fuel_consumption(
            throttle=1.0, engine_mode_name="push",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        assert push > standard

    def test_conserve_consumes_less_than_standard(self):
        standard = compute_fuel_consumption(
            throttle=1.0, engine_mode_name="standard",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        conserve = compute_fuel_consumption(
            throttle=1.0, engine_mode_name="conserve",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        assert conserve < standard

    def test_half_throttle_half_consumption(self):
        full = compute_fuel_consumption(
            throttle=1.0, engine_mode_name="standard",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        half = compute_fuel_consumption(
            throttle=0.5, engine_mode_name="standard",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        assert abs(half - full * 0.5) < 1e-10

    def test_consumption_scales_with_dt(self):
        dt1 = compute_fuel_consumption(
            throttle=1.0, engine_mode_name="standard",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        dt2 = compute_fuel_consumption(
            throttle=1.0, engine_mode_name="standard",
            base_rate_per_tick=0.0001, dt=2.0,
        )
        assert abs(dt2 - dt1 * 2.0) < 1e-10

    def test_result_never_negative(self):
        result = compute_fuel_consumption(
            throttle=1.0, engine_mode_name="standard",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        assert result >= 0.0

    def test_invalid_mode_uses_standard_rate(self):
        standard = compute_fuel_consumption(
            throttle=1.0, engine_mode_name="standard",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        invalid = compute_fuel_consumption(
            throttle=1.0, engine_mode_name="bogus",
            base_rate_per_tick=0.0001, dt=1.0,
        )
        assert invalid == standard


# --- Cycle 4: Weight from fuel ---


class TestComputeWeightFromFuel:
    def test_full_tank_returns_max_factor(self):
        weight = compute_weight_from_fuel(fuel_kg=20.0, max_fuel_kg=20.0)
        assert abs(weight - MAX_FUEL_WEIGHT_FACTOR) < 0.001

    def test_empty_tank_returns_zero(self):
        weight = compute_weight_from_fuel(fuel_kg=0.0, max_fuel_kg=20.0)
        assert weight == 0.0

    def test_half_tank_returns_half_factor(self):
        weight = compute_weight_from_fuel(fuel_kg=10.0, max_fuel_kg=20.0)
        assert abs(weight - MAX_FUEL_WEIGHT_FACTOR * 0.5) < 0.001

    def test_weight_decreases_as_fuel_burns(self):
        w_full = compute_weight_from_fuel(fuel_kg=20.0, max_fuel_kg=20.0)
        w_half = compute_weight_from_fuel(fuel_kg=10.0, max_fuel_kg=20.0)
        w_empty = compute_weight_from_fuel(fuel_kg=0.0, max_fuel_kg=20.0)
        assert w_full > w_half > w_empty

    def test_weight_in_zero_to_one_range(self):
        weight = compute_weight_from_fuel(fuel_kg=20.0, max_fuel_kg=20.0)
        assert 0.0 <= weight <= 1.0

    def test_negative_fuel_clamps_to_zero(self):
        weight = compute_weight_from_fuel(fuel_kg=-5.0, max_fuel_kg=20.0)
        assert weight == 0.0


# --- Constants ---


class TestConstants:
    def test_base_consumption_positive(self):
        assert BASE_CONSUMPTION_KG_PER_M > 0

    def test_fuel_margin_above_one(self):
        assert FUEL_MARGIN > 1.0

    def test_max_weight_factor_in_range(self):
        assert 0.0 < MAX_FUEL_WEIGHT_FACTOR <= 1.0

    def test_engine_modes_has_three_entries(self):
        assert len(ENGINE_MODES) == 3


# --- Cycle 5: TUMFTM calibration (Monza 2017 data) ---


class TestTUMFTMCalibration:
    def test_monza_fuel_near_2kg_per_lap(self):
        """Monza 5793m * BASE_CONSUMPTION_KG_PER_M should be ~2.0 kg/lap."""
        kg_per_lap = 5793 * BASE_CONSUMPTION_KG_PER_M
        assert 1.8 <= kg_per_lap <= 2.2

    def test_fuel_sensitivity_constant_exists(self):
        """FUEL_LAP_TIME_SENSITIVITY is importable and positive."""
        assert FUEL_LAP_TIME_SENSITIVITY > 0

    def test_fuel_sensitivity_value(self):
        """FUEL_LAP_TIME_SENSITIVITY should be 0.030 s/kg/lap."""
        assert FUEL_LAP_TIME_SENSITIVITY == 0.030
