"""Tests for the dirty air aerodynamic turbulence model."""

from engine.dirty_air import compute_dirty_air_factor


class TestDirtyAir:
    """Tests for compute_dirty_air_factor."""

    def test_clean_air_no_penalty(self) -> None:
        """Gap=5.0, curvature=0.1 -> clean air, no effect."""
        grip, wear = compute_dirty_air_factor(gap_ahead_s=5.0, curvature=0.1)
        assert grip == 1.0
        assert wear == 1.0

    def test_dirty_air_in_corner_reduces_grip(self) -> None:
        """Gap=0.5, curvature=0.1 -> grip reduced below 1.0."""
        grip, wear = compute_dirty_air_factor(gap_ahead_s=0.5, curvature=0.1)
        assert grip < 1.0

    def test_dirty_air_on_straight_no_grip_penalty(self) -> None:
        """Gap=0.5, curvature=0.0 -> straight, no effect."""
        grip, wear = compute_dirty_air_factor(gap_ahead_s=0.5, curvature=0.0)
        assert grip == 1.0
        assert wear == 1.0

    def test_dirty_air_below_curvature_min_no_effect(self) -> None:
        """Gap=0.5, curvature=0.01 -> below min curvature, no effect."""
        grip, wear = compute_dirty_air_factor(gap_ahead_s=0.5, curvature=0.01)
        assert grip == 1.0
        assert wear == 1.0

    def test_dirty_air_increases_tire_wear(self) -> None:
        """Gap=0.5, curvature=0.1 -> tire wear multiplier > 1.0."""
        grip, wear = compute_dirty_air_factor(gap_ahead_s=0.5, curvature=0.1)
        assert wear > 1.0

    def test_dirty_air_scales_with_gap(self) -> None:
        """Closer gap produces stronger penalty than larger gap."""
        grip_close, wear_close = compute_dirty_air_factor(gap_ahead_s=0.3, curvature=0.1)
        grip_far, wear_far = compute_dirty_air_factor(gap_ahead_s=1.0, curvature=0.1)
        assert grip_close < grip_far
        assert wear_close > wear_far

    def test_dirty_air_beyond_threshold_no_effect(self) -> None:
        """Gap=2.0 is beyond 1.5s threshold -> clean air."""
        grip, wear = compute_dirty_air_factor(gap_ahead_s=2.0, curvature=0.1)
        assert grip == 1.0
        assert wear == 1.0

    def test_dirty_air_maximum_penalty(self) -> None:
        """Gap=0.0, curvature=0.1 -> maximum penalty, grip ~0.92."""
        grip, wear = compute_dirty_air_factor(gap_ahead_s=0.0, curvature=0.1)
        assert abs(grip - 0.92) < 0.001
        assert abs(wear - 1.10) < 0.001
