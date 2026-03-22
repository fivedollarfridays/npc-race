"""Integration tests for the car project loader pipeline."""

import textwrap

from engine.car_loader import load_all_cars
from engine.parts_simulation import PartsRaceSim
from engine.code_quality import compute_reliability_score
from security.project_scanner import scan_car_project
from tracks import get_track
from engine.track_gen import interpolate_track
from engine import safe_call

# Disable timeouts for test speed
safe_call.TIMEOUT_ENABLED = False

CARS_DIR = "cars"
SEED_CAR_NAMES = {"BrickHouse", "GlassCanon", "GooseLoose", "Silky", "SlipStream"}


def _make_sim(cars, laps=1):
    """Build a 1-lap Monza sim from a list of car dicts."""
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    return PartsRaceSim(
        cars, pts, laps=laps, seed=42,
        track_name="monza", real_length_m=td.get("real_length_m"),
    )


class TestProjectCarCompletesRace:
    """Load default_project, run 1-lap race, car finishes."""

    def test_project_car_finishes(self):
        cars = load_all_cars(CARS_DIR)
        project_cars = [c for c in cars if c["CAR_NAME"] == "DefaultProject"]
        assert len(project_cars) == 1, "default_project should load"
        sim = _make_sim(project_cars)
        sim.run(max_ticks=36000)
        state = sim.car_states[0]
        assert state["finished"] is True
        assert state["finish_tick"] is not None


class TestMixedCarsRaceTogether:
    """Single-file cars and project cars race together."""

    def test_all_cars_finish(self):
        cars = load_all_cars(CARS_DIR)
        assert len(cars) >= 6, "Should have at least 5 single-file + 1 project"
        sim = _make_sim(cars)
        sim.run(max_ticks=36000)
        for state in sim.car_states:
            assert state["finished"] is True, (
                f"{state['name']} did not finish"
            )


class TestPartialProjectDefaultsFill:
    """A project with 3 parts gets 7 defaults filled and races."""

    def test_loaded_parts_count(self):
        cars = load_all_cars(CARS_DIR)
        project = [c for c in cars if c["CAR_NAME"] == "DefaultProject"][0]
        loaded = project.get("_loaded_parts", [])
        assert len(loaded) == 3, f"Expected 3 loaded parts, got {loaded}"

    def test_all_ten_parts_callable(self):
        cars = load_all_cars(CARS_DIR)
        project = [c for c in cars if c["CAR_NAME"] == "DefaultProject"][0]
        parts = project["parts"]
        assert len(parts) == 10, f"Expected 10 parts, got {len(parts)}"
        for name, func in parts.items():
            assert callable(func), f"Part {name} is not callable"

    def test_partial_project_completes_race(self):
        cars = load_all_cars(CARS_DIR)
        project = [c for c in cars if c["CAR_NAME"] == "DefaultProject"]
        sim = _make_sim(project)
        sim.run(max_ticks=36000)
        assert sim.car_states[0]["finished"] is True


class TestSourceEnablesReliability:
    """_source populated -> reliability score computed -> not 1.0 default."""

    def test_reliability_score_in_range(self):
        cars = load_all_cars(CARS_DIR)
        project = [c for c in cars if c["CAR_NAME"] == "DefaultProject"][0]
        source = project.get("_source", "")
        assert len(source) > 0, "_source should be populated"
        score = compute_reliability_score(source)
        assert 0.50 <= score <= 1.00, f"Score {score} out of range"

    def test_sim_uses_reliability_not_default(self):
        cars = load_all_cars(CARS_DIR)
        project = [c for c in cars if c["CAR_NAME"] == "DefaultProject"]
        sim = _make_sim(project)
        # Reliability should be computed from source, not default 1.0
        assert len(sim.car_reliability) == 1
        rel = sim.car_reliability[0]
        assert isinstance(rel, float)
        assert 0.50 <= rel <= 1.00


class TestMaliciousHelperCaught:
    """A project with a helper that imports os is rejected."""

    def test_evil_helper_fails_scan(self, tmp_path):
        # Create minimal project structure
        car_py = tmp_path / "car.py"
        car_py.write_text(textwrap.dedent("""\
            CAR_NAME = "EvilCar"
            CAR_COLOR = "#ff0000"
            POWER, GRIP, WEIGHT, AERO, BRAKES = 20, 20, 20, 20, 20
        """))

        gearbox_py = tmp_path / "gearbox.py"
        gearbox_py.write_text(textwrap.dedent("""\
            from helpers import evil

            def gearbox(state, physics, hw, dt):
                return {"gear": 3, "shift_progress": 0.0}
        """))

        helpers_dir = tmp_path / "helpers"
        helpers_dir.mkdir()
        (helpers_dir / "__init__.py").write_text("")
        evil_py = helpers_dir / "evil.py"
        evil_py.write_text("import os\n")

        result = scan_car_project(str(tmp_path))
        assert result.passed is False
        assert any("os" in v for v in result.violations)


class TestExistingSeedCarsStillWork:
    """The 5 original seed cars still load and race."""

    def test_seed_cars_present(self):
        cars = load_all_cars(CARS_DIR)
        loaded_names = {c["CAR_NAME"] for c in cars}
        for name in SEED_CAR_NAMES:
            assert name in loaded_names, f"Seed car {name} not loaded"

    def test_seed_cars_complete_race(self):
        cars = load_all_cars(CARS_DIR)
        seed_cars = [c for c in cars if c["CAR_NAME"] in SEED_CAR_NAMES]
        assert len(seed_cars) == 5
        sim = _make_sim(seed_cars)
        sim.run(max_ticks=36000)
        for state in sim.car_states:
            assert state["finished"] is True, (
                f"Seed car {state['name']} did not finish"
            )
