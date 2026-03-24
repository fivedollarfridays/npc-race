"""Sprint 11 integration gate — ERS + brake temp verification (T11.6)."""

import pathlib

import pytest

from engine.simulation import RaceSim
from engine.car_loader import load_all_cars
from engine.track_gen import interpolate_track
from engine.brake_model import get_brake_efficiency
from engine.ers_model import get_ers_speed_bonus
from tracks import get_track

pytestmark = pytest.mark.smoke

CARS_DIR = str(pathlib.Path(__file__).resolve().parent.parent / "cars")


def _run_race(seed=42, laps=3):
    track_data = get_track("monza")
    track_points = interpolate_track(track_data["control_points"], resolution=500)
    cars = load_all_cars(CARS_DIR)
    sim = RaceSim(
        cars=cars, track_points=track_points, laps=laps, seed=seed,
        track_name="monza", real_length_m=track_data.get("real_length_m"),
        drs_zones=track_data.get("drs_zones", []),
    )
    sim.run()
    return sim, sim.export_replay()


class TestERSIntegration:
    def test_ers_energy_in_replay(self):
        _, replay = _run_race(seed=42, laps=2)
        for car in replay["frames"][0]:
            assert "ers_energy" in car
            assert isinstance(car["ers_energy"], (int, float))

    def test_ers_depletes_during_race(self):
        _, replay = _run_race(seed=42, laps=2)
        found = any(
            car.get("ers_energy", 4.0) < 3.5
            for frame in replay["frames"][100:] for car in frame
        )
        assert found, "ERS never depleted in race"

    def test_ers_mode_affects_speed(self):
        ers = {"energy": 4.0, "lap_deploy": 0.0, "lap_harvest": 0.0}
        assert get_ers_speed_bonus(ers, "attack") > get_ers_speed_bonus(ers, "harvest")


class TestBrakeTempIntegration:
    def test_brake_temp_in_replay(self):
        _, replay = _run_race(seed=42, laps=2)
        for car in replay["frames"][0]:
            assert "brake_temp" in car
            assert isinstance(car["brake_temp"], (int, float))

    def test_brakes_heat_during_race(self):
        _, replay = _run_race(seed=42, laps=2)
        max_temp = max(
            car.get("brake_temp", 20.0)
            for frame in replay["frames"] for car in frame
        )
        assert max_temp > 20.0, f"Brakes never heated: {max_temp}"

    def test_brake_fade_reduces_braking(self):
        assert get_brake_efficiency(800.0) < 1.0
        assert get_brake_efficiency(400.0) == 1.0


class TestArchCompliance:
    def test_simulation_under_limits(self):
        lines = len(pathlib.Path("engine/simulation.py").read_text().splitlines())
        assert lines <= 400, f"simulation.py has {lines} lines"

    def test_simulation_function_count(self):
        text = pathlib.Path("engine/simulation.py").read_text()
        count = text.count("\n    def ") + text.count("\ndef ")
        assert count <= 15, f"simulation.py has {count} functions"

    def test_new_modules_under_limits(self):
        limits = {
            "engine/ers_model.py": 100,
            "engine/brake_model.py": 90,
            "engine/drama.py": 80,
        }
        for path, limit in limits.items():
            lines = len(pathlib.Path(path).read_text().splitlines())
            assert lines <= limit, f"{path} has {lines} lines (limit: {limit})"
