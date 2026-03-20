"""Tests for racing line model (T19.2)."""

from engine.racing_line import compute_racing_line
from engine.track_gen import interpolate_track, compute_track_data, compute_track_headings
from tracks import get_track


def _monza_line():
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    d, c, tl = compute_track_data(pts)
    h = compute_track_headings(pts)
    line = compute_racing_line(pts, c, h)
    return line, d, tl, c


class TestRacingLine:
    def test_line_length_matches_track(self):
        line, _, _, curvs = _monza_line()
        assert len(line) == len(curvs)

    def test_straight_section_centered(self):
        line, _, _, curvs = _monza_line()
        straights = [line[i] for i in range(len(curvs)) if curvs[i] < 0.005]
        if straights:
            avg = sum(abs(s) for s in straights) / len(straights)
            assert avg < 0.3  # mostly centered

    def test_corner_goes_inside(self):
        line, _, _, curvs = _monza_line()
        corners = [abs(line[i]) for i in range(len(curvs)) if curvs[i] > 0.05]
        if corners:
            avg = sum(corners) / len(corners)
            assert avg > 0.2  # moves off center

    def test_lateral_range(self):
        line, _, _, _ = _monza_line()
        for val in line:
            assert -1.0 <= val <= 1.0

    def test_smooth_transitions(self):
        line, _, _, _ = _monza_line()
        for i in range(1, len(line)):
            assert abs(line[i] - line[i - 1]) < 0.4  # no sudden jumps
