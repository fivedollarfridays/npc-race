"""Tests for CurvatureLookup — O(log n) bisect-based curvature lookup."""

from engine.track_gen import get_curvature_at, CurvatureLookup


def _sample_track_data():
    """Return small sample distances/curvatures for testing."""
    distances = [0.0, 10.0, 25.0, 50.0, 80.0]
    curvatures = [0.1, 0.5, 0.2, 0.8, 0.3]
    track_length = 100.0
    return distances, curvatures, track_length


class TestCurvatureLookupBasic:
    """CurvatureLookup matches get_curvature_at for known distances."""

    def test_exact_distance_matches(self):
        distances, curvatures, track_length = _sample_track_data()
        lookup = CurvatureLookup(distances, curvatures, track_length)
        for d in distances:
            expected = get_curvature_at(d, distances, curvatures, track_length)
            assert lookup[d] == expected, f"Mismatch at distance {d}"

    def test_midpoint_distances_match(self):
        distances, curvatures, track_length = _sample_track_data()
        lookup = CurvatureLookup(distances, curvatures, track_length)
        midpoints = [5.0, 17.5, 37.5, 65.0, 90.0]
        for d in midpoints:
            expected = get_curvature_at(d, distances, curvatures, track_length)
            assert lookup[d] == expected, f"Mismatch at distance {d}"

    def test_getitem_interface(self):
        distances, curvatures, track_length = _sample_track_data()
        lookup = CurvatureLookup(distances, curvatures, track_length)
        # Should support bracket notation
        result = lookup[25.0]
        assert isinstance(result, float)


class TestCurvatureLookupWrapping:
    """CurvatureLookup handles wrapping and edge cases."""

    def test_distance_beyond_track_length_wraps(self):
        distances, curvatures, track_length = _sample_track_data()
        lookup = CurvatureLookup(distances, curvatures, track_length)
        # distance 110 should wrap to 10
        assert lookup[110.0] == lookup[10.0]

    def test_distance_zero(self):
        distances, curvatures, track_length = _sample_track_data()
        lookup = CurvatureLookup(distances, curvatures, track_length)
        assert lookup[0.0] == curvatures[0]

    def test_distance_equals_track_length(self):
        distances, curvatures, track_length = _sample_track_data()
        lookup = CurvatureLookup(distances, curvatures, track_length)
        # track_length % track_length == 0 => should return curvatures[0]
        assert lookup[track_length] == lookup[0.0]

    def test_negative_distance_wraps(self):
        distances, curvatures, track_length = _sample_track_data()
        lookup = CurvatureLookup(distances, curvatures, track_length)
        # -10 % 100 = 90 in Python
        expected = get_curvature_at(-10, distances, curvatures, track_length)
        assert lookup[-10.0] == expected

    def test_zero_track_length_no_crash(self):
        distances = [0.0, 10.0]
        curvatures = [0.5, 0.3]
        lookup = CurvatureLookup(distances, curvatures, 0.0)
        # Should not crash; returns some value
        result = lookup[5.0]
        assert isinstance(result, float)


class TestCurvatureLookupRealTrack:
    """CurvatureLookup matches linear scan on realistic track data."""

    def test_all_points_match_on_generated_track(self):
        from engine.track_gen import generate_track, interpolate_track, compute_track_data
        points = generate_track(seed=42)
        track = interpolate_track(points)
        distances, curvatures, track_length = compute_track_data(track)
        lookup = CurvatureLookup(distances, curvatures, track_length)

        # Test every 10th distance point
        for i in range(0, len(distances), 10):
            d = distances[i]
            expected = get_curvature_at(d, distances, curvatures, track_length)
            assert lookup[d] == expected, f"Mismatch at index {i}, distance {d}"

    def test_arbitrary_distances_match_on_generated_track(self):
        from engine.track_gen import generate_track, interpolate_track, compute_track_data
        points = generate_track(seed=99)
        track = interpolate_track(points)
        distances, curvatures, track_length = compute_track_data(track)
        lookup = CurvatureLookup(distances, curvatures, track_length)

        import random
        rng = random.Random(123)
        for _ in range(50):
            d = rng.uniform(0, track_length * 2)  # includes wrapping
            expected = get_curvature_at(d, distances, curvatures, track_length)
            assert lookup[d] == expected, f"Mismatch at distance {d}"
