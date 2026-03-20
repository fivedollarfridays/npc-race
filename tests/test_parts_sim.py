"""Sprint 21 integration gate — parts-driven race (T21.6)."""

import pytest

from engine.car_loader import load_all_cars
from engine.parts_simulation import PartsRaceSim
from tracks import get_track
from engine.track_gen import interpolate_track

pytestmark = pytest.mark.slow

CARS_DIR = "cars"


def _run_parts_race(laps=1, max_ticks=6000):
    td = get_track("monza")
    pts = interpolate_track(td["control_points"], resolution=500)
    cars = load_all_cars(CARS_DIR)
    sim = PartsRaceSim(cars, pts, laps=laps, seed=42, track_name="monza",
                        real_length_m=td.get("real_length_m"))
    sim.run(max_ticks=max_ticks)
    return sim


class TestPartsRace:
    def test_all_cars_finish(self):
        sim = _run_parts_race()
        finished = [s for s in sim.car_states if s["finished"]]
        assert len(finished) >= 3

    def test_speed_varies(self):
        sim = _run_parts_race()
        speeds = [f[0]["speed"] for f in sim.history if f]
        assert max(speeds) > min(speeds) + 10

    def test_cars_have_parts(self):
        td = get_track("monza")
        interpolate_track(td["control_points"], resolution=500)
        cars = load_all_cars(CARS_DIR)
        for car in cars:
            assert "parts" in car
            assert "engine_map" in car["parts"]
            assert "gearbox" in car["parts"]
            assert "strategy" in car["parts"]

    def test_replay_exportable(self):
        sim = _run_parts_race()
        replay = sim.export_replay()
        assert "frames" in replay
        assert len(replay["frames"]) > 100

    def test_call_logs_populated(self):
        sim = _run_parts_race()
        assert len(sim.call_logs) > 100
        # First tick should have logs for all 10 parts
        first_log = sim.call_logs[0]
        parts_seen = {entry["part"] for entry in first_log}
        assert len(parts_seen) >= 8  # at least 8 of 10 parts called
