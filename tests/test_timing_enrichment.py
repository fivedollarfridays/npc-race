"""Tests for T6.5: Timing + gaps enrichment in replay frames and results."""

import json
import pytest

from engine import run_race

pytestmark = pytest.mark.smoke


def _run_short_race(tmp_path, **kwargs):
    """Run a short race and return the parsed replay dict."""
    output = str(tmp_path / "replay.json")
    kwargs["output"] = output
    kwargs.setdefault("car_dir", "cars")
    run_race(**kwargs)
    with open(output) as f:
        return json.load(f)


class TestFrameTimingFields:
    """Replay frames must contain timing data for each car."""

    def test_frame_has_elapsed_s(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for tick_frames in replay["frames"]:
            for car in tick_frames:
                assert "elapsed_s" in car
                assert isinstance(car["elapsed_s"], (int, float))

    def test_frame_has_gap_ahead_s(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for tick_frames in replay["frames"]:
            for car in tick_frames:
                assert "gap_ahead_s" in car

    def test_frame_has_current_sector(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for tick_frames in replay["frames"]:
            for car in tick_frames:
                assert "current_sector" in car
                assert car["current_sector"] in (0, 1, 2)

    def test_elapsed_s_increases(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        # Check that elapsed_s generally increases across frames
        if len(replay["frames"]) > 1:
            first = replay["frames"][0][0]["elapsed_s"]
            last = replay["frames"][-1][0]["elapsed_s"]
            assert last > first


class TestResultTimingFields:
    """Race results must contain timing summary data."""

    def test_results_have_total_time(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for r in replay["results"]:
            assert "total_time_s" in r
            if r["finished"]:
                assert r["total_time_s"] > 0

    def test_results_have_best_lap(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for r in replay["results"]:
            assert "best_lap_s" in r

    def test_results_have_lap_times(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for r in replay["results"]:
            assert "lap_times" in r
            assert isinstance(r["lap_times"], list)

    def test_results_have_pit_stops(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for r in replay["results"]:
            assert "pit_stops" in r


class TestStrategyStateTimingFields:
    """Strategy state passed to cars must include timing info."""

    def test_strategy_state_has_elapsed_s(self, tmp_path):
        """Verify elapsed_s is in strategy state by checking it flows to frames."""
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        # If elapsed_s is in frames, it was computed during simulation
        mid = len(replay["frames"]) // 2
        assert replay["frames"][mid][0]["elapsed_s"] > 0


class TestDashboardFields:
    """T8.1: New replay frame fields for pit wall dashboard."""

    def test_frame_has_gap_behind_s(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for tick in replay["frames"][:50]:
            for car in tick:
                assert "gap_behind_s" in car

    def test_frame_has_last_lap_time(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=3)
        # After lap 1, at least some frames should have a last_lap_time
        found = False
        for tick in replay["frames"][3000:]:
            for car in tick:
                if car.get("last_lap_time") is not None:
                    found = True
                    break
        assert found, "No frame with last_lap_time found after lap 1"

    def test_frame_has_best_lap_s(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=3)
        found = any(
            car.get("best_lap_s") is not None
            for tick in replay["frames"][3000:]
            for car in tick
        )
        assert found, "No frame with best_lap_s found"

    def test_frame_has_tire_age_laps(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for tick in replay["frames"][:50]:
            for car in tick:
                assert "tire_age_laps" in car
                assert isinstance(car["tire_age_laps"], int)

    def test_frame_has_pit_stops(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for tick in replay["frames"][:50]:
            for car in tick:
                assert "pit_stops" in car
                assert isinstance(car["pit_stops"], int)

    def test_frame_has_dirty_air_factor(self, tmp_path):
        replay = _run_short_race(tmp_path, track_name="monza", laps=2)
        for tick in replay["frames"][:50]:
            for car in tick:
                assert "dirty_air_factor" in car
                assert isinstance(car["dirty_air_factor"], (int, float))
