"""Tests for cross-race data persistence infrastructure (T4.2)."""

import json
import os
import sys
import tempfile
from unittest.mock import patch

from car_template import load_data, save_data
from engine.race_runner import run_race
from engine.replay import _compute_positions
from engine.simulation import RaceSim
from engine.track_gen import generate_track, interpolate_track
from play import main as play_main


def _make_cars(n=2):
    """Create minimal car dicts for testing."""
    cars = []
    for i in range(n):
        cars.append({
            "CAR_NAME": f"Car{i}",
            "CAR_COLOR": "#ff0000",
            "POWER": 20, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
            "strategy": lambda state: {"throttle": 1.0},
        })
    return cars


def _make_track():
    """Generate a simple track for testing."""
    control = generate_track(seed=42, num_points=8)
    return interpolate_track(control, resolution=100)


# --- Cycle 1: build_strategy_state includes data_file and race_number ---

class TestStrategyStateDataFields:
    """build_strategy_state returns data_file and race_number keys."""

    def test_data_file_none_when_no_car_data_dir(self):
        cars = _make_cars()
        track = _make_track()
        sim = RaceSim(cars, track, laps=1, seed=42)
        positions = _compute_positions(sim.states)
        state = sim.build_strategy_state(sim.states[0], positions)
        assert "data_file" in state
        assert state["data_file"] is None

    def test_data_file_correct_path_when_car_data_dir_set(self):
        cars = _make_cars()
        track = _make_track()
        sim = RaceSim(cars, track, laps=1, seed=42, car_data_dir="/tmp/race_data")
        positions = _compute_positions(sim.states)
        state = sim.build_strategy_state(sim.states[0], positions)
        assert state["data_file"] == "/tmp/race_data/Car0.json"

    def test_data_file_uses_car_name(self):
        cars = _make_cars()
        track = _make_track()
        sim = RaceSim(cars, track, laps=1, seed=42, car_data_dir="/tmp/data")
        positions = _compute_positions(sim.states)
        state = sim.build_strategy_state(sim.states[1], positions)
        assert state["data_file"] == "/tmp/data/Car1.json"

    def test_race_number_defaults_to_1(self):
        cars = _make_cars()
        track = _make_track()
        sim = RaceSim(cars, track, laps=1, seed=42)
        positions = _compute_positions(sim.states)
        state = sim.build_strategy_state(sim.states[0], positions)
        assert "race_number" in state
        assert state["race_number"] == 1

    def test_race_number_custom_value(self):
        cars = _make_cars()
        track = _make_track()
        sim = RaceSim(cars, track, laps=1, seed=42, race_number=5)
        positions = _compute_positions(sim.states)
        state = sim.build_strategy_state(sim.states[0], positions)
        assert state["race_number"] == 5

    def test_track_name_in_strategy_state(self):
        cars = _make_cars()
        track = _make_track()
        sim = RaceSim(cars, track, laps=1, seed=42, track_name="monza")
        positions = _compute_positions(sim.states)
        state = sim.build_strategy_state(sim.states[0], positions)
        assert "track_name" in state
        assert state["track_name"] == "monza"

    def test_track_name_none_when_not_set(self):
        cars = _make_cars()
        track = _make_track()
        sim = RaceSim(cars, track, laps=1, seed=42)
        positions = _compute_positions(sim.states)
        state = sim.build_strategy_state(sim.states[0], positions)
        assert "track_name" in state
        assert state["track_name"] is None


# --- Cycle 2: load_data / save_data helpers ---

class TestLoadSaveData:
    """load_data and save_data handle persistence correctly."""

    def test_load_data_returns_empty_for_nonexistent(self):
        result = load_data("/tmp/nonexistent_abc123.json")
        assert result == {}

    def test_load_data_returns_empty_for_none_path(self):
        result = load_data(None)
        assert result == {}

    def test_load_data_returns_data_for_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False) as f:
            json.dump({"wins": 3, "best_lap": 58.2}, f)
            path = f.name
        try:
            result = load_data(path)
            assert result == {"wins": 3, "best_lap": 58.2}
        finally:
            os.unlink(path)

    def test_load_data_returns_empty_for_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False) as f:
            f.write("not valid json {{{")
            path = f.name
        try:
            result = load_data(path)
            assert result == {}
        finally:
            os.unlink(path)

    def test_save_data_creates_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "car.json")
            save_data(path, {"wins": 1})
            assert os.path.exists(path)
            with open(path) as f:
                data = json.load(f)
            assert data == {"wins": 1}

    def test_save_data_noop_for_none_path(self):
        # Should not raise
        save_data(None, {"wins": 1})

    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "car.json")
            original = {"race_1": {"position": 3, "laps": [60.1, 59.8]}}
            save_data(path, original)
            loaded = load_data(path)
            assert loaded == original


