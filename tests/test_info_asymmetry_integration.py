"""Sprint 12 integration gate — information asymmetry verification (T12.4)."""

import pathlib

import pytest

from engine.simulation import RaceSim
from engine.car_loader import load_all_cars
from engine.track_gen import interpolate_track
from engine.visibility import PRIVATE_FIELDS
from tracks import get_track

pytestmark = pytest.mark.smoke

CARS_DIR = str(pathlib.Path(__file__).resolve().parent.parent / "cars")


def _run_race(seed=42, laps=2):
    track_data = get_track("monza")
    track_points = interpolate_track(track_data["control_points"], resolution=500)
    cars = load_all_cars(CARS_DIR)
    sim = RaceSim(
        cars=cars, track_points=track_points, laps=laps, seed=seed,
        track_name="monza", real_length_m=track_data.get("real_length_m"),
        drs_zones=track_data.get("drs_zones", []),
    )
    # Capture strategy state from first car
    captured = {}
    original = cars[0]["strategy"]
    def spy(state):
        captured.update(state)
        return original(state)
    sim.cars[0]["strategy"] = spy
    sim.run()
    return sim, captured


class TestAsymmetryEnforced:
    def test_own_car_has_private_data(self):
        _, state = _run_race()
        assert "tire_wear" in state
        assert "fuel_remaining" in state
        assert "damage" in state
        assert "ers_energy" in state

    def test_opponent_info_no_private_data(self):
        _, state = _run_race()
        for opp in state.get("opponent_info", []):
            for field in PRIVATE_FIELDS:
                assert field not in opp, f"Private: {field}"

    def test_opponent_info_has_observable(self):
        _, state = _run_race()
        assert len(state.get("opponent_info", [])) >= 1
        opp = state["opponent_info"][0]
        assert "name" in opp
        assert "position" in opp
        assert "speed" in opp
        assert "tire_compound" in opp


class TestBackwardCompat:
    def test_existing_cars_still_work(self):
        sim, _ = _run_race(laps=2)
        results = sim.get_results()
        finished = [r for r in results if r["finished"]]
        assert len(finished) >= 3


class TestArchCompliance:
    def test_simulation_under_limits(self):
        lines = len(pathlib.Path("engine/simulation.py").read_text().splitlines())
        assert lines <= 400, f"simulation.py has {lines} lines"

    def test_simulation_function_count(self):
        text = pathlib.Path("engine/simulation.py").read_text()
        count = text.count("\n    def ") + text.count("\ndef ")
        assert count <= 15, f"simulation.py has {count} functions"

    def test_visibility_module_under_limits(self):
        lines = len(pathlib.Path("engine/visibility.py").read_text().splitlines())
        assert lines <= 60, f"visibility.py has {lines} lines"
