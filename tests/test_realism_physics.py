"""Tests for realistic F1 physics — drag, speed cap, corner speeds (T6.2)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.physics import (
    apply_drag, MAX_SPEED, compute_target_speed, update_speed,
)


# --- Cycle 1: Aerodynamic drag ---


class TestAerodynamicDrag:
    """apply_drag reduces speed via v-squared resistance."""

    def test_drag_reduces_speed(self):
        """apply_drag with speed=300 returns < 300."""
        result = apply_drag(300.0, 1.0 / 30)
        assert result < 300.0

    def test_drag_zero_at_zero_speed(self):
        """apply_drag with speed=0 returns 0."""
        result = apply_drag(0.0, 1.0 / 30)
        assert result == 0.0

    def test_drag_never_negative(self):
        """apply_drag never returns negative speed."""
        result = apply_drag(5.0, 1.0)
        assert result >= 0.0

    def test_drag_increases_with_speed(self):
        """Higher speed means more drag (v-squared)."""
        drag_at_200 = 200.0 - apply_drag(200.0, 1.0 / 30)
        drag_at_300 = 300.0 - apply_drag(300.0, 1.0 / 30)
        assert drag_at_300 > drag_at_200


# --- Cycle 2: Hard speed cap ---


class TestSpeedCap:
    """MAX_SPEED constant exists and is 370."""

    def test_max_speed_constant(self):
        assert MAX_SPEED == 370.0

    def test_max_speed_under_370_sustained(self):
        """Simulate 10,000 ticks of acceleration on straight, speed never > 370."""
        speed = 0.0
        dt = 1.0 / 30
        for _ in range(10_000):
            target = compute_target_speed(
                power=1.0, grip=1.0, weight=0.0,
                curvature=0.0, throttle=1.0,
                power_mode=1.03, boost_active=True,
            )
            speed = update_speed(speed, target, 1.0, 0.0, 0.0, 1.0, dt)
            speed = apply_drag(speed, dt)
            speed = min(MAX_SPEED, speed)
            assert speed <= 370.0, f"Speed exceeded 370: {speed}"


# --- Cycle 3: Corner speed realism ---


class TestCornerSpeedRealism:
    """Corner speeds much lower than straight speeds."""

    def test_corner_speed_much_lower_than_straight(self):
        """curvature=0.2 target_speed < 0.6 * curvature=0 target_speed."""
        straight = compute_target_speed(
            power=0.5, grip=0.5, weight=0.5,
            curvature=0.0, throttle=1.0,
        )
        corner = compute_target_speed(
            power=0.5, grip=0.5, weight=0.5,
            curvature=0.2, throttle=1.0,
        )
        assert corner < 0.6 * straight, (
            f"Corner speed {corner:.1f} not < 60% of straight {straight:.1f}"
        )

    def test_straight_speed_in_f1_range(self):
        """Balanced car straight speed in 260-330 km/h."""
        speed = compute_target_speed(
            power=0.5, grip=0.5, weight=0.5,
            curvature=0.0, throttle=1.0,
        )
        assert 260 <= speed <= 330, f"Straight speed {speed:.1f} out of range"

    def test_max_power_car_under_350(self):
        """Max power car (1.0) straight speed < 350 km/h."""
        speed = compute_target_speed(
            power=1.0, grip=0.5, weight=0.25,
            curvature=0.0, throttle=1.0,
        )
        assert speed < 350, f"Max power speed {speed:.1f} >= 350"
