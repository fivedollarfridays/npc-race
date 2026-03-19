"""Sprint 10: Weather system integration tests (T10.3)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.simulation import RaceSim
from engine.track_gen import generate_track, interpolate_track


def _make_cars(n=2):
    return [
        {
            "CAR_NAME": f"Car{i}", "CAR_COLOR": f"#FF000{i}",
            "POWER": 20, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
            "strategy": lambda s: {"throttle": 1.0, "boost": False, "tire_mode": "balanced"},
        }
        for i in range(n)
    ]


def _sim(laps=1, n_cars=2):
    track = interpolate_track(generate_track(seed=42), resolution=500)
    return RaceSim(_make_cars(n_cars), track, laps=laps, seed=42)


class TestWeatherIntegration:
    """Weather model wired into simulation."""

    def test_weather_state_initialized(self):
        sim = _sim()
        assert hasattr(sim, "weather")
        assert sim.weather["state"] == "dry"
        assert sim.weather["wetness"] == 0.0

    def test_wetness_in_strategy_state(self):
        sim = _sim()
        from engine.replay import _compute_positions
        positions = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], positions)
        assert "track_wetness" in ss
        assert isinstance(ss["track_wetness"], float)

    def test_forecast_in_strategy_state(self):
        sim = _sim()
        from engine.replay import _compute_positions
        positions = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], positions)
        assert "weather_forecast" in ss
        assert isinstance(ss["weather_forecast"], list)

    def test_weather_state_in_strategy(self):
        sim = _sim()
        from engine.replay import _compute_positions
        positions = _compute_positions(sim.states)
        ss = sim.build_strategy_state(sim.states[0], positions)
        assert "weather_state" in ss
        assert ss["weather_state"] == "dry"

    def test_replay_has_wetness(self):
        sim = _sim()
        sim.run()
        replay = sim.export_replay()
        for car in replay["frames"][0]:
            assert "track_wetness" in car
            assert isinstance(car["track_wetness"], (int, float))
