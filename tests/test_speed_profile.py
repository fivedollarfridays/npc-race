"""Tests for track speed profile (T19.1)."""

from engine.speed_profile import compute_speed_profile, get_profile_speed
from engine.track_gen import interpolate_track, compute_track_data
from tracks import get_track


def _monza_profile():
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    distances, curvatures, track_length = compute_track_data(pts)
    car = {"power": 0.625, "grip": 0.625, "weight": 0.375}
    profile = compute_speed_profile(pts, curvatures, distances, track_length, car)
    return profile, distances, track_length, curvatures


class TestSpeedProfile:
    def test_profile_length_matches_track(self):
        profile, distances, _, curvs = _monza_profile()
        assert len(profile) == len(curvs)

    def test_straight_track_high_speed(self):
        from engine.track_gen import interpolate_track, compute_track_data
        pts = [(0, 0), (100, 0), (200, 0), (300, 0)]  # dead straight
        pts_interp = interpolate_track(pts, resolution=50)
        d, c, tl = compute_track_data(pts_interp)
        car = {"power": 0.5, "grip": 0.5, "weight": 0.5}
        profile = compute_speed_profile(pts_interp, c, d, tl, car)
        assert max(profile) > 200

    def test_corner_reduces_speed(self):
        profile, _, _, curvatures = _monza_profile()
        max_curv_idx = curvatures.index(max(curvatures))
        straight_speed = max(profile)
        corner_speed = profile[max_curv_idx]
        assert corner_speed < straight_speed

    def test_braking_before_corner(self):
        profile, _, _, curvatures = _monza_profile()
        max_curv_idx = curvatures.index(max(curvatures))
        if max_curv_idx > 5:
            before = profile[max_curv_idx - 5]
            at_corner = profile[max_curv_idx]
            assert before >= at_corner  # speed decreasing into corner

    def test_monza_max_speed_realistic(self):
        profile, _, _, _ = _monza_profile()
        assert max(profile) <= 355

    def test_monza_min_speed_realistic(self):
        profile, _, _, _ = _monza_profile()
        assert min(profile) >= 50
        assert min(profile) <= 150

    def test_get_profile_speed(self):
        profile, distances, tl, _ = _monza_profile()
        speed = get_profile_speed(profile, 100.0, distances, tl)
        assert isinstance(speed, float)
        assert speed > 0
