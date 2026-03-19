"""Tests for engine module decomposition (T1.2).

Verifies that engine.py is properly split into focused modules
under 400 lines each, with backward-compatible imports.
"""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Cycle 1: Track generation spoke ─────────────────────────────────────────

class TestTrackGen:
    """Track generation functions live in engine.track_gen."""

    def test_generate_track_importable(self):
        from engine.track_gen import generate_track
        points = generate_track(seed=42, num_points=8)
        assert len(points) == 8
        assert all(isinstance(p, tuple) and len(p) == 2 for p in points)

    def test_interpolate_track_importable(self):
        from engine.track_gen import interpolate_track, generate_track
        control = generate_track(seed=42)
        track = interpolate_track(control, resolution=100)
        assert len(track) > len(control)
        assert all(isinstance(p, tuple) and len(p) == 2 for p in track)

    def test_compute_track_data_importable(self):
        from engine.track_gen import (
            compute_track_data, generate_track, interpolate_track,
        )
        control = generate_track(seed=42)
        track = interpolate_track(control, resolution=100)
        distances, curvatures, total_length = compute_track_data(track)
        assert len(distances) == len(track)
        assert len(curvatures) == len(track)
        assert total_length > 0

    def test_generate_track_deterministic(self):
        from engine.track_gen import generate_track
        a = generate_track(seed=99)
        b = generate_track(seed=99)
        assert a == b

    def test_generate_track_different_seeds(self):
        from engine.track_gen import generate_track
        a = generate_track(seed=1)
        b = generate_track(seed=2)
        assert a != b


# ── Cycle 2: Car loader spoke ───────────────────────────────────────────────

class TestCarLoader:
    """Car loading and validation lives in engine.car_loader."""

    def test_constants_importable(self):
        from engine.car_loader import STAT_BUDGET, STAT_FIELDS, REQUIRED_FIELDS
        assert STAT_BUDGET == 100
        assert "POWER" in STAT_FIELDS
        assert "CAR_NAME" in REQUIRED_FIELDS

    def test_load_car_valid(self, tmp_path):
        from engine.car_loader import load_car
        car_file = tmp_path / "test_car.py"
        car_file.write_text(
            'CAR_NAME = "TestCar"\n'
            'CAR_COLOR = "#FF0000"\n'
            'POWER = 20\nGRIP = 20\nWEIGHT = 20\nAERO = 20\nBRAKES = 20\n'
        )
        car = load_car(str(car_file))
        assert car["CAR_NAME"] == "TestCar"
        assert car["POWER"] == 20
        assert callable(car["strategy"])

    def test_load_car_rejects_over_budget(self, tmp_path):
        from engine.car_loader import load_car
        import pytest
        car_file = tmp_path / "over.py"
        car_file.write_text(
            'CAR_NAME = "Over"\n'
            'CAR_COLOR = "#FF0000"\n'
            'POWER = 30\nGRIP = 30\nWEIGHT = 30\nAERO = 30\nBRAKES = 30\n'
        )
        with pytest.raises(ValueError, match="budget"):
            load_car(str(car_file))

    def test_load_car_rejects_bad_color(self, tmp_path):
        from engine.car_loader import load_car
        import pytest
        car_file = tmp_path / "badcolor.py"
        car_file.write_text(
            'CAR_NAME = "Bad"\n'
            'CAR_COLOR = "not-a-color"\n'
            'POWER = 20\nGRIP = 20\nWEIGHT = 20\nAERO = 20\nBRAKES = 20\n'
        )
        with pytest.raises(ValueError, match="hex"):
            load_car(str(car_file))

    def test_load_car_rejects_negative_stat(self, tmp_path):
        from engine.car_loader import load_car
        import pytest
        car_file = tmp_path / "neg.py"
        car_file.write_text(
            'CAR_NAME = "Neg"\n'
            'CAR_COLOR = "#FF0000"\n'
            'POWER = -5\nGRIP = 20\nWEIGHT = 20\nAERO = 20\nBRAKES = 20\n'
        )
        with pytest.raises(ValueError, match="negative"):
            load_car(str(car_file))

    def test_load_all_cars(self, tmp_path):
        from engine.car_loader import load_all_cars
        for i in range(3):
            (tmp_path / f"car{i}.py").write_text(
                f'CAR_NAME = "Car{i}"\n'
                f'CAR_COLOR = "#FF000{i}"\n'
                f'POWER = 20\nGRIP = 20\nWEIGHT = 20\nAERO = 20\nBRAKES = 20\n'
            )
        # Underscore-prefixed files should be skipped
        (tmp_path / "_hidden.py").write_text('x = 1\n')
        cars = load_all_cars(str(tmp_path))
        assert len(cars) == 3


# ── Cycle 3: Simulation spoke ───────────────────────────────────────────────