# --- Cycle 3: run_race passes car_data_dir, creates directory ---

class TestRunRaceDataDir:
    """run_race creates data directory and passes params to RaceSim."""

    def test_run_race_creates_data_dir(self):
        with tempfile.TemporaryDirectory() as d:
            data_dir = os.path.join(d, "race_data")
            assert not os.path.exists(data_dir)
            mock_cars = _make_cars(2)
            with patch("engine.race_runner.load_all_cars", return_value=mock_cars):
                run_race(car_dir="cars", laps=1, track_seed=42,
                         output=os.path.join(d, "replay.json"),
                         car_data_dir=data_dir)
            assert os.path.isdir(data_dir)

    def test_run_race_without_data_dir_backward_compat(self):
        """run_race works without car_data_dir (backward compatible)."""
        mock_cars = _make_cars(2)
        with tempfile.TemporaryDirectory() as d:
            with patch("engine.race_runner.load_all_cars", return_value=mock_cars):
                run_race(car_dir="cars", laps=1, track_seed=42,
                         output=os.path.join(d, "replay.json"))

    def test_run_race_passes_race_number_to_sim(self):
        """run_race forwards race_number to RaceSim."""
        mock_cars = _make_cars(2)
        with tempfile.TemporaryDirectory() as d:
            with patch("engine.race_runner.load_all_cars", return_value=mock_cars), \
                 patch("engine.race_runner.RaceSim") as mock_sim:
                mock_sim.return_value.run.return_value = []
                mock_sim.return_value.export_replay.return_value = {"frames": []}
                run_race(car_dir="cars", laps=1, track_seed=42,
                         output=os.path.join(d, "replay.json"),
                         race_number=3)
                # Check RaceSim was called with race_number=3
                _, kwargs = mock_sim.call_args
                assert kwargs.get("race_number") == 3


# --- Cycle 4: play.py --data-dir argument ---

class TestPlayDataDir:
    """play.py passes --data-dir to run_race."""

    def test_play_passes_data_dir_to_run_race(self):
        with patch("engine.race_runner.load_all_cars", return_value=_make_cars(2)), \
             patch("engine.race_runner.RaceSim") as mock_sim:
            mock_sim.return_value.run.return_value = []
            mock_sim.return_value.export_replay.return_value = {"frames": []}
            with tempfile.TemporaryDirectory() as d:
                data_dir = os.path.join(d, "data")
                replay_out = os.path.join(d, "replay.json")
                test_args = [
                    "play.py", "--car-dir", "cars", "--laps", "1",
                    "--no-browser", "--output", replay_out,
                    "--data-dir", data_dir,
                ]
                with patch.object(sys, "argv", test_args), \
                     patch("os.path.isdir", return_value=True):
                    play_main()
                _, kwargs = mock_sim.call_args
                assert kwargs.get("car_data_dir") == data_dir

    def test_play_default_no_data_dir(self):
        """Without --data-dir, car_data_dir is None."""
        with patch("engine.race_runner.load_all_cars", return_value=_make_cars(2)), \
             patch("engine.race_runner.RaceSim") as mock_sim:
            mock_sim.return_value.run.return_value = []
            mock_sim.return_value.export_replay.return_value = {"frames": []}
            with tempfile.TemporaryDirectory() as d:
                replay_out = os.path.join(d, "replay.json")
                test_args = [
                    "play.py", "--car-dir", "cars", "--laps", "1",
                    "--no-browser", "--output", replay_out,
                ]
                with patch.object(sys, "argv", test_args), \
                     patch("os.path.isdir", return_value=True):
                    play_main()
                _, kwargs = mock_sim.call_args
                assert kwargs.get("car_data_dir") is None
