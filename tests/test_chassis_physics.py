"""Tests for engine/chassis_physics.py — aero, braking, suspension, cooling."""

from engine.chassis_physics import (
    compute_downforce,
    compute_drag,
    compute_braking_force,
    apply_brake_bias,
    compute_brake_temp_change,
    compute_ride_height_effect,
    compute_cooling_effect,
)


class TestAerodynamics:
    """Downforce and drag computations."""

    def test_downforce_increases_with_speed(self):
        low = compute_downforce(speed_kmh=100, cl=3.0, ride_height=0.0)
        high = compute_downforce(speed_kmh=300, cl=3.0, ride_height=0.0)
        assert high > low
        assert low > 0

    def test_lower_ride_height_more_downforce(self):
        low_ride = compute_downforce(speed_kmh=250, cl=3.0, ride_height=-0.8)
        high_ride = compute_downforce(speed_kmh=250, cl=3.0, ride_height=0.5)
        assert low_ride > high_ride

    def test_drag_increases_with_speed(self):
        low = compute_drag(speed_kmh=100, cd=1.0, cooling_effort=0.0)
        high = compute_drag(speed_kmh=300, cd=1.0, cooling_effort=0.0)
        assert high > low
        assert low > 0

    def test_cooling_adds_drag(self):
        no_cool = compute_drag(speed_kmh=250, cd=1.0, cooling_effort=0.0)
        full_cool = compute_drag(speed_kmh=250, cd=1.0, cooling_effort=1.0)
        assert full_cool > no_cool


class TestBraking:
    """Braking force, bias, and temperature."""

    def test_braking_force_positive(self):
        df = compute_downforce(speed_kmh=200, cl=3.0, ride_height=0.0)
        force = compute_braking_force(
            speed_kmh=200, brake_g=5.0, downforce_n=df, mass_kg=800
        )
        assert force > 0

    def test_brake_bias_splits_force(self):
        front, rear = apply_brake_bias(total_force=10000, front_pct=57)
        assert front > rear
        assert abs(front + rear - 10000) < 0.01

    def test_brake_temp_rises_under_braking(self):
        initial_temp = 400.0
        new_temp = compute_brake_temp_change(
            current_temp=initial_temp,
            braking_force=5000,
            speed_kmh=200,
            cooling_effort=0.0,
            dt=1.0,
        )
        assert new_temp > initial_temp


class TestSuspension:
    """Ride height and bottoming out."""

    def test_suspension_bottoming_at_low_height(self):
        _, bottoming = compute_ride_height_effect(
            ride_height_target=-0.9, speed_kmh=300
        )
        assert bottoming is True

    def test_no_bottoming_at_normal_height(self):
        _, bottoming = compute_ride_height_effect(
            ride_height_target=0.5, speed_kmh=200
        )
        assert bottoming is False

    def test_compression_increases_with_speed(self):
        actual_low, _ = compute_ride_height_effect(
            ride_height_target=0.0, speed_kmh=100
        )
        actual_high, _ = compute_ride_height_effect(
            ride_height_target=0.0, speed_kmh=300
        )
        # Higher speed compresses more, so actual ride height is lower
        assert actual_high < actual_low


class TestCooling:
    """Cooling effect on engine, brake, battery temps."""

    def test_cooling_reduces_temps(self):
        e_cool, b_cool, bat_cool = compute_cooling_effect(
            cooling_effort=1.0,
            engine_temp=120.0,
            brake_temp=500.0,
            battery_temp=45.0,
            dt=1.0,
        )
        assert e_cool > 0
        assert b_cool > 0
        assert bat_cool > 0

    def test_no_cooling_at_zero_effort(self):
        e_cool, b_cool, bat_cool = compute_cooling_effect(
            cooling_effort=0.0,
            engine_temp=120.0,
            brake_temp=500.0,
            battery_temp=45.0,
            dt=1.0,
        )
        assert e_cool == 0.0
        assert b_cool == 0.0
        assert bat_cool == 0.0
