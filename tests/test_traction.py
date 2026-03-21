"""Tests for traction limits (T22.2)."""

from engine.chassis_physics import compute_traction_limit, apply_traction_circle


class TestTractionLimit:
    def test_traction_from_weight_only(self):
        limit = compute_traction_limit(1.4, 800, 0)
        expected = 1.4 * 800 * 9.81
        assert abs(limit - expected) < 1

    def test_downforce_increases_traction(self):
        no_df = compute_traction_limit(1.4, 800, 0)
        with_df = compute_traction_limit(1.4, 800, 5000)
        assert with_df > no_df

    def test_higher_mu_more_traction(self):
        low = compute_traction_limit(1.0, 800, 0)
        high = compute_traction_limit(1.8, 800, 0)
        assert high > low


class TestTractionCircle:
    def test_no_lateral_full_longitudinal(self):
        force = apply_traction_circle(5000, 0, 10000, 800)
        assert force == 5000  # under limit

    def test_lateral_reduces_longitudinal(self):
        full = apply_traction_circle(8000, 0, 10000, 800)
        reduced = apply_traction_circle(8000, 2.0, 10000, 800)
        assert reduced < full

    def test_clamped_when_over_limit(self):
        force = apply_traction_circle(20000, 0, 10000, 800)
        assert force <= 10000

    def test_braking_clamped_too(self):
        force = apply_traction_circle(-20000, 0, 10000, 800)
        assert force >= -10000

    def test_high_lateral_kills_longitudinal(self):
        # If lateral force nearly equals traction limit
        limit = compute_traction_limit(1.4, 800, 0)
        high_lat_g = limit / (800 * 9.81) * 0.95  # 95% of grip used laterally
        force = apply_traction_circle(5000, high_lat_g, limit, 800)
        assert abs(force) < 4000  # significantly reduced from 5000 requested
