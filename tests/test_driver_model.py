"""Tests for F1 driver model (T19.3 + T19.4)."""

from engine.driver_model import (
    create_driver, compute_driver_inputs, adjust_profile_for_conditions,
    compute_reactive_inputs, update_reactive_data, DEFAULT_REACTIVE,
)
from engine.track_gen import interpolate_track, compute_track_data, compute_track_headings
from tracks import get_track


def _make_driver():
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    d, c, tl = compute_track_data(pts)
    h = compute_track_headings(pts)
    car = {"power": 0.625, "grip": 0.625, "weight": 0.375}
    return create_driver(pts, c, d, h, tl, car)


class TestCreateDriver:
    def test_returns_dict(self):
        driver = _make_driver()
        assert "profile" in driver
        assert "line" in driver
        assert "reactive" in driver


class TestDeterministicInputs:
    def test_full_throttle_when_slow(self):
        driver = _make_driver()
        inputs = compute_driver_inputs(driver, {"distance": 100.0, "speed": 50.0})
        assert inputs["throttle"] >= 0.8

    def test_lift_when_fast(self):
        driver = _make_driver()
        inputs = compute_driver_inputs(driver, {"distance": 100.0, "speed": 400.0})
        assert inputs["throttle"] <= 0.5

    def test_lateral_follows_line(self):
        driver = _make_driver()
        inputs = compute_driver_inputs(driver, {"distance": 100.0, "speed": 200.0})
        assert -1.0 <= inputs["lateral_target"] <= 1.0

    def test_condition_reduces_speed(self):
        base = adjust_profile_for_conditions(300.0, tire_wear=0.5, wetness=0.0, damage=0.0)
        assert base < 300.0

    def test_rain_reduces_speed(self):
        dry = adjust_profile_for_conditions(300.0, 0.0, 0.0, 0.0)
        wet = adjust_profile_for_conditions(300.0, 0.0, 0.5, 0.0)
        assert wet < dry

    def test_damage_reduces_speed(self):
        clean = adjust_profile_for_conditions(300.0, 0.0, 0.0, 0.0)
        dmg = adjust_profile_for_conditions(300.0, 0.0, 0.0, 0.5)
        assert dmg < clean


class TestReactiveDriver:
    def test_post_collision_reduces_throttle(self):
        driver = _make_driver()
        driver["last_speed"] = 300.0  # was going fast
        # Sudden speed drop simulates collision
        compute_driver_inputs(driver, {"distance": 100.0, "speed": 100.0})
        assert driver["recovery_ticks"] > 0

    def test_default_reactive_conservative(self):
        assert DEFAULT_REACTIVE["recovery_throttle"] < 0.8
        assert DEFAULT_REACTIVE["wet_caution"] >= 0.2

    def test_tire_cliff_reduces_speed(self):
        result = compute_reactive_inputs({}, {"tire_wear": 0.8}, DEFAULT_REACTIVE)
        assert "speed_factor" in result
        assert result["speed_factor"] < 1.0

    def test_reactive_data_updates(self):
        data = dict(DEFAULT_REACTIVE)
        updated = update_reactive_data(data, [])  # no spins
        assert updated["recovery_throttle"] >= data["recovery_throttle"]

    def test_wet_reduces_speed(self):
        dry = adjust_profile_for_conditions(300.0, 0.0, 0.0, 0.0)
        wet = adjust_profile_for_conditions(300.0, 0.0, 0.8, 0.0)
        assert wet < dry * 0.85
