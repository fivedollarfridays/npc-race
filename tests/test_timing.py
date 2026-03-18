"""Tests for engine/timing.py — lap timing, sector splits, fastest lap."""

from engine.timing import (
    CarTiming, create_timing, update_timing,
    get_sector_boundaries, get_fastest_lap, get_timing_summary,
    SECTOR_BOUNDARIES,
)


class TestCarTiming:
    def test_create_timing_initializes_all_cars(self):
        timings = create_timing(["CarA", "CarB", "CarC"])
        assert len(timings) == 3
        assert "CarA" in timings
        assert isinstance(timings["CarA"], CarTiming)
        assert timings["CarA"].lap_times == []

    def test_create_timing_empty_list(self):
        timings = create_timing([])
        assert len(timings) == 0


class TestUpdateTiming:
    def test_detects_lap_completion(self):
        timings = create_timing(["Car"])
        # Simulate: car on lap 0, then crosses to lap 1
        r = update_timing(timings, "Car", 0.5, 0, 0, 30, SECTOR_BOUNDARIES)
        assert r["lap_completed"] is False
        # Cross to lap 1 at tick 2400
        r = update_timing(timings, "Car", 0.01, 1, 2400, 30, SECTOR_BOUNDARIES)
        assert r["lap_completed"] is True
        assert r["lap_time"] is not None
        assert r["lap_time"] == 2400 / 30  # 80 seconds

    def test_records_lap_time(self):
        timings = create_timing(["Car"])
        update_timing(timings, "Car", 0.5, 0, 0, 30, SECTOR_BOUNDARIES)
        update_timing(timings, "Car", 0.01, 1, 2400, 30, SECTOR_BOUNDARIES)
        assert len(timings["Car"].lap_times) == 1
        assert timings["Car"].lap_times[0] == 80.0

    def test_detects_sector_change(self):
        timings = create_timing(["Car"])
        # Start in sector 0
        r = update_timing(timings, "Car", 0.1, 0, 0, 30, SECTOR_BOUNDARIES)
        assert r["current_sector"] == 0
        # Cross into sector 1 (past 33.3%)
        r = update_timing(timings, "Car", 0.4, 0, 800, 30, SECTOR_BOUNDARIES)
        assert r["sector_completed"] is True
        assert r["current_sector"] == 1

    def test_records_sector_time(self):
        timings = create_timing(["Car"])
        update_timing(timings, "Car", 0.1, 0, 0, 30, SECTOR_BOUNDARIES)
        r = update_timing(timings, "Car", 0.4, 0, 800, 30, SECTOR_BOUNDARIES)
        assert r["sector_time"] is not None
        assert r["sector_time"] > 0

    def test_best_lap_tracks_minimum(self):
        timings = create_timing(["Car"])
        # Lap 0->1 at 80s
        update_timing(timings, "Car", 0.5, 0, 0, 30, SECTOR_BOUNDARIES)
        update_timing(timings, "Car", 0.01, 1, 2400, 30, SECTOR_BOUNDARIES)
        # Lap 1->2 at 78s (faster)
        update_timing(timings, "Car", 0.01, 2, 4740, 30, SECTOR_BOUNDARIES)
        assert timings["Car"].best_lap == 78.0

    def test_elapsed_time_increases(self):
        timings = create_timing(["Car"])
        r1 = update_timing(timings, "Car", 0.1, 0, 0, 30, SECTOR_BOUNDARIES)
        r2 = update_timing(timings, "Car", 0.2, 0, 300, 30, SECTOR_BOUNDARIES)
        assert r2["elapsed_s"] > r1["elapsed_s"]


class TestGetFastestLap:
    def test_returns_none_when_no_laps(self):
        timings = create_timing(["A", "B"])
        assert get_fastest_lap(timings) is None

    def test_returns_correct_car_and_time(self):
        timings = create_timing(["A", "B"])
        # A does lap in 80s
        update_timing(timings, "A", 0.5, 0, 0, 30, SECTOR_BOUNDARIES)
        update_timing(timings, "A", 0.01, 1, 2400, 30, SECTOR_BOUNDARIES)
        # B does lap in 75s
        update_timing(timings, "B", 0.5, 0, 0, 30, SECTOR_BOUNDARIES)
        update_timing(timings, "B", 0.01, 1, 2250, 30, SECTOR_BOUNDARIES)
        result = get_fastest_lap(timings)
        assert result == ("B", 75.0)


class TestGetTimingSummary:
    def test_structure(self):
        timings = create_timing(["A"])
        update_timing(timings, "A", 0.5, 0, 0, 30, SECTOR_BOUNDARIES)
        update_timing(timings, "A", 0.01, 1, 2400, 30, SECTOR_BOUNDARIES)
        summary = get_timing_summary(timings)
        assert len(summary) == 1
        s = summary[0]
        assert s["name"] == "A"
        assert "best_lap" in s
        assert "lap_times" in s


class TestSectorBoundaries:
    def test_default_boundaries(self):
        assert SECTOR_BOUNDARIES == (0.333, 0.666, 1.0)

    def test_custom_boundaries_from_track(self):
        track = {"sector_boundaries": (0.35, 0.65, 1.0)}
        boundaries = get_sector_boundaries(track)
        assert boundaries == (0.35, 0.65, 1.0)

    def test_default_when_no_key(self):
        boundaries = get_sector_boundaries({})
        assert boundaries == SECTOR_BOUNDARIES
