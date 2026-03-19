"""Tests for engine/physics.py — extracted physics constants and functions (T6.1)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.physics import (
    BASE_SPEED, POWER_SPEED_FACTOR, WEIGHT_SPEED_PENALTY, CURVATURE_FACTOR,
    GRIP_BASE_SPEED, GRIP_SPEED_RANGE, ACCEL_BASE, ACCEL_POWER_FACTOR,
    WEIGHT_MASS_FACTOR, BRAKE_BASE, BRAKE_FACTOR, DRAFT_BONUS_BASE,
    DRAFT_MAX_DISTANCE,
    compute_target_speed, compute_acceleration, compute_braking,
    compute_draft_bonus, compute_mass_factor, compute_aero_grip,
)


def test_physics_constants_exist():
    """All physics constants are importable with expected values (T6.2 recalibrated)."""
    assert BASE_SPEED == 250
    assert POWER_SPEED_FACTOR == 90
    assert WEIGHT_SPEED_PENALTY == 20
    assert CURVATURE_FACTOR == 18.0
    assert GRIP_BASE_SPEED == 80
    assert GRIP_SPEED_RANGE == 160
    assert ACCEL_BASE == 40
    assert ACCEL_POWER_FACTOR == 45
    assert WEIGHT_MASS_FACTOR == 1.2
    assert BRAKE_BASE == 180
    assert BRAKE_FACTOR == 120
    assert DRAFT_BONUS_BASE == 5
    assert DRAFT_MAX_DISTANCE == 40


def test_compute_target_speed_straight():
    """Curvature=0, throttle=1.0 gives pure base_max_speed (T6.2 recalibrated)."""
    # power=0.5, grip=0.5, weight=0.5, curvature=0, throttle=1.0
    # base_max_speed = 250 + 0.5*90*1.0 - 0.5*20 = 250 + 45 - 10 = 285
    # curv_severity = min(1.0, 0 * 18.0) = 0
    # target = (285 * 1.0 + grip_speed * 0.0) * 1.0 = 285
    speed = compute_target_speed(
        power=0.5, grip=0.5, weight=0.5,
        curvature=0.0, throttle=1.0,
    )
    assert abs(speed - 285.0) < 0.01


def test_compute_target_speed_corner():
    """Curvature=0.02, throttle=0.8 gives speed lower than straight."""
    straight = compute_target_speed(
        power=0.5, grip=0.5, weight=0.5,
        curvature=0.0, throttle=1.0,
    )
    corner = compute_target_speed(
        power=0.5, grip=0.5, weight=0.5,
        curvature=0.02, throttle=0.8,
    )
    assert corner < straight


def test_compute_acceleration_toward_target():
    """Speed < target: new speed is closer to target."""
    new_speed = compute_acceleration(
        speed=100.0, target_speed=200.0,
        power=0.5, mass_factor=2.0, dt=1 / 30,
    )
    assert 100.0 < new_speed <= 200.0


def test_compute_acceleration_at_target():
    """Speed == target: no change."""
    new_speed = compute_acceleration(
        speed=150.0, target_speed=150.0,
        power=0.5, mass_factor=2.0, dt=1 / 30,
    )
    assert abs(new_speed - 150.0) < 0.001


def test_compute_braking_toward_target():
    """Speed > target: new speed is closer to target."""
    new_speed = compute_braking(
        speed=200.0, target_speed=100.0,
        brakes=0.5, dt=1 / 30,
    )
    assert 100.0 <= new_speed < 200.0


def test_compute_mass_factor():
    """Known weight + fuel_weight gives expected mass factor."""
    # mass_factor = 1.0 + weight * WEIGHT_MASS_FACTOR + fuel_weight
    # = 1.0 + 0.5 * 1.2 + 0.3 = 1.0 + 0.6 + 0.3 = 1.9
    mf = compute_mass_factor(weight=0.5, fuel_weight=0.3)
    assert abs(mf - 1.9) < 0.001


def test_compute_draft_bonus_within_range():
    """Distance=20 (within DRAFT_MAX_DISTANCE=40) gives positive bonus."""
    bonus = compute_draft_bonus(aero=0.5, distance_ahead=20.0, dt=1 / 30)
    assert bonus > 0.0


def test_compute_draft_bonus_out_of_range():
    """Distance=50 (beyond DRAFT_MAX_DISTANCE=40) gives zero bonus."""
    bonus = compute_draft_bonus(aero=0.5, distance_ahead=50.0, dt=1 / 30)
    assert bonus == 0.0


class TestAeroGrip:
    def test_aero_grip_zero_at_zero_speed(self):
        assert compute_aero_grip(0.0, 1.0) == 0.0

    def test_aero_grip_increases_with_speed(self):
        low = compute_aero_grip(100.0, 1.0)
        high = compute_aero_grip(250.0, 1.0)
        assert high > low

    def test_aero_grip_proportional_to_v_squared(self):
        g100 = compute_aero_grip(100.0, 1.0)
        g200 = compute_aero_grip(200.0, 1.0)
        # Should be roughly 4x (200²/100² = 4)
        ratio = g200 / g100 if g100 > 0 else 0
        assert 3.5 <= ratio <= 4.5

    def test_aero_grip_increases_with_aero_stat(self):
        low_aero = compute_aero_grip(200.0, 0.5)
        high_aero = compute_aero_grip(200.0, 1.0)
        assert high_aero > low_aero

    def test_aero_grip_wing_positive_increases(self):
        neutral = compute_aero_grip(200.0, 1.0, wing_angle=0.0)
        high_wing = compute_aero_grip(200.0, 1.0, wing_angle=1.0)
        assert high_wing > neutral

    def test_aero_grip_wing_negative_decreases(self):
        neutral = compute_aero_grip(200.0, 1.0, wing_angle=0.0)
        low_wing = compute_aero_grip(200.0, 1.0, wing_angle=-1.0)
        assert low_wing < neutral

    def test_aero_grip_reasonable_magnitude(self):
        # At 300 km/h with aero=1.0, should be meaningful but not overwhelming
        grip = compute_aero_grip(300.0, 1.0)
        assert 0.1 <= grip <= 0.5