class TestSimulation:
    """RaceSim class lives in engine.simulation."""

    def _make_cars(self):
        return [
            {
                "CAR_NAME": f"Car{i}", "CAR_COLOR": f"#FF000{i}",
                "POWER": 20, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
                "strategy": lambda s: {"throttle": 1.0, "boost": False, "tire_mode": "balanced"},
            }
            for i in range(3)
        ]

    def _make_track(self):
        from engine.track_gen import generate_track, interpolate_track
        control = generate_track(seed=42)
        return interpolate_track(control, resolution=500)

    def test_racesim_importable(self):
        from engine.simulation import RaceSim
        cars = self._make_cars()
        track = self._make_track()
        sim = RaceSim(cars, track, laps=1, seed=42)
        assert sim.tick == 0
        assert not sim.race_over

    def test_racesim_step(self):
        from engine.simulation import RaceSim
        cars = self._make_cars()
        track = self._make_track()
        sim = RaceSim(cars, track, laps=1, seed=42)
        sim.step()
        assert sim.tick == 1
        assert len(sim.history) == 1

    def test_racesim_run_completes(self):
        from engine.simulation import RaceSim
        cars = self._make_cars()
        track = self._make_track()
        sim = RaceSim(cars, track, laps=1, seed=42)
        results = sim.run(max_ticks=20000)
        assert len(results) == 3
        assert results[0]["position"] == 1

    def test_racesim_export_replay(self):
        from engine.simulation import RaceSim
        cars = self._make_cars()
        track = self._make_track()
        sim = RaceSim(cars, track, laps=1, seed=42, track_name="TestTrack")
        sim.run(max_ticks=20000)
        replay = sim.export_replay()
        assert "track" in replay
        assert "frames" in replay
        assert "results" in replay
        assert replay["track_name"] == "TestTrack"
        assert replay["laps"] == 1

    def test_racesim_track_name_default(self):
        from engine.simulation import RaceSim
        cars = self._make_cars()
        track = self._make_track()
        sim = RaceSim(cars, track, laps=1, seed=42)
        assert sim.track_name is None


# ── Cycle 4: Race runner spoke ──────────────────────────────────────────────

class TestRaceRunner:
    """run_race entry point lives in engine.race_runner."""

    def test_run_race_importable(self):
        from engine.race_runner import run_race
        assert callable(run_race)

    def test_run_race_produces_results(self, tmp_path):
        from engine.race_runner import run_race
        # Create two valid cars
        for i in range(2):
            (tmp_path / f"car{i}.py").write_text(
                f'CAR_NAME = "Car{i}"\n'
                f'CAR_COLOR = "#FF000{i}"\n'
                f'POWER = 20\nGRIP = 20\nWEIGHT = 20\nAERO = 20\nBRAKES = 20\n'
            )
        output = tmp_path / "replay.json"
        results = run_race(
            car_dir=str(tmp_path), laps=1, track_seed=42,
            output=str(output),
        )
        assert len(results) == 2
        assert output.exists()

    def test_run_race_too_few_cars(self, tmp_path):
        from engine.race_runner import run_race
        import pytest
        (tmp_path / "solo.py").write_text(
            'CAR_NAME = "Solo"\nCAR_COLOR = "#FF0000"\n'
            'POWER = 20\nGRIP = 20\nWEIGHT = 20\nAERO = 20\nBRAKES = 20\n'
        )
        with pytest.raises(ValueError, match="at least 2"):
            run_race(car_dir=str(tmp_path), laps=1, output=str(tmp_path / "r.json"))


# ── Cycle 5: Hub re-exports (backward compat) ──────────────────────────────

class TestHubReExports:
    """engine/__init__.py re-exports the public API."""

    def test_import_run_race(self):
        from engine import run_race
        assert callable(run_race)

    def test_import_racesim(self):
        from engine import RaceSim
        assert RaceSim is not None

    def test_import_generate_track(self):
        from engine import generate_track
        assert callable(generate_track)

    def test_import_load_car(self):
        from engine import load_car
        assert callable(load_car)

    def test_import_load_all_cars(self):
        from engine import load_all_cars
        assert callable(load_all_cars)

    def test_import_constants(self):
        from engine import STAT_BUDGET, STAT_FIELDS, REQUIRED_FIELDS
        assert STAT_BUDGET == 100
        assert "POWER" in STAT_FIELDS
        assert "CAR_NAME" in REQUIRED_FIELDS

    def test_import_track_helpers(self):
        from engine import interpolate_track, compute_track_data
        assert callable(interpolate_track)
        assert callable(compute_track_data)


# ── Cycle 6: File size constraints ──────────────────────────────────────────

class TestFileSizes:
    """All module files must be under 400 lines."""

    def test_all_modules_under_400_lines(self):
        engine_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "engine",
        )
        assert os.path.isdir(engine_dir), "engine/ must be a directory (package)"
        for fname in os.listdir(engine_dir):
            if fname.endswith(".py"):
                fpath = os.path.join(engine_dir, fname)
                with open(fpath) as f:
                    line_count = sum(1 for _ in f)
                assert line_count <= 400, f"{fname} has {line_count} lines (limit 400)"

    def test_no_old_engine_py_module(self):
        """engine.py file should not exist as a module (replaced by package)."""
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        engine_py = os.path.join(project_root, "engine.py")
        assert not os.path.exists(engine_py), (
            "engine.py still exists as a file -- should be replaced by engine/ package"
        )
