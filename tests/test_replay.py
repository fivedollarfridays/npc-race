"""Tests for engine.replay — extracted replay/results helpers."""

import math

from engine.replay import record_frame, get_results, export_replay
from engine.track_gen import compute_track_headings


class TestComputeTrackHeadings:
    """Test heading computation for track points."""

    def test_square_track_headings(self):
        """A square track should have headings at 0, -pi/2, pi, pi/2."""
        track = [(0, 0), (100, 0), (100, 100), (0, 100)]
        headings = compute_track_headings(track)
        assert len(headings) == 4
        # (0,0)->(100,0): heading = atan2(0,100) = 0
        assert abs(headings[0] - 0.0) < 0.01
        # (100,0)->(100,100): heading = atan2(100,0) = pi/2
        assert abs(headings[1] - math.pi / 2) < 0.01
        # (100,100)->(0,100): heading = atan2(0,-100) = pi
        assert abs(headings[2] - math.pi) < 0.01
        # (0,100)->(0,0): heading = atan2(-100,0) = -pi/2
        assert abs(headings[3] - (-math.pi / 2)) < 0.01

    def test_heading_count_matches_track_length(self):
        """Number of headings must equal number of track points."""
        track = [(0, 0), (10, 0), (20, 5), (15, 15), (5, 10)]
        headings = compute_track_headings(track)
        assert len(headings) == len(track)

    def test_headings_are_floats(self):
        """All heading values should be floats."""
        track = [(0, 0), (100, 0), (100, 100)]
        headings = compute_track_headings(track)
        for h in headings:
            assert isinstance(h, float)


class TestRecordFrame:
    """Test the frame recording function."""

    def test_record_frame_returns_list(self):
        track = [(0, 0), (100, 0), (100, 100), (0, 100)]
        states = [
            {
                "car_idx": 0,
                "name": "TestCar",
                "color": "#ff0000",
                "speed": 50.0,
                "lap": 0,
                "distance": 10.0,
                "lateral": 0.0,
                "tire_wear": 0.0,
                "boost_active": 0,
                "finished": False,
            }
        ]
        positions = {0: 1}
        frame = record_frame(
            states=states,
            positions=positions,
            track=track,
            distances=[0.0, 100.0, 200.0, 300.0],
            track_length=400.0,
            track_width=50,
        )
        assert isinstance(frame, list)
        assert len(frame) == 1

    def test_record_frame_has_required_keys(self):
        track = [(0, 0), (100, 0), (100, 100), (0, 100)]
        states = [
            {
                "car_idx": 0,
                "name": "TestCar",
                "color": "#ff0000",
                "speed": 50.0,
                "lap": 0,
                "distance": 10.0,
                "lateral": 0.0,
                "tire_wear": 0.0,
                "boost_active": 0,
                "finished": False,
            }
        ]
        positions = {0: 1}
        frame = record_frame(
            states=states,
            positions=positions,
            track=track,
            distances=[0.0, 100.0, 200.0, 300.0],
            track_length=400.0,
            track_width=50,
        )
        entry = frame[0]
        for key in ("x", "y", "name", "color", "speed", "lap", "position",
                     "tire_wear", "boost", "finished", "seg"):
            assert key in entry, f"Missing key: {key}"

    def test_record_frame_seg_is_valid_index(self):
        """seg should be an integer index into the track."""
        track = [(0, 0), (100, 0), (100, 100), (0, 100)]
        states = [
            {
                "car_idx": 0,
                "name": "TestCar",
                "color": "#ff0000",
                "speed": 50.0,
                "lap": 0,
                "distance": 150.0,  # should be in segment 1
                "lateral": 0.0,
                "tire_wear": 0.0,
                "boost_active": 0,
                "finished": False,
            }
        ]
        positions = {0: 1}
        frame = record_frame(
            states=states,
            positions=positions,
            track=track,
            distances=[0.0, 100.0, 200.0, 300.0],
            track_length=400.0,
            track_width=50,
        )
        entry = frame[0]
        assert isinstance(entry["seg"], int)
        assert 0 <= entry["seg"] < len(track)


