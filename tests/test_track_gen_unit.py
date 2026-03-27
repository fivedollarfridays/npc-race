"""Unit tests for engine/track_gen.py — track generation and curvature lookup."""

from engine.track_gen import (
    CurvatureLookup,
    compute_track_data,
    generate_track,
    get_curvature_at,
    interpolate_track,
)


class TestInterpolateTrack:
    """Tests for Catmull-Rom spline interpolation."""

    def test_returns_list_of_xy_tuples(self):
        control = [(0, 0), (100, 0), (100, 100), (0, 100)]
        result = interpolate_track(control, resolution=100)
        assert isinstance(result, list)
        assert len(result) > 0
        for pt in result:
            assert isinstance(pt, tuple)
            assert len(pt) == 2

    def test_output_length_matches_resolution(self):
        control = [(0, 0), (100, 0), (100, 100), (0, 100)]
        result = interpolate_track(control, resolution=200)
        # Each of 4 segments gets resolution // n = 50 points
        assert len(result) == 200

    def test_different_seeds_produce_different_tracks(self):
        cp1 = generate_track(seed=1, num_points=6)
        cp2 = generate_track(seed=99, num_points=6)
        t1 = interpolate_track(cp1)
        t2 = interpolate_track(cp2)
        assert t1 != t2


class TestCurvatureLookup:
    """Tests for CurvatureLookup bisect-based access."""

    def _make_lookup(self):
        control = generate_track(seed=42, num_points=8)
        track = interpolate_track(control, resolution=200)
        distances, curvatures, total_length = compute_track_data(track)
        return CurvatureLookup(distances, curvatures, total_length), distances, curvatures, total_length

    def test_getitem_returns_float(self):
        lookup, *_ = self._make_lookup()
        val = lookup[0.0]
        assert isinstance(val, float)

    def test_wraps_beyond_track_length(self):
        lookup, _, _, total_length = self._make_lookup()
        val_at_zero = lookup[0.0]
        val_at_wrap = lookup[total_length]
        # Wrapping should return the same curvature region
        assert abs(val_at_zero - val_at_wrap) < 0.01

    def test_matches_get_curvature_at(self):
        lookup, distances, curvatures, total_length = self._make_lookup()
        test_distances = [0.0, total_length * 0.25, total_length * 0.5, total_length * 0.75]
        for d in test_distances:
            expected = get_curvature_at(d, distances, curvatures, total_length)
            actual = lookup[d]
            assert abs(actual - expected) < 1e-9, f"Mismatch at d={d}: {actual} vs {expected}"


class TestGetCurvatureAt:
    """Tests for linear-scan curvature lookup."""

    def test_returns_zero_for_out_of_range(self):
        # distances = [0, 10, 20], curvatures = [0.1, 0.2, 0.3], length = 25
        val = get_curvature_at(22.0, [0, 10, 20], [0.1, 0.2, 0.3], 25)
        assert val == 0.0

    def test_returns_correct_segment(self):
        val = get_curvature_at(5.0, [0, 10, 20], [0.1, 0.2, 0.3], 25)
        assert val == 0.1

    def test_wraps_negative_distance(self):
        val = get_curvature_at(-5.0, [0, 10, 20], [0.1, 0.2, 0.3], 25)
        # -5 % 25 = 20, which is at the boundary of last segment
        assert isinstance(val, float)


class TestGenerateTrack:
    """Tests for random control point generation."""

    def test_returns_correct_number_of_points(self):
        pts = generate_track(seed=1, num_points=10)
        assert len(pts) == 10

    def test_deterministic_with_same_seed(self):
        a = generate_track(seed=42, num_points=8)
        b = generate_track(seed=42, num_points=8)
        assert a == b
