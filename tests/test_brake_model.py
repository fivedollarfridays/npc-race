"""Tests for engine/brake_model.py — brake temperature and fade model."""

from engine.brake_model import (
    BRAKE_AMBIENT,
    BRAKE_FADE_MAX,
    BRAKE_FADE_START,
    BRAKE_MIN_EFFICIENCY,
    create_brake_state,
    get_brake_efficiency,
    get_brake_temp_from_state,
    update_brake_temp,
)


class TestCreateBrakeState:
    def test_initial_temp_ambient(self):
        """Brake state starts at ambient 20C."""
        state = create_brake_state()
        assert state["temp"] == BRAKE_AMBIENT
        assert state["temp"] == 20.0


class TestUpdateBrakeTemp:
    def test_braking_heats_up(self):
        """Heavy braking increases brake temperature."""
        state = create_brake_state()
        updated = update_brake_temp(state, braking_force=1.0, speed=300.0, dt=1.0)
        assert updated["temp"] > BRAKE_AMBIENT

    def test_no_braking_cools_down(self):
        """When temp > ambient and no braking, temp decreases from airflow."""
        state = {"temp": 500.0}
        updated = update_brake_temp(state, braking_force=0.0, speed=200.0, dt=1.0)
        assert updated["temp"] < 500.0

    def test_airflow_cooling_proportional(self):
        """Higher speed produces faster cooling (more airflow)."""
        state_slow = {"temp": 600.0}
        state_fast = {"temp": 600.0}
        slow = update_brake_temp(state_slow, braking_force=0.0, speed=100.0, dt=1.0)
        fast = update_brake_temp(state_fast, braking_force=0.0, speed=300.0, dt=1.0)
        # Higher speed → more cooling → lower temp
        assert fast["temp"] < slow["temp"]


class TestGetBrakeEfficiency:
    def test_efficiency_optimal(self):
        """At 400C (within optimal range), efficiency is 1.0."""
        assert get_brake_efficiency(400.0) == 1.0

    def test_efficiency_fade_start(self):
        """At exactly 700C (fade start), efficiency is still 1.0."""
        assert get_brake_efficiency(BRAKE_FADE_START) == 1.0

    def test_efficiency_mid_fade(self):
        """At 800C (midpoint of fade range), efficiency is ~0.8."""
        eff = get_brake_efficiency(800.0)
        assert abs(eff - 0.8) < 0.01

    def test_efficiency_max_fade(self):
        """At 900C (fade max), efficiency reaches minimum 0.6."""
        assert get_brake_efficiency(BRAKE_FADE_MAX) == BRAKE_MIN_EFFICIENCY

    def test_efficiency_above_max(self):
        """Above 900C, efficiency is clamped at 0.6."""
        assert get_brake_efficiency(1000.0) == BRAKE_MIN_EFFICIENCY


class TestGetBrakeTempFromState:
    def test_returns_temp(self):
        """Extracts temperature from brake state dict."""
        state = {"temp": 456.7}
        assert get_brake_temp_from_state(state) == 456.7
