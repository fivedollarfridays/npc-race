"""Verify replay frames contain drama engine fields (T9.6)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.simulation import RaceSim
from engine.track_gen import generate_track, interpolate_track


def _make_cars(n=3):
    """Create n minimal test cars."""
    return [
        {
            "CAR_NAME": f"Car{i}", "CAR_COLOR": f"#FF000{i}",
            "POWER": 20, "GRIP": 20, "WEIGHT": 20, "AERO": 20, "BRAKES": 20,
            "strategy": lambda s: {"throttle": 1.0, "boost": False, "tire_mode": "balanced"},
        }
        for i in range(n)
    ]


def _make_sim(laps=1, n_cars=2):
    """Create a simple simulation for testing."""
    track = interpolate_track(generate_track(seed=42), resolution=500)
    return RaceSim(_make_cars(n_cars), track, laps=laps, seed=42)


class TestDramaReplayFields:
    """Every replay frame contains drama engine fields."""

    def test_replay_has_damage_field(self):
        """Every replay frame has 'damage' float."""
        sim = _make_sim()
        sim.run()
        replay = sim.export_replay()
        for frame in replay["frames"][:5]:
            for car in frame:
                assert "damage" in car
                assert isinstance(car["damage"], (int, float))

    def test_replay_has_in_spin_field(self):
        """Every replay frame has 'in_spin' bool."""
        sim = _make_sim()
        sim.run()
        replay = sim.export_replay()
        for frame in replay["frames"][:5]:
            for car in frame:
                assert "in_spin" in car
                assert isinstance(car["in_spin"], bool)

    def test_replay_has_safety_car_field(self):
        """Every replay frame has 'safety_car' bool."""
        sim = _make_sim()
        sim.run()
        replay = sim.export_replay()
        for frame in replay["frames"][:5]:
            for car in frame:
                assert "safety_car" in car
                assert isinstance(car["safety_car"], bool)
