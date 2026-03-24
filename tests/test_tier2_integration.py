"""Integration tests for Sprint 5 -- Tier 2 realism features.

Covers: tire temperature in replay, DRS activation on named tracks,
car setup loading, backward compatibility, and architecture compliance.
"""

import json
import os

import pytest

from engine import run_race

pytestmark = pytest.mark.integration

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARS_DIR = os.path.join(PROJECT_ROOT, "cars")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_race_to_file(tmp_path, **kwargs):
    """Run a race and return parsed replay JSON."""
    output = str(tmp_path / "replay.json")
    kwargs.setdefault("car_dir", CARS_DIR)
    kwargs["output"] = output
    run_race(**kwargs)
    with open(output) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Cycle 1: Tire temperature in replay frames
# ---------------------------------------------------------------------------


class TestTireTemperatureIntegration:
    """Tire temperature appears in every replay frame and behaves correctly."""

    def test_tire_temp_in_every_replay_frame(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=2)
        for i, frame in enumerate(replay["frames"]):
            for car in frame:
                assert "tire_temp" in car, (
                    f"Frame {i}: missing tire_temp for {car['name']}"
                )
                assert isinstance(car["tire_temp"], (int, float)), (
                    f"Frame {i}: tire_temp not numeric for {car['name']}"
                )

    def test_tire_temp_rises_from_cold_start(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=2)
        frames = replay["frames"]
        # Compare first 10 frames vs mid-race frames (not last --
        # finished cars stop updating). Use frames at ~25% through race.
        first_temps = [
            car["tire_temp"]
            for frame in frames[:10]
            for car in frame
        ]
        mid_point = len(frames) // 4
        mid_temps = [
            car["tire_temp"]
            for frame in frames[mid_point:mid_point + 10]
            for car in frame
        ]
        avg_first = sum(first_temps) / len(first_temps)
        avg_mid = sum(mid_temps) / len(mid_temps)
        assert avg_mid > avg_first, (
            f"Tires should warm up: first avg={avg_first:.1f}, "
            f"mid-race avg={avg_mid:.1f}"
        )

    def test_tire_temp_within_bounds(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=2)
        for i, frame in enumerate(replay["frames"]):
            for car in frame:
                assert 20.0 <= car["tire_temp"] <= 150.0, (
                    f"Frame {i}: tire_temp={car['tire_temp']} out of bounds "
                    f"for {car['name']}"
                )


# ---------------------------------------------------------------------------
# Cycle 2: DRS activation in replay frames
# ---------------------------------------------------------------------------


class TestDRSIntegration:
    """DRS fields present in replay and activate on tracks with DRS zones."""

    def test_drs_active_field_in_replay_frames(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=2)
        for i, frame in enumerate(replay["frames"]):
            for car in frame:
                assert "drs_active" in car, (
                    f"Frame {i}: missing drs_active for {car['name']}"
                )
                assert isinstance(car["drs_active"], bool), (
                    f"Frame {i}: drs_active not bool for {car['name']}"
                )

    def test_drs_activates_on_monza(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=3)
        drs_count = sum(
            1
            for frame in replay["frames"]
            for car in frame
            if car["drs_active"]
        )
        assert drs_count >= 1, (
            "Expected at least 1 DRS activation on Monza (has 2 DRS zones)"
        )

    def test_no_drs_on_procedural_track(self, tmp_path):
        replay = _run_race_to_file(
            tmp_path, track_seed=42, laps=2,
        )
        drs_count = sum(
            1
            for frame in replay["frames"]
            for car in frame
            if car.get("drs_active", False)
        )
        assert drs_count == 0, (
            f"Procedural track should have no DRS, found {drs_count} activations"
        )


# ---------------------------------------------------------------------------
# Cycle 3: Setup integration
# ---------------------------------------------------------------------------


class TestSetupIntegration:
    """Car setup loads and races complete with setup-equipped cars."""

    def test_setup_loaded_for_slipstream(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=2)
        # Verify race completed cleanly with all cars (including setup cars)
        assert len(replay["results"]) == 5
        for r in replay["results"]:
            assert r["finished"]

    def test_race_completes_with_mixed_setup_cars(self, tmp_path):
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=2)
        results = replay["results"]
        assert len(results) == 5, (
            f"Expected 5 cars, got {len(results)}"
        )
        for r in results:
            assert r["finished"], f"{r['name']} did not finish"


# ---------------------------------------------------------------------------
# Cycle 4: Backward compatibility
# ---------------------------------------------------------------------------


class TestBackwardCompatibility:
    """Cars without DRS/setup fields still race cleanly."""

    def test_strategy_without_drs_request_runs(self, tmp_path):
        # Real cars already include some without drs_request --
        # verify the race completes without error
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=2)
        assert len(replay["results"]) == 5
        for r in replay["results"]:
            assert r["finished"]

    def test_strategy_without_setup_runs(self, tmp_path):
        # BrickHouse and GlassCanon have no SETUP dict --
        # verify they race cleanly alongside setup cars
        replay = _run_race_to_file(tmp_path, track_name="monza", laps=2)
        assert len(replay["results"]) == 5
        for r in replay["results"]:
            assert r["finished"]


# ---------------------------------------------------------------------------
# Cycle 5: Architecture compliance
# ---------------------------------------------------------------------------


class TestArchCompliance:
    """Architecture gate tests for file size limits."""

    def test_simulation_py_line_count(self):
        with open(os.path.join(PROJECT_ROOT, "engine", "simulation.py")) as f:
            lines = f.readlines()
        assert len(lines) <= 400, (
            f"simulation.py is {len(lines)} lines (limit 400)"
        )

    def test_new_modules_line_count(self):
        limits = {
            "engine/tire_temperature.py": 130,
            "engine/drs_system.py": 130,
            "engine/setup_model.py": 130,
        }
        for path, limit in limits.items():
            full_path = os.path.join(PROJECT_ROOT, path)
            with open(full_path) as f:
                count = len(f.readlines())
            assert count <= limit, (
                f"{path} has {count} lines (limit {limit})"
            )