class TestGetResults:
    """Test the results extraction function."""

    def test_get_results_sorted_by_position(self):
        states = [
            {"car_idx": 0, "name": "A", "color": "#ff0000", "lap": 1,
             "distance": 100, "finished": True, "finish_tick": 200},
            {"car_idx": 1, "name": "B", "color": "#00ff00", "lap": 1,
             "distance": 100, "finished": True, "finish_tick": 150},
        ]
        results = get_results(states, len(states))
        assert results[0]["name"] == "B"
        assert results[1]["name"] == "A"

    def test_get_results_has_required_fields(self):
        states = [
            {"car_idx": 0, "name": "A", "color": "#ff0000", "lap": 1,
             "distance": 100, "finished": True, "finish_tick": 200},
        ]
        results = get_results(states, len(states))
        for key in ("name", "color", "position", "finish_tick", "finished"):
            assert key in results[0]


class TestExportReplay:
    """Test the replay export function."""

    def test_export_replay_has_track_name(self):
        replay = export_replay(
            track=[(0, 0), (100, 0)],
            track_width=50,
            track_name="monza",
            laps=3,
            ticks_per_sec=30,
            history=[],
            states=[],
            num_cars=0,
        )
        assert replay["track_name"] == "monza"

    def test_export_replay_has_all_keys(self):
        replay = export_replay(
            track=[(0, 0), (100, 0)],
            track_width=50,
            track_name="monza",
            laps=3,
            ticks_per_sec=30,
            history=[],
            states=[],
            num_cars=0,
            track_curvatures=[0.1, 0.2],
            track_headings=[0.0, 1.57],
        )
        for key in ("track", "track_width", "track_name", "laps",
                     "ticks_per_sec", "frames", "results", "car_count",
                     "track_curvatures", "track_headings"):
            assert key in replay

    def test_export_replay_curvatures_length(self):
        """track_curvatures length must match track length."""
        track = [(0, 0), (100, 0), (100, 100), (0, 100)]
        curvatures = [0.1, 0.2, 0.3, 0.4]
        headings = [0.0, 1.57, 3.14, -1.57]
        replay = export_replay(
            track=track,
            track_width=50,
            track_name="test",
            laps=3,
            ticks_per_sec=30,
            history=[],
            states=[],
            num_cars=0,
            track_curvatures=curvatures,
            track_headings=headings,
        )
        assert len(replay["track_curvatures"]) == len(track)

    def test_export_replay_headings_length(self):
        """track_headings length must match track length."""
        track = [(0, 0), (100, 0), (100, 100), (0, 100)]
        curvatures = [0.1, 0.2, 0.3, 0.4]
        headings = [0.0, 1.57, 3.14, -1.57]
        replay = export_replay(
            track=track,
            track_width=50,
            track_name="test",
            laps=3,
            ticks_per_sec=30,
            history=[],
            states=[],
            num_cars=0,
            track_curvatures=curvatures,
            track_headings=headings,
        )
        assert len(replay["track_headings"]) == len(track)

    def test_export_replay_curvatures_rounded(self):
        """Curvatures should be rounded to 4 decimal places."""
        track = [(0, 0), (100, 0)]
        replay = export_replay(
            track=track,
            track_width=50,
            track_name="test",
            laps=1,
            ticks_per_sec=30,
            history=[],
            states=[],
            num_cars=0,
            track_curvatures=[0.123456789, 0.987654321],
            track_headings=[0.0, 1.0],
        )
        for val in replay["track_curvatures"]:
            # Check rounding: at most 4 decimal places
            assert val == round(val, 4)

    def test_export_replay_headings_rounded(self):
        """Headings should be rounded to 4 decimal places."""
        track = [(0, 0), (100, 0)]
        replay = export_replay(
            track=track,
            track_width=50,
            track_name="test",
            laps=1,
            ticks_per_sec=30,
            history=[],
            states=[],
            num_cars=0,
            track_curvatures=[0.1, 0.2],
            track_headings=[1.234567890, 2.345678901],
        )
        for val in replay["track_headings"]:
            assert val == round(val, 4)
