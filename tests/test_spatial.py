"""Tests for spatial neighbor lookup (T34.5).

Validates SortedCarIndex provides O(1) neighbor lookup
with identical results to O(n^2) brute-force loops.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _make_state(car_idx, distance, finished=False, speed=100.0, lateral=0.0):
    """Create a minimal car state dict for spatial tests."""
    return {
        "car_idx": car_idx,
        "distance": distance,
        "finished": finished,
        "speed": speed,
        "lateral": lateral,
    }


class TestSortedCarIndexConstruction:
    """Cycle 1: Basic construction and neighbor lookup."""

    def test_sorts_by_distance(self):
        from engine.spatial import SortedCarIndex
        states = [_make_state(0, 100.0), _make_state(1, 50.0), _make_state(2, 200.0)]
        idx = SortedCarIndex(states)
        # Internal sorted order should be by distance
        assert idx._distances == [50.0, 100.0, 200.0]

    def test_neighbors_returns_cars_within_range(self):
        from engine.spatial import SortedCarIndex
        states = [
            _make_state(0, 100.0),
            _make_state(1, 120.0),
            _make_state(2, 500.0),
        ]
        idx = SortedCarIndex(states)
        neighbors = idx.neighbors(0, max_distance=40.0)
        car_idxs = [n["car_idx"] for n in neighbors]
        assert 1 in car_idxs
        assert 2 not in car_idxs

    def test_neighbors_excludes_self(self):
        from engine.spatial import SortedCarIndex
        states = [_make_state(0, 100.0), _make_state(1, 105.0)]
        idx = SortedCarIndex(states)
        neighbors = idx.neighbors(0, max_distance=50.0)
        car_idxs = [n["car_idx"] for n in neighbors]
        assert 0 not in car_idxs
        assert 1 in car_idxs

    def test_neighbors_excludes_finished_cars(self):
        from engine.spatial import SortedCarIndex
        states = [
            _make_state(0, 100.0),
            _make_state(1, 110.0, finished=True),
            _make_state(2, 115.0),
        ]
        idx = SortedCarIndex(states)
        neighbors = idx.neighbors(0, max_distance=50.0)
        car_idxs = [n["car_idx"] for n in neighbors]
        assert 1 not in car_idxs
        assert 2 in car_idxs

    def test_neighbors_empty_when_all_far(self):
        from engine.spatial import SortedCarIndex
        states = [_make_state(0, 0.0), _make_state(1, 1000.0)]
        idx = SortedCarIndex(states)
        neighbors = idx.neighbors(0, max_distance=40.0)
        assert neighbors == []

    def test_neighbors_both_directions(self):
        """Cars both ahead and behind should be returned."""
        from engine.spatial import SortedCarIndex
        states = [
            _make_state(0, 100.0),
            _make_state(1, 80.0),   # behind
            _make_state(2, 120.0),  # ahead
        ]
        idx = SortedCarIndex(states)
        neighbors = idx.neighbors(0, max_distance=25.0)
        car_idxs = sorted(n["car_idx"] for n in neighbors)
        assert car_idxs == [1, 2]

    def test_single_car_no_neighbors(self):
        from engine.spatial import SortedCarIndex
        states = [_make_state(0, 100.0)]
        idx = SortedCarIndex(states)
        assert idx.neighbors(0, max_distance=100.0) == []


class TestDraftingEquivalence:
    """Cycle 2: Spatial drafting produces same result as brute-force."""

    def test_drafting_identical_results(self):
        """Drafting bonus via spatial index matches O(n^2) loop."""
        from engine.physics import compute_draft_bonus, MAX_SPEED
        from engine.spatial import SortedCarIndex

        states = [
            _make_state(0, 100.0, speed=200.0),
            _make_state(1, 120.0, speed=210.0),  # 20 ahead
            _make_state(2, 500.0, speed=190.0),  # far away
            _make_state(3, 130.0, speed=205.0),  # 30 ahead
        ]
        aero = 0.5
        dt = 1.0 / 30.0

        # Old brute-force approach
        bonus_old = 0.0
        for other in states:
            if other["car_idx"] == 0 or other["finished"]:
                continue
            dist_ahead = other["distance"] - states[0]["distance"]
            bonus_old += compute_draft_bonus(aero, dist_ahead, dt)

        # New spatial approach
        idx = SortedCarIndex(states)
        bonus_new = 0.0
        for other in idx.neighbors(0, max_distance=40.0):
            dist_ahead = other["distance"] - states[0]["distance"]
            bonus_new += compute_draft_bonus(aero, dist_ahead, dt)

        assert abs(bonus_old - bonus_new) < 1e-10

    def test_lateral_push_identical_results(self):
        """Lateral push via spatial index matches O(n^2) loop."""
        from engine.physics import compute_lateral_push
        from engine.spatial import SortedCarIndex

        states = [
            _make_state(0, 100.0, lateral=0.2),
            _make_state(1, 105.0, lateral=0.1),   # close
            _make_state(2, 500.0, lateral=-0.3),   # far
            _make_state(3, 103.0, lateral=0.3),    # close
        ]
        dt = 1.0 / 30.0

        # Old brute-force
        push_old = 0.0
        for other in states:
            if other["car_idx"] == 0 or other["finished"]:
                continue
            dist = abs(other["distance"] - states[0]["distance"])
            push_old += compute_lateral_push(
                states[0]["lateral"] - other["lateral"], dist, dt)

        # New spatial
        idx = SortedCarIndex(states)
        push_new = 0.0
        for other in idx.neighbors(0, max_distance=10.0):
            dist = abs(other["distance"] - states[0]["distance"])
            push_new += compute_lateral_push(
                states[0]["lateral"] - other["lateral"], dist, dt)

        assert abs(push_old - push_new) < 1e-10
